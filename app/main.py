from dotenv import load_dotenv, find_dotenv

# Find and load the .env file
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes.message import message_router
from app.routes.user import user_router
from app.db.mongo_connection import ensure_indexes
from app.routes.business import business_router
from app.routes.conversations import conversations_router
from app.routes.dashboard import dashboard_router

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

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

app.include_router(message_router)
app.include_router(user_router)
app.include_router(business_router)
app.include_router(conversations_router)
app.include_router(dashboard_router)


@app.on_event("startup")
async def startup_event():
    # Ensure MongoDB indexes are created on startup
    try:
        await ensure_indexes()
    except Exception:
        # ensure_indexes logs exceptions internally; don't crash startup here
        pass