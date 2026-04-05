from openclaw_sdk import OpenClawClient


PORTAL_URL = "https://progressivesf.appfolio.com/connect"


async def submit_maintenance_request(description: str) -> str:
    """Use OpenClaw to submit a maintenance request via the AppFolio portal chatbot.

    Assumes you've already logged into AppFolio in the OpenClaw browser profile.
    Run `openclaw browser` and sign in manually first.
    """
    task = f"""Go to {PORTAL_URL}

You should already be logged in. If you see a login page, STOP and report "Not logged in — please log in manually via `openclaw browser`".

1. Tap "Maintenance"
2. Tap "Request Maintenance"
3. A chatbot will appear. Talk to the chatbot and provide these details for the maintenance issue:
   {description}
4. Follow the chatbot's prompts until the request is submitted.
5. When done, report back what happened — did the request go through? Any confirmation or ticket number?"""

    async with OpenClawClient.connect() as client:
        agent = client.get_agent("maintenance-bot")
        result = await agent.execute(task)
        return result.content
