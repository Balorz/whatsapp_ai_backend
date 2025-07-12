from fastapi import FastAPI
from app.routes.message import message_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="WhatsApp AI Assistant",
    description="A scalable FastAPI backend for auto-replying to WhatsApp messages using AI.",
    version="0.1.0"
)

app.include_router(message_router)
