import os
from airtable import Airtable

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_TABLE = os.getenv("AIRTABLE_TABLE")

# Initialisation correcte du client Airtable avec les 3 paramètres requis
client = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE, AIRTABLE_API_KEY)

def get_graph_data():
    records = client.get_all()
    nodes = [{"id": "mailing", "label": "Mailing", "type": "mail"}]
    links = []

    for r in records:
        email = r["fields"].get("Email")
        event_type = r["fields"].get("Type")
        url = r["fields"].get("URL")

        if not email:
            continue

        if event_type == "open":
            nodes.append({"id": email, "label": email, "type": "user"})
            links.append({"source": "mailing", "target": email})
        elif event_type == "click":
            if url:
                nodes.append({"id": url, "label": url, "type": "url"})
                links.append({"source": email, "target": url})

    return {"nodes": nodes, "links": links}
