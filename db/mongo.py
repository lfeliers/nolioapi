import os
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.collection import Collection

_client: MongoClient | None = None


def _get_db():
    global _client
    if _client is None:
        _client = MongoClient(os.environ["MONGODB_URI"])
    return _client[os.environ.get("MONGODB_DB", "nolioapi")]


def _get_collection() -> Collection:
    return _get_db()["users"]


def _get_athletes_collection() -> Collection:
    return _get_db()["athletes"]


def _get_trainings_collection() -> Collection:
    return _get_db()["trainings"]


def upsert_user(
    user_id: str,
    token: str,
    token_type: str,
    profile: dict,
    refresh_token: str = "",
) -> None:
    col = _get_collection()
    col.update_one(
        {"_id": user_id},
        {
            "$set": {
                "access_token": token,
                "refresh_token": refresh_token,
                "token_type": token_type,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "profile": profile,
            }
        },
        upsert=True,
    )


def get_user(user_id: str) -> dict | None:
    col = _get_collection()
    return col.find_one({"_id": user_id})


def get_any_user() -> dict | None:
    """Returns the single stored user, or None if the collection is empty."""
    return _get_collection().find_one()


def delete_user(user_id: str) -> None:
    col = _get_collection()
    col.delete_one({"_id": user_id})


def upsert_athlete(athlete: dict) -> None:
    col = _get_athletes_collection()
    col.update_one(
        {"_id": athlete["nolio_id"]},
        {"$set": {**athlete, "synced_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )


def get_athlete(nolio_id: int) -> dict | None:
    return _get_athletes_collection().find_one({"_id": nolio_id})


def get_all_athletes() -> list[dict]:
    return list(_get_athletes_collection().find())


def upsert_training(training: dict, athlete_id: int) -> None:
    col = _get_trainings_collection()
    col.update_one(
        {"_id": training["nolio_id"]},
        {"$set": {**training, "athlete_id": athlete_id, "synced_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )


def get_trainings_for_athlete(athlete_id: int, from_date: str, to_date: str) -> list[dict]:
    return list(
        _get_trainings_collection().find(
            {"athlete_id": athlete_id, "date_start": {"$gte": from_date, "$lte": to_date}},
            sort=[("date_start", -1)],
        )
    )
