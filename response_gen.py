import os
from openai import OpenAI

SYSTEM_PROMPT = """You are a helpful house agent for a group of roommates. You communicate via WhatsApp.

Keep your replies SHORT — 1-2 sentences max. This is WhatsApp, not email.

You will receive a roommate's message along with its classification. Your job:
- Acknowledge the request briefly
- Do NOT ask follow-up questions — just confirm what you logged
- Be friendly and casual"""

EXTRACT_PROMPT = """Extract the following from this message. Return ONLY a JSON object with these fields:
- "name": the person's name (or null if not found)
- "start_date": start date they want (or null)
- "end_date": end date they want (or null)
- "socials": any social media links, profile URLs, or handles mentioned (or null)
- "phone": phone number if visible (or null)
- "notes": any other relevant details in one short line (or null)

Return ONLY the JSON, no other text."""


def generate_reply(message: str, classification: dict, sender: str) -> str:
    """Generate a short acknowledgment reply."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    context = (
        f"Roommate message: {message}\n\n"
        f"Classification: {classification['intent']} (confidence: {classification['intent_confidence']:.2f})\n"
        f"Sender: {sender}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=150,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
    )

    return response.choices[0].message.content


def extract_details(message: str) -> dict:
    """Extract name, dates, socials from a message using OpenAI."""
    import json
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=200,
        messages=[
            {"role": "system", "content": EXTRACT_PROMPT},
            {"role": "user", "content": message},
        ],
    )

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {}
