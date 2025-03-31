from fastapi import FastAPI, Request, HTTPException, WebSocket
from graph_data import get_graph_data
import os
from dotenv import load_dotenv
import httpx
import uvicorn
import airtable

load_dotenv()

app = FastAPI()

MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL')
TARGET_CUSTOM_CAMPAIGNS = os.getenv('TARGET_CUSTOM_CAMPAIGNS', "").split(",")

# Airtable
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_TABLE = os.getenv("AIRTABLE_TABLE")
airtable_client = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)

# WebSocket clients
clients = set()

@app.get("/")
async def root():
    return {"status": "API Mailjet Webhook Filter OK"}

@app.post("/mailjet")
async def filter_mailjet(request: Request):
    payload = await request.json()

    print(f"📨 Payload brut reçu : {payload}")

    event_type = payload.get('event')
    custom_campaign = payload.get('customcampaign', '')
    email = payload.get('email', '')
    url = payload.get('url', '')

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

        # ➤ Log dans Airtable
        log_event_to_airtable(campaign_id, event_type, email, url)

        # ➤ Broadcast aux WebSockets
        await broadcast_event({
            "mailing_id": campaign_id,
            "type": event_type,
            "email": email,
            "url": url
        })

        return {
            "status": "forwarded to Make & logged to Airtable",
            "customcampaign_id": campaign_id
        }
    else:
        print(f"⛔ CustomCampaign ID {campaign_id} non autorisé → Ignoré")
        return {
            "status": "ignored",
            "customcampaign_id": campaign_id
        }

# ➤ Enregistrer un événement dans Airtable
def log_event_to_airtable(mailing_id, event_type, email, url):
    fields = {
        "MailingID": mailing_id,
        "Type": event_type,
        "Email": email
    }
    if url:
        fields["URL"] = url

    airtable_client.insert(AIRTABLE_TABLE, fields)
    print(f"✅ Événement ajouté dans Airtable : {fields}")

# ➤ Graph Data Endpoint
@app.get("/graph-data")
async def graph_data():
    return get_graph_data()

# ➤ WebSocket
@app.websocket("/ws/graph")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # Ping/Pong
    except:
        clients.remove(websocket)

# ➤ Diffuser un événement en temps réel
async def broadcast_event(event):
    for ws in clients.copy():
        try:
            await ws.send_json(event)
        except:
            clients.remove(ws)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
