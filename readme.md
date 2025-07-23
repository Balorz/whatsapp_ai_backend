# WhatsApp AI Backend

## Setup Instructions

### 1. Environment Variables
Create a `.env` file in the root directory with the following variables:

```
MONGO_URI=your_mongodb_uri
DB_NAME=your_db_name
WHATSAPP_TOKEN=your_whatsapp_token
PHONE_NUMBER_ID=your_phone_number_id
VERIFY_TOKEN=your_webhook_verify_token
GROQ_API_KEY=your_groq_api_key
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
```

### 2. Install Dependencies
```
pip install -r requirements.txt
```

### 3. Ngrok Setup
Start your FastAPI server locally, then run:
```
ngrok http 8000
```
Copy the HTTPS URL from ngrok and set it as your webhook URL in the Meta (Facebook) developer portal.

### 4. Facebook Authentication
- Users must provide a valid Facebook access token during signup.
- The backend verifies the token and fetches the Facebook user ID.
- Make sure your Facebook app is set up to allow user access tokens for testing.

### 5. User Signup
Send a POST request to `/signup` with JSON body:
```
{
  "whatsapp_number": "+12345678901",
  "facebook_access_token": "user_facebook_access_token"
}
```

### 6. Testing
- Use [pytest](https://docs.pytest.org/) for unit and integration tests.
- Place your tests in a `tests/` directory and follow standard pytest conventions.

### 7. Running the App
```
uvicorn app.main:app --reload
```

---
For more details, see inline comments in the codebase.