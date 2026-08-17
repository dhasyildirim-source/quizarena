"""Core: DB connection, auth, constants, and game math for QuizArena."""
import os
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
SESSION_DATA_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


# ---------------- Rewards / progression ----------------
XP_REWARDS = {
    "matchWin": 50, "matchLoss": 20, "correctAnswer": 3,
    "dailyQuestComplete": 30, "weeklyQuestComplete": 100,
    "achievementUnlock": 50, "loginStreak7": 100, "loginStreak30": 500,
}
COIN_REWARDS = {
    "matchWin": 100, "matchLoss": 30,
    "dailyQuestComplete": 50, "weeklyQuestComplete": 200,
    "rewardedAd": 50, "loginStreak3": 50, "loginStreak7": 150,
}

LEAGUES = [
    {"tier": "BRONZE", "min": 0, "max": 999},
    {"tier": "SILVER", "min": 1000, "max": 1499},
    {"tier": "GOLD", "min": 1500, "max": 1999},
    {"tier": "PLATINUM", "min": 2000, "max": 2499},
    {"tier": "DIAMOND", "min": 2500, "max": 2999},
    {"tier": "MASTER", "min": 3000, "max": 3499},
    {"tier": "CHAMPION", "min": 3500, "max": 10 ** 9},
]

CATEGORIES = [
    "HISTORY", "GEOGRAPHY", "SCIENCE", "TECHNOLOGY", "SPORTS", "ART_CULTURE",
    "MUSIC", "CINEMA", "LITERATURE", "MYTHOLOGY", "FOOD", "NATURE",
    "POLITICS", "ECONOMY", "GAMING", "ANIMATION",
]


def xp_for_level(level: int) -> int:
    return math.floor(100 * math.pow(1.15, level - 1))


def league_for_points(points: int) -> dict:
    for lg in LEAGUES:
        if lg["min"] <= points <= lg["max"]:
            return lg
    return LEAGUES[0]


def calculate_rank_change(winner_rp: int, loser_rp: int):
    K = 32
    expected = 1 / (1 + math.pow(10, (loser_rp - winner_rp) / 400))
    return {
        "winnerGain": round(K * (1 - expected)),
        "loserLoss": round(K * expected),
    }


def speed_points(time_ms: int, time_limit_ms: int = 20000) -> int:
    """Correct-answer points with speed bonus (10..15)."""
    pts = math.floor(10 + 5 * (1 - min(time_ms, time_limit_ms) / time_limit_ms))
    return max(10, min(15, pts))


def apply_xp(user: dict, xp_gain: int):
    """Return (new_level, new_current_xp, total_xp, leveled_up)."""
    level = user.get("level", 1)
    current = user.get("currentXP", 0) + xp_gain
    total = user.get("totalXP", 0) + xp_gain
    leveled = False
    while current >= xp_for_level(level):
        current -= xp_for_level(level)
        level += 1
        leveled = True
    return level, current, total, leveled


PUBLIC_USER_FIELDS = {
    "_id": 0,
}


def public_user(user: dict) -> dict:
    """Strip internal fields for API responses."""
    if not user:
        return user
    u = {k: v for k, v in user.items() if k != "_id"}
    for key in ("lastLoginDate", "premiumExpiresAt", "createdAt", "lastSeenAt"):
        if isinstance(u.get(key), datetime):
            u[key] = iso(u[key])
    return u


# ---------------- Auth ----------------
async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1].strip()
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    expires = session.get("expires_at")
    if isinstance(expires, datetime):
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now_utc():
            raise HTTPException(status_code=401, detail="Session expired")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def fetch_session_data(session_id: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as hc:
        resp = await hc.get(SESSION_DATA_URL, headers={"X-Session-ID": session_id})
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session id")
    return resp.json()


async def ensure_indexes():
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.user_sessions.create_index("session_token", unique=True)
    await db.user_sessions.create_index("user_id")
    await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
    await db.questions.create_index("category")
    await db.matches.create_index("createdAt")
