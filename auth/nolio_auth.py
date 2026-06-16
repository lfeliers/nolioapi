import os

import requests

CLIENT_ID = "zu5tAhsMKaMv23BHK4eUO6o5NwOVUB0uDULy7Udf"
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
