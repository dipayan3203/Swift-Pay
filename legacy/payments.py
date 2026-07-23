import json
from http.server import BaseHTTPRequestHandler

from ..server import storage, compose_response, error_response, validate_payment, add_webhook, parse_body


def handle_payments_routes(handler: BaseHTTPRequestHandler, path: str, payload: dict, idempotency_key: str):
    if path == "/api/payments":
        if handler.command == "GET":
            handler._send_json(200, {"payments": storage.list("payments")})
            return True
        if handler.command == "POST":
            if idempotency_key:
                if idempotency_key in storage.idempotency_keys:
                    existing = next((p for p in storage.list("payments") if p.get("idempotency_key") == idempotency_key), None)
                    if existing:
                        handler._send_json(200, compose_response("payment_created", existing))
                        return True
            valid, err = validate_payment(payload)
            if not valid:
                handler._send_json(400, error_response("invalid_request", err))
                return True
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
            handler._send_json(201, compose_response("payment_created", payment))
            return True

    return False