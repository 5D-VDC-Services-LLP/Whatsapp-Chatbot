# handlers/webhook_handler.py

import json
import logging
import re
from fastapi.responses import JSONResponse
from src.handlers.message_handler import handle_text_message
from src.handlers.button_handler import handle_button_reply

logger = logging.getLogger(__name__)

async def handle_incoming_webhook(body: dict):
    try:
        logger.info(f"Incoming webhook body:\n{json.dumps(body, indent=2)}")
        value = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {})

        if not value.get("messages"):
            return JSONResponse(content={"message": "No messages"}, status_code=200)

        message = value["messages"][0]
        if message.get("interactive"):
            return await handle_button_reply(value)

        return await handle_text_message(value)

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        fallback_phone = (
            body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {}).get("phone_number_id", "unknown")
        )
        from src.utils.whatsapp import send_whatsapp_message
        await send_whatsapp_message(fallback_phone, "\u26a0\ufe0f Internal error occurred. Try again.")
        return JSONResponse(content={"message": "Internal server error"}, status_code=500)