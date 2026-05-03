from fastapi import FastAPI, Request
import requests
import os
import time

app = FastAPI()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


@app.get("/")
def home():
    return {"status": "relay running"}


@app.post("/send")
async def send_message(req: Request):
    data = await req.json()

    chat_id = data.get("chat_id")
    text = data.get("text", "")

    if not chat_id or not text:
        return {"ok": False, "error": "Missing chat_id or text"}

    last_error = None

    for attempt in range(3):
        try:
            r = requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text[:4000]
                },
                timeout=60
            )
            if r.status_code == 200:
                return {"ok": True}
            last_error = f"Telegram status {r.status_code}: {r.text}"
        except Exception as e:
            last_error = str(e)
            time.sleep(2)

    return {"ok": False, "error": last_error}
