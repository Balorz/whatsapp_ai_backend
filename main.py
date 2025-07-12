from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def home():
    return JSONResponse(content={"message": "WhatsApp AI Backend is running!"})
