# handlers/message_handler.py

import json
import re
import logging
from fastapi.responses import JSONResponse
from src.core.cache import cache
from src.services import token_service, user_service, project_service
from src.repositories import postgres_repo
from src.integrations.autodesk_api import IssuesAPI
from src.integrations.intent_agent import intent_parser
from src.utils.transformations import format_response
from src.utils.buttons import create_user_buttons, create_project_buttons
from src.utils.whatsapp import send_whatsapp_message, send_whatsapp_buttons

from src.handlers.common_handler import get_session, set_session

logger = logging.getLogger(__name__)


def add_prefix(data, key, prefix):
    for item in data:
        if key in item and not item[key].startswith(prefix):
            item[key] = f"{prefix}{item[key]}"
    return data


async def handle_text_message(value: dict):
    message = value["messages"][0]
    user_input = message["text"]["body"]
    user_phone_number = message["from"]

    user_cache_key = f"user:{user_phone_number}"
    user = await cache.get(user_cache_key) or await postgres_repo.get_user_by_phone(user_phone_number)
    if not user:
        await send_whatsapp_message(user_phone_number, "You are not assigned to any account.")
        return JSONResponse(content={"message": "User not assigned"}, status_code=200)
    await cache.set(user_cache_key, user)

    raw_response = await intent_parser.arun(user_input)
    raw_text = raw_response.get_content_as_string()

    try:
        json_str = (
            re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_text).group(1).strip()
            if "```" in raw_text else raw_text.strip()
        )
        agent_response = json.loads(json_str)
    except Exception:
        await send_whatsapp_message(user_phone_number, "Sorry, I couldn’t understand your request.")
        return JSONResponse(content={"message": "Intent parsing failed"}, status_code=200)

    intent = agent_response.get("intent")
    parameters = agent_response.get("parameters", {})

    if intent == "greet":
        await send_whatsapp_message(user_phone_number, "Hello I am 5DVDC Bot here to help you with your ACC Forms, Issues and Reviews data. Please Let me know how can I assist you today!")
        return JSONResponse(content={"message": "Greet sent"}, status_code=200)

    config = await postgres_repo.get_company_config(user["hub_id"])
    if not config:
        await send_whatsapp_message(user_phone_number, "Configuration not found. Contact support.")
        return JSONResponse(content={"message": "Missing config"}, status_code=200)

    three_legged_token = await token_service.get_three_legged_token(
        mongo_uri=config["mongodb_uri"],
        autodesk_id=user["autodesk_id"],
        client_id=config["client_id"],
        client_secret=config["client_secret"]
    )
    two_legged_token = await token_service.get_two_legged_token(
        client_id=config["client_id"],
        client_secret=config["client_secret"]
    )

    if not three_legged_token or not two_legged_token:
        await send_whatsapp_message(user_phone_number, "Auth error. Try again later.")
        return JSONResponse(content={"message": "Token error"}, status_code=200)

    assignee_name = parameters.get("assignee_name")
    matched_users = await user_service.search_users_by_name(
        name=assignee_name,
        access_token=two_legged_token,
        hub_id=user["hub_id"]
    )

    if not matched_users or matched_users["match_count"] == 0:
        await send_whatsapp_message(user_phone_number, f"No user found named '{assignee_name}'.")
        return JSONResponse(content={"message": "Assignee not found"}, status_code=200)

    if matched_users["match_count"] > 1:
        prefixed_users = add_prefix(matched_users["matches"], key="user_id", prefix="user::")
        buttons_payload = create_user_buttons(prefixed_users, prompt="Please select the correct user:")
        await send_whatsapp_buttons(user_phone_number, buttons_payload)
        await set_session(user_phone_number, {
            "intent": intent,
            "parameters": parameters,
            "user": user,
            "config": config,
            "three_legged_token": three_legged_token,
            "two_legged_token": two_legged_token
        }, autodesk_id=user["autodesk_id"])

        return JSONResponse(content={"message": "Sent user clarification buttons"}, status_code=200)

    selected_user = matched_users["matches"][0]
    project_name = parameters.get("project_name")
    matched_projects = await project_service.search_projects_by_name(
        project_name=project_name,
        access_token=two_legged_token,
        account_id=user["hub_id"]
    )

    if not matched_projects or matched_projects["match_count"] == 0:
        await send_whatsapp_message(user_phone_number, f"No project found named '{project_name}'.")
        return JSONResponse(content={"message": "Project not found"}, status_code=200)

    if matched_projects["match_count"] > 1:
        prefixed_projects = add_prefix(matched_projects["matches"], key="project_id", prefix="project::")
        buttons_payload = create_project_buttons(prefixed_projects, prompt="Please select the correct project:")
        await send_whatsapp_buttons(user_phone_number, buttons_payload)
        session_key = f"session:{user_phone_number}"
        await cache.set(session_key, {
            "intent": intent,
            "parameters": parameters,
            "user": user,
            "config": config,
            "three_legged_token": three_legged_token,
            "two_legged_token": two_legged_token
        })
        return JSONResponse(content={"message": "Sent project clarification buttons"}, status_code=200)

    selected_project = matched_projects["matches"][0]

    data = None
    if intent == "get_issues":
        api = IssuesAPI(three_legged_token, selected_project["project_id"])
        data = await api.get_issues({**parameters, "assignee_id": selected_user["user_id"]})

    if not data or "error" in data:
        await send_whatsapp_message(user_phone_number, f"Error fetching data: {data.get('error', 'Unknown error')}")
        return JSONResponse(content={"message": "Data fetch error"}, status_code=200)

    final_message = format_response(intent, data, parameters, count_only=parameters.get("count_only", False))
    await send_whatsapp_message(user_phone_number, final_message)

    logger.info(f"Processed request for {user['autodesk_id']} → {assignee_name} @ {project_name}")
    return JSONResponse(content={"message": "Success"}, status_code=200)
