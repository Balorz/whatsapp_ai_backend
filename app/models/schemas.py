from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

class TenantModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    slug: str
    status: str = "active"
    phone_number_id: str
    phone_e164_enc: Optional[str]
    phone_hash: Optional[str]
    access_token_enc: Optional[str]
    verify_token_enc: Optional[str]
    password: Optional[str]
    settings: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        validate_by_name = True

class LoginRequest(BaseModel):
    phone_number: str
    password: str

class ContactModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    tenant_id: str
    wa_phone_e164_enc: str
    wa_phone_hash: str
    display_name: Optional[str]
    locale: Optional[str]
    timezone: Optional[str]
    consents: Optional[List[str]]
    attributes: Optional[Dict[str, Any]]
    last_seen_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        validate_by_name = True

class ConversationModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    tenant_id: str
    contact_id: str
    channel: str = "whatsapp"
    mode: str = "bot"
    status: str = "open"
    last_message_at: Optional[datetime]
    session_window_expires_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        validate_by_name = True

class MessageContentModel(BaseModel):
    text: Optional[str]
    media_url: Optional[str]
    caption: Optional[str]
    interactive: Optional[Dict[str, Any]]
    payload: Optional[Dict[str, Any]]

class MessageModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    tenant_id: str
    conversation_id: str
    contact_id: str
    direction: str  # inbound|outbound
    wa_message_id: Optional[str]
    wa_timestamp: Optional[datetime]
    wa_type: str = "text"
    channel: str = "whatsapp"
    content: Optional[MessageContentModel]
    status: str = "received"
    error_code: Optional[str]
    error_message: Optional[str]
    ai: Optional[Dict[str, Any]]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
        validate_by_name = True
