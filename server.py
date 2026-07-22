import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT / "public"


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
        self._seed()

    def _seed(self):
        self.data["merchants"] = [
            {"id": "m_1001", "legal_name": "Acme Commerce", "status": "active", "risk_band": "low", "email": "ops@acme.example", "kyc_status": "approved", "metadata": {}},
            {"id": "m_1002", "legal_name": "Bright Goods", "status": "pending_kyc", "risk_band": "medium", "email": "ops@bright.example", "kyc_status": "pending", "metadata": {}},
            {"id": "m_1003", "legal_name": "Zeta Retail", "status": "active", "risk_band": "low", "email": "ops@zeta.example", "kyc_status": "approved", "metadata": {}},
        ]

    def list(self, collection):
        return list(self.data.get(collection, []))

    def append(self, collection, item):
        self.data.setdefault(collection, []).append(item)
        return item

    def update(self, collection, item_id, updates):
        items = self.data.setdefault(collection, [])
        for item in items:
            if item.get("id") == item_id:
                item.update(updates)
                return item
        return None


storage = Storage()


def compose_response(status, data):
    return {"status": status, "data": data, "timestamp": "2026-07-22T00:00:00Z"}


def error_response(code, message, param=None):
    return {"error": {"code": code, "message": message, "param": param}}


def parse_body(raw):
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


class SwiftPayHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_html(self, file_path):
        try:
            html = (PUBLIC_DIR / file_path).read_text(encoding="utf-8")
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self.send_response(404)
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
                "total_disputes": 0,
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

        if path == "/api/merchants":
            merchant = {
                "id": f"m_{len(storage.list('merchants')) + 1000}",
                "legal_name": payload.get("legal_name", "New Merchant"),
                "status": "active",
                "risk_band": "low",
                "email": payload.get("email", "ops@example.com"),
                "kyc_status": "approved",
                "metadata": {},
            }
            storage.append("merchants", merchant)
            storage.append("webhooks", {"event": "merchant.created", "payload": {"merchant_id": merchant["id"]}})
            self._send_json(201, compose_response("merchant_created", merchant))
            return

        if path == "/api/payments":
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
            storage.append("payments", payment)
            storage.append("webhooks", {"event": "payment.initiated", "paymentId": payment["id"]})
            self._send_json(201, compose_response("payment_created", payment))
            return

        if path == "/api/plans":
            plan = {"id": f"plan_{len(storage.list('plans')) + 1}", **payload}
            storage.append("plans", plan)
            self._send_json(201, compose_response("plan_created", plan))
            return

        if path == "/api/subscriptions":
            plan = next((item for item in storage.list("plans") if item.get("id") == payload.get("plan_id")), None)
            sub = {
                "id": f"sub_{len(storage.list('subscriptions')) + 1}",
                "plan_id": payload.get("plan_id"),
                "merchant_id": payload.get("merchant_id", "m_1001"),
                "status": "active",
                "trial_end": None,
                "plan": plan,
            }
            storage.append("subscriptions", sub)
            self._send_json(201, compose_response("subscription_created", sub))
            return

        if path == "/api/payouts":
            payout = {
                "id": f"payout_{len(storage.list('payouts')) + 1}",
                "merchant_id": payload.get("merchant_id", "m_1001"),
                "amount_minor": payload.get("amount_minor", 0),
                "status": "processing",
                "method": payload.get("method", "upi"),
            }
            storage.append("payouts", payout)
            self._send_json(201, compose_response("payout_created", payout))
            return

        if path == "/api/payouts/validate-account":
            self._send_json(200, compose_response("account_validated", {"valid": True, "account_number": payload.get("account_number"), "ifsc_code": payload.get("ifsc_code")}))
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
            dispute = {"id": dispute_id, "status": payload.get("status", "needs_response")}
            storage.append("disputes", dispute)
            self._send_json(200, compose_response("dispute_updated", dispute))
            return

        self._send_json(404, error_response("not_found", f"Route {path} not found"))

    def do_PUT(self):
        self.do_POST()

    def log_message(self, format, *args):
        return


def run_server(port=3000):
    server = ThreadingHTTPServer(("127.0.0.1", port), SwiftPayHandler)
    print(f"Swift Pay API running on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else int(os.getenv("PORT", "3000"))
    run_server(port)
