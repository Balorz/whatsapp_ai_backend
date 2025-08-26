import re
import os
import httpx
import hashlib
from datetime import datetime
from app.db.mongo_connection import users_collection, tenants_collection
from app.models.user import UserModel
from app.models.schemas import TenantModel
import httpx
import os
import logging
from passlib.context import CryptContext

GRAPH_API = os.getenv("FACEBOOK_GRAPH_URL", "https://graph.facebook.com")

FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_GRAPH_URL = os.getenv("FACEBOOK_GRAPH_URL", "https://graph.facebook.com")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRegistrationError(Exception):
    pass

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password_sync(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def verify_password(phone_number: str, plain_password: str):
    tenant = await tenants_collection.find_one({"phone_e164_enc": phone_number})
    if not tenant:
        return None
    if not verify_password_sync(plain_password, tenant["password"]):
        return None
    return tenant

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

import re
import os
import httpx
import hashlib
from datetime import datetime
from app.db.mongo_connection import users_collection, tenants_collection
from app.models.user import UserModel
from app.models.schemas import TenantModel
import httpx
import os
import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

GRAPH_API = os.getenv("FACEBOOK_GRAPH_URL", "https://graph.facebook.com")

FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_GRAPH_URL = os.getenv("FACEBOOK_GRAPH_URL", "https://graph.facebook.com")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRegistrationError(Exception):
    pass

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password_sync(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def verify_password(phone_number: str, plain_password: str):
    tenant = await tenants_collection.find_one({"phone_e164_enc": phone_number})
    if not tenant:
        return None
    if not verify_password_sync(plain_password, tenant["password"]):
        return None
    return tenant

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
    password: str,
    facebook_user_id: str,
    waba_id: str,
    phone_number_id: str,
    access_token: str
):
    """
    Onboarding/upsert for embedded signup. This will create or update a tenant document
    in the `tenants` collection using the provided onboarding payload.

    Fields set:
    - name, slug, status
    - phone_number_id (provider id), phone_e164_enc (raw number), phone_hash (sha256)
    - access_token_enc (stored as-is here), waba_id, verify_token_enc (left empty)
    - settings (empty), created_at, updated_at
    """

    def _slugify(s: str) -> str:
        s = s.lower()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        s = s.strip("-")
        return s or "tenant"

    def _phone_hash(phone: str) -> str:
        # simple sha256 hash for idempotent lookup (not cryptographic secrecy)
        if not phone:
            return ""
        h = hashlib.sha256()
        h.update(phone.encode("utf-8"))
        return h.hexdigest()

    # Normalize phone input - assume caller provides E.164; keep as-is
    phone_e164 = whatsapp_number
    slug_base = f"{waba_id or phone_number_id or whatsapp_number}"
    slug = _slugify(slug_base)
    phone_hash = _phone_hash(phone_e164)
    hashed_password = get_password_hash(password) if password else None

    tenant_query = {"$or": [
        {"phone_number_id": phone_number_id},
        {"waba_id": waba_id},
        {"phone_e164_enc": phone_e164}
    ]}

    now = datetime.utcnow()
    update_doc = {
        "name": slug.replace("-", " "),
        "slug": slug,
        "status": "active",
        "phone_number_id": phone_number_id,
        "phone_e164_enc": phone_e164,
        "phone_hash": phone_hash,
        "access_token_enc": access_token,
        "verify_token_enc": None,
        "waba_id": waba_id,
        "settings": {},
        "updated_at": now
    }
    if hashed_password:
        update_doc["password"] = hashed_password

    tenant_doc = {
        "$set": update_doc,
        "$setOnInsert": {
            "created_at": now
        }
    }

    # Upsert tenant
    await tenants_collection.update_one(tenant_query, tenant_doc, upsert=True)

    # Return the tenant document
    tenant = await tenants_collection.find_one({"phone_number_id": phone_number_id})
    if not tenant:
        # fallback: try waba_id
        tenant = await tenants_collection.find_one({"waba_id": waba_id})
    logger.info(f"Tenant _id: {tenant.get('_id')}")
    return tenant


async def get_tenant_by_phone_number_id(phone_number_id: str):
    return await tenants_collection.find_one({"phone_number_id": phone_number_id})


async def get_tenant_by_phone_hash(phone_hash: str):
    return await tenants_collection.find_one({"phone_hash": phone_hash})


async def discover_tenant_from_facebook(access_token: str, whatsapp_number: str, password: str = None):
    # Verify facebook token user id
    facebook_user_id = None
    try:
        facebook_user_id = await verify_facebook_token(facebook_access_token)
    except Exception:
        # still proceed but with no facebook_user_id
        facebook_user_id = None

    # Try discovery
    disco = await discover_tenant_from_facebook(facebook_access_token, whatsapp_number)
    if disco:
        tenant = await upsert_user_with_onboarding(
            whatsapp_number=whatsapp_number,
            password=password,
            facebook_user_id=facebook_user_id,
            waba_id=disco.get("waba_id"),
            phone_number_id=disco.get("phone_number_id"),
            access_token=disco.get("access_token")
        )
        return tenant

    # Fallback: create tenant placeholder using available fields
    tenant = await upsert_user_with_onboarding(
        whatsapp_number=whatsapp_number,
        password=password,
        facebook_user_id=facebook_user_id,
        waba_id=None,
        phone_number_id=None,
        access_token=None
    )
    return tenant


async def get_tenant_by_phone_number_id(phone_number_id: str):
    return await tenants_collection.find_one({"phone_number_id": phone_number_id})


async def get_tenant_by_phone_hash(phone_hash: str):
    return await tenants_collection.find_one({"phone_hash": phone_hash})


async def discover_tenant_from_facebook(access_token: str, whatsapp_number: str) -> dict | None:
    """Best-effort discovery of waba_id, phone_number_id and page access token using Graph API.

    Returns a dict with keys: waba_id, phone_number_id, phone_number, access_token (page token)
    or None on failure.
    """
    logger = logging.getLogger(__name__)
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # Verify token and get user id
            me = await client.get(f"{GRAPH_API}/me?access_token={access_token}")
            if me.status_code != 200:
                logger.debug("/me returned non-200: %s %s", me.status_code, me.text)
                return None

            # List pages the user manages
            pages_resp = await client.get(f"{GRAPH_API}/me/accounts?access_token={access_token}")
            if pages_resp.status_code != 200:
                logger.debug("/me/accounts returned non-200: %s %s", pages_resp.status_code, pages_resp.text)
                return None
            pages = pages_resp.json().get("data", [])
            if not pages:
                logger.debug("No pages found for user during discovery")

            # For each page, try to get whatsapp_business_account field and phone numbers
            for page in pages:
                page_id = page.get("id")
                # Prefer access_token included in /me/accounts entry if present
                page_token = page.get("access_token")

                # Request whatsapp_business_account field (requires appropriate scopes)
                page_info = await client.get(f"{GRAPH_API}/{page_id}?fields=whatsapp_business_account&access_token={access_token}")
                if page_info.status_code != 200:
                    logger.debug("Page info lookup failed for %s: %s %s", page_id, page_info.status_code, page_info.text)
                    continue
                pi = page_info.json()
                waba = pi.get("whatsapp_business_account")
                if not waba:
                    logger.debug("Page %s has no whatsapp_business_account", page_id)
                    continue
                waba_id = waba.get("id") if isinstance(waba, dict) else waba

                # Get phone numbers for this WABA using the user token (or page token if available)
                token_for_call = page_token or access_token
                phones_resp = await client.get(f"{GRAPH_API}/{waba_id}/phone_numbers?access_token={token_for_call}")
                if phones_resp.status_code != 200:
                    logger.debug("WABA phone_numbers lookup failed for %s: %s %s", waba_id, phones_resp.status_code, phones_resp.text)
                    continue
                phones = phones_resp.json().get("data", [])
                if not phones:
                    logger.debug("No phone numbers for WABA %s", waba_id)
                    continue

                # Try to match by provided whatsapp_number, else pick the first
                matched = None
                for p in phones:
                    candidate = p.get("phone_number") or p.get("display_phone_number")
                    if not candidate:
                        continue
                    if candidate == whatsapp_number or whatsapp_number in candidate:
                        matched = p
                        break

                if not matched:
                    matched = phones[0]

                logger.info("Discovered WABA %s phone %s (phone_number_id=%s) via page %s", waba_id, matched.get("phone_number"), matched.get("id"), page_id)

                return {
                    "waba_id": waba_id,
                    "phone_number_id": matched.get("id"),
                    "phone_number": matched.get("phone_number") or matched.get("display_phone_number"),
                    "access_token": page_token or access_token
                }

        except Exception as exc:
            logger.exception("Exception during Graph discovery: %s", exc)
            return None

    return None


async def discover_and_upsert_tenant(facebook_access_token: str, whatsapp_number: str, password: str = None):
    # Verify facebook token user id
    facebook_user_id = None
    try:
        facebook_user_id = await verify_facebook_token(facebook_access_token)
    except Exception:
        # still proceed but with no facebook_user_id
        facebook_user_id = None

    # Try discovery
    disco = await discover_tenant_from_facebook(facebook_access_token, whatsapp_number)
    if disco:
        tenant = await upsert_user_with_onboarding(
            whatsapp_number=whatsapp_number,
            password=password,
            facebook_user_id=facebook_user_id,
            waba_id=disco.get("waba_id"),
            phone_number_id=disco.get("phone_number_id"),
            access_token=disco.get("access_token")
        )
        return tenant

    # Fallback: create tenant placeholder using available fields
    tenant = await upsert_user_with_onboarding(
        whatsapp_number=whatsapp_number,
        password=password,
        facebook_user_id=facebook_user_id,
        waba_id=None,
        phone_number_id=None,
        access_token=None
    )
    return tenant