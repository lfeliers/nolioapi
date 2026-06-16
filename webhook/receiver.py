import hmac
import os

from fastapi import FastAPI, Header, HTTPException, Request

from webhook.handlers import dispatch

app = FastAPI(redirect_slashes=False)

WEBHOOK_KEY = os.environ.get("NOLIO_WEBHOOK_KEY", "")


@app.post("/webhook/nolio")
@app.post("/webhook/nolio/")
async def nolio_webhook(
    request: Request,
    x_nolio_key: str = Header(...),
) -> dict:
    if not hmac.compare_digest(x_nolio_key, WEBHOOK_KEY):
        raise HTTPException(status_code=403, detail="Invalid webhook key")

    payload = await request.json()
    dispatch(payload)
    return {"status": "ok"}
