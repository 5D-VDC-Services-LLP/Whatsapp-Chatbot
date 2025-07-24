# src/core/session.py
from datetime import datetime
from src.core.cache import cache

def build_session_key(user_phone, autodesk_id=None):
    return f"session:{user_phone}" if not autodesk_id else f"session:{user_phone}:{autodesk_id}"

async def set_session(user_phone, session_data: dict, autodesk_id=None):
    session_key = build_session_key(user_phone, autodesk_id)
    # Set full session (overwrites previous) with default expiration
    await cache.set(session_key, {
        **session_data,
        "timestamp": datetime.utcnow().isoformat()
    })

async def get_session(user_phone, autodesk_id=None):
    session_key = build_session_key(user_phone, autodesk_id)
    session = await cache.get(session_key)
    if session:
        # Optionally re-save it to reset TTL if not handled by cache layer
        await cache.set(session_key, session)
    return session

def validate_session_state(session: dict, required_keys: list):
    missing = [k for k in required_keys if not session.get(k)]
    return missing  # returns list of missing keys; empty if all present

