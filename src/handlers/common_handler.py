
# src/handlers/common_handler.py
from src.integrations.autodesk_api import IssuesAPI
from src.utils.transformations import format_response
from src.utils.whatsapp import send_whatsapp_message


from src.core.cache import cache

SESSION_TTL = 1800  # 30 minutes

async def get_session(phone_number: str) -> dict | None:
    return await cache.get(f"session:{phone_number}")

async def set_session(phone_number: str, session: dict, autodesk_id: str | None = None):
    await cache.set(f"session:{phone_number}", session, ttl=SESSION_TTL)


async def process_user_request(user_phone_number: str, session: dict):
    intent = session["intent"]
    parameters = session["parameters"]
    user = session["user"]
    config = session["config"]
    three_legged_token = session["three_legged_token"]
    selected_user = session["selected_user"]
    selected_project = session["selected_project"]

    data = None
    if intent == "get_issues":
        api = IssuesAPI(three_legged_token, selected_project["project_id"])
        data = await api.get_issues({**parameters, "assignee_id": selected_user["user_id"]})

    if not data or "error" in data:
        await send_whatsapp_message(user_phone_number, f"Error fetching data: {data.get('error', 'Unknown error')}")
        return JSONResponse(content={"message": "Data fetch error"}, status_code=200)

    final_message = format_response(intent, data, parameters, count_only=parameters.get("count_only", False))
    await send_whatsapp_message(user_phone_number, final_message)
    return JSONResponse(content={"message": "Success"}, status_code=200)
