# House Agent — Architecture

## Overview

A WhatsApp group agent that roommates can message to manage shared house tasks. The agent receives messages via WhatsApp, uses Typesafe to classify intent and extract structured decisions, and uses Claude to generate natural language responses.

---

## V0 — Conversational Agent

Classify messages, respond intelligently. No external actions.

### Flow

```
Roommate sends WhatsApp message
        │
        ▼
┌─────────────────────┐
│  Twilio Webhook      │  ← Twilio forwards incoming WhatsApp messages
│  (FastAPI server)    │     as POST requests to our endpoint
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Typesafe API        │  ← Classify the message: what does the user want?
│  (Intent + Traits)   │     Is it urgent? Is it a chore request? A complaint?
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Action Router       │  ← Code branches on Typesafe results + confidence
│  (Python logic)      │     High confidence → auto-act
│                      │     Low confidence → ask for clarification
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Claude API          │  ← Generate a natural language reply
│  (Response gen)      │     Given the structured decision, compose a
│                      │     human-friendly message back to the roommate
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Twilio API          │  ← Send the reply back via WhatsApp
│  (Outbound message)  │
└─────────────────────┘
```

### Components

#### 1. Webhook Server (FastAPI)

- Single endpoint: `POST /webhook` receives messages from Twilio
- Extracts sender phone number, message body, and any media
- Each roommate is identified by their phone number — no auth needed
- Stores message in conversation history (SQLite)

#### 2. Typesafe — Intent Classification & Trait Detection

Typesafe handles the structured decision-making layer. Every incoming message gets evaluated in a single fan-out call:

**Choice — Intent:**
```json
{
  "key": "intent",
  "type": "choice",
  "instructions": "What action is this roommate requesting?",
  "options": [
    { "option": "maintenance_request", "description": "Requests that can be made through the maintenance portal" },
    { "option": "potential_roommates", "description": "Add potential roommates for the house" },
    { "option": "potential_subletters", "description": "Add potential subletters for the house" },
    { "option": "actual_subletter", "description": "Update the sheet with a subletter for a specific room + date range" },
    { "option": "uncategorized", "description": "Does not fit any of the above categories" }
  ]
}
```

**Noul — Trait detection:**
- `is_urgent` — Does this message convey urgency or time-sensitivity?
- `is_urgent` — Does this message convey urgency or time-sensitivity?

All prompts fire in one API call with no latency penalty. The structured results feed directly into the action router.

#### 3. Action Router

Python logic that branches on Typesafe results:

```
All intents with confidence > 0.8                           → log to requests table in SQLite
intent = "maintenance_request" + is_urgent > 0.7            → log as urgent, (v1: submit emergency ticket)
intent = "maintenance_request" + confidence > 0.8            → log request, (v1: submit normal ticket)
intent = "potential_roommates" + confidence > 0.8             → log candidate info + append to Google Sheet
intent = "potential_subletters" + confidence > 0.8            → log candidate info + append to Google Sheet
intent = "actual_subletter" + confidence > 0.8                → log subletter details (room + dates) + append to Google Sheet
intent = "uncategorized" or confidence < 0.6                  → ask roommate to clarify
```

#### 4. Claude — Response Generation

Claude generates the actual reply text. It receives:
- The original message
- Typesafe's structured evaluation (intent, traits, scores)
- Conversation history for that user
- House context (who the roommates are, any pending chores/expenses)

Claude is used for generation only. Typesafe handles all judgment/classification.

#### 5. State (SQLite)

- `roommates` — phone number, name
- `messages` — conversation history per roommate
- `requests` — every classified request:
  - `id`, `roommate_id`, `intent`, `confidence`, `is_urgent`, `raw_message`
  - `extracted_details` (JSON — Claude-extracted fields like room, description, name, dates)
  - `status` (pending / done / rejected)
  - `created_at`

This is the core of V0. Every request gets logged regardless of whether automation exists yet. Roommates can ask "what's pending?" and the agent can query this table. In V1, the action router starts executing against external systems instead of just logging.

#### 6. Google Sheets — Subletter/Roommate Tracking

When a message is classified as `potential_subletter`, `potential_roommate`, or `actual_subletter` with confidence > 0.6, the agent:

1. Extracts structured details from the message via OpenAI (name, phone, socials, dates, notes)
2. Inserts a new row at the top of the "Applicants" sheet (row 2, right after headers)

**Column mapping:**

| Sheet Column | Source |
|---|---|
| Person | Extracted name |
| Contact | Phone + socials (falls back to WhatsApp sender number) |
| Notes | Date range + any additional notes |
| Next step | Defaults to "New — needs interview" |
| Interviewers | Left blank |
| Interview notes | Left blank |

Uses a Google Cloud service account (`service_account.json`) with the Sheets API. The sheet must be shared with the service account's email as an Editor.

#### 7. Twilio (WhatsApp)

- Twilio Sandbox for development (no Meta approval needed)
- Each roommate texts the sandbox number
- Outbound replies sent via Twilio REST API

---

## V1 — Maintenance Portal Automation

Everything in V0, plus: when Typesafe classifies a message as a maintenance request with high confidence, the agent **logs into the building's maintenance portal and submits a ticket** on behalf of the roommate.

### Flow (maintenance path)

```
Roommate: "The kitchen sink is leaking again"
        │
        ▼
┌─────────────────────┐
│  Typesafe API        │  intent = "maintenance" (confidence: 0.93)
│                      │  is_urgent = 0.72
│                      │  severity = 2.1 / 3
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Action Router       │  confidence > 0.8 → maintenance path
└────────┬────────────┘
         │
    ┌────┴─────────────────┐
    │                      │
    ▼                      ▼
┌────────────┐    ┌──────────────────┐
│ Claude API │    │ OpenClaw         │
│ (reply)    │    │ (Browser agent)  │
└────┬───────┘    └────────┬─────────┘
     │                     │
     │              ┌──────┴──────┐
     │              │ Maintenance │  ← OpenClaw handles the full browser flow:
     │              │ Portal      │     1. Login with stored credentials
     │              │ (Web)       │     2. Navigate to "New Request"
     │              └──────┬──────┘     3. Fill form (unit, description, urgency)
     │                     │            4. Submit
     │              ┌──────┴──────┐
     │              │ Ticket ID   │  ← Capture confirmation/ticket number
     │              └──────┬──────┘
     │                     │
     ▼                     ▼
┌─────────────────────────────────┐
│  Twilio API                      │
│  "I submitted a maintenance      │
│   request (#4821) for the        │
│   kitchen sink leak. They        │
│   should respond within 48hrs."  │
└─────────────────────────────────┘
```

### New Components in V1

#### Portal Automator (OpenClaw)

- Uses [OpenClaw](https://openclaw.ai/) for browser automation
- OpenClaw runs locally as an AI agent with browser control — it can navigate, fill forms, and interact with web UIs via natural language instructions
- Stores portal credentials in env vars (`PORTAL_URL`, `PORTAL_USER`, `PORTAL_PASS`)
- Our server sends OpenClaw a task like: "Log into {PORTAL_URL}, submit a maintenance request for: {description}, unit: {unit}, urgency: {level}"
- OpenClaw handles the full browser flow autonomously — no brittle selectors or step-by-step scripting

#### Claude's Expanded Role

Claude now also:
- Extracts structured fields from the roommate's message for the form (location, description, urgency level)
- Composes the confirmation reply including the ticket ID

#### Confidence-Gated Safety

Since submitting a ticket is a **real-world action**, the confidence bar is higher:

```
confidence > 0.9 + is_maintenance > 0.85  → auto-submit, confirm to user
confidence > 0.7 + is_maintenance > 0.7   → ask user to confirm before submitting
confidence < 0.7                          → "Did you mean to report a maintenance issue?"
```

#### New Env Vars

```
PORTAL_URL=https://your-building-portal.com
PORTAL_USER=unit42@building.com
PORTAL_PASS=...
```

#### New Dependency

- OpenClaw running locally (see https://openclaw.ai/ for setup)

---

## Why Two AI Models?

| Concern | Typesafe | Claude |
|---------|----------|--------|
| "What does this message want?" | ✓ | |
| "How urgent is it?" | ✓ | |
| "Which category?" | ✓ | |
| "Is this a maintenance issue?" | ✓ | |
| "Extract form fields from message" | | ✓ |
| "Compose a friendly reply" | | ✓ |
| Speed | ~ms | ~1-2s |
| Output type | Structured data | Natural language |

Typesafe gives fast, structured, confidence-scored decisions that code can branch on reliably. Claude generates the human-facing text and extracts unstructured details. Neither does the other's job well.

## Deployment

- FastAPI server behind ngrok (dev) or deployed to Fly.io (prod)
- Twilio webhook URL points to the server
- SQLite file persisted on a Fly.io volume (`fly volumes create`)
- OpenClaw runs locally for browser automation (v1)
- Google Sheets service account key (`service_account.json`) for subletter tracking
- Environment variables: `TYPESAFE_API_KEY`, `ANTHROPIC_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`, `PORTAL_URL`, `PORTAL_USER`, `PORTAL_PASS`
- Optional: `GOOGLE_SERVICE_ACCOUNT_FILE` (defaults to `service_account.json`)
