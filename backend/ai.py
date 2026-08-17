"""AI question generation + content moderation via Emergent LLM Key (Claude Sonnet)."""
import json
import re
import uuid

from emergentintegrations.llm.chat import LlmChat, UserMessage

from core import EMERGENT_LLM_KEY, now_utc

MODEL_PROVIDER = "anthropic"
MODEL_NAME = "claude-sonnet-4-6"


def _new_chat(system: str) -> LlmChat:
    return LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"quizarena-{uuid.uuid4().hex[:8]}",
        system_message=system,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)


def _extract_json(text: str):
    text = text.strip()
    # strip markdown fences if present
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    start = text.find("[")
    if start == -1:
        start = text.find("{")
    if start == -1:
        return None
    snippet = text[start:]
    try:
        return json.loads(snippet)
    except Exception:
        # try to find balanced array
        try:
            end = snippet.rfind("]")
            return json.loads(snippet[: end + 1])
        except Exception:
            return None


async def generate_questions(category: str, difficulty: int, count: int) -> list[dict]:
    """Generate trivia questions (Turkish) for a category. Returns parsed list."""
    chat = _new_chat("You are a trivia question generator. Return only valid JSON.")
    prompt = f"""Generate {count} trivia questions.
Category: {category}
Difficulty: {difficulty}/5 (1=very easy general knowledge, 5=expert level)
Style: Who Wants to Be a Millionaire — engaging, clear, no trick questions
Language: Turkish

Return ONLY a valid JSON array, no markdown:
[{{
  "text": "question text",
  "options": ["A", "B", "C", "D"],
  "correctIndex": 0,
  "explanation": "brief explanation",
  "source": "topic area"
}}]

Rules: all 4 options must be plausible, correct answer must be definitively correct, no duplicate questions, no inappropriate content."""
    resp = await chat.send_message(UserMessage(text=prompt))
    data = _extract_json(resp if isinstance(resp, str) else str(resp))
    if not isinstance(data, list):
        return []
    cleaned = []
    for q in data:
        if not isinstance(q, dict):
            continue
        opts = q.get("options")
        if not isinstance(opts, list) or len(opts) != 4:
            continue
        ci = q.get("correctIndex")
        if not isinstance(ci, int) or ci < 0 or ci > 3:
            continue
        cleaned.append({
            "id": f"q_{uuid.uuid4().hex[:12]}",
            "text": str(q.get("text", "")),
            "options": [str(o) for o in opts],
            "correctIndex": ci,
            "category": category,
            "difficulty": difficulty,
            "type": "TEXT",
            "audioUrl": None,
            "imageUrl": None,
            "explanation": str(q.get("explanation", "")),
            "source": str(q.get("source", category)),
            "usageCount": 0,
            "correctRate": 0.0,
            "reportCount": 0,
            "isActive": False,
            "verifiedAt": None,
            "createdAt": now_utc(),
        })
    return cleaned


async def moderate_content(text: str) -> dict:
    """Return {'safe': bool, 'reason': str}."""
    if not text or not text.strip():
        return {"safe": True}
    try:
        chat = _new_chat("You are a content moderation system. Return only JSON.")
        prompt = f"""Is this text safe for a family-friendly trivia game? Check for: profanity, sexual content, hate speech, harassment.
Text: "{text}"
Respond with JSON only: {{ "safe": true/false, "reason": "..." }}"""
        resp = await chat.send_message(UserMessage(text=prompt))
        data = _extract_json(resp if isinstance(resp, str) else str(resp))
        if isinstance(data, dict) and "safe" in data:
            return {"safe": bool(data["safe"]), "reason": data.get("reason", "")}
    except Exception:
        pass
    return {"safe": True}
