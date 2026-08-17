"""QuizArena FastAPI server: REST API + WebSocket real-time game engine."""
import asyncio
import logging
import random
import re
import uuid
from datetime import datetime, timezone

from fastapi import (FastAPI, APIRouter, Depends, HTTPException, Query,
                     WebSocket, WebSocketDisconnect)
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

import core
import ai
from core import (db, now_utc, iso, public_user, get_current_user, ensure_indexes,
                  fetch_session_data, league_for_points, calculate_rank_change,
                  speed_points, apply_xp, xp_for_level, XP_REWARDS, COIN_REWARDS,
                  LEAGUES)
from seed import seed_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quizarena")

app = FastAPI(title="QuizArena")
api = APIRouter(prefix="/api")

QUEST_METRIC = {
    "quest_d1": "correct", "quest_d2": "win", "quest_d3": "science",
    "quest_w1": "match", "quest_w2": "private_room", "quest_w3": "ranked_win",
}


# ---------------- helpers ----------------
def slugify(text: str) -> str:
    text = (text or "user").lower()
    text = re.sub(r"[^a-z0-9]", "", text)
    return text[:12] or "user"


async def unique_username(base: str) -> str:
    base = slugify(base)
    candidate = base
    while await db.users.find_one({"username": candidate}):
        candidate = f"{base}{random.randint(10, 9999)}"
    return candidate


async def create_user(email: str, name: str, picture: str | None) -> dict:
    uid = f"user_{uuid.uuid4().hex[:12]}"
    username = await unique_username((name or email.split("@")[0]).replace(" ", ""))
    user = {
        "user_id": uid, "username": username, "displayName": name or username,
        "email": email, "googleId": uid, "avatarUrl": picture,
        "gender": "UNSPECIFIED", "level": 1, "currentXP": 0, "totalXP": 0,
        "coins": 100, "rankPoints": 1000, "isPremium": False, "premiumExpiresAt": None,
        "activeTitle": None, "activeFrameId": None, "activeCardId": None,
        "totalMatches": 0, "wins": 0, "losses": 0, "currentStreak": 0,
        "longestStreak": 0, "loginStreak": 0, "lastLoginDate": None,
        "countryCode": "TR", "isBot": False, "correctAnswersTotal": 0,
        "itemsPurchased": 0, "friendsCount": 0,
        "createdAt": now_utc(), "lastSeenAt": now_utc(),
    }
    await db.users.insert_one(dict(user))
    return user


async def assign_quests(user_id: str):
    quests = await db.quests.find({"isActive": True}, {"_id": 0}).to_list(50)
    for q in quests:
        existing = await db.user_quests.find_one({"userId": user_id, "questId": q["id"]})
        if not existing:
            await db.user_quests.insert_one({
                "id": f"uq_{uuid.uuid4().hex[:10]}", "userId": user_id,
                "questId": q["id"], "progress": 0, "status": "ACTIVE",
                "assignedAt": now_utc(), "expiresAt": None,
            })


async def update_quest_progress(user_id: str, events: dict):
    await assign_quests(user_id)
    quests = await db.quests.find({"isActive": True}, {"_id": 0}).to_list(50)
    for q in quests:
        metric = QUEST_METRIC.get(q["id"])
        inc = events.get(metric, 0) if metric else 0
        if inc <= 0:
            continue
        uq = await db.user_quests.find_one({"userId": user_id, "questId": q["id"]}, {"_id": 0})
        if not uq or uq["status"] not in ("ACTIVE",):
            continue
        new_progress = min(q["target"], uq["progress"] + inc)
        new_status = "COMPLETED" if new_progress >= q["target"] else "ACTIVE"
        await db.user_quests.update_one(
            {"userId": user_id, "questId": q["id"]},
            {"$set": {"progress": new_progress, "status": new_status}},
        )


