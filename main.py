from fastapi import FastAPI, Request, HTTPException
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

app = FastAPI()

MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL')
TARGET_CUSTOM_IDS = os.getenv('TARGET_CUSTOM_IDS', "").split(",")

@app.get("/")
async def root():
    return {"status": "API Mailjet Webhook Filter OK"}

@app.post("/mailjet")
async def filter_mailjet(request: Request):
    payload = await request.json()

    event_custom_id = payload.get('CustomID')

    if event_custom_id in TARGET_CUSTOM_IDS:
        # Transmet l'événement vers Make
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(MAKE_WEBHOOK_URL, json=payload)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise HTTPException(status_code=500, detail=f"Erreur en envoyant vers Make: {str(e)}")

        return {"status": "forwarded to Make", "custom_id": event_custom_id}
    else:
        return {"status": "ignored", "custom_id": event_custom_id}
