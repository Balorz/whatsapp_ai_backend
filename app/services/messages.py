import logging
from datetime import datetime
from app.db.mongo_connection import messages_collection
from app.services.conversations import touch_conversation

logger = logging.getLogger(__name__)


async def insert_message(msg_doc: dict):
    """Insert a message document and update its conversation timestamp."""
    try:
        # Ensure created_at exists
        msg_doc.setdefault("created_at", datetime.now())
        res = await messages_collection.insert_one(msg_doc)
        # Update conversation last_message_at
        conv_id = msg_doc.get("conversation_id")
        if conv_id:
            await touch_conversation(conv_id)
        return res
    except Exception:
        logger.exception("Failed to insert message")
        raise


async def find_messages(query: dict, limit: int = 50, skip: int = 0):
    cursor = messages_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)
