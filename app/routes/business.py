from fastapi import APIRouter, HTTPException, Depends
from app.models.business import Business
from app.db.mongo_connection import db
from app.utils.auth import get_current_tenant
from app.utils.auth import TokenData

business_router = APIRouter(prefix="/business", tags=["Business"])

@business_router.post("/add")
async def add_business(business: Business, current_tenant: TokenData = Depends(get_current_tenant)):
    business_data = business.model_dump()
    business_data["tenant_id"] = current_tenant.tenant_id
    
    collection = db.businesses
    result = await collection.insert_one(business_data)
    if result.inserted_id:
        return {"message": "Business added successfully", "id": str(result.inserted_id)}
    raise HTTPException(status_code=500, detail="Failed to add business")

@business_router.get("/")
async def get_business(current_tenant: TokenData = Depends(get_current_tenant)):
    collection = db.businesses
    business = await collection.find_one({"tenant_id": current_tenant.tenant_id})
    if business:
        business["_id"] = str(business["_id"])
        return business
    raise HTTPException(status_code=404, detail="Business not found")