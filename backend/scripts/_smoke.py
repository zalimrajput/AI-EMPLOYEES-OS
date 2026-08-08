"""Dev smoke test - verify protected endpoints with a real Supabase JWT.

Usage (backend running on :8100):
    .venv\\Scripts\\python.exe scripts\\_smoke.py
"""
import sys

import httpx

from app.core.config import settings


def get_token(email: str, password: str) -> str:
    url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {"apikey": settings.SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    r = httpx.post(url, json={"email": email, "password": password}, headers=headers, timeout=30)
    if r.status_code != 200:
        print(f"LOGIN_FAIL {r.status_code}: {r.text[:300]}")
        sys.exit(2)
    return r.json()["access_token"]


def req(token: str, method: str, path: str, body=None):
    headers = {"Authorization": f"Bearer {token}"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    r = httpx.request(method, f"http://127.0.0.1:8000{path}", headers=headers, json=body, timeout=30)
    print(f"{method} {path} -> {r.status_code} | {r.text[:400]}")
    return r


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "org"
    if mode == "org":
        token = get_token("orgadmin@demo.com", "OrgAdmin@123")
    else:
        token = get_token("employee@demo.com", "Employee@123")
    print("TOKEN OK")
    req(token, "GET", "/api/v1/auth/me")
    req(token, "GET", "/api/v1/modules/")
    req(token, "GET", "/api/v1/customers/")
    req(token, "GET", "/api/v1/analytics/summary")
    req(token, "GET", "/api/v1/tasks/")
    req(token, "GET", "/api/v1/organization-settings/")
    req(token, "GET", "/api/v1/ai-employees/")
    req(token, "GET", "/api/v1/departments/")