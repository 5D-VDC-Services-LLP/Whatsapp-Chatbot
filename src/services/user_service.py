import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
AUTODESK_API_BASE_URL = "https://developer.api.autodesk.com"

async def search_users_by_name(name: str, access_token: str, hub_id: str) -> Dict[str, Any]:
    """
    Searches for users in the Autodesk account using partial name match
    (via Autodesk's `/users/search` endpoint). No fuzzy matching used.

    Args:
        name: The full or partial name of the user.
        access_token: Valid Autodesk API token.
        hub_id: Autodesk Construction Cloud account ID (starts with "b.").

    Returns:
        Dict with list of matched users and count.
    """
    if not all([name, access_token, hub_id]):
        logger.error("Missing required arguments: name, access_token, or hub_id.")
        return {"matches": [], "match_count": 0}

    url = f"{AUTODESK_API_BASE_URL}/hq/v1/accounts/{hub_id}/users/search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    params = {"name": name}

    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"🔍 Searching for users with name '{name}' in hub '{hub_id}'...")
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()

            users = response.json()

            filtered_users = [
                {
                    "name": user.get("name", "N/A"),
                    "email": user.get("email", "N/A"),
                    "user_id": user.get("uid", "N/A")
                }
                for user in users
            ]

            return {
                "matches": filtered_users,
                "match_count": len(filtered_users)
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error during user search: {e}")
            logger.debug(f"Response body: {e.response.text}")
            return {"matches": [], "match_count": 0}
        except Exception as e:
            logger.exception(f"❌ Unexpected error during user search: {e}")
            return {"matches": [], "match_count": 0}