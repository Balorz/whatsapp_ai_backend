from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserModel(BaseModel):
    whatsapp_number: str
    facebook_user_id: str
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    status: Optional[str] = "active"
    id: Optional[str] = Field(default=None, alias="_id")
    waba_id: Optional[str] = None
    phone_number_id: Optional[str] = None
    access_token: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True 