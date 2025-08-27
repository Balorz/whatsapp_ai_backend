# WhatsApp AI Backend MVP

This project provides a Minimum Viable Product (MVP) for a WhatsApp AI Assistant backend using FastAPI, designed to automatically reply to WhatsApp messages using an AI model (Groq).

## Features

-   **WhatsApp Webhook:** Receives incoming messages from WhatsApp.
-   **AI-Powered Replies:** Integrates with the Groq API to generate intelligent responses.
-   **Automatic Replies:** Sends AI-generated replies back to WhatsApp users.
-   **Scalable Architecture:** Built with FastAPI for high performance and scalability.
-   **MongoDB Integration:** Stores messages, contacts, and conversations.

## Setup and Installation

Follow these steps to set up and run the WhatsApp AI Backend MVP.

### Prerequisites

-   Python 3.9+
-   MongoDB (running locally or accessible via a connection string)
-   WhatsApp Business Account and API access
-   Groq API Key

### 1. Clone the Repository

```bash
git clone <repository_url>
cd whatsapp_ai_backend
```

### 2. Create and Activate a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the `whatsapp_ai_backend` directory based on the `.env.example` provided, and fill in your credentials.

```dotenv
# WhatsApp API Configuration
WHATSAPP_TOKEN="YOUR_WHATSAPP_ACCESS_TOKEN"
PHONE_NUMBER_ID="YOUR_WHATSAPP_PHONE_NUMBER_ID"
VERIFY_TOKEN="YOUR_WEBHOOK_VERIFY_TOKEN" # Choose a strong, random token

# Groq API Configuration
GROQ_API_KEY="YOUR_GROQ_API_KEY"

# MongoDB Configuration
MONGO_URI="mongodb://localhost:27017/whatsapp_ai_db"
```

**Explanation of Environment Variables:**

-   `WHATSAPP_TOKEN`: Your permanent access token from the WhatsApp Business Platform.
-   `PHONE_NUMBER_ID`: The ID of your WhatsApp Business Phone Number.
-   `VERIFY_TOKEN`: A token you define. This is used by WhatsApp to verify your webhook URL. Make sure it's a strong, random string.
-   `GROQ_API_KEY`: Your API key obtained from the Groq platform.
-   `MONGO_URI`: The connection string for your MongoDB instance. If running locally with default settings, `mongodb://localhost:27017/whatsapp_ai_db` should work.

### 5. Run the Application

Start the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

This will start the server on `http://0.0.0.0:8000`. The `--reload` flag is useful for development as it restarts the server on code changes.

### 6. Configure WhatsApp Webhook

1.  **Deploy your application:** For WhatsApp to reach your webhook, your backend needs to be publicly accessible. You can use services like Ngrok (for local testing) or deploy to a cloud provider (e.g., AWS, Heroku, Render).
2.  **Set up Webhook in WhatsApp Business Platform:**
    *   Go to your WhatsApp Business Account in Meta for Developers.
    *   Navigate to your App Dashboard -> WhatsApp -> Configuration.
    *   Under "Webhook," click "Edit."
    *   Set the "Callback URL" to your deployed backend's webhook endpoint (e.g., `https://your-deployed-url.com/webhook`).
    *   Enter the `VERIFY_TOKEN` you defined in your `.env` file.
    *   Click "Verify and Save."
3.  **Subscribe to Message Webhook Fields:** After successful verification, click "Manage" next to the Webhook URL and subscribe to the `messages` field.

Now, when a message is sent to your WhatsApp Business Number, your backend will receive it, process it with AI, and send a reply.

## Project Structure

```
whatsapp_ai_backend/
├── app/
│   ├── main.py             # Main FastAPI application entry point
│   ├── config/             # Configuration files (e.g., prompt_loader)
│   ├── db/                 # Database connection and operations
│   ├── models/             # Pydantic models for data validation
│   ├── routes/             # API routes (e.g., message, user)
│   ├── services/           # Business logic and external service integrations (e.g., bot, replies)
│   └── utils/              # Utility functions
├── .env.example            # Example environment variables file
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
```

## Contributing

Feel free to fork the repository, open issues, and submit pull requests.