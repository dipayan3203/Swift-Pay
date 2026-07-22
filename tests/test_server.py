import json
import socket
import subprocess
import sys
import time
import urllib.request
import unittest
from pathlib import Path


class PythonBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.port = cls._find_free_port()
        cls.process = subprocess.Popen(
            [sys.executable, str(cls.repo_root / "server.py"), "--port", str(cls.port)],
            cwd=cls.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        cls._wait_for_server(cls.port)

    @classmethod
    def tearDownClass(cls):
        if cls.process.poll() is None:
            cls.process.terminate()
            try:
                cls.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.process.kill()

    @staticmethod
    def _find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    @classmethod
    def _wait_for_server(cls, port, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as response:
                    if response.status == 200:
                        return
            except Exception:
                time.sleep(0.2)
        raise RuntimeError("Python backend did not start")

    def _request(self, path, method="GET", data=None, headers=None):
        body = None if data is None else json.dumps(data).encode("utf-8")
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=body, method=method, headers=headers or {})
        with urllib.request.urlopen(req, timeout=5) as response:
            payload = response.read().decode("utf-8")
            return response.status, json.loads(payload) if payload else None

    def test_health_endpoint(self):
        status, payload = self._request("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_payment_creation(self):
        status, payload = self._request(
            "/api/payments",
            method="POST",
            data={"merchant_id": "m_1001", "amount_minor": 19900, "currency": "INR", "payment_method": "card"},
            headers={"Content-Type": "application/json", "Idempotency-Key": "test-key-001"},
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload["data"]["status"], "initiated")
        self.assertEqual(payload["data"]["amount_minor"], 19900)


if __name__ == "__main__":
    unittest.main()
