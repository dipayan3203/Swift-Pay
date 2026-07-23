import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.database.storage import Storage

def add_webhook(storage: 'Storage', event: str, payload: dict):
    existing_webhooks = storage.list("webhooks")
    key = json.dumps({"event": event, "payload": payload}, sort_keys=True)
    normalized = json.loads(key)
    # Check if a webhook with the same event and payload already exists
    for webhook in existing_webhooks:
        if json.dumps(webhook, sort_keys=True) == key:
            return webhook # Return existing webhook if found

    return storage.append("webhooks", normalized)