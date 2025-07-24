# src/utils/transformations.py

from typing import List, Dict, Any, Optional

def build_filter_description(filters: Dict[str, Any]) -> str:
    """
    Build a human-readable description of applied filters for the message.
    Example output:
    "assigned to Ashrik in project Sample Residential with status open or closed due today"
    """
    parts = []

    assignee = filters.get("assignee_name")
    if assignee:
        parts.append(f"assigned to *{assignee}*")

    project = filters.get("project_name")
    if project:
        parts.append(f"in project *{project}*")

    # Status can be a list for issues/reviews/forms
    status = filters.get("issue_status") or filters.get("review_status") or filters.get("form_status")
    if status and isinstance(status, list) and status:
        status_str = ", ".join(status)
        parts.append(f"with status {status_str}")

    due_date = filters.get("due_date") or filters.get("created_on")
    if due_date:
        parts.append(f"due {due_date}")

    # Add other filters as needed here, e.g., issue_type, review_workflow etc.

    return " ".join(parts) if parts else ""

def generate_issue_url(issue_id: str, project_id: Optional[str] = None) -> str:
    """
    Generate a URL link to the issue in Autodesk or your platform.
    Modify this function to match your actual URL patterns.
    """
    base_url = "https://autodesk.example.com/issues"
    if project_id:
        return f"{base_url}/{project_id}/issue/{issue_id}"
    else:
        return f"{base_url}/issue/{issue_id}"

def format_issues_response(
    data: List[Dict[str, Any]],
    filters: Dict[str, Any],
    count_only: bool,
    project_id: Optional[str] = None
) -> str:
    """
    Format issues response message based on count_only flag.
    """
    filter_desc = build_filter_description(filters)
    issues = data["data"]
    count = len(issues)

    if count_only:
        return f"You have *{count}* issue{'s' if count != 1 else ''} {filter_desc}."

    if count == 0:
        return f"No issues found {filter_desc}."

    lines = [f"There are *{count}* issue{'s' if count != 1 else ''} {filter_desc}:"]
    for idx, issue in enumerate(issues, start=1):
        issue_id = issue.get("displayId")
        due_date = issue.get("dueDate") or "No due date"
        title = issue.get("title") or issue.get("summary") or "No title"

        url = generate_issue_url(issue_id, project_id)
        lines.append(f"{idx}. Issue *#{issue_id}* - *{title}* - Due: {due_date} - {url}")

    return "\n".join(lines)

def format_response(
    intent: str,
    data: List[Dict[str, Any]],
    filters: Dict[str, Any],
    count_only: bool
) -> str:
    """
    Dispatch formatting based on intent.
    """
    if intent == "get_issues":
        return format_issues_response(data, filters, count_only, project_id=filters.get("project_id"))
    elif intent == "get_reviews":
        # Implement similarly when ready
        return "Review formatting not implemented yet."
    elif intent == "get_forms":
        # Implement similarly when ready
        return "Form formatting not implemented yet."
    else:
        return "Unsupported intent."
