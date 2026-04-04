import os
import json
import anthropic

INTENTS = ["maintenance_request", "potential_roommate", "potential_subletter", "actual_subletter", "uncategorized"]

SYSTEM_PROMPT = f"""You are a classification engine for a house agent that manages requests from roommates.

Given a message, return a JSON object with exactly these fields:
- "intent": one of {json.dumps(INTENTS)}
  - "maintenance_request": requests that can be made through the maintenance portal
  - "potential_roommate": add potential roommates for the house
  - "potential_subletter": someone is inquiring about subletting or expressing interest — not yet confirmed
  - "actual_subletter": a subletter has been confirmed and needs to be recorded with their room and date range
  - "uncategorized": does not fit any of the above categories
- "intent_confidence": float 0-1, how confident you are in the classification
- "is_urgent": float 0-1, how urgent or time-sensitive the message is

Return ONLY the JSON object, no other text."""


async def classify_message_llm(message: str) -> dict:
    """Fallback classifier using Claude when Typesafe is down."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=150,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
    )

    result = json.loads(response.content[0].text)

    return {
        "intent": result["intent"],
        "intent_confidence": result["intent_confidence"],
        "intent_probabilities": {},
        "is_urgent": result["is_urgent"],
    }
