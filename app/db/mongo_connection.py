import motor.motor_asyncio
import os
from dotenv import load_dotenv
import logging
from typing import Optional

load_dotenv()

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
if not DB_NAME:
    raise ValueError("DB_NAME environment variable is not set")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Collections following the requested design
tenants_collection = db["tenants"]
contacts_collection = db["contacts"]
conversations_collection = db["conversations"]
messages_collection = db["messages"]

# Backwards compatibility alias (existing code expects users_collection)
users_collection = tenants_collection


async def ensure_indexes() -> None:
    """Create required indexes for the collections. Safe to call on startup (idempotent).

    This implements the indexes described in the new DB design.
    """
    try:
        # Tenants indexes
        await tenants_collection.create_index("slug", unique=True)
        await tenants_collection.create_index("phone_number_id", unique=True)
        await tenants_collection.create_index("phone_hash", unique=True)

        # Contacts indexes
        await contacts_collection.create_index([("tenant_id", 1), ("wa_phone_hash", 1)], unique=True)
        await contacts_collection.create_index([("tenant_id", 1), ("last_seen_at", -1)])

        # Conversations indexes
        await conversations_collection.create_index([("tenant_id", 1), ("contact_id", 1), ("channel", 1)])
        await conversations_collection.create_index([("tenant_id", 1), ("status", 1), ("last_message_at", -1)])
        await conversations_collection.create_index([("tenant_id", 1), ("last_message_at", -1)])

        # Messages indexes
        await messages_collection.create_index([("tenant_id", 1), ("conversation_id", 1), ("created_at", -1)])
        await messages_collection.create_index([("tenant_id", 1), ("contact_id", 1), ("created_at", -1)])

        # Ensure uniqueness for wa_message_id but only when it exists.
        # Previous implementation enforced uniqueness even when wa_message_id was null,
        # which caused E11000 errors when inserting multiple local-only messages.
        # To fix this, drop any existing conflicting index and create a partial unique index
        # that only applies when wa_message_id exists.
        try:
            # Inspect existing indexes and drop any index matching the key pattern
            existing = await messages_collection.index_information()
            for name, info in existing.items():
                # info['key'] is a list of tuples
                if info.get('key') == [('tenant_id', 1), ('wa_message_id', 1), ('contact_id', 1)]:
                    # Drop the old index to replace with a partial index
                    await messages_collection.drop_index(name)
                    logger.info(f"Dropped old messages index: {name}")
        except Exception:
            # Non-fatal if we can't inspect/drop (permissions), proceed to create the index
            logger.exception("Could not inspect or drop existing messages index (continuing)")

        # Create a partial unique index that only enforces uniqueness when wa_message_id exists
        await messages_collection.create_index(
            [("tenant_id", 1), ("wa_message_id", 1), ("contact_id", 1)],
            unique=True,
            partialFilterExpression={"wa_message_id": {"$exists": True}}
        )

        await messages_collection.create_index([("tenant_id", 1), ("status", 1), ("created_at", -1)])

        logger.info("MongoDB indexes ensured")
    except Exception as e:
        logger.exception(f"Failed to ensure MongoDB indexes: {e}")
