import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path

from app.database.storage import Storage
from app.utils.http_utils import compose_response, error_response, parse_body, cors_headers
from app.services.payment_validation import validate_payment # This will be used by routes
from app.services.webhook_service import add_webhook # This will be used by routes

# Import route handlers
from app.routes.payments import handle_payments_routes
# ... other route handlers will be imported here later

class SwiftPayHandler(BaseHTTPRequestHandler):
    # Class-level attributes for shared resources, initialized in app/main.py
    storage: Storage = None
    PUBLIC_DIR: Path = None
    VALID_IFSC_LEN: int = 11 # This constant should probably be in a config or utils file

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
            html = (self.PUBLIC_DIR / file_path).read_text(encoding="utf-8")
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
        cors_headers(self)
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
            self._send_json(200, {"merchants": self.storage.list("merchants")})
            return

        # Delegate to payments route handler
        if handle_payments_routes(self, path, {}, ""):
            return

        self._send_json(404, error_response("not_found", f"Route {path} not found"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        payload = parse_body(raw)
        idempotency_key = self.headers.get("Idempotency-Key", "")

        # Delegate to payments route handler
        if handle_payments_routes(self, path, payload, idempotency_key):
            return

        if path == "/api/merchants":
            if idempotency_key:
                if idempotency_key in self.storage.idempotency_keys:
                    existing = next((m for m in self.storage.list("merchants") if m.get("idempotency_key") == idempotency_key), None)
                    if existing:
                        self._send_json(200, compose_response("merchant_created", existing))
                        return
                else:
                    self.storage.idempotency_keys.add(idempotency_key)
            merchant = {
                "id": f"m_{len(self.storage.list('merchants')) + 1000}",
                "legal_name": payload.get("legal_name", "New Merchant"),
                "status": "active",
                "risk_band": "low",
                "email": payload.get("email", "ops@example.com"),
                "kyc_status": "approved",
                "metadata": {},
            }
            if idempotency_key:
                merchant["idempotency_key"] = idempotency_key
            self.storage.append("merchants", merchant)
            add_webhook(self.storage, "merchant.created", {"merchant_id": merchant["id"]})
            self._send_json(201, compose_response("merchant_created", merchant))
            return

        if path == "/api/plans":
            plan = {"id": f"plan_{len(self.storage.list('plans')) + 1}", **payload}
            self.storage.append("plans", plan)
            self._send_json(201, compose_response("plan_created", plan))
            return

        if path == "/api/subscriptions":
            plan = self.storage.find("plans", payload.get("plan_id"))
            if not plan:
                self._send_json(404, error_response("not_found", "plan_id not found"))
                return
            merchant_id = payload.get("merchant_id", "m_1001")
            sub = {
                "id": f"sub_{len(self.storage.list('subscriptions')) + 1}",
                "plan_id": payload.get("plan_id"),
                "merchant_id": merchant_id,
                "status": "active",
                "trial_end": None,
                "plan": plan,
            }
            self.storage.append("subscriptions", sub)
            self._send_json(201, compose_response("subscription_created", sub))
            return

        if path == "/api/payouts":
            merchant_id = payload.get("merchant_id", "m_1001")
            if not self.storage.find("merchants", merchant_id):
                self._send_json(404, error_response("not_found", "merchant_id not found"))
                return
            payout = {
                "id": f"payout_{len(self.storage.list('payouts')) + 1}",
                "merchant_id": merchant_id,
                "amount_minor": payload.get("amount_minor", 0),
                "status": "processing",
                "method": payload.get("method", "upi"),
            }
            self.storage.append("payouts", payout)
            self._send_json(201, compose_response("payout_created", payout))
            return

        if path == "/api/payouts/validate-account":
            account = str(payload.get("account_number", ""))
            ifsc = str(payload.get("ifsc_code", "")).upper()
            valid = account.isdigit() and len(account) >= 9 and len(ifsc) == self.VALID_IFSC_LEN and ifsc[:4].isalpha() and ifsc[4].isdigit() and ifsc[5:7].isalpha() and ifsc[7:].isdigit()
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
            dispute = self.storage.find("disputes", dispute_id)
            if dispute:
                dispute.update(payload)
                self.storage._persist("disputes")
            else:
                dispute = {"id": dispute_id, "status": payload.get("status", "needs_response")}
                self.storage.append("disputes", dispute)
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
            payout = self.storage.find("payouts", payout_id)
            if not payout:
                self._send_json(404, error_response("not_found", "payout not found"))
                return
            allowed = {"status", "method"}
            updates = {k: v for k, v in payload.items() if k in allowed}
            if not updates:
                self._send_json(400, error_response("invalid_request", "no updatable fields provided"))
                return
            updated = self.storage.update("payouts", payout_id, updates)
            self._send_json(200, compose_response("payout_updated", updated))
            return

        if path.startswith("/api/merchants/"):
            merchant_id = path.split("/")[-1]
            merchant = self.storage.find("merchants", merchant_id)
            if not merchant:
                self._send_json(404, error_response("not_found", "merchant not found"))
                return
            allowed = {"legal_name", "email", "status", "kyc_status"}
            updates = {k: v for k, v in payload.items() if k in allowed}
            if not updates:
                self._send_json(400, error_response("invalid_request", "no updatable fields provided"))
                return
            updated = self.storage.update("merchants", merchant_id, updates)
            self._send_json(200, compose_response("merchant_updated", updated))
            return

        self._send_json(404, error_response("not_found", f"Route {path} not found"))

    def log_message(self, format, *args):
        return