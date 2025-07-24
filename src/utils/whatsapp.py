# utils/whatsapp.py

import httpx
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)


async def send_whatsapp_message(phone_number: str, message: str):
    url = f"https://graph.facebook.com/v17.0/{settings.PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        logger.info(f"Sent message response: {response.status_code} {response.text}")


async def send_whatsapp_buttons(phone_number: str, interactive_payload: dict):
    url = f"https://graph.facebook.com/v17.0/{settings.PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        **interactive_payload
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        logger.info(f"Sent list message response: {response.status_code} {response.text}")
        if response.status_code != 200:
            logger.error(f"Failed to send list message: {response.status_code} {response.text}")