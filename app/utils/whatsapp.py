import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def _mask_token(token: Optional[str]) -> str:
    if not token:
        return "<no-token>"
    if len(token) <= 10:
        return token[:4] + "..."
    return token[:8] + "..." + token[-4:]


async def send_message(phone_number_id: str, to: str, payload: Dict[str, Any], access_token: str, api_url: str) -> Dict[str, Any]:
    """Send a WhatsApp message via Graph API. Returns response.json() on success or raises.

    This function logs a masked token and the phone_number_id for diagnostics.
    """
    url = f"{api_url}/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    logger.info("WhatsApp send -> phone_number_id=%s token=%s to=%s payload=%s", phone_number_id, _mask_token(access_token), to, {k: v for k, v in payload.items() if k != 'text'})

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        content = None
        try:
            content = resp.json()
        except Exception:
            content = {"raw": resp.text}

        if resp.status_code == 200 or resp.status_code == 201:
            logger.info("WhatsApp API success status=%s", resp.status_code)
            return content
        else:
            logger.error("WhatsApp API error status=%s body=%s", resp.status_code, content)
            raise Exception({"status_code": resp.status_code, "body": content})
