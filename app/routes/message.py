from fastapi import APIRouter, Query,Request
from fastapi.responses import JSONResponse
import os
from typing import Optional
from app.services.replies import handle_incoming_message

message_router = APIRouter()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@message_router.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN and hub_challenge is not None:
        return int(hub_challenge)
    return JSONResponse(status_code=403, content={"error": "Forbidden"})

@message_router.post("/webhook")
async def receive_message(request: Request):
    try:
        body = await request.json()
        print("📩 Incoming message:", body)
        await handle_incoming_message(body)
        return {"status": "received"}
    except Exception as e:
        print("❌ Error processing webhook:", e)
        return {"status": "error", "detail": str(e)}