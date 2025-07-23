import re
import os
import httpx
from datetime import datetime
from app.db.mongo_connection import users_collection
from app.models.user import UserModel

FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_GRAPH_URL = os.getenv("FACEBOOK_GRAPH_URL", "https://graph.facebook.com")

class UserRegistrationError(Exception):
    pass

def validate_phone_number(phone: str) -> bool:
    # Basic E.164 format validation
    return bool(re.match(r"^\+\d{10,15}$", phone))

async def verify_facebook_token(access_token: str) -> str:
    # Verify token and get user id
    url = f"{FACEBOOK_GRAPH_URL}/me?access_token={access_token}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("id")
        raise UserRegistrationError("Invalid Facebook access token.")

async def register_user(whatsapp_number: str, fb_access_token: str) -> UserModel:
    if not validate_phone_number(whatsapp_number):
        raise UserRegistrationError("Invalid phone number format. Use E.164 format (e.g., +12345678901)")
    facebook_user_id = await verify_facebook_token(fb_access_token)
    # Check if user already exists
    existing = await users_collection.find_one({"whatsapp_number": whatsapp_number})
    if existing:
        raise UserRegistrationError("User already registered.")
    user = UserModel(
        whatsapp_number=whatsapp_number,
        facebook_user_id=facebook_user_id,
        registered_at=datetime.utcnow(),
        status="active"
    )
    await users_collection.insert_one(user.dict(by_alias=True, exclude_none=True))
    return user

async def get_user_by_whatsapp(whatsapp_number: str):
    return await users_collection.find_one({"whatsapp_number": whatsapp_number})

async def get_user_by_facebook_id(facebook_user_id: str):
    return await users_collection.find_one({"facebook_user_id": facebook_user_id})

async def upsert_user_with_onboarding(
    whatsapp_number: str,
    facebook_user_id: str,
    waba_id: str,
    phone_number_id: str,
    access_token: str
):
    # Upsert user by whatsapp_number or facebook_user_id
    query = {"$or": [
        {"whatsapp_number": whatsapp_number},
        {"facebook_user_id": facebook_user_id}
    ]}
    update = {
        "$set": {
            "whatsapp_number": whatsapp_number,
            "facebook_user_id": facebook_user_id,
            "waba_id": waba_id,
            "phone_number_id": phone_number_id,
            "access_token": access_token,
            "status": "active"
        },
        "$setOnInsert": {"registered_at": datetime.utcnow()}
    }
    await users_collection.update_one(query, update, upsert=True) 