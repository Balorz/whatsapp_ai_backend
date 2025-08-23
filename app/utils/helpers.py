from typing import Dict, Any
from bson.objectid import ObjectId
from datetime import datetime


def _objid_to_str(val):
    try:
        return str(val)
    except Exception:
        return val


def _dt_to_iso(val):
    try:
        return val.isoformat()
    except Exception:
        return val


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize a MongoDB document into JSON-friendly types.

    - ObjectId -> str
    - datetime -> ISO string
    """
    if not doc:
        return {}
    out = dict(doc)
    # Convert ObjectId fields to str where obvious
    for k in ("_id", "tenant_id", "conversation_id", "contact_id"):
        if k in out and out[k] is not None and isinstance(out[k], ObjectId):
            out[k] = _objid_to_str(out[k])
    # Convert datetimes to isoformat
    for dt_key in ("wa_timestamp", "created_at", "last_message_at", "updated_at", "last_seen_at"):
        if dt_key in out and out[dt_key] is not None and isinstance(out[dt_key], datetime):
            out[dt_key] = _dt_to_iso(out[dt_key])
    return out


def serialize_tenant(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return {}
    out = dict(doc)
    # Convert common ObjectId fields to string
    if "_id" in out and isinstance(out["_id"], ObjectId):
        out["_id"] = _objid_to_str(out["_id"])
    # Convert datetimes to isoformat
    for dt_key in ("created_at", "updated_at"):
        if dt_key in out and isinstance(out[dt_key], datetime):
            out[dt_key] = _dt_to_iso(out[dt_key])
    return out
