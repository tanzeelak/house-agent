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

## Task List

### V0 — Core Agent
- [x] FastAPI webhook server (receives WhatsApp messages via Twilio)
- [x] Twilio WhatsApp Sandbox connected
- [ ] Typesafe intent classification (maintenance, roommates, subletters, etc.)
- [ ] Typesafe urgency detection (is_urgent noul)
- [ ] Claude response generation
- [ ] Action router (branch on Typesafe results + confidence)
- [ ] SQLite database (roommates, messages, requests)

### V1 — Automation
- [ ] OpenClaw browser automation for maintenance portal
- [ ] Confidence-gated safety for real-world actions
- [ ] Google Sheets integration (subletter tracking)
