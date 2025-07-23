from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from app.services.user import register_user, UserRegistrationError, upsert_user_with_onboarding
import logging
import os

user_router = APIRouter()

class SignupRequest(BaseModel):
    whatsapp_number: str
    facebook_access_token: str

@user_router.post("/signup")
async def signup(request: SignupRequest):
    try:
        user = await register_user(request.whatsapp_number, request.facebook_access_token)
        return {"success": True, "user": user.dict(by_alias=True, exclude_none=True)}
    except UserRegistrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@user_router.get("/embedded-signup", response_class=HTMLResponse)
async def embedded_signup_page():
    app_id = os.getenv("FACEBOOK_APP_ID")
    # This is the config_id from your Facebook Login for Business configuration
    config_id = os.getenv("FB_LOGIN_CONFIG_ID")  # Add this to your .env
    graph_api_version = "v19.0"  # Or latest supported version
    print(f"app_id: {app_id}, config_id: {config_id}")
    if not app_id or not config_id:
        return HTMLResponse(
            "<h2>Configuration Error</h2><p>FACEBOOK_APP_ID or FB_LOGIN_CONFIG_ID not set in .env.</p>",
            status_code=500
        )

    html_content = f"""
    <html>
    <head>
      <title>WhatsApp Embedded Signup</title>
      <script async defer crossorigin="anonymous" src="https://connect.facebook.net/en_US/sdk.js"></script>
    </head>
    <body>
      <h2>WhatsApp Business Embedded Signup</h2>
      <button onclick="launchWhatsAppSignup()">Start Signup</button>
      <div id="result"></div>
      <script>
        window.fbAsyncInit = function() {{
          FB.init({{
            appId      : '{app_id}',
            autoLogAppEvents: true,
            xfbml      : true,
            version    : '{graph_api_version}'
          }});
        }};

        // Listen for onboarding result
        window.addEventListener('message', (event) => {{
          if (!event.origin.endsWith('facebook.com')) return;
          try {{
            const data = JSON.parse(event.data);
            if (data.type === 'WA_EMBEDDED_SIGNUP') {{
              document.getElementById('result').innerText = 'Onboarding result: ' + JSON.stringify(data, null, 2);
              // Send onboarding data to your backend for processing
              fetch('/facebook/onboarding-result', {{
                method: 'POST',
                headers: {{
                  'Content-Type': 'application/json'
                }},
                body: JSON.stringify(data)
              }})
              .then(res => res.text())
              .then(msg => {{
                document.getElementById('result').innerHTML += '<br>' + msg;
              }});
            }}
          }} catch (e) {{
            console.log('message event error:', e, event.data);
          }}
        }});

        // Launch embedded signup
        function launchWhatsAppSignup() {{
          FB.login(function(response) {{
            if (response.authResponse) {{
              // The onboarding result will be sent via the message event listener above
              // You can also handle the response here if needed
              console.log('FB.login response:', response);
            }} else {{
              alert('User cancelled login or did not fully authorize.');
            }}
          }}, {{
            config_id: '{config_id}',
            response_type: 'code',
            override_default_response_type: true,
            extras: {{
              feature: 'whatsapp_embedded_signup',
              version: 2,
              sessionInfoVersion: 3
            }}
          }});
        }}
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@user_router.post("/facebook/onboarding-result")
async def facebook_onboarding_result(request: Request):
    data = await request.json()
    print(f"Received onboarding data: {data}")
    # Extract the relevant info from the data object
    # Example structure: data = { "data": { "phone_number_id": "...", "waba_id": "...", ... }, "type": "WA_EMBEDDED_SIGNUP", "event": "FINISH" }
    onboarding = data.get("data", {})
    waba_id = onboarding.get("waba_id")
    phone_number_id = onboarding.get("phone_number_id")
    business_id = onboarding.get("business_id")
    # You may want to store these in your DB, or trigger further onboarding steps
    # For now, just acknowledge receipt
    print("Received onboarding data:", onboarding)
    return PlainTextResponse("Onboarding data received. You can now complete backend onboarding steps.")

@user_router.get("/facebook/callback")
async def facebook_callback(request: Request):
    params = dict(request.query_params)
    logging.info(f"Facebook callback params: {params}")
    # Extract required onboarding params
    waba_id = params.get("waba_id")
    phone_number_id = params.get("phone_number_id")
    access_token = params.get("access_token")
    whatsapp_number = params.get("whatsapp_number")
    facebook_user_id = params.get("facebook_user_id")
    if waba_id and phone_number_id and access_token and whatsapp_number and facebook_user_id:
        await upsert_user_with_onboarding(
            whatsapp_number=whatsapp_number,
            facebook_user_id=facebook_user_id,
            waba_id=waba_id,
            phone_number_id=phone_number_id,
            access_token=access_token
        )
        return HTMLResponse(f"<h2>Signup Complete!</h2><p>Your WhatsApp Business number is now onboarded and ready to use.</p><pre>{params}</pre>")
    else:
        return HTMLResponse(f"<h2>Signup Failed</h2><p>Missing required onboarding parameters.</p><pre>{params}</pre>", status_code=400) 