import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

import httpx
from src.core.cache import cache
from src.repositories import mongodb_repo

TOKEN_URL = "https://developer.api.autodesk.com/authentication/v2/token"
REFRESH_URL = TOKEN_URL

async def get_three_legged_token(mongo_uri: str, autodesk_id: str, client_id: str, client_secret: str) -> Optional[str]:
    """
    Fetches a valid 3-legged token for the user, refreshing it if needed.
    """
    logging.info("[3-LEG] Starting...")
    token_doc = await mongodb_repo.get_aps_token(mongo_uri, autodesk_id)
    logging.info(f"[3-LEG] Token document found: {'Yes' if token_doc else 'No'}")

    if not token_doc or token_doc.get("status") != "active":
        logging.warning(f"[3-LEG] No active token found for user {autodesk_id}.")
        return None

    expires_at = token_doc.get("expires_at")
    expiry_ts = 0
    if isinstance(expires_at, str):
        expiry_ts = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc).timestamp()
    elif isinstance(expires_at, datetime):
        expiry_ts = expires_at.replace(tzinfo=timezone.utc).timestamp()

    if datetime.now(timezone.utc).timestamp() + 300 >= expiry_ts:
        logging.info("[3-LEG] Token requires refreshing. Calling _refresh_three_legged...")
        refreshed_token_doc = await _refresh_three_legged(mongo_uri, token_doc, client_id, client_secret)
        if not refreshed_token_doc:
            logging.error(f"[3-LEG] Failed to refresh token for user {autodesk_id}.")
            return None
        logging.info("[3-LEG] Refresh successful. Returning new token.")
        return refreshed_token_doc.get("access_token")

    logging.info("[3-LEG] Token is valid. Returning existing token.")
    return token_doc.get("access_token")


async def _refresh_three_legged(mongo_uri: str, token_doc: Dict, client_id: str, client_secret: str) -> Optional[Dict]:
    """
    Refreshes the 3-legged token using the provided credentials.
    Returns the new token dict on success, or None on failure.
    """
    refresh_token = token_doc.get("refresh_token")
    logging.info(f"Refreshing 3-legged token for autodesk_id: {token_doc.get('autodesk_id')}")

    auth_str = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(auth_str.encode()).decode()
    headers = { "Authorization": f"Basic {encoded}", "Content-Type": "application/x-www-form-urlencoded" }
    data = { "grant_type": "refresh_token", "refresh_token": refresh_token, "scope": "data:read account:read" }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(REFRESH_URL, headers=headers, data=data)
            resp.raise_for_status()
            body = resp.json()
            new_doc = {
                "autodesk_id": token_doc.get("autodesk_id"),
                "access_token": body["access_token"],
                "refresh_token": body.get("refresh_token", refresh_token),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=body["expires_in"])).isoformat(),
                "status": "active",
            }
            success = await mongodb_repo.upsert_aps_token(mongo_uri, new_doc)
            if success:
                return new_doc
            else:
                logging.error("Failed to upsert refreshed token into DB.")
                return None
        except Exception as e:
            logging.error(f"Failed to refresh 3-legged token: {e}")
            return None


async def get_two_legged_token(client_id: str, client_secret: str, scope: str = "data:read account:read") -> Optional[str]:
    """
    Retrieves a cached 2-legged token, or generates a new one if expired.
    """
    cache_key = f"two_legged_token:{client_id}"
    
    logging.info("[2-LEG] Checking cache for 2-legged token...")
    cached_token = await cache.get(cache_key)
    if cached_token:
        logging.info("[2-LEG] Cache HIT.")
        return cached_token.decode('utf-8') if isinstance(cached_token, bytes) else cached_token

    logging.info("[2-LEG] Cache MISS. Generating new token.")
    auth_str = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_auth}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials", "scope": scope}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(TOKEN_URL, headers=headers, data=data)
            resp.raise_for_status()
            body = resp.json()
            access_token = body["access_token"]
            expires_in = body["expires_in"]
            
            # **THE FIX**: Pass expiration as a positional argument, not a keyword.
            logging.info("[2-LEG] Storing new token in cache.")
            await cache.set(cache_key, access_token, expires_in - 60)
            
            return access_token
        except Exception as e:
            logging.error(f"[2-LEG] Failed to obtain token: {e}")
            return None
        

    