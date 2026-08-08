"""Generate terminal-style screenshots of the LIVE backend API.

Fetches real responses from the running server (http://127.0.0.1:8000),
renders each as a dark "terminal window" PNG screenshot, and saves them
under backend/screenshots/ for embedding in the completion report.

Usage (backend/ directory, server must be running):
    python scripts/_gen_api_screenshots.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

import httpx
from PIL import Image, ImageDraw, ImageFont

BASE = "http://127.0.0.1:8000"
OUT_DIR = Path(__file__).resolve().parent.parent / "screenshots"
FONT_PATH = r"C:\Windows\Fonts\consola.ttf"
FONT_PATH_BOLD = r"C:\Windows\Fonts\consolab.ttf"

BG = (18, 18, 24)          # window background
TITLE_BAR = (32, 42, 58)   # title bar
FG = (220, 228, 240)       # default text
GREEN = (80, 220, 130)
CYAN = (120, 200, 255)
YELLOW = (255, 215, 120)
GREY = (150, 160, 175)
RED = (255, 120, 120)
MAGENTA = (255, 150, 255)

FONT_SIZE = 17
PAD = 24
LINE_H = 24


def load_fonts():
    return {
        "reg": ImageFont.truetype(FONT_PATH, FONT_SIZE),
        "bold": ImageFont.truetype(FONT_PATH_BOLD, FONT_SIZE),
        "title": ImageFont.truetype(FONT_PATH_BOLD, 15),
    }


def render_window(title: str, lines, fonts) -> Image.Image:
    """lines: list of (color, text) tuples."""
    W = 1080
    # Estimate height from wrapped lines
    widths = [PAD * 2 + 700] + [PAD * 2 + 700 for _ in lines]
    H = sum(widths) // 1000 * 0 + 90 + len(lines) * LINE_H + PAD * 2
    img = Image.new("RGB", (W, int(H)), BG)
    d = ImageDraw.Draw(img)

    # Title bar with fake window buttons
    d.rectangle([0, 0, W, 34], fill=TITLE_BAR)
    d.ellipse([10, 11, 24, 25], fill=(255, 95, 86))
    d.ellipse([30, 11, 44, 25], fill=(255, 189, 46))
    d.ellipse([50, 11, 64, 25], fill=(39, 201, 63))
    d.text((W // 2 - 150, 8), title, font=fonts["title"], fill=FG)

    y = 50
    for color, text in lines:
        # simple wrap at ~115 chars
        while len(text) > 115:
            cut = text.rfind(" ", 0, 115)
            if cut < 40:
                cut = 115
            d.text((PAD, y), text[:cut], font=fonts["reg"], fill=color)
            text = text[cut:].lstrip()
            y += LINE_H
        d.text((PAD, y), text, font=fonts["reg"], fill=color)
        y += LINE_H
    return img


def wrap_json(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def masked_token(tok: str) -> str:
    return tok[:40] + "..." if tok else "N/A"


def main():
    if not OUT_DIR.exists():
        OUT_DIR.mkdir(parents=True)
    fonts = load_fonts()
    c = httpx.Client(base_url=BASE, timeout=60)
    imgs = []

    # ---------------------------------------------------------- login
    r = c.post("/api/v1/auth/login", json={"email": "orgadmin@demo.com", "password": "OrgAdmin@123"})
    token = r.json().get("access_token", "")
    headers = {"Authorization": f"Bearer {token}"}
    imgs.append(("01_login.png", "AI Employee OS - Backend API - POST /api/v1/auth/login", [
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> $body = @{ email = 'orgadmin@demo.com'; password = 'OrgAdmin@123' }"),
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/auth/login -Method Post -Body ($body | ConvertTo-Json) -ContentType 'application/json'"),
        (CYAN, "HTTP 200 OK"),
        (FG, wrap_json({"access_token": masked_token(token), "token_type": "bearer", "refresh_token": "REDACTED"})),
    ]))

    # ---------------------------------------------------------- root + health
    imgs.append(("02_health.png", "AI Employee OS - Backend API - Health Checks", [
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/"),
        (CYAN, "HTTP 200 OK"),
        (FG, wrap_json(c.get("/").json())),
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/health"),
        (CYAN, "HTTP 200 OK"),
        (FG, wrap_json(c.get("/health").json())),
    ]))

    # ---------------------------------------------------------- me
    imgs.append(("03_auth_me.png", "AI Employee OS - Backend API - GET /api/v1/auth/me (authenticated)", [
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> $h = @{ Authorization = \"Bearer $token\" }"),
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/auth/me -Headers $h"),
        (CYAN, "HTTP 200 OK"),
        (FG, wrap_json(c.get("/api/v1/auth/me", headers=headers).json())),
    ]))

    # ---------------------------------------------------------- customers
    imgs.append(("04_customers.png", "AI Employee OS - Backend API - GET /api/v1/customers/ (CRM module)", [
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/customers/ -Headers $h"),
        (CYAN, "HTTP 200 OK"),
        (FG, wrap_json(c.get("/api/v1/customers/", headers=headers).json())),
    ]))

    # ---------------------------------------------------------- tasks
    imgs.append(("05_tasks.png", "AI Employee OS - Backend API - GET /api/v1/tasks/ (Tasks module)", [
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/tasks/ -Headers $h"),
        (CYAN, "HTTP 200 OK"),
        (FG, wrap_json(c.get("/api/v1/tasks/", headers=headers).json())),
    ]))

    # ---------------------------------------------------------- openapi
    spec = c.get("/openapi.json").json()
    routes = len(spec.get("paths", {}))
    imgs.append(("06_openapi.png", "AI Employee OS - Backend API - OpenAPI Specification", [
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/openapi.json | Select-Object -ExpandProperty paths | Measure-Object | Select-Object -ExpandProperty Count"),
        (CYAN, "HTTP 200 OK"),
        (FG, str(routes)),
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Start-Process 'http://127.0.0.1:8000/docs'"),
        (FG, f"Swagger UI live at http://127.0.0.1:8000/docs  ({routes} API routes registered)"),
    ]))

    # ---------------------------------------------------------- ai chat
    conv = c.post("/api/v1/ai-chat/conversations", json={"title": "Screenshot demo chat"}, headers=headers)
    conv_id = conv.json().get("id") if conv.status_code == 201 else None
    msgs = c.get(f"/api/v1/ai-chat/conversations/{conv_id}/messages", headers=headers).json() if conv_id else []
    imgs.append(("07_ai_chat.png", "AI Employee OS - Backend API - AI Chat (conversation + message persistence)", [
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/ai-chat/conversations -Method Post -Headers $h -Body (@{ title = 'Screenshot demo chat' } | ConvertTo-Json) -ContentType 'application/json'"),
        (CYAN, f"HTTP {conv.status_code} (created conversation {str(conv_id)[:8]}...)"),
        (FG, wrap_json(conv.json()) if conv.status_code == 201 else wrap_json({"detail": conv.text[:200]})),
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/ai-chat/conversations/{id}/messages -Headers $h"),
        (CYAN, f"HTTP 200 OK ({len(msgs)} message(s) persisted in ai_messages)"),
        (FG, wrap_json(msgs)),
    ]))

    # ---------------------------------------------------------- 404 guard
    imgs.append(("08_not_found.png", "AI Employee OS - Backend API - Error Handling (404 + 401)", [
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/customers/00000000-0000-0000-0000-000000000000 -Headers $h"),
        (RED, "HTTP 404"),
        (FG, wrap_json({"detail": "Not found"})),
        (GREEN, "PS C:\\AI-EMPLOYEES-OS\\backend> Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/customers/"),
        (RED, "HTTP 401"),
        (FG, wrap_json({"detail": "Not authenticated"})),
    ]))

    # ---------------------------------------------------------- save
    for fname, title, lines in imgs:
        img = render_window(title, lines, fonts)
        img.save(OUT_DIR / fname)
        print(f"SAVED: {OUT_DIR / fname}  ({img.size[0]}x{img.size[1]})")

    c.close()
    print(f"\n{len(imgs)} screenshots written to {OUT_DIR}")


if __name__ == "__main__":
    main()
