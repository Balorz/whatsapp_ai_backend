from typing import Dict, Any, List
from bson.objectid import ObjectId
from datetime import datetime

def serialize_doc(doc: Any) -> Any:
    """
    Recursively serialize a MongoDB document (or a list of documents)
    into JSON-friendly types.
    - ObjectId -> str
    - datetime -> ISO string
    """
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    
    if not isinstance(doc, dict):
        return doc

    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = serialize_doc(v)
        elif isinstance(v, list):
            out[k] = serialize_doc(v)
        else:
            out[k] = v
            
    # Rename "_id" to "id" for frontend convenience
    if "_id" in out:
        out["id"] = out.pop("_id")
        
    return out

def serialize_tenant(doc: Dict[str, Any]) -> Dict[str, Any]:
    return serialize_doc(doc)