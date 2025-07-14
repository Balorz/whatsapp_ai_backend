from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import JSONResponse
import os
import traceback
from typing import Optional
from app.services.replies import handle_incoming_message
from app.db.mongo_connection import messages_collection

message_router = APIRouter()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@message_router.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN and hub_challenge:
        return int(hub_challenge)
    
    raise HTTPException(status_code=403, detail="Invalid verification token or mode")


@message_router.post("/webhook")
async def receive_message(request: Request):
    try:
        body = await request.json()
        await handle_incoming_message(body)
        return JSONResponse(status_code=200, content={"success": True, "message": "Message processed."})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
