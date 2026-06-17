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


async def _handle(request: Request, x_nolio_key: str) -> dict:
    if not WEBHOOK_KEY:
        logger.error("NOLIO_WEBHOOK_KEY is not set")
        raise HTTPException(status_code=500, detail="Webhook key not configured")

    if not hmac.compare_digest(x_nolio_key, WEBHOOK_KEY):
        logger.warning("auth failed — received key: %r", x_nolio_key)
        raise HTTPException(status_code=403, detail="Invalid webhook key")

    payload = await request.json()

    if not payload.get("livemode", True):
        logger.info("test delivery received — notif_type=%s, ignoring", payload.get("notif_type"))
        return {"status": "ok"}

    logger.info("payload: %s", payload)
    dispatch(payload)
    return {"status": "ok"}


@app.post("/webhook/nolio/events")
@app.post("/webhook/nolio/events/")
async def webhook_events(
    request: Request,
    x_nolio_key: str = Header(default=""),
) -> dict:
    return await _handle(request, x_nolio_key)


@app.post("/webhook/nolio/planned")
@app.post("/webhook/nolio/planned/")
async def webhook_planned(
    request: Request,
    x_nolio_key: str = Header(default=""),
) -> dict:
    return await _handle(request, x_nolio_key)


@app.post("/webhook/nolio/metrics")
@app.post("/webhook/nolio/metrics/")
async def webhook_metrics(
    request: Request,
    x_nolio_key: str = Header(default=""),
) -> dict:
    return await _handle(request, x_nolio_key)
