import os
import httpx

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def generate_ai_reply(user_message: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-70b-8192",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a polite and professional AI assistant for a small local business on WhatsApp. "
                                "Answer clearly and concisely to help customers with product availability, pricing, and order support. "
                                "If you don't know the answer, politely say so and ask the customer to wait."
                            )
                        },
                        {
                            "role": "user",
                            "content": "Do you have basmati rice 5kg?"
                        },
                        {
                            "role": "assistant",
                            "content": "Yes, we have 5kg basmati rice available. Would you like to place an order?"
                        },
                        {
                            "role": "user",
                            "content": "What is the price of 2-liter mustard oil?"
                        },
                        {
                            "role": "assistant",
                            "content": "The 2-liter mustard oil is ₹280. Would you like it delivered today?"
                        },
                        {
                            "role": "user",
                            "content": user_message
                        }
                    ]
                }
            )

        data = response.json()
        print("📤 Groq raw response:", data)

        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        else:
            return "Sorry, I couldn't generate a valid reply. (No 'choices' found)"

    except Exception as e:
        return f"Sorry, I couldn't understand that. Error: {str(e)}"