async def check_achievements(user: dict) -> list[dict]:
    """Evaluate and unlock achievements. Returns newly unlocked achievement docs."""
    uid = user["user_id"]
    unlocked_keys = set()
    async for ua in db.user_achievements.find({"userId": uid}, {"_id": 0}):
        unlocked_keys.add(ua["achievementId"])
    achievements = await db.achievements.find({}, {"_id": 0}).to_list(50)
    newly = []
    conds = {
        "ach_first_blood": user.get("wins", 0) >= 1,
        "ach_wise": user.get("correctAnswersTotal", 0) >= 100,
        "ach_legend": user.get("wins", 0) >= 50,
        "ach_streak_killer": user.get("longestStreak", 0) >= 10,
        "ach_collector": user.get("itemsPurchased", 0) >= 10,
        "ach_social_butterfly": user.get("friendsCount", 0) >= 10,
        "ach_speed_demon": user.get("speedDemon", False),
    }
    for ach in achievements:
        if ach["id"] in unlocked_keys:
            continue
        if conds.get(ach["id"]):
            await db.user_achievements.insert_one({
                "id": f"ua_{uuid.uuid4().hex[:10]}", "userId": uid,
                "achievementId": ach["id"], "unlockedAt": now_utc(),
            })
            await db.users.update_one({"user_id": uid}, {"$inc": {
                "coins": ach["coinReward"], "totalXP": ach["xpReward"], "currentXP": ach["xpReward"]}})
            newly.append(ach)
    return newly


# ==================== AUTH ====================
class SessionIn(BaseModel):
    session_id: str


@api.post("/auth/session")
async def auth_session(body: SessionIn):
    data = await fetch_session_data(body.session_id)
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="No email in session")
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        user = await create_user(email, data.get("name", ""), data.get("picture"))
    session_token = data.get("session_token") or uuid.uuid4().hex
    from datetime import timedelta
    await db.user_sessions.update_one(
        {"session_token": session_token},
        {"$set": {"session_token": session_token, "user_id": user["user_id"],
                  "expires_at": now_utc() + timedelta(days=7), "created_at": now_utc()}},
        upsert=True,
    )
    return {"session_token": session_token, "user": public_user(user)}


@api.get("/auth/me")
async def auth_me(user: dict = Depends(get_current_user)):
    # login streak update
    today = now_utc().date()
    last = user.get("lastLoginDate")
    streak = user.get("loginStreak", 0)
    if isinstance(last, datetime):
        last_date = last.date()
        if last_date == today:
            pass
        elif (today - last_date).days == 1:
            streak += 1
        else:
            streak = 1
    else:
        streak = 1
    if not isinstance(last, datetime) or last.date() != today:
        await db.users.update_one({"user_id": user["user_id"]},
                                  {"$set": {"loginStreak": streak, "lastLoginDate": now_utc(),
                                            "lastSeenAt": now_utc()}})
        user["loginStreak"] = streak
    await assign_quests(user["user_id"])
    return public_user(user)


@api.post("/auth/logout")
async def auth_logout(authorization: str = Query(default=None), user: dict = Depends(get_current_user)):
    await db.user_sessions.delete_many({"user_id": user["user_id"]})
    return {"ok": True}


# ==================== USERS ====================
class UpdateMe(BaseModel):
    displayName: str | None = None
    gender: str | None = None
    avatarUrl: str | None = None


@api.get("/users/me")
async def users_me(user: dict = Depends(get_current_user)):
    return public_user(user)


@api.put("/users/me")
async def update_me(body: UpdateMe, user: dict = Depends(get_current_user)):
    updates = {}
    if body.displayName is not None:
        mod = await ai.moderate_content(body.displayName)
        if not mod["safe"]:
            raise HTTPException(status_code=400, detail="İsim uygunsuz içerik barındırıyor")
        updates["displayName"] = body.displayName
    if body.gender in ("MALE", "FEMALE", "UNSPECIFIED"):
        updates["gender"] = body.gender
    if body.avatarUrl is not None:
        updates["avatarUrl"] = body.avatarUrl
    if updates:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": updates})
    fresh = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return public_user(fresh)


@api.get("/users/search")
async def users_search(q: str, user: dict = Depends(get_current_user)):
    cursor = db.users.find({"username": {"$regex": re.escape(q), "$options": "i"},
                            "isBot": {"$ne": True}}, {"_id": 0}).limit(20)
    return [public_user(u) for u in await cursor.to_list(20)]


@api.get("/users/{uid}")
async def user_public(uid: str, user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"user_id": uid}, {"_id": 0})
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return public_user(u)


# ==================== GAME MODES ====================
@api.get("/modes")
async def get_modes(user: dict = Depends(get_current_user)):
    modes = await db.game_modes.find({}, {"_id": 0}).to_list(50)
    for m in modes:
        m["activePlayers"] = random.randint(120, 4800)
        m["locked"] = user.get("level", 1) < m.get("minLevel", 1)
    return modes


