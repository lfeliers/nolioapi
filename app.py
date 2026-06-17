import os
import secrets

import streamlit as st

from auth.nolio_auth import (
    exchange_code_for_token,
    get_authorize_url,
    get_user,
    refresh_access_token,
)
from db.mongo import delete_user, get_any_user, get_user as db_get_user, upsert_user

REDIRECT_URI = os.environ.get("NOLIO_REDIRECT_URI", "http://localhost:8501")

st.set_page_config(page_title="Nolio Connect", page_icon="🔗")
st.title("Nolio Integration")

if "oauth_state" not in st.session_state:
    st.session_state["oauth_state"] = secrets.token_urlsafe(16)

# On cold load, restore session from DB if an account is already stored
if "nolio_user_id" not in st.session_state:
    db_user = get_any_user()
    if db_user:
        st.session_state["nolio_user_id"] = str(db_user["_id"])
        st.session_state["nolio_profile"] = db_user.get("profile", {})

params = st.query_params

# Handle OAuth callback — only if no account is linked yet
if "code" in params and "nolio_token" not in st.session_state:
    if "nolio_user_id" in st.session_state:
        st.warning("An account is already linked. Unlink it first.")
        st.query_params.clear()
    else:
        code = params["code"]
        with st.spinner("Linking your Nolio account…"):
            try:
                token_data = exchange_code_for_token(code, REDIRECT_URI)
                access_token = token_data["access_token"]
                refresh_token = token_data.get("refresh_token", "")
                profile = get_user(access_token)
                user_id = str(profile["id"])
                upsert_user(
                    user_id=user_id,
                    token=access_token,
                    token_type=token_data.get("token_type", "Bearer"),
                    profile=profile,
                    refresh_token=refresh_token,
                )
                st.session_state["nolio_token"] = access_token
                st.session_state["nolio_user_id"] = user_id
                st.session_state["nolio_profile"] = profile
                st.session_state["oauth_state"] = secrets.token_urlsafe(16)
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to link account: {e}")

# Auto-refresh: session knows user_id but has no token — try stored refresh_token
if "nolio_user_id" in st.session_state and "nolio_token" not in st.session_state:
    user_id = st.session_state["nolio_user_id"]
    db_user = db_get_user(user_id)
    if db_user and db_user.get("refresh_token"):
        try:
            token_data = refresh_access_token(db_user["refresh_token"])
            access_token = token_data["access_token"]
            new_refresh = token_data.get("refresh_token", "")
            upsert_user(
                user_id=user_id,
                token=access_token,
                token_type=token_data.get("token_type", "Bearer"),
                profile=db_user.get("profile", {}),
                refresh_token=new_refresh,
            )
            st.session_state["nolio_token"] = access_token
            st.session_state["nolio_profile"] = db_user.get("profile", {})
            st.rerun()
        except RuntimeError:
            st.session_state.pop("nolio_user_id", None)

# --- UI ---
if "nolio_user_id" in st.session_state:
    profile = st.session_state.get("nolio_profile", {})
    st.success(f"Nolio account linked — {profile.get('email', profile.get('username', ''))}")
    st.json(profile)
    if st.button("Unlink Account"):
        user_id = st.session_state.get("nolio_user_id")
        if user_id:
            delete_user(user_id)
        st.session_state.pop("nolio_token", None)
        st.session_state.pop("nolio_user_id", None)
        st.session_state.pop("nolio_profile", None)
        st.rerun()
else:
    st.write("Connect your Nolio account to get started.")
    auth_url = get_authorize_url(REDIRECT_URI, st.session_state["oauth_state"])
    st.link_button("Link Nolio Account", auth_url, type="primary")
