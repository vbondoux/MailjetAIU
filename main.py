from fastapi import FastAPI, Request, HTTPException
import os
from dotenv import load_dotenv
import httpx
import uvicorn

load_dotenv()

app = FastAPI()

MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL')
TARGET_CAMPAIGN_IDS = os.getenv('TARGET_CAMPAIGN_IDS', "").split(",")

@app.get("/")
async def root():
    return {"status": "API Mailjet Webhook Filter OK"}

@app.post("/mailjet")
async def filter_mailjet(request: Request):
    payload = await request.json()

    event_campaign_id = str(payload.get('CampaignID'))

    if event_campaign_id in TARGET_CAMPAIGN_IDS:
        # Transmet l'événement vers Make
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(MAKE_WEBHOOK_URL, json=payload)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise HTTPException(status_code=500, detail=f"Erreur en envoyant vers Make: {str(e)}")

        return {
            "status": "forwarded to Make",
            "campaign_id": event_campaign_id
        }
    else:
        return {
            "status": "ignored",
            "campaign_id": event_campaign_id
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # IMPORTANT POUR RAILWAY
    uvicorn.run("main:app", host="0.0.0.0", port=port)