# ==================== SHOP ====================
@api.get("/shop")
async def get_shop(user: dict = Depends(get_current_user)):
    items = await db.shop_items.find({"isActive": True}, {"_id": 0}).to_list(100)
    owned = set()
    async for ui in db.user_items.find({"userId": user["user_id"]}, {"_id": 0}):
        owned.add(ui["itemId"])
    for it in items:
        it["owned"] = it["id"] in owned
        it["equipped"] = user.get("activeFrameId") == it["id"] or user.get("activeCardId") == it["id"] or user.get("activeTitle") == it["id"]
    return items


@api.get("/shop/inventory")
async def get_inventory(user: dict = Depends(get_current_user)):
    owned = []
    async for ui in db.user_items.find({"userId": user["user_id"]}, {"_id": 0}):
        item = await db.shop_items.find_one({"id": ui["itemId"]}, {"_id": 0})
        if item:
            item["equippedAt"] = iso(ui.get("equippedAt"))
            owned.append(item)
    return owned


@api.post("/shop/buy/{item_id}")
async def buy_item(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.shop_items.find_one({"id": item_id, "isActive": True}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    if await db.user_items.find_one({"userId": user["user_id"], "itemId": item_id}):
        raise HTTPException(status_code=400, detail="Bu ürüne zaten sahipsin")
    # atomic coin deduction
    res = await db.users.update_one(
        {"user_id": user["user_id"], "coins": {"$gte": item["coinPrice"]}},
        {"$inc": {"coins": -item["coinPrice"], "itemsPurchased": 1}},
    )
    if res.modified_count == 0:
        raise HTTPException(status_code=400, detail="Yetersiz altın")
    await db.user_items.insert_one({
        "id": f"ui_{uuid.uuid4().hex[:10]}", "userId": user["user_id"],
        "itemId": item_id, "equippedAt": None, "createdAt": now_utc(),
    })
    fresh = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    await check_achievements(fresh)
    fresh = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {"ok": True, "coins": fresh["coins"]}


@api.post("/shop/equip/{item_id}")
async def equip_item(item_id: str, user: dict = Depends(get_current_user)):
    owned = await db.user_items.find_one({"userId": user["user_id"], "itemId": item_id})
    if not owned:
        raise HTTPException(status_code=400, detail="Bu ürüne sahip değilsin")
    item = await db.shop_items.find_one({"id": item_id}, {"_id": 0})
    field_map = {"FRAME": "activeFrameId", "CARD": "activeCardId", "TITLE": "activeTitle"}
    field = field_map.get(item["type"], "activeFrameId")
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {field: item_id}})
    await db.user_items.update_one({"userId": user["user_id"], "itemId": item_id},
                                   {"$set": {"equippedAt": now_utc()}})
    fresh = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return public_user(fresh)


# ==================== LEADERBOARD ====================
def _lb_entry(u: dict, rank: int) -> dict:
    return {
        "rank": rank, "user_id": u["user_id"], "username": u["username"],
        "displayName": u["displayName"], "avatarUrl": u.get("avatarUrl"),
        "rankPoints": u.get("rankPoints", 1000), "level": u.get("level", 1),
        "league": league_for_points(u.get("rankPoints", 1000))["tier"],
        "wins": u.get("wins", 0),
    }


@api.get("/leaderboard/global")
async def leaderboard_global(period: str = "weekly", user: dict = Depends(get_current_user)):
    users = await db.users.find({}, {"_id": 0}).sort("rankPoints", -1).limit(100).to_list(100)
    return [_lb_entry(u, i + 1) for i, u in enumerate(users)]


@api.get("/leaderboard/country/{code}")
async def leaderboard_country(code: str, user: dict = Depends(get_current_user)):
    users = await db.users.find({"countryCode": code.upper()}, {"_id": 0}).sort("rankPoints", -1).limit(100).to_list(100)
    return [_lb_entry(u, i + 1) for i, u in enumerate(users)]


@api.get("/leaderboard/friends")
async def leaderboard_friends(user: dict = Depends(get_current_user)):
    friend_ids = await _get_friend_ids(user["user_id"])
    friend_ids.append(user["user_id"])
    users = await db.users.find({"user_id": {"$in": friend_ids}}, {"_id": 0}).sort("rankPoints", -1).to_list(100)
    return [_lb_entry(u, i + 1) for i, u in enumerate(users)]


# ==================== QUESTS ====================
@api.get("/quests")
async def get_quests(user: dict = Depends(get_current_user)):
    await assign_quests(user["user_id"])
    quests = await db.quests.find({"isActive": True}, {"_id": 0}).to_list(50)
    result = []
    for q in quests:
        uq = await db.user_quests.find_one({"userId": user["user_id"], "questId": q["id"]}, {"_id": 0})
        result.append({**q, "progress": uq["progress"] if uq else 0,
                       "status": uq["status"] if uq else "ACTIVE"})
    return result


@api.post("/quests/{quest_id}/claim")
async def claim_quest(quest_id: str, user: dict = Depends(get_current_user)):
    uq = await db.user_quests.find_one({"userId": user["user_id"], "questId": quest_id}, {"_id": 0})
    quest = await db.quests.find_one({"id": quest_id}, {"_id": 0})
    if not uq or not quest:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    if uq["status"] != "COMPLETED":
        raise HTTPException(status_code=400, detail="Görev henüz tamamlanmadı")
    await db.user_quests.update_one({"userId": user["user_id"], "questId": quest_id},
                                    {"$set": {"status": "CLAIMED"}})
    fresh = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    level, current, total, leveled = apply_xp(fresh, quest["xpReward"])
    await db.users.update_one({"user_id": user["user_id"]}, {
        "$inc": {"coins": quest["coinReward"]},
        "$set": {"level": level, "currentXP": current, "totalXP": total}})
    fresh = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {"ok": True, "coinReward": quest["coinReward"], "xpReward": quest["xpReward"],
            "user": public_user(fresh)}


# ==================== ACHIEVEMENTS ====================
@api.get("/achievements")
async def get_achievements(user: dict = Depends(get_current_user)):
    achs = await db.achievements.find({}, {"_id": 0}).to_list(50)
    unlocked = {}
    async for ua in db.user_achievements.find({"userId": user["user_id"]}, {"_id": 0}):
        unlocked[ua["achievementId"]] = iso(ua["unlockedAt"])
    for a in achs:
        a["unlocked"] = a["id"] in unlocked
        a["unlockedAt"] = unlocked.get(a["id"])
    return achs


# ==================== SEASON / LEAGUES ====================
@api.get("/season/current")
async def season_current(user: dict = Depends(get_current_user)):
    s = await db.seasons.find_one({"isActive": True}, {"_id": 0})
    if s:
        s["startDate"] = iso(s["startDate"])
        s["endDate"] = iso(s["endDate"])
    return s or {}


@api.get("/season/battlepass")
async def season_battlepass(user: dict = Depends(get_current_user)):
    tiers = []
    for i in range(1, 21):
        tiers.append({
            "tier": i, "requiredXP": i * 500,
            "freeReward": {"type": "coins", "amount": 50 * i},
            "premiumReward": {"type": "item" if i % 5 == 0 else "coins",
                              "amount": 100 * i},
            "unlocked": user.get("totalXP", 0) >= i * 500,
        })
    return {"currentXP": user.get("totalXP", 0), "tiers": tiers,
            "isPremium": user.get("isPremium", False)}


@api.get("/leagues/current")
async def leagues_current(user: dict = Depends(get_current_user)):
    rp = user.get("rankPoints", 1000)
    lg = league_for_points(rp)
    rank = await db.users.count_documents({"rankPoints": {"$gt": rp}}) + 1
    return {"league": lg["tier"], "rankPoints": rp, "min": lg["min"],
            "max": lg["max"] if lg["max"] < 10 ** 9 else None, "globalRank": rank,
            "leagues": LEAGUES}


# ==================== FRIENDS ====================
async def _get_friend_ids(user_id: str) -> list[str]:
    ids = []
    async for f in db.friendships.find({"status": "ACCEPTED", "$or": [
            {"senderId": user_id}, {"receiverId": user_id}]}, {"_id": 0}):
        ids.append(f["receiverId"] if f["senderId"] == user_id else f["senderId"])
    return ids


@api.get("/friends")
async def get_friends(user: dict = Depends(get_current_user)):
    ids = await _get_friend_ids(user["user_id"])
    friends = await db.users.find({"user_id": {"$in": ids}}, {"_id": 0}).to_list(200)
    return [{**_lb_entry(f, 0), "online": random.random() > 0.5} for f in friends]


@api.get("/friends/requests")
async def friend_requests(user: dict = Depends(get_current_user)):
    reqs = await db.friendships.find({"receiverId": user["user_id"], "status": "PENDING"}, {"_id": 0}).to_list(100)
    out = []
    for r in reqs:
        sender = await db.users.find_one({"user_id": r["senderId"]}, {"_id": 0})
        if sender:
            out.append({"requestId": r["id"], "sender": _lb_entry(sender, 0)})
    return out


@api.post("/friends/request/{target_id}")
async def send_friend_request(target_id: str, user: dict = Depends(get_current_user)):
    if target_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Kendine istek gönderemezsin")
    target = await db.users.find_one({"user_id": target_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    existing = await db.friendships.find_one({"$or": [
        {"senderId": user["user_id"], "receiverId": target_id},
        {"senderId": target_id, "receiverId": user["user_id"]}]})
    if existing:
        raise HTTPException(status_code=400, detail="İstek zaten mevcut")
    fid = f"fr_{uuid.uuid4().hex[:10]}"
    await db.friendships.insert_one({
        "id": fid, "senderId": user["user_id"], "receiverId": target_id,
        "status": "PENDING", "createdAt": now_utc()})
    # bots auto-accept
    if target.get("isBot"):
        await db.friendships.update_one({"id": fid}, {"$set": {"status": "ACCEPTED"}})
        await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"friendsCount": 1}})
    return {"ok": True, "requestId": fid}


@api.put("/friends/request/{request_id}")
async def respond_friend_request(request_id: str, action: str, user: dict = Depends(get_current_user)):
    fr = await db.friendships.find_one({"id": request_id, "receiverId": user["user_id"]}, {"_id": 0})
    if not fr:
        raise HTTPException(status_code=404, detail="İstek bulunamadı")
    status = "ACCEPTED" if action == "accept" else "REJECTED"
    await db.friendships.update_one({"id": request_id}, {"$set": {"status": status}})
    if status == "ACCEPTED":
        await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"friendsCount": 1}})
        await db.users.update_one({"user_id": fr["senderId"]}, {"$inc": {"friendsCount": 1}})
        fresh = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
        await check_achievements(fresh)
    return {"ok": True, "status": status}


@api.delete("/friends/{target_id}")
async def remove_friend(target_id: str, user: dict = Depends(get_current_user)):
    await db.friendships.delete_many({"$or": [
        {"senderId": user["user_id"], "receiverId": target_id},
        {"senderId": target_id, "receiverId": user["user_id"]}]})
    await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"friendsCount": -1}})
    return {"ok": True}


# ==================== MESSAGES ====================
class MessageIn(BaseModel):
    content: str


async def _are_friends(a: str, b: str) -> bool:
    f = await db.friendships.find_one({"status": "ACCEPTED", "$or": [
        {"senderId": a, "receiverId": b}, {"senderId": b, "receiverId": a}]})
    return f is not None


@api.get("/messages/{other_id}")
async def get_messages(other_id: str, user: dict = Depends(get_current_user)):
    msgs = await db.messages.find({"$or": [
        {"senderId": user["user_id"], "receiverId": other_id},
        {"senderId": other_id, "receiverId": user["user_id"]}]}, {"_id": 0}).sort("createdAt", 1).to_list(200)
    for m in msgs:
        m["createdAt"] = iso(m["createdAt"])
    return msgs


@api.post("/messages/{other_id}")
async def send_message(other_id: str, body: MessageIn, user: dict = Depends(get_current_user)):
    if not await _are_friends(user["user_id"], other_id):
        count = await db.messages.count_documents({"senderId": user["user_id"], "receiverId": other_id})
        if count >= 3:
            raise HTTPException(status_code=403, detail="Mesaj limitine ulaştınız. Arkadaşlık isteği gönderin.")
    mod = await ai.moderate_content(body.content)
    if not mod["safe"]:
        raise HTTPException(status_code=400, detail="Mesaj uygunsuz içerik barındırıyor")
    msg = {"id": f"msg_{uuid.uuid4().hex[:10]}", "senderId": user["user_id"],
           "receiverId": other_id, "content": body.content, "isRead": False,
           "createdAt": now_utc()}
    await db.messages.insert_one(dict(msg))
    msg["createdAt"] = iso(msg["createdAt"])
    return msg


@api.put("/messages/{other_id}/read")
async def mark_read(other_id: str, user: dict = Depends(get_current_user)):
    await db.messages.update_many({"senderId": other_id, "receiverId": user["user_id"]},
                                  {"$set": {"isRead": True}})
    return {"ok": True}


