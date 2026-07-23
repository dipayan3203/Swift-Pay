import json
from pathlib import Path


class Storage:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data = {
            "merchants": [],
            "payments": [],
            "refunds": [],
            "webhooks": [],
            "subscriptions": [],
            "plans": [],
            "payouts": [],
            "settlements": [],
            "disputes": [],
        }
        self.idempotency_keys: set[str] = set()
        self._load()

    def _file(self, collection):
        return self.data_dir / f"{collection}.json"

    def _load(self):
        for collection in self.data:
            path = self._file(collection)
            if path.exists():
                try:
                    self.data[collection] = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    self.data[collection] = []
        self._seed()

    def _persist(self, collection):
        path = self._file(collection)
        path.write_text(json.dumps(self.data.get(collection, []), indent=2), encoding="utf-8")

    def _seed(self):
        if not self.data["merchants"]:
            self.data["merchants"] = [
                {"id": "m_1001", "legal_name": "Acme Commerce", "status": "active", "risk_band": "low", "email": "ops@acme.example", "kyc_status": "approved", "metadata": {}},
                {"id": "m_1002", "legal_name": "Bright Goods", "status": "pending_kyc", "risk_band": "medium", "email": "ops@bright.example", "kyc_status": "pending", "metadata": {}},
                {"id": "m_1003", "legal_name": "Zeta Retail", "status": "active", "risk_band": "low", "email": "ops@zeta.example", "kyc_status": "approved", "metadata": {}},
            ]
            for c in self.data:
                self._persist(c)

    def list(self, collection):
        return list(self.data.get(collection, []))

    def append(self, collection, item):
        self.data.setdefault(collection, []).append(item)
        self._persist(collection)
        return item

    def update(self, collection, item_id, updates):
        items = self.data.setdefault(collection, [])
        for item in items:
            if item.get("id") == item_id:
                item.update(updates)
                self._persist(collection)
                return item
        return None

    def find(self, collection, item_id):
        return next((item for item in self.data.get(collection, []) if item.get("id") == item_id), None)