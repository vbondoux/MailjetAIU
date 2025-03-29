from fastapi import FastAPI, Request, HTTPException
import os
from dotenv import load_dotenv
import httpx
import uvicorn

load_dotenv()

app = FastAPI()

MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL')
TARGET_CUSTOM_CAMPAIGNS = os.getenv('TARGET_CUSTOM_CAMPAIGNS', "").split(",")

@app.get("/")
async def root():
    return {"status": "API Mailjet Webhook Filter OK"}

@app.post("/mailjet")
async def filter_mailjet(request: Request):
    payload = await request.json()

    print(f"📨 Payload brut reçu : {payload}")

    event_type = payload.get('event')
    custom_campaign = payload.get('customcampaign', '')

    # Extraire l'ID numérique de customcampaign
    campaign_id = ''
    if custom_campaign.startswith('mj.nl='):
        campaign_id = custom_campaign.replace('mj.nl=', '')

    print(f"📩 Reçu événement : {event_type} pour CustomCampaign ID : {campaign_id}")

    if campaign_id in TARGET_CUSTOM_CAMPAIGNS:
        print(f"✅ CustomCampaign ID autorisé → Forward vers Make")
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
            "customcampaign_id": campaign_id
        }
    else:
        print(f"⛔ CustomCampaign ID {campaign_id} non autorisé → Ignoré")
        return {
            "status": "ignored",
            "customcampaign_id": campaign_id
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
