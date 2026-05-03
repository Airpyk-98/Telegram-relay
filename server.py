import os
import asyncio
import httpx
from fastapi import FastAPI, Request, Response
import requests

app = FastAPI()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


@app.get("/")
def home():
    return {"status": "relay running"}


# Simple relay: HF posts here, we forward to Telegram
@app.post("/send")
async def send_message(req: Request):
    data = await req.json()
    chat_id = data.get("chat_id")
    text = data.get("text", "")

    if not chat_id or not text:
        return {"ok": False, "error": "Missing chat_id or text"}

    for attempt in range(3):
        try:
            r = requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={"chat_id": chat_id, "text": text[:4000]},
                timeout=60
            )
            if r.status_code == 200:
                return {"ok": True}
        except Exception as e:
            if attempt == 2:
                return {"ok": False, "error": str(e)}

    return {"ok": False, "error": "failed"}


# HTTP CONNECT proxy — Hermes routes Telegram outbound calls through here
@app.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str, req: Request):
    url = f"https://{path}"
    body = await req.body()
    headers = dict(req.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=req.method,
            url=url,
            headers=headers,
            content=body,
            timeout=60
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers)
        )
