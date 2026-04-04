import os
from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN"),
)
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")


@app.post("/webhook")
async def webhook(request: Request):
    form = await request.form()
    sender = form.get("From", "")       # e.g. "whatsapp:+1234567890"
    body = form.get("Body", "").strip()

    print(f"[{sender}] {body}")

    # TODO: Typesafe classification
    # TODO: action router
    # TODO: Claude response generation
    # TODO: log to SQLite

    # For now, echo back to confirm the webhook works
    reply_text = f"Got your message: {body}"

    resp = MessagingResponse()
    resp.message(reply_text)
    return Response(content=str(resp), media_type="application/xml")
