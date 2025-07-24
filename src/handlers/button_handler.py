from src.handlers.common_handler import get_session, set_session
from src.handlers.common_handler import process_user_request

async def handle_button_reply(value: dict):
    try:
        message = value["messages"][0]
        user_phone_number = message["from"]
        interactive = message.get("interactive", {})
        button_reply = interactive.get("list_reply", {})
        selected_payload = button_reply.get("id")

        if not selected_payload or "::" not in selected_payload:
            await send_whatsapp_message(user_phone_number, "Invalid selection format. Please try again.")
            return JSONResponse(content={"message": "Invalid button format"}, status_code=200)

        prefix, actual_value = selected_payload.split("::", 1)

        session = await get_session(user_phone_number)
        if not session:
            await send_whatsapp_message(user_phone_number, "Your session has expired. Please start again.")
            return JSONResponse(content={"message": "Session expired"}, status_code=200)

        if prefix == "user":
            # Fetch full user info from existing match list or API if needed
            matches = await user_service.search_users_by_name(
                name=session["parameters"].get("assignee_name"),
                access_token=session["two_legged_token"],
                hub_id=session["user"]["hub_id"]
            )
            selected_user = next((u for u in matches["matches"] if u["user_id"] == actual_value), None)
            if not selected_user:
                await send_whatsapp_message(user_phone_number, "User not found in selection.")
                return JSONResponse(content={"message": "User match not found"}, status_code=200)
            session["selected_user"] = selected_user

        elif prefix == "project":
            matches = await project_service.search_projects_by_name(
                project_name=session["parameters"].get("project_name"),
                access_token=session["two_legged_token"],
                account_id=session["user"]["hub_id"]
            )
            selected_project = next((p for p in matches["matches"] if p["project_id"] == actual_value), None)
            if not selected_project:
                await send_whatsapp_message(user_phone_number, "Project not found in selection.")
                return JSONResponse(content={"message": "Project match not found"}, status_code=200)
            session["selected_project"] = selected_project

        else:
            await send_whatsapp_message(user_phone_number, "Unrecognized selection type.")
            return JSONResponse(content={"message": "Unrecognized prefix"}, status_code=200)

        # Save updated session and resume
        await set_session(user_phone_number, session, autodesk_id=session["user"]["autodesk_id"])
        return await process_user_request(user_phone_number, session)

    except Exception as e:
        logger.error(f"Button reply handling error: {e}", exc_info=True)
        await send_whatsapp_message(user_phone_number, "Internal error handling your response. Please try again.")
        return JSONResponse(content={"message": "Internal server error"}, status_code=500)
