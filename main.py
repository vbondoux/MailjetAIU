from fastapi import FastAPI, Request, HTTPException
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

app = FastAPI()

MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL')
TARGET_CUSTOM_ID = os.getenv('TARGET_CUSTOM_ID')

@app.get("/")
async def root():
    return {"status": "API Mailjet Webhook Filter OK"}

@app.post("/mailjet")
async def filter_mailjet(request: Request):
    payload = await request.json()

    # Exemple pour CustomID, adapte à CampaignID si besoin
    event_custom_id = payload.get('CustomID')
    
    if event_custom_id == TARGET_CUSTOM_ID:
        # Transmet l'événement vers Make
        async with httpx.AsyncClient() as client:
            response = await client.post(MAKE_WEBHOOK_URL, json=payload)
            response.raise_for_status()

        return {"status": "forwarded to Make"}
    else:
        # Ignore l'événement
        return {"status": "ignored"}
