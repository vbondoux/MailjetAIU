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
    event_type = payload.get('Event')

    print(f"📩 Reçu événement : {event_type} pour CampaignID : {event_campaign_id}")

    if event_campaign_id in TARGET_CAMPAIGN_IDS:
        print(f"✅ CampaignID autorisé → Forward vers Make")
        # Transmet l'événement vers Make
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(MAKE_WEBHOOK_URL, json=payload)
                response.raise_for_status()
                print(f"🚀 Forward réussi → Make a répondu {response.status_code}")
            except httpx.HTTPError as e:
                print(f"❌ Erreur lors du forward vers Make : {str(e)}")
                raise HTTPException(status_code=500, detail=f"Erreur en envoyant vers Make: {str(e)}")

        return {
            "status": "forwarded to Make",
            "campaign_id": event_campaign_id
        }
    else:
        print(f"⛔ CampaignID {event_campaign_id} non autorisé → Ignoré")
        return {
            "status": "ignored",
            "campaign_id": event_campaign_id
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
