# house-agent

A WhatsApp agent for roommates to manage shared house tasks — maintenance requests, subletter tracking, and more.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

## Running

**Terminal 1** — start the server:

```bash
source .venv/bin/activate
uvicorn app:app --reload --port 8000
```

**Terminal 2** — expose via ngrok:

```bash
ngrok http 8000
```

Then set the ngrok URL as your Twilio WhatsApp Sandbox webhook at:
https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

Set "When a message comes in" to:

```
https://<your-ngrok-url>.ngrok-free.app/webhook
```

Method: POST

## Joining the Agent (Sandbox)

We're currently using the Twilio WhatsApp Sandbox. Each roommate must opt in before they can message the agent:

1. Save `+1 (415) 523-8886` as a contact
2. Send `join her-so` to that contact on WhatsApp
3. Wait for the confirmation message

This must be repeated every 72 hours (sandbox limitation). Once we have an approved WhatsApp Business number, this step goes away.

## Task List

### V0 — Core Agent
- [x] FastAPI webhook server (receives WhatsApp messages via Twilio)
- [x] Twilio WhatsApp Sandbox connected
- [x] Typesafe intent classification (maintenance, roommates, subletters, etc.)
- [x] Typesafe urgency detection (is_urgent noul)
- [x] SQLite database (roommates, messages, requests)
- [ ] LLM fallback for classification when Typesafe is down
- [ ] Claude response generation
- [ ] Action router (branch on Typesafe results + confidence)
- [ ] Test with multiple people messaging the agent

### Backlog
- [ ] Deploy to Fly.io with persistent volume for SQLite
- [ ] Approved WhatsApp Business number (remove join step)

### V1 — Automation
- [ ] OpenClaw browser automation for maintenance portal
- [ ] Confidence-gated safety for real-world actions
- [ ] Google Sheets integration (subletter tracking)
