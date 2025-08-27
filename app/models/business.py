from pydantic import BaseModel, Field
from typing import Optional

class Business(BaseModel):
    business_name: str
    business_type: str
    email: str
    owner_name: str
