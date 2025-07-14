import os
import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from app.services.bot import generate_ai_reply
from app.db.mongo_connection import messages_collection
from app.models.message import MessageModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_API_URL = "https://graph.facebook.com/v19.0"

class WhatsAppAPIError(Exception):
    pass

class MessageProcessingError(Exception):
    pass

async def handle_incoming_message(data: Dict[str, Any]) -> None:
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.error("Missing WhatsApp configuration: WHATSAPP_TOKEN or PHONE_NUMBER_ID")
        return
    
    try:
        messages = _extract_messages(data)
        if not messages:
            logger.info("No messages found in webhook data")
            return
        
        for message_data in messages:
            await _process_single_message(message_data)
            
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
                messages.extend(entry_messages)
    except Exception as e:
        logger.error(f"Error extracting messages: {e}")
        return []
    return messages

async def _process_single_message(message_data: Dict[str, Any]) -> bool:
    try:
        user_message = _extract_user_message(message_data)
        sender_id = message_data.get("from")
        message_id = message_data.get("id", "unknown")

        if not user_message or not sender_id:
            logger.warning(f"⚠️ Incomplete message data: sender={sender_id}, message={user_message}")
            return False

        logger.info(f"📩 [{message_id}] Incoming from {sender_id}: {user_message}")

        # Save user message
        user_msg = MessageModel(
            sender_id=sender_id,
            message=user_message,
            timestamp=datetime.now(timezone.utc),
            role="user",
            message_id=message_id
        )
        await messages_collection.insert_one(user_msg.dict(by_alias=True, exclude_none=True))

        # Generate reply
        ai_reply = await generate_ai_reply(user_message)
        ai_msg = MessageModel(
            sender_id=sender_id,
            message=ai_reply,
            timestamp=datetime.now(timezone.utc),
            role="assistant"
        )
        await messages_collection.insert_one(ai_msg.dict(by_alias=True, exclude_none=True))
        logger.info(f"🤖 Reply to {sender_id}: {ai_reply}")

        # Send reply
        await send_whatsapp_reply(sender_id, ai_reply)
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

async def send_whatsapp_reply(recipient_id: str, message: str) -> bool:
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.error("Missing WhatsApp configuration")
        return False

    url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "text": {"body": message}
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                logger.info(f"✅ Message sent to {recipient_id}")
                return True
            else:
                error_data = response.json() if response.content else {}
                logger.error(f"❌ API Error {response.status_code}: {error_data}")
                return False

    except httpx.TimeoutException:
        logger.error(f"⏰ Timeout while sending message to {recipient_id}")
        return False
    except httpx.RequestError as e:
        logger.error(f"🌐 Network error sending to {recipient_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"💥 Unexpected error sending to {recipient_id}: {e}")
        return False
