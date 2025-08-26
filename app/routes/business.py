from fastapi import APIRouter, HTTPException
from app.models.business import Business
from app.db.mongo_connection import db

business_router = APIRouter(prefix="/business", tags=["Business"])

@business_router.post("/add")
async def add_business(business: Business):
    collection = db.businesses
    result = await collection.insert_one(business.model_dump())
    if result.inserted_id:
        return {"message": "Business added successfully", "id": str(result.inserted_id)}
    raise HTTPException(status_code=500, detail="Failed to add business")