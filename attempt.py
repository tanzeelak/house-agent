from typesafe_client import TypesafeClient
from typesafe_client.values import ChoicePrompt, ScorePrompt, NoulPrompt
import os
 
client = TypesafeClient(os.getenv("TYPESAFE_API_KEY"))
 
ticket = "Hi, I've been trying to connect my Stripe account for 3 days and it keeps failing. I'm losing sales. Please help ASAP."
 
response = client.evaluate(
    "speed_latest",
    {"support_ticket": ticket},
    [
        ChoicePrompt(
            key="department",
            instructions="Which team should handle this",
            options={
                "billing": "Payment or subscription issues",
                "technical": "Bugs or integration problems",
                "sales": "Pricing or account questions",
            }
        ),
        ScorePrompt(
            key="frustration",
            instructions="How frustrated the customer appears",
            levels={
                1: "Calm, just stating facts",
                2: "Frustrated but civil",
                3: "Very angry, strong language",
            }
        ),
        NoulPrompt(
            key="is_urgent",
            instructions="The message conveys urgency or time-sensitivity"
        ),
    ]
)
 
print(response.choice("department").chosen)      # "technical"
print(response.score("frustration").expectation)  # 2.035
print(response.noul("is_urgent").probability)     # 0.999