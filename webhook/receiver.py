import hmac
import logging
import os

from fastapi import FastAPI, Header, HTTPException, Request

from webhook.handlers import dispatch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("nolio.receiver")

app = FastAPI(redirect_slashes=False)

WEBHOOK_KEY = os.environ.get("NOLIO_WEBHOOK_KEY", "")


@app.post("/webhook/nolio")
@app.post("/webhook/nolio/")
async def nolio_webhook(
    request: Request,
    x_nolio_key: str = Header(default=""),
) -> dict:
    logger.info("incoming webhook — headers: %s", dict(request.headers))

    if not WEBHOOK_KEY:
        logger.error("NOLIO_WEBHOOK_KEY is not set")
        raise HTTPException(status_code=500, detail="Webhook key not configured")

    if not hmac.compare_digest(x_nolio_key, WEBHOOK_KEY):
        logger.warning("auth failed — received key: %r", x_nolio_key)
        raise HTTPException(status_code=403, detail="Invalid webhook key")

    payload = await request.json()
    logger.info("payload: %s", payload)
    dispatch(payload)
    return {"status": "ok"}
