from fastapi import APIRouter, HTTPException, Depends, Query
from app.db.mongo_connection import db
from app.utils.auth import get_current_tenant, TokenData
from bson.objectid import ObjectId
from app.utils.helpers import serialize_doc

conversations_router = APIRouter(prefix="/conversations", tags=["Conversations"])

@conversations_router.get("/")
async def get_conversations(current_tenant: TokenData = Depends(get_current_tenant)):
    tenant_id = ObjectId(current_tenant.tenant_id)
    
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {
            "$lookup": {
                "from": "contacts",
                "localField": "contact_id",
                "foreignField": "_id",
                "as": "contact_info"
            }
        },
        {"$unwind": "$contact_info"},
        {
            "$lookup": {
                "from": "messages",
                "localField": "_id",
                "foreignField": "conversation_id",
                "as": "messages"
            }
        },
        {
            "$addFields": {
                "last_message": {"$last": "$messages"}
            }
        },
        {
            "$project": {
                "messages": 0  # Exclude the full messages array
            }
        }
    ]
    
    conversations = await db.conversations.aggregate(pipeline).to_list(length=None)
    
    return [serialize_doc(conv) for conv in conversations]

@conversations_router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_tenant: TokenData = Depends(get_current_tenant),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    tenant_id = ObjectId(current_tenant.tenant_id)
    
    # First, verify that the conversation belongs to the tenant
    conversation = await db.conversations.find_one(
        {"_id": ObjectId(conversation_id), "tenant_id": tenant_id}
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        await db.messages.find({"conversation_id": ObjectId(conversation_id)})
        .sort("created_at", 1)
        .skip(offset)
        .limit(limit)
        .to_list(length=limit)
    )
    
    return [serialize_doc(msg) for msg in messages]
