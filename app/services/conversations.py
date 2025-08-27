import logging
from datetime import datetime
from app.db.mongo_connection import conversations_collection

logger = logging.getLogger(__name__)


async def get_or_create_conversation(tenant_id, contact_id, channel: str = "whatsapp"):
    query = {"tenant_id": tenant_id, "contact_id": contact_id, "channel": channel}
    conv = await conversations_collection.find_one(query)
    if conv:
        return conv

    conv_doc = {
        "tenant_id": tenant_id,
        "contact_id": contact_id,
        "channel": channel,
        "mode": "bot",
        "status": "open",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    res = await conversations_collection.insert_one(conv_doc)
    conv = await conversations_collection.find_one({"_id": res.inserted_id})
    return conv


async def touch_conversation(conv_id):
    """Update last_message_at and updated_at to now."""
    try:
        now = datetime.now()
        await conversations_collection.update_one({"_id": conv_id}, {"$set": {"last_message_at": now, "updated_at": now}})
    except Exception:
        logger.exception("Failed to touch conversation %s", conv_id)