# ==================== MATCHES ====================
@api.get("/matches/recent")
async def recent_matches(user: dict = Depends(get_current_user)):
    matches = await db.matches.find({"$or": [
        {"player1Id": user["user_id"]}, {"player2Id": user["user_id"]}],
        "status": "COMPLETED"}, {"_id": 0}).sort("createdAt", -1).limit(10).to_list(10)
    out = []
    for m in matches:
        is_p1 = m["player1Id"] == user["user_id"]
        opp_id = m["player2Id"] if is_p1 else m["player1Id"]
        opp = await db.users.find_one({"user_id": opp_id}, {"_id": 0})
        out.append({
            "id": m["id"], "mode": m["mode"],
            "myScore": m["player1Score"] if is_p1 else m["player2Score"],
            "oppScore": m["player2Score"] if is_p1 else m["player1Score"],
            "won": m.get("winnerId") == user["user_id"],
            "opponent": opp.get("displayName") if opp else "Rakip",
            "opponentAvatar": opp.get("avatarUrl") if opp else None,
            "coinsAwarded": m.get("coinsAwarded", 0), "xpAwarded": m.get("xpAwarded", 0),
            "createdAt": iso(m["createdAt"]),
        })
    return out


# ==================== ADS / REWARDS ====================
@api.post("/ads/reward")
async def ad_reward(user: dict = Depends(get_current_user)):
    await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"coins": COIN_REWARDS["rewardedAd"]}})
    fresh = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {"ok": True, "coins": fresh["coins"], "rewarded": COIN_REWARDS["rewardedAd"]}


@api.get("/home/summary")
async def home_summary(user: dict = Depends(get_current_user)):
    """Aggregated data for HomeScreen."""
    rp = user.get("rankPoints", 1000)
    lg = league_for_points(rp)
    rank = await db.users.count_documents({"rankPoints": {"$gt": rp}}) + 1
    # wins today
    from datetime import timedelta
    start_today = now_utc().replace(hour=0, minute=0, second=0, microsecond=0)
    wins_today = await db.matches.count_documents({
        "winnerId": user["user_id"], "createdAt": {"$gte": start_today}})
    return {
        "league": lg["tier"], "rankPoints": rp, "globalRank": rank,
        "leagueMin": lg["min"], "leagueMax": lg["max"] if lg["max"] < 10 ** 9 else rp + 500,
        "winsToday": wins_today, "coins": user.get("coins", 0),
        "currentStreak": user.get("currentStreak", 0), "loginStreak": user.get("loginStreak", 0),
        "level": user.get("level", 1), "currentXP": user.get("currentXP", 0),
        "xpForNextLevel": xp_for_level(user.get("level", 1)),
    }


# ==================== ADMIN / AI ====================
class GenerateIn(BaseModel):
    category: str
    difficulty: int = 2
    count: int = 5


@api.post("/admin/questions/generate")
async def admin_generate(body: GenerateIn, user: dict = Depends(get_current_user)):
    questions = await ai.generate_questions(body.category.upper(), body.difficulty, min(body.count, 10))
    if questions:
        await db.questions.insert_many([dict(q) for q in questions])
    return {"generated": len(questions),
            "questions": [{"id": q["id"], "text": q["text"]} for q in questions]}


class SuggestIn(BaseModel):
    text: str
    options: list[str]
    correctIndex: int
    category: str
    explanation: str = ""


@api.post("/questions/suggest")
async def suggest_question(body: SuggestIn, user: dict = Depends(get_current_user)):
    mod = await ai.moderate_content(body.text + " " + " ".join(body.options))
    if not mod["safe"]:
        raise HTTPException(status_code=400, detail="Soru uygunsuz içerik barındırıyor")
    q = {"id": f"q_{uuid.uuid4().hex[:12]}", "text": body.text, "options": body.options,
         "correctIndex": body.correctIndex, "category": body.category.upper(), "difficulty": 2,
         "type": "TEXT", "audioUrl": None, "imageUrl": None, "explanation": body.explanation,
         "source": "Kullanıcı önerisi", "usageCount": 0, "correctRate": 0.0,
         "reportCount": 0, "isActive": False, "verifiedAt": None,
         "suggestedBy": user["user_id"], "createdAt": now_utc()}
    await db.questions.insert_one(dict(q))
    return {"ok": True, "message": "Öneriniz inceleme kuyruğuna eklendi"}


@api.post("/questions/{question_id}/report")
async def report_question(question_id: str, user: dict = Depends(get_current_user)):
    await db.question_reports.insert_one({
        "id": f"qr_{uuid.uuid4().hex[:10]}", "questionId": question_id,
        "userId": user["user_id"], "reason": "user_report", "createdAt": now_utc()})
    await db.questions.update_one({"id": question_id}, {"$inc": {"reportCount": 1}})
    return {"ok": True}


# ==================== WEBSOCKET GAME ENGINE ====================
async def authenticate_ws(token: str) -> dict | None:
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        return None
    return await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})


