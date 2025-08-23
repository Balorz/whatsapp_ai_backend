import os
import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from app.services.bot import generate_ai_reply
from app.db.mongo_connection import tenants_collection
from app.models.message import MessageModel
from app.services.user import get_user_by_whatsapp, get_tenant_by_phone_number_id
from app.utils.whatsapp import send_message
from app.services.contacts import upsert_contact
from app.services.conversations import get_or_create_conversation
from app.services.messages import insert_message
from app.models.schemas import ContactModel, ConversationModel, MessageModel as NewMessageModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v19.0")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", f"https://graph.facebook.com/{WHATSAPP_API_VERSION}")

class WhatsAppAPIError(Exception):
    pass

class MessageProcessingError(Exception):
    pass

async def handle_incoming_message(data: Dict[str, Any]) -> None:
    if not WHATSAPP_TOKEN and not PHONE_NUMBER_ID:
        logger.error("Missing WhatsApp configuration: WHATSAPP_TOKEN or PHONE_NUMBER_ID")
        return
    
    try:
        messages = _extract_messages(data)
        if not messages:
            logger.info("No messages found in webhook data")
            return
        
        for message_data in messages:
            sender_id = message_data.get("from")
            logger.info(f"Processing message : {message_data}")
            if not sender_id:
                logger.warning("Message missing sender_id. Skipping.")
                continue

            # Try to resolve phone_number_id from the webhook message metadata (preferred)
            phone_number_id = message_data.get("phone_number_id") or PHONE_NUMBER_ID

            # Resolve tenant by phone_number_id; we need a tenant to attach contacts/messages to
            tenant = await get_tenant_by_phone_number_id(phone_number_id)
            if not tenant:
                logger.warning(f"Received message for unknown tenant phone_number_id={phone_number_id}. Skipping.")
                continue

            # Use tenant's access token if present, else fall back to global WHATSAPP_TOKEN
            access_token = tenant.get("access_token") or tenant.get("access_token_enc") or WHATSAPP_TOKEN
            if not access_token:
                logger.error(f"Tenant for phone_number_id={phone_number_id} has no access token configured. Skipping reply.")
                continue

            # Proceed to process message: contacts will be upserted inside _process_single_message
            await _process_single_message(message_data, phone_number_id, access_token)
            
    except Exception as e:
        logger.error(f"❌ Error handling incoming message: {e}")
        raise MessageProcessingError(f"Failed to process incoming message: {e}")

def _extract_messages(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    messages = []
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                entry_messages = value.get("messages", [])
                # extract phone_number_id if present in metadata
                phone_number_id = None
                try:
                    phone_number_id = value.get("metadata", {}).get("phone_number_id")
                except Exception:
                    phone_number_id = None

                for m in entry_messages:
                    # attach phone_number_id to each message for downstream processing
                    if phone_number_id:
                        m["phone_number_id"] = phone_number_id
                    messages.append(m)
    except Exception as e:
        logger.error(f"Error extracting messages: {e}")
        return []
    return messages

async def _process_single_message(message_data: Dict[str, Any], phone_number_id: str, access_token: str) -> bool:
    try:
        user_message = _extract_user_message(message_data)
        sender_id = message_data.get("from")
        message_id = message_data.get("id", "unknown")

        if not user_message or not sender_id:
            logger.warning(f"⚠️ Incomplete message data: sender={sender_id}, message={user_message}")
            return False

        logger.info(f"📩 [{message_id}] Incoming from {sender_id}: {user_message}")

        # Resolve tenant by phone_number_id
        tenant = await get_tenant_by_phone_number_id(phone_number_id)
        tenant_id = tenant.get("_id") if tenant else None

        # Upsert contact for this tenant
        contact = await upsert_contact(tenant_id, sender_id)
        contact_id = contact.get("_id") if contact else None

        # Get or create conversation
        conv = await get_or_create_conversation(tenant_id, contact_id, "whatsapp")
        conv_id = conv.get("_id")

        # Save user message into messages collection using messages service
        msg_doc = {
            "tenant_id": tenant_id,
            "conversation_id": conv_id,
            "contact_id": contact_id,
            "direction": "inbound",
            "wa_message_id": message_id,
            "wa_timestamp": datetime.now(),
            "wa_type": "text",
            "channel": "whatsapp",
            "content": {"text": user_message},
            "status": "received",
            "created_at": datetime.now()
        }
        try:
            await insert_message(msg_doc)
        except Exception:
            # idempotency or other insert failure; continue processing
            pass

        # Generate reply
        ai_reply = await generate_ai_reply(user_message)

        # Save assistant reply
        ai_msg_doc = {
            "tenant_id": tenant_id,
            "conversation_id": conv_id,
            "contact_id": contact_id,
            "direction": "outbound",
            "wa_type": "text",
            "channel": "whatsapp",
            "content": {"text": ai_reply},
            "status": "sent",
            "created_at": datetime.now(),
            "ai": {"model": None}
        }
        await insert_message(ai_msg_doc)
        logger.info(f"🤖 Reply to {sender_id}: {ai_reply}")

        # Send reply
        await send_whatsapp_reply(sender_id, ai_reply, phone_number_id, access_token)
        return True

    except Exception as e:
        logger.error(f"💥 Error processing message from {message_data.get('from', 'unknown')}: {e}")
        return False

def _extract_user_message(message_data: Dict[str, Any]) -> Optional[str]:
    try:
        return message_data.get("text", {}).get("body")
    except Exception as e:
        logger.error(f"Error extracting user message: {e}")
        return None

async def send_whatsapp_reply(recipient_id: str, message: str, phone_number_id: str, access_token: str) -> bool:
    if not access_token or not phone_number_id:
        logger.error("Missing WhatsApp credentials for user")
        return False

    url = f"{WHATSAPP_API_URL}/{phone_number_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "text": {"body": message}
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        resp = await send_message(phone_number_id, recipient_id, payload, access_token, WHATSAPP_API_URL)
        logger.info(f"✅ Message sent to {recipient_id} resp=%s", resp)
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send WhatsApp message: %s", e)
        return False
