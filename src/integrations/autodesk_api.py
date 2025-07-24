# autodesk_api.py
import httpx
import logging
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class IssuesAPI:
    BASE_URL = "https://developer.api.autodesk.com/construction/issues/v1"

    def __init__(self, three_legged_token: str, project_id: str):
        self.token = three_legged_token
        self.project_id = project_id
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def get_issues(self, parameters: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Fetches issues with filters: assignee, issue type, status, due date, count_only.
        """
        try:
            filters = self._build_filters(parameters)

            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/projects/{self.project_id}/issues"
                response = await client.get(url, headers=self.headers, params=filters)
                response.raise_for_status()
                data = response.json()

            if parameters.get("count_only"):
                count = data.get("pagination", {}).get("totalResults", 0)
                return {"status": "success", "count": count}
            return {"status": "success", "data": data.get("results", [])}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while fetching issues: {e.response.text}")
            return {"error": f"API request failed: {e.response.text}"}
        except Exception as e:
            logger.exception("Unexpected error in get_issues")
            return {"error": f"Unexpected error: {str(e)}"}

    def _build_filters(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """
        Builds filter dictionary from parsed parameters.
        """
        filters = {}

        if assignee_id := parameters.get("assignee_id"):
            filters["filter[assignedTo]"] = assignee_id
        if issue_type_id := parameters.get("issue_type_id"):
            filters["filter[issueTypeId]"] = issue_type_id
        if status := parameters.get("issue_status"):
            filters["filter[status]"] = status
        if due_date := parameters.get("due_date"):
            filters["filter[dueDate]"] = due_date

        return filters

    async def get_issue_type_id(self, issue_type_title: str) -> Optional[str]:
        """
        Returns the ID of the issue type given its title.
        """
        try:
            url = f"{self.BASE_URL}/projects/{self.project_id}/issue-types"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()

            for issue_type in data.get("results", []):
                if issue_type.get("title", "").lower() == issue_type_title.lower():
                    return issue_type.get("id")
        except Exception as e:
            logger.error(f"Error fetching issue types: {e}")
        return None