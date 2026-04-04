import os
import httpx

TYPESAFE_API_URL = "https://api.typesafe.ai/preview/evaluation"
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY")

PROMPTS = [
    {
        "key": "intent",
        "type": "choice",
        "instructions": "What action is this roommate requesting?",
        "options": [
            {"option": "maintenance_request", "description": "Requests that can be made through the maintenance portal"},
            {"option": "potential_roommates", "description": "Add potential roommates for the house"},
            {"option": "potential_subletters", "description": "Add potential subletters for the house"},
            {"option": "actual_subletter", "description": "Update the sheet with a subletter for a specific room + date range"},
            {"option": "uncategorized", "description": "Does not fit any of the above categories"},
        ],
    },
    {
        "key": "is_urgent",
        "type": "noul",
        "instructions": "Does this message convey urgency or time-sensitivity?",
    },
]


async def classify_message(message: str) -> dict:
    """Send a message to Typesafe for intent classification and urgency detection."""
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
        )
        response.raise_for_status()
        data = response.json()

    intent_result = data["responses"][0]
    urgency_result = data["responses"][1]

    return {
        "intent": intent_result["chosen"],
        "intent_confidence": intent_result["confidence"],
        "intent_probabilities": {p["option"]: p["probability"] for p in intent_result["probabilities"]},
        "is_urgent": urgency_result["probability"],
    }
