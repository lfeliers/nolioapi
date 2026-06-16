from __future__ import annotations


def handle_event(payload: dict) -> None:
    notif_type = payload["notif_type"]
    object_type = payload["object_type"]
    object_id = payload["object_id"]
    user_id = payload["user_id"]
    date_object = payload.get("date_object")  # absent on deletes

    if notif_type == "deleted_event":
        print(f"[event] deleted {object_type} #{object_id} by user {user_id}")
        return

    print(f"[event] {notif_type} — {object_type} #{object_id} at {date_object} by user {user_id}")


def handle_metric(payload: dict) -> None:
    notif_type = payload["notif_type"]
    object_id = payload["object_id"]
    user_id = payload["user_id"]
    metric_type = payload.get("metric_type")
    date_object = payload.get("date_object")

    if notif_type == "deleted_metric":
        print(f"[metric] deleted #{object_id} (type={metric_type}) by user {user_id}")
        return

    print(f"[metric] {notif_type} — type={metric_type} #{object_id} at {date_object} by user {user_id}")


def handle_planned(payload: dict) -> None:
    notif_type = payload["notif_type"]
    object_type = payload["object_type"]
    object_id = payload["object_id"]
    user_id = payload["user_id"]
    date_object = payload.get("date_object")

    if notif_type == "deleted_planned_event":
        print(f"[planned] deleted {object_type} #{object_id} for athlete {user_id}")
        return

    print(f"[planned] {notif_type} — {object_type} #{object_id} at {date_object} for athlete {user_id}")


def dispatch(payload: dict) -> None:
    notif_type = payload["notif_type"]
    livemode = payload["livemode"]

    if not livemode:
        print(f"[test delivery] notif_type={notif_type}")

    # Check "planned" BEFORE "event" — new_planned_event contains both substrings
    if "planned" in notif_type:
        handle_planned(payload)
    elif "metric" in notif_type:
        handle_metric(payload)
    elif "event" in notif_type:
        handle_event(payload)
    else:
        print(f"[webhook] unknown notif_type={notif_type!r}, payload={payload}")
