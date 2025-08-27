from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

GRAPH_API = os.getenv("FACEBOOK_GRAPH_URL", "https://graph.facebook.com")


class TokenCheckRequest(BaseModel):
    token: str


@router.post("/debug/token")
async def debug_token(req: TokenCheckRequest):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(f"{GRAPH_API}/debug_token?input_token={req.token}")
            return r.json()
    except Exception as e:
        logger.exception("debug_token failed")
        raise HTTPException(status_code=500, detail=str(e))


class PhoneCheckRequest(BaseModel):
    token: str
    phone_number_id: str


@router.post("/debug/phone")
async def debug_phone(req: PhoneCheckRequest):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(f"{GRAPH_API}/{req.phone_number_id}?access_token={req.token}&fields=id,phone_number,whatsapp_business_account")
            return r.json()
    except Exception as e:
        logger.exception("debug_phone failed")
        raise HTTPException(status_code=500, detail=str(e))
