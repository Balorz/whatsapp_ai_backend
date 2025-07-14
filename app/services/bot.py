import os
import httpx
import asyncio
from typing import Dict, Any
from app.config.prompt_loader import prompt_loader

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

class GroqAPIError(Exception):
    """Custom exception for Groq API errors."""
    pass

# List of fallback models in priority order
MODEL_FALLBACKS = [
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "llama3-8b-8192"
]

async def generate_ai_reply(user_message: str) -> str:
    """
    Try generating reply using fallback models if primary fails.
    """
    if not GROQ_API_KEY:
        return "Error: GROQ_API_KEY not configured"

    last_error = None

    for model in MODEL_FALLBACKS:
        try:
            payload = await _build_request_payload(user_message, model)
            response = await _make_api_request(payload)
            return _parse_response(response)

        except GroqAPIError as e:
            print(f"⚠️ Model {model} failed: {e}")
            last_error = e
            continue

    return f"Sorry, I couldn't process your message right now. Please try again later. ({last_error})"

async def _build_request_payload(user_message: str, model_name: str) -> Dict[str, Any]:
    """Build the API request payload using specified model."""
    api_config = prompt_loader.get_api_config()
    messages = prompt_loader.build_messages(user_message)

    return {
        "model": model_name,
        "messages": messages,
        "max_tokens": api_config.get("max_tokens", 500),
        "temperature": api_config.get("temperature", 0.7)
    }

async def _make_api_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make the API request to Groq with retry logic on rate limit.
    """
    retries = 3
    backoff = 5  # fallback backoff in case the API doesn't suggest retry time

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(retries):
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 429:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "")
                print(f"⚠️ Rate limit hit: {error_message}")

                # Try to extract retry time from message
                try:
                    retry_seconds = float(error_message.split("try again in ")[-1].split("s")[0])
                except Exception:
                    retry_seconds = backoff

                await asyncio.sleep(retry_seconds)
                continue  # retry again

            else:
                error_data = response.json() if response.content else {}
                raise GroqAPIError(f"HTTP {response.status_code}: {error_data}")

        raise GroqAPIError("Retry limit exceeded due to rate limiting.")

def _parse_response(response_data: Dict[str, Any]) -> str:
    """Parse the API response and extract the generated text."""
    print("📤 Groq raw response:", response_data)

    if "choices" not in response_data or not response_data["choices"]:
        return "Sorry, I couldn't generate a valid reply. (No 'choices' found)"
    
    try:
        content = response_data["choices"][0]["message"]["content"]
        return content.strip()
    except (KeyError, IndexError) as e:
        return f"Sorry, I couldn't parse the response. Error: {str(e)}"
