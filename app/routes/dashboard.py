from fastapi import APIRouter, HTTPException, Depends, Query
from app.db.mongo_connection import db
from app.utils.auth import get_current_tenant, TokenData
from bson.objectid import ObjectId
from typing import List
from app.models.schemas import MessageModel

dashboard_router = APIRouter(
    prefix="/tenants",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_tenant)]
)

@dashboard_router.get("/{tenant_id}/messages", response_model=List[MessageModel])
async def get_tenant_messages(
    tenant_id: str,
    current_tenant: TokenData = Depends(get_current_tenant),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    if tenant_id != current_tenant.tenant_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this tenant's messages")

    messages = (
        await db.messages.find({"tenant_id": ObjectId(tenant_id)})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
        .to_list(length=limit)
    )
    
    for msg in messages:
        msg["_id"] = str(msg["_id"])
        msg["conversation_id"] = str(msg["conversation_id"])
        msg["tenant_id"] = str(msg["tenant_id"])

    return messages
