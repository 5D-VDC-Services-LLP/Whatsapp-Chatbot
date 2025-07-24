import httpx
import logging
from typing import List, Dict, Any
from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

async def search_projects_by_name(project_name: str, access_token: str, account_id: str) -> Dict[str, Any]:
    """
    Fetches all projects matching a name from the ACC API using direct + fuzzy matching.

    Args:
        project_name: The partial or full name of the project to search for.
        access_token: A valid 2-legged or 3-legged access token.
        account_id: The Autodesk Construction Cloud account ID (hub ID).

    Returns:
        A dict containing matched projects and the match count.
    """
    if not all([project_name, access_token, account_id]):
        logger.error("Missing required arguments: project_name, access_token, or account_id.")
        return {"matches": [], "match_count": 0}

    logger.info(f"🔍 Attempting direct search for project '{project_name}' in account '{account_id}'...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        direct_results = await _fetch_all_pages(
            client=client,
            account_id=account_id,
            access_token=access_token,
            name_filter=project_name
        )

        if direct_results:
            logger.info(f"✅ Found {len(direct_results)} project(s) via direct search.")
            return {
                "matches": [
                    {"project_id": p.get("id"), "project_name": p.get("name")}
                    for p in direct_results
                ],
                "match_count": len(direct_results)
            }

        logger.info(f"No direct matches. Falling back to fuzzy matching...")

        all_projects = await _fetch_all_pages(
            client=client,
            account_id=account_id,
            access_token=access_token,
            name_filter=None
        )

        if not all_projects:
            logger.info("⚠️ No projects found for fuzzy matching.")
            return {"matches": [], "match_count": 0}

        logger.info(f"Applying fuzzy matching on {len(all_projects)} projects...")

        name_to_project = {
            proj["name"]: proj
            for proj in all_projects if "name" in proj
        }

        matched_names = process.extract(
            project_name,
            name_to_project.keys(),
            scorer=fuzz.WRatio,
            score_cutoff=80,
            limit=10
        )

        fuzzy_matches = [
            {
                "project_id": name_to_project[name]["id"],
                "project_name": name
            }
            for name, _, _ in matched_names
        ]

        logger.info(f"✅ Found {len(fuzzy_matches)} fuzzy-matched project(s).")
        return {
            "matches": fuzzy_matches,
            "match_count": len(fuzzy_matches)
        }

async def _fetch_all_pages(client: httpx.AsyncClient, account_id: str, access_token: str, name_filter: str = None) -> List[Dict[str, Any]]:
    base_url = f"https://developer.api.autodesk.com/construction/admin/v1/accounts/{account_id}/projects"
    headers = {"Authorization": f"Bearer {access_token}"}

    params = {"limit": 100}
    if name_filter:
        params["filter[name]"] = name_filter

    all_results = []
    current_url = base_url

    try:
        while current_url:
            request_params = params if current_url == base_url else None
            response = await client.get(current_url, headers=headers, params=request_params)
            response.raise_for_status()
            data = response.json()

            if "results" in data:
                all_results.extend(data["results"])

            current_url = data.get("pagination", {}).get("nextUrl")
            if current_url:
                logger.info(f"📄 Fetching next page: {current_url}")

        return all_results

    except httpx.HTTPStatusError as http_err:
        logger.error(f"❌ HTTP error while fetching projects: {http_err}")
        return []
    except Exception as e:
        logger.exception(f"🔥 Unexpected error during project fetch: {e}")
        return []
