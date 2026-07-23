import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

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

def cors_headers(handler: BaseHTTPRequestHandler):
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Idempotency-Key")