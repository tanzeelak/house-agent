import os
from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from typesafe_client_raw import classify_message
from db import upsert_roommate, save_message, save_request

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

    # Typesafe classification
    classification = await classify_message(body)
    intent = classification["intent"]
    confidence = classification["intent_confidence"]
    is_urgent = classification["is_urgent"]

    print(f"  → intent={intent} (confidence={confidence:.2f}), urgent={is_urgent:.2f}")

    # Store in SQLite
    upsert_roommate(sender)
    save_message(sender, body, "inbound")
    if intent != "uncategorized" and confidence > 0.6:
        save_request(sender, intent, confidence, is_urgent, body)

    # TODO: action router
    # TODO: Claude response generation

    # For now, reply with the classification results
    reply_text = (
        f"Intent: {intent} (confidence: {confidence:.2f})\n"
        f"Urgent: {'yes' if is_urgent > 0.7 else 'no'} ({is_urgent:.2f})"
    )

    resp = MessagingResponse()
    resp.message(reply_text)
    return Response(content=str(resp), media_type="application/xml")
