import os

import requests

CLIENT_ID = os.environ.get("NOLIO_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("NOLIO_CLIENT_SECRET", "")
BASE_URL = "https://www.nolio.io/api"


def get_authorize_url(redirect_uri: str, state: str) -> str:
    return (
        f"{BASE_URL}/authorize/"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )


def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/token/",
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(refresh_token: str) -> dict:
    """Returns new token dict. CRITICAL: store the new refresh_token — old one is invalidated."""
    resp = requests.post(
        f"{BASE_URL}/token/",
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    if resp.status_code == 400:
        raise RuntimeError("refresh_token invalid or revoked — full re-auth required")
    resp.raise_for_status()
    return resp.json()


def get_trainings(token: str, athlete_id: int, from_date: str, to_date: str) -> list[dict]:
    resp = requests.get(
        f"{BASE_URL}/get/training/",
        headers={"Authorization": f"Bearer {token}"},
        params={"athlete_id": athlete_id, "from": from_date, "to": to_date, "limit": 300},
    )
    resp.raise_for_status()
    return resp.json()


def get_athletes(token: str) -> list[dict]:
    resp = requests.get(
        f"{BASE_URL}/get/athletes/",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


def get_user(token: str) -> dict:
    resp = requests.get(
        f"{BASE_URL}/get/user/",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()
