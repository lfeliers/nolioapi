import os
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.collection import Collection

_client: MongoClient | None = None


def _get_collection() -> Collection:
    global _client
    if _client is None:
        _client = MongoClient(os.environ["MONGO_URI"])
    db_name = os.environ.get("MONGODB_DB", "nolioapi")
    return _client[db_name]["users"]


def upsert_user(user_id: str, token: str, token_type: str, profile: dict) -> None:
    col = _get_collection()
    col.update_one(
        {"_id": user_id},
        {
            "$set": {
                "access_token": token,
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


def delete_user(user_id: str) -> None:
    col = _get_collection()
    col.delete_one({"_id": user_id})
