from __future__ import annotations

import logging

logger = logging.getLogger("nolio.webhook")


def handle_event(payload: dict) -> None:
    notif_type = payload["notif_type"]
    object_type = payload["object_type"]
    object_id = payload["object_id"]
    user_id = payload["user_id"]
    date_object = payload.get("date_object")

    if notif_type == "deleted_event":
        logger.info("[event] deleted %s #%s by user %s", object_type, object_id, user_id)
        return

    logger.info("[event] %s — %s #%s at %s by user %s", notif_type, object_type, object_id, date_object, user_id)


def handle_metric(payload: dict) -> None:
    notif_type = payload["notif_type"]
    object_id = payload["object_id"]
    user_id = payload["user_id"]
    metric_type = payload.get("metric_type")
    date_object = payload.get("date_object")

    if notif_type == "deleted_metric":
        logger.info("[metric] deleted #%s (type=%s) by user %s", object_id, metric_type, user_id)
        return

    logger.info("[metric] %s — type=%s #%s at %s by user %s", notif_type, metric_type, object_id, date_object, user_id)


def handle_planned(payload: dict) -> None:
    notif_type = payload["notif_type"]
    object_type = payload["object_type"]
    object_id = payload["object_id"]
    user_id = payload["user_id"]
    date_object = payload.get("date_object")

    if notif_type == "deleted_planned_event":
        logger.info("[planned] deleted %s #%s for athlete %s", object_type, object_id, user_id)
        return

    logger.info("[planned] %s — %s #%s at %s for athlete %s", notif_type, object_type, object_id, date_object, user_id)


def dispatch(payload: dict) -> None:
    notif_type = payload["notif_type"]
    livemode = payload["livemode"]

    if not livemode:
        logger.info("[test delivery] notif_type=%s", notif_type)

    # Check "planned" BEFORE "event" — new_planned_event contains both substrings
    if "planned" in notif_type:
        handle_planned(payload)
    elif "metric" in notif_type:
        handle_metric(payload)
    elif "event" in notif_type:
        handle_event(payload)
    else:
        logger.warning("[webhook] unknown notif_type=%r payload=%s", notif_type, payload)
