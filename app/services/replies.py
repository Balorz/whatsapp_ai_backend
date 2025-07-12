import os
import requests
from app.services.bot import generate_ai_reply

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

async def handle_incoming_message(data: dict):
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                if messages:
                    for message in messages:
                        user_message = message.get("text", {}).get("body")
                        sender_id = message.get("from")
                        reply = await generate_ai_reply(user_message)
                        print(f"Sending reply to {sender_id}: {reply}")
                        await send_whatsapp_reply(sender_id, reply)
    except Exception as e:
        print(f"Error handling message: {e}")

async def send_whatsapp_reply(recipient_id: str, message: str):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "text": {"body": message}
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Sent reply:", response.status_code, response.text)
