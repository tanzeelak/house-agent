import os
import httpx
from llm_fallback import classify_message_llm

TYPESAFE_API_URL = "https://api.typesafe.ai/preview/evaluation"
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY")

PROMPTS = [
    {
        "key": "intent",
        "type": "choice",
        "instructions": "What action is this roommate requesting?",
        "options": [
            {"option": "maintenance_request", "description": "Something in the house is broken, damaged, or needs fixing — appliances, plumbing, furniture, fixtures, etc."},
            {"option": "potential_roommate", "description": "Add potential roommates for the house"},
            {"option": "potential_subletter", "description": "Someone is inquiring about subletting or expressing interest — not yet confirmed"},
            {"option": "actual_subletter", "description": "A subletter has been confirmed and needs to be recorded with their room and date range"},
            {"option": "uncategorized", "description": "Does not fit any of the above categories"},
        ],
    },
    {
        "key": "is_urgent",
        "type": "noul",
        "instructions": "Does this message convey urgency or time-sensitivity?",
    },
    {
        "key": "is_directed_at_agent",
        "type": "noul",
        "instructions": "Is this message about something the house agent could help with — maintenance, sublets, roommates, or house logistics? Only casual greetings and off-topic chatter should score low.",
    },
]


async def classify_message(message: str) -> dict:
    """Send a message to Typesafe for intent classification and urgency detection.
    Falls back to Claude if Typesafe is unavailable."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TYPESAFE_API_URL,
                headers={
                    "Authorization": f"Bearer {TYPESAFE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "document": message,
                    "model": "speed_latest",
                    "prompts": PROMPTS,
                },
                timeout=5.0,
            )
            response.raise_for_status()
            data = response.json()

        intent_result = data["responses"][0]
        urgency_result = data["responses"][1]
        directed_result = data["responses"][2]

        print("  → classified via Typesafe")
        return {
            "intent": intent_result["chosen"],
            "intent_confidence": intent_result["confidence"],
            "intent_probabilities": {p["option"]: p["probability"] for p in intent_result["probabilities"]},
            "is_urgent": urgency_result["probability"],
            "is_directed_at_agent": directed_result["probability"],
        }
    except Exception as e:
        print(f"  → Typesafe unavailable ({e}), falling back to Claude")
        return await classify_message_llm(message)
