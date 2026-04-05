import os
from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from typesafe_client_raw import classify_message
from db import upsert_roommate, save_message, save_request
from response_gen import generate_reply, extract_details
from sheets import append_candidate
from maintenance import submit_maintenance_request

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

    is_directed = classification.get("is_directed_at_agent", 1.0)

    print(f"  → intent={intent} (confidence={confidence:.2f}), urgent={is_urgent:.2f}, directed={is_directed:.2f}")

    # Simple reply for general chatter not directed at the agent
    if is_directed < 0.5:
        print("  → not directed at agent, simple reply")
        save_message(sender, body, "inbound")
        resp = MessagingResponse()
        resp.message("Hey! I'm the house agent 🏠 I can help with maintenance requests, subletter tracking, and roommate stuff. Just let me know what you need!")
        return Response(content=str(resp), media_type="application/xml")

    # Extract details for subletter/roommate intents
    extracted = None
    if intent in ("potential_subletter", "potential_roommate", "actual_subletter") and confidence > 0.6:
        extracted = extract_details(body)
        print(f"  → extracted: {extracted}")
        if extracted:
            try:
                append_candidate(extracted, intent, sender)
            except Exception as e:
                print(f"  → sheets error: {e}")

    # Submit maintenance request via OpenClaw
    maintenance_result = None
    if intent == "maintenance_request" and confidence > 0.6:
        try:
            print("  → submitting maintenance request via OpenClaw...")
            maintenance_result = await submit_maintenance_request(body)
            print(f"  → maintenance result: {maintenance_result}")
        except Exception as e:
            print(f"  → maintenance error: {e}")

    # Store in SQLite
    upsert_roommate(sender)
    save_message(sender, body, "inbound")
    if intent != "uncategorized" and confidence > 0.6:
        save_request(sender, intent, confidence, is_urgent, body, extracted)

    # Response generation
    if maintenance_result:
        classification["maintenance_result"] = maintenance_result
    reply_text = generate_reply(body, classification, sender)
    save_message(sender, reply_text, "outbound")

    resp = MessagingResponse()
    resp.message(reply_text)
    return Response(content=str(resp), media_type="application/xml")
