from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.message import message_router
from app.routes.user import user_router
from dotenv import load_dotenv
from app.db.mongo_connection import ensure_indexes

load_dotenv()

app = FastAPI(
    title="WhatsApp AI Assistant",
    description="A scalable FastAPI backend for auto-replying to WhatsApp messages using AI.",
    version="0.1.0"
)

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(message_router)
app.include_router(user_router)


@app.on_event("startup")
async def startup_event():
    # Ensure MongoDB indexes are created on startup
    try:
        await ensure_indexes()
    except Exception:
        # ensure_indexes logs exceptions internally; don't crash startup here
        pass