async def pick_questions(mode: str, category: str | None, count: int = 10):
    query = {"isActive": True}
    if mode == "CATEGORY" and category:
        query["category"] = category.upper()
    qs = await db.questions.find(query, {"_id": 0}).to_list(500)
    if len(qs) < count:
        qs = await db.questions.find({"isActive": True}, {"_id": 0}).to_list(500)
    random.shuffle(qs)
    return qs[:count]


async def finalize_match(user_id: str, match_id: str, mode: str, p_score: int,
                         o_score: int, correct_count: int, science_correct: int,
                         fastest_correct_ms: int, opp_id: str, opp_rp: int,
                         answers_log: list):
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    won = p_score > o_score
    draw = p_score == o_score
    ranked = mode in ("RANKED", "DAILY_TOURNAMENT", "WEEKLY_LEAGUE")
    rp_change = 0
    if not draw:
        if ranked:
            ch = calculate_rank_change(user["rankPoints"], opp_rp) if won else calculate_rank_change(opp_rp, user["rankPoints"])
            rp_change = ch["winnerGain"] if won else -ch["loserLoss"]
        else:
            rp_change = 12 if won else -6
    xp_gain = (XP_REWARDS["matchWin"] if won else XP_REWARDS["matchLoss"]) + correct_count * XP_REWARDS["correctAnswer"]
    coin_gain = COIN_REWARDS["matchWin"] if won else COIN_REWARDS["matchLoss"]

    level, current, total, leveled = apply_xp(user, xp_gain)
    new_streak = (user.get("currentStreak", 0) + 1) if won else 0
    longest = max(user.get("longestStreak", 0), new_streak)
    new_rp = max(0, user.get("rankPoints", 1000) + rp_change)

    set_fields = {"level": level, "currentXP": current, "totalXP": total,
                  "rankPoints": new_rp, "currentStreak": new_streak,
                  "longestStreak": longest, "lastSeenAt": now_utc()}
    if fastest_correct_ms and fastest_correct_ms < 3000:
        set_fields["speedDemon"] = True
    inc_fields = {"coins": coin_gain, "totalMatches": 1,
                  "correctAnswersTotal": correct_count}
    if won:
        inc_fields["wins"] = 1
    elif not draw:
        inc_fields["losses"] = 1
    await db.users.update_one({"user_id": user_id}, {"$set": set_fields, "$inc": inc_fields})

    # persist match
    await db.matches.update_one({"id": match_id}, {"$set": {
        "player1Score": p_score, "player2Score": o_score,
        "winnerId": (user_id if won else (opp_id if not draw else None)),
        "status": "COMPLETED", "endedAt": now_utc(),
        "coinsAwarded": coin_gain, "xpAwarded": xp_gain, "answers": answers_log}})

    # quests
    events = {"match": 1, "correct": correct_count, "science": science_correct}
    if won:
        events["win"] = 1
        if ranked:
            events["ranked_win"] = 1
    await update_quest_progress(user_id, events)

    fresh = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    new_achs = await check_achievements(fresh)

    return {
        "winnerId": (user_id if won else (opp_id if not draw else None)),
        "draw": draw, "won": won,
        "finalScores": {"player": p_score, "opponent": o_score},
        "xpGained": xp_gain, "coinsGained": coin_gain, "rankPointsChange": rp_change,
        "newLevel": level if leveled else None, "leveledUp": leveled,
        "newAchievements": [{"title": a["title"], "coinReward": a["coinReward"]} for a in new_achs],
    }


@app.websocket("/api/ws/game")
async def ws_game(websocket: WebSocket, token: str = Query(...)):
    await websocket.accept()
    user = await authenticate_ws(token)
    if not user:
        await websocket.send_json({"event": "error", "message": "unauthorized"})
        await websocket.close()
        return
    try:
        while True:
            msg = await websocket.receive_json()
            action = msg.get("action")
            if action == "joinQueue":
                await run_match(websocket, user, msg)
            elif action == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        return
    except Exception as e:
        logger.exception("ws error")
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except Exception:
            pass


async def run_match(websocket: WebSocket, user: dict, msg: dict):
    mode = msg.get("mode", "CLASSIC")
    category = msg.get("category")
    # pick a bot opponent near rank
    rp = user.get("rankPoints", 1000)
    bots = await db.users.find({"isBot": True}, {"_id": 0}).to_list(50)
    bots.sort(key=lambda b: abs(b.get("rankPoints", 1000) - rp))
    bot = bots[0] if bots else None
    if not bot:
        await websocket.send_json({"event": "error", "message": "no opponent"})
        return
    skill = bot.get("skill", 0.6)

    questions = await pick_questions(mode, category, 10)
    if len(questions) < 1:
        await websocket.send_json({"event": "error", "message": "Yeterli soru yok"})
        return

    match_id = f"match_{uuid.uuid4().hex[:12]}"
    await db.matches.insert_one({
        "id": match_id, "mode": mode, "player1Id": user["user_id"],
        "player2Id": bot["user_id"], "player1Score": 0, "player2Score": 0,
        "winnerId": None, "questions": [q["id"] for q in questions], "answers": [],
        "status": "ACTIVE", "startedAt": now_utc(), "endedAt": None,
        "coinsAwarded": 0, "xpAwarded": 0, "createdAt": now_utc()})

    opponent = {"id": bot["user_id"], "displayName": bot["displayName"],
                "avatarUrl": bot.get("avatarUrl"), "level": bot.get("level", 1),
                "rankPoints": bot.get("rankPoints", 1000),
                "league": league_for_points(bot.get("rankPoints", 1000))["tier"]}
    await websocket.send_json({"event": "matchFound", "matchId": match_id, "opponent": opponent})
    await asyncio.sleep(0.6)
    await websocket.send_json({"event": "prepareMatch", "matchId": match_id,
                               "opponent": opponent, "countdown": 3})

    time_limit = 20
    p_score = 0
    o_score = 0
    correct_count = 0
    science_correct = 0
    fastest_correct = None
    answers_log = []

    for idx, q in enumerate(questions):
        # bot pre-decides its answer
        bot_correct = random.random() < skill
        bot_time = random.randint(2500, 16000)
        bot_answer = q["correctIndex"] if bot_correct else random.choice(
            [i for i in range(4) if i != q["correctIndex"]])

        await websocket.send_json({
            "event": "question", "matchId": match_id, "questionId": q["id"],
            "text": q["text"], "options": q["options"], "category": q["category"],
            "difficulty": q["difficulty"], "timeLimit": time_limit,
            "questionIndex": idx, "totalQuestions": len(questions)})

        # await player's answer
        answer_index = -1
        time_ms = time_limit * 1000
        try:
            while True:
                amsg = await asyncio.wait_for(websocket.receive_json(), timeout=time_limit + 8)
                if amsg.get("action") == "answer" and amsg.get("questionId") == q["id"]:
                    answer_index = amsg.get("answerIndex", -1)
                    time_ms = min(int(amsg.get("timeMs", time_limit * 1000)), time_limit * 1000)
                    break
                elif amsg.get("action") == "ping":
                    await websocket.send_json({"event": "pong"})
        except asyncio.TimeoutError:
            answer_index = -1

        p_correct = answer_index == q["correctIndex"]
        p_pts = speed_points(time_ms, time_limit * 1000) if p_correct else 0
        o_pts = speed_points(bot_time, time_limit * 1000) if bot_correct else 0
        p_score += p_pts
        o_score += o_pts
        if p_correct:
            correct_count += 1
            if q["category"] == "SCIENCE":
                science_correct += 1
            if fastest_correct is None or time_ms < fastest_correct:
                fastest_correct = time_ms

        answers_log.append({"questionId": q["id"], "playerAnswer": answer_index,
                            "playerCorrect": p_correct, "timeMs": time_ms,
                            "points": p_pts, "correctIndex": q["correctIndex"]})

        await websocket.send_json({
            "event": "questionResult", "questionIndex": idx, "correct": p_correct,
            "points": p_pts, "opponentAnswered": True, "opponentCorrect": bot_correct,
            "opponentAnswer": bot_answer, "correctIndex": q["correctIndex"],
            "explanation": q["explanation"],
            "scores": {"player": p_score, "opponent": o_score}})

        await db.questions.update_one({"id": q["id"]}, {"$inc": {"usageCount": 1}})

    result = await finalize_match(
        user["user_id"], match_id, mode, p_score, o_score, correct_count,
        science_correct, fastest_correct or 0, bot["user_id"],
        bot.get("rankPoints", 1000), answers_log)
    await websocket.send_json({"event": "matchEnd", "matchId": match_id, **result})


# ---------------- app wiring ----------------
app.include_router(api)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()
    await seed_all()
    logger.info("QuizArena ready")


@app.on_event("shutdown")
async def on_shutdown():
    core.client.close()
