from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MessageModel(BaseModel):
    sender_id: str
    message: str
    timestamp: datetime
    role: str  # 'user', 'assistant', or 'owner'
    session_id: Optional[str] = None
    message_id: Optional[str] = None
    status: Optional[str] = None
    id: Optional[str] = Field(default=None, alias="_id")

    class Config:
        from_attributes = True
        populate_by_name = True 