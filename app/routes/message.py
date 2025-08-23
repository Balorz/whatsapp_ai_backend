from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import JSONResponse
import os
import traceback
from typing import Optional
from app.services.replies import handle_incoming_message
from app.db.mongo_connection import messages_collection
from bson.objectid import ObjectId
from app.utils.helpers import serialize_doc

@staticmethod
def _serialize_doc(doc: dict) -> dict:
    # kept for backward compatibility within this module
    return serialize_doc(doc)

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


@message_router.get("/tenants/{tenant_id}/messages")
async def get_tenant_messages(
    tenant_id: str,
    contact_id: Optional[str] = Query(None),
    wa_message_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    skip: int = Query(0, ge=0)
):
    """Return messages for a given tenant. Optional filters: contact_id, wa_message_id."""
    try:
        query = {"tenant_id": ObjectId(tenant_id)}
    except Exception:
        # tenant_id might be stored as string; fall back
        query = {"tenant_id": tenant_id}

    if contact_id:
        try:
            query["contact_id"] = ObjectId(contact_id)
        except Exception:
            query["contact_id"] = contact_id

    if wa_message_id:
        query["wa_message_id"] = wa_message_id

    cursor = messages_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return {"count": len(docs), "messages": [_serialize_doc(d) for d in docs]}


@message_router.get("/tenants/{tenant_id}/messages/by-wa/{wa_message_id}")
async def get_tenant_message_by_wa(tenant_id: str, wa_message_id: str):
    """Fetch a particular message for a tenant by the WhatsApp message id (wa_message_id)."""
    try:
        try:
            t_query = {"tenant_id": ObjectId(tenant_id)}
        except Exception:
            t_query = {"tenant_id": tenant_id}

        query = {**t_query, "wa_message_id": wa_message_id}
        doc = await messages_collection.find_one(query)
        if not doc:
            raise HTTPException(status_code=404, detail="Message not found")
        return _serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
