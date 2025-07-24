# utils/buttons.py

from typing import List, Dict

MAX_LIST_ITEMS = 10
MAX_TITLE_LENGTH = 24

def create_user_buttons(users: List[Dict], prompt: str) -> dict:
    """
    Create a WhatsApp interactive list message payload to disambiguate users.

    Args:
        users: List of dicts with keys 'name', 'email', 'user_id'.
        prompt: The message text asking user to choose email for the correct user.

    Returns:
        Dict payload formatted for WhatsApp List Message API.
    """
    rows = []
    for user in users[:MAX_LIST_ITEMS]:
        email = user.get("email", "unknown@example.com")
        user_id = user.get("user_id", "")
        # Use email username (before @) for title, truncated if needed
        username = email.split("@")[0]
        title = username if len(username) <= MAX_TITLE_LENGTH else username[:21] + "..."
        rows.append({
            "id": f"user_id:{user_id}",
            "title": title,
            "description": email  # show full email here
        })

    payload = {
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "User Selection"
            },
            "body": {
                "text": prompt
            },
            "footer": {
                "text": "Please tap to select"
            },
            "action": {
                "button": "Select User",
                "sections": [
                    {
                        "title": "Matched Users",
                        "rows": rows
                    }
                ]
            }
        }
    }
    return payload


MAX_BUTTONS = 10
MAX_TITLE_LENGTH = 24

def create_project_buttons(projects: List[Dict], prompt: str) -> Dict:
    """
    Create a WhatsApp interactive button message payload to disambiguate projects.

    Args:
        projects: List of dicts with keys 'project_id', 'project_name'.
        prompt: The message text asking user to choose project name + id.

    Returns:
        Dict payload formatted for WhatsApp API.
    """
    buttons = []
    for project in projects[:MAX_BUTTONS]:
        name = project.get("project_name", "Unnamed Project")
        proj_id = project.get("project_id", "")
        title = name
        if len(title) > MAX_TITLE_LENGTH:
            title = title[:MAX_TITLE_LENGTH - 3] + "..."
        buttons.append({
            "type": "reply",
            "reply": {
                "id": f"project_id:{proj_id}",
                "title": title
            }
        })

    payload = {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": prompt},
            "action": {"buttons": buttons}
        }
    }
    return payload
