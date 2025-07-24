from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from src.core.config import settings
from src.handlers.webhook_handler import handle_incoming_webhook

webhook_router = APIRouter()

@webhook_router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Forbidden")


@webhook_router.post("/")
async def receive_message(request: Request):
    body = await request.json()
    return await handle_incoming_webhook(body)