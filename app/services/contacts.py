import logging
from datetime import datetime
from app.db.mongo_connection import contacts_collection

logger = logging.getLogger(__name__)


async def upsert_contact(tenant_id, wa_phone_hash, display_name: str | None = None):
    """Upsert a contact by tenant_id + wa_phone_hash and return the stored document."""
    try:
        query = {"tenant_id": tenant_id, "wa_phone_hash": wa_phone_hash}
        update = {
            "$set": {"tenant_id": tenant_id, "wa_phone_hash": wa_phone_hash, "last_seen_at": datetime.now()},
            "$setOnInsert": {"created_at": datetime.now()}
        }
        if display_name:
            update["$set"]["display_name"] = display_name

        await contacts_collection.update_one(query, update, upsert=True)
        doc = await contacts_collection.find_one(query)
        return doc
    except Exception as e:
        logger.exception("Failed to upsert contact: %s", e)
        return None
