import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT / "public"
DATA_DIR = ROOT / ".data"

ALLOWED_CURRENCIES = {"INR", "USD", "EUR"}
ALLOWED_METHODS = {"card", "upi", "wallet"}
VALID_IFSC_LEN = 11


class Storage:
    def __init__(self):
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

    @staticmethod
    def _file(collection):
        return DATA_DIR / f"{collection}.json"

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


storage = Storage()


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compose_response(status, data):
    return {"status": status, "data": data, "timestamp": now_iso()}


def error_response(code, message, param=None):
    return {"error": {"code": code, "message": message, "param": param}}


def parse_body(raw):
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def validate_payment(payload, require_merchant=True):
    amount_minor = payload.get("amount_minor")
    if not isinstance(amount_minor, int) or amount_minor <= 0:
        return False, "amount_minor must be a positive integer"
    if payload.get("currency") not in ALLOWED_CURRENCIES:
        return False, f"currency must be one of {sorted(ALLOWED_CURRENCIES)}"
    if payload.get("payment_method") not in ALLOWED_METHODS:
        return False, f"payment_method must be one of {sorted(ALLOWED_METHODS)}"
    merchant_id = payload.get("merchant_id")
    if require_merchant and not merchant_id:
        return False, "merchant_id is required"
    if merchant_id and not storage.find("merchants", merchant_id):
        return False, "merchant_id not found"
    return True, None


def add_webhook(event, payload):
    existing = storage.list("webhooks")
    key = json.dumps({"event": event, "payload": payload}, sort_keys=True)
    normalized = json.loads(key)
    if normalized in existing:
        return existing[existing.index(normalized)]
    return storage.append("webhooks", normalized)


def cors_headers(self):
    self.send_header("Access-Control-Allow-Origin", "*")
    self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, OPTIONS")
    self.send_header("Access-Control-Allow-Headers", "Content-Type, Idempotency-Key")


class SwiftPayHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        cors_headers(self)
        self.end_headers()
        self.wfile.write(body)

    def _serve_html(self, file_path):
        try:
            html = (PUBLIC_DIR / file_path).read_text(encoding="utf-8")
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            cors_headers(self)
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Idempotency-Key")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            self._serve_html("index.html")
            return

        if path == "/api/health":
            self._send_json(200, {"status": "ok", "service": "swift-pay-api"})
            return

        if path == "/api/payment-methods":
            self._send_json(200, {"payment_methods": [
                {"id": "pm_card", "name": "Card"},
                {"id": "pm_upi", "name": "UPI"},
                {"id": "pm_wallet", "name": "Wallet"},
            ]})
            return

        if path == "/api/banks":
            self._send_json(200, {"banks": ["HDFC", "ICICI", "SBI", "Axis", "Kotak", "IDFC", "Yes Bank", "PNB", "Canara", "Indian Bank"]})
            return

        if path == "/api/merchants":
            self._send_json(200, {"merchants": storage.list("merchants")})
            return

        if path == "/api/payments":
            self._send_json(200, {"payments": storage.list("payments")})
            return

        if path == "/api/webhooks/events":
            self._send_json(200, {"webhooks": storage.list("webhooks")})
            return

        if path == "/api/dashboard":
            payments = storage.list("payments")
            success_rate = 0.0
            if payments:
                success_rate = sum(1 for payment in payments if payment.get("status") == "captured") / len(payments)
            payload = {
                "success_rate": round(success_rate, 4),
                "volume_today": sum(payment.get("amount_minor", 0) for payment in payments),
                "pending_settlements": 0,
                "active_subscriptions": 0,
                "total_refunds": len(storage.list("refunds")),
                "total_disputes": len(storage.list("disputes")),
                "avg_transaction_value": 0 if not payments else round(sum(payment.get("amount_minor", 0) for payment in payments) / len(payments), 2),
                "payment_methods_breakdown": [
                    {"id": "pm_card", "name": "Card", "count": sum(1 for payment in payments if payment.get("payment_method") == "card")},
                    {"id": "pm_upi", "name": "UPI", "count": sum(1 for payment in payments if payment.get("payment_method") == "upi")},
                    {"id": "pm_wallet", "name": "Wallet", "count": sum(1 for payment in payments if payment.get("payment_method") == "wallet")},
                ],
            }
            self._send_json(200, payload)
            return

        self._send_json(404, error_response("not_found", f"Route {path} not found"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        payload = parse_body(raw)
        idempotency_key = self.headers.get("Idempotency-Key", "")

        if path == "/api/merchants":
            if idempotency_key:
                if idempotency_key in storage.idempotency_keys:
                    existing = next((m for m in storage.list("merchants") if m.get("idempotency_key") == idempotency_key), None)
                    if existing:
                        self._send_json(200, compose_response("merchant_created", existing))
                        return
                else:
                    storage.idempotency_keys.add(idempotency_key)
            merchant = {
                "id": f"m_{len(storage.list('merchants')) + 1000}",
                "legal_name": payload.get("legal_name", "New Merchant"),
                "status": "active",
                "risk_band": "low",
                "email": payload.get("email", "ops@example.com"),
                "kyc_status": "approved",
                "metadata": {},
            }
            if idempotency_key:
                merchant["idempotency_key"] = idempotency_key
            storage.append("merchants", merchant)
            add_webhook("merchant.created", {"merchant_id": merchant["id"]})
            self._send_json(201, compose_response("merchant_created", merchant))
            return

        if path == "/api/payments":
            if idempotency_key:
                if idempotency_key in storage.idempotency_keys:
                    existing = next((p for p in storage.list("payments") if p.get("idempotency_key") == idempotency_key), None)
                    if existing:
                        self._send_json(200, compose_response("payment_created", existing))
                        return
            valid, err = validate_payment(payload)
            if not valid:
                self._send_json(400, error_response("invalid_request", err))
                return
            merchant_id = payload.get("merchant_id") or "m_1001"
            payment = {
                "id": f"pay_{len(storage.list('payments')) + 1}",
                "merchant_id": merchant_id,
                "amount_minor": payload.get("amount_minor", 0),
                "currency": payload.get("currency", "INR"),
                "payment_method": payload.get("payment_method", "card"),
                "status": "initiated",
                "amount": payload.get("amount_minor", 0) / 100,
                "method": payload.get("payment_method", "card"),
                "routing": {"primaryAcquirer": "swift-pay-acquirer", "secondaryAcquirer": "backup-acquirer"},
            }
            if idempotency_key:
                payment["idempotency_key"] = idempotency_key
                storage.idempotency_keys.add(idempotency_key)
            storage.append("payments", payment)
            add_webhook("payment.initiated", {"paymentId": payment["id"]})
            self._send_json(201, compose_response("payment_created", payment))
            return

        if path == "/api/plans":
            plan = {"id": f"plan_{len(storage.list('plans')) + 1}", **payload}
            storage.append("plans", plan)
            self._send_json(201, compose_response("plan_created", plan))
            return

        if path == "/api/subscriptions":
            plan = storage.find("plans", payload.get("plan_id"))
            if not plan:
                self._send_json(404, error_response("not_found", "plan_id not found"))
                return
            merchant_id = payload.get("merchant_id", "m_1001")
            sub = {
                "id": f"sub_{len(storage.list('subscriptions')) + 1}",
                "plan_id": payload.get("plan_id"),
                "merchant_id": merchant_id,
                "status": "active",
                "trial_end": None,
                "plan": plan,
            }
            storage.append("subscriptions", sub)
            self._send_json(201, compose_response("subscription_created", sub))
            return

        if path == "/api/payouts":
            merchant_id = payload.get("merchant_id", "m_1001")
            if not storage.find("merchants", merchant_id):
                self._send_json(404, error_response("not_found", "merchant_id not found"))
                return
            payout = {
                "id": f"payout_{len(storage.list('payouts')) + 1}",
                "merchant_id": merchant_id,
                "amount_minor": payload.get("amount_minor", 0),
                "status": "processing",
                "method": payload.get("method", "upi"),
            }
            storage.append("payouts", payout)
            self._send_json(201, compose_response("payout_created", payout))
            return

        if path == "/api/payouts/validate-account":
            account = str(payload.get("account_number", ""))
            ifsc = str(payload.get("ifsc_code", "")).upper()
            valid = account.isdigit() and len(account) >= 9 and len(ifsc) == VALID_IFSC_LEN and ifsc[:4].isalpha() and ifsc[4].isdigit() and ifsc[5:7].isalpha() and ifsc[7:].isdigit()
            self._send_json(200, compose_response("account_validated", {"valid": valid, "account_number": account, "ifsc_code": ifsc}))
            return

        self._send_json(404, error_response("not_found", f"Route {path} not found"))

    def do_PATCH(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        payload = parse_body(raw)

        if path.startswith("/api/disputes/"):
            dispute_id = path.split("/")[-1]
            dispute = storage.find("disputes", dispute_id)
            if dispute:
                dispute.update(payload)
                storage._persist("disputes")
            else:
                dispute = {"id": dispute_id, "status": payload.get("status", "needs_response")}
                storage.append("disputes", dispute)
            self._send_json(200, compose_response("dispute_updated", dispute))
            return

        self._send_json(404, error_response("not_found", f"Route {path} not found"))

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        payload = parse_body(raw)

        if path.startswith("/api/payouts/"):
            payout_id = path.split("/")[-1]
            payout = storage.find("payouts", payout_id)
            if not payout:
                self._send_json(404, error_response("not_found", "payout not found"))
                return
            allowed = {"status", "method"}
            updates = {k: v for k, v in payload.items() if k in allowed}
            if not updates:
                self._send_json(400, error_response("invalid_request", "no updatable fields provided"))
                return
            updated = storage.update("payouts", payout_id, updates)
            self._send_json(200, compose_response("payout_updated", updated))
            return

        if path.startswith("/api/merchants/"):
            merchant_id = path.split("/")[-1]
            merchant = storage.find("merchants", merchant_id)
            if not merchant:
                self._send_json(404, error_response("not_found", "merchant not found"))
                return
            allowed = {"legal_name", "email", "status", "kyc_status"}
            updates = {k: v for k, v in payload.items() if k in allowed}
            if not updates:
                self._send_json(400, error_response("invalid_request", "no updatable fields provided"))
                return
            updated = storage.update("merchants", merchant_id, updates)
            self._send_json(200, compose_response("merchant_updated", updated))
            return

        self._send_json(404, error_response("not_found", f"Route {path} not found"))

    def log_message(self, format, *args):
        return


def run_server(port=3000):
    DATA_DIR.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", int(port)), SwiftPayHandler)
    print(f"Swift Pay API running on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else int(os.getenv("PORT", "3000"))
    run_server(port)
