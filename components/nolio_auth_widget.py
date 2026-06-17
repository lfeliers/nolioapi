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


def _restore_session_from_db() -> None:
    """On cold load, check DB for a linked account and populate session state."""
    if "nolio_user_id" not in st.session_state:
        db_user = get_any_user()
        if db_user:
            st.session_state["nolio_user_id"] = str(db_user["_id"])
            st.session_state["nolio_profile"] = db_user.get("profile", {})


def _handle_oauth_callback() -> None:
    params = st.query_params
    if "code" not in params or "nolio_token" in st.session_state:
        return

    if "nolio_user_id" in st.session_state:
        st.warning("An account is already linked. Unlink it first.")
        st.query_params.clear()
        return

    code = params["code"]
    with st.spinner("Linking your Nolio account…"):
        try:
            token_data = exchange_code_for_token(code, REDIRECT_URI)
            access_token = token_data["access_token"]
            profile = get_user(access_token)
            user_id = str(profile["id"])
            upsert_user(
                user_id=user_id,
                token=access_token,
                token_type=token_data.get("token_type", "Bearer"),
                profile=profile,
                refresh_token=token_data.get("refresh_token", ""),
            )
            st.session_state["nolio_token"] = access_token
            st.session_state["nolio_user_id"] = user_id
            st.session_state["nolio_profile"] = profile
            st.session_state["oauth_state"] = secrets.token_urlsafe(16)
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Failed to link account: {e}")


def _handle_token_refresh() -> None:
    if "nolio_user_id" not in st.session_state or "nolio_token" in st.session_state:
        return
    user_id = st.session_state["nolio_user_id"]
    db_user = db_get_user(user_id)
    if db_user and db_user.get("refresh_token"):
        try:
            token_data = refresh_access_token(db_user["refresh_token"])
            access_token = token_data["access_token"]
            upsert_user(
                user_id=user_id,
                token=access_token,
                token_type=token_data.get("token_type", "Bearer"),
                profile=db_user.get("profile", {}),
                refresh_token=token_data.get("refresh_token", ""),
            )
            st.session_state["nolio_token"] = access_token
            st.session_state["nolio_profile"] = db_user.get("profile", {})
            st.rerun()
        except RuntimeError:
            st.session_state.pop("nolio_user_id", None)


def render_navbar() -> None:
    """Render the Nolio auth widget in a top-right navbar. Call once per page."""
    if "oauth_state" not in st.session_state:
        st.session_state["oauth_state"] = secrets.token_urlsafe(16)

    _restore_session_from_db()
    _handle_oauth_callback()
    _handle_token_refresh()

    linked = "nolio_user_id" in st.session_state
    profile = st.session_state.get("nolio_profile", {})
    display_name = profile.get("email", profile.get("username", "Nolio"))

    st.markdown(
        """
        <style>
        /* scrollable athlete list column */
        div.main div[data-testid="stHorizontalBlock"] > div:first-child {
            height: 75vh;
            overflow-y: auto;
            overflow-x: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, right = st.columns([6, 1])
    with right:
        if linked:
            st.markdown(
                f"<span style='color:#ccc; font-size:0.85rem; white-space:nowrap;'>"
                f"✓ {display_name}</span>",
                unsafe_allow_html=True,
            )
            if st.button("Unlink", key="navbar_unlink"):
                user_id = st.session_state.get("nolio_user_id")
                if user_id:
                    delete_user(user_id)
                st.session_state.pop("nolio_token", None)
                st.session_state.pop("nolio_user_id", None)
                st.session_state.pop("nolio_profile", None)
                st.rerun()
        else:
            auth_url = get_authorize_url(REDIRECT_URI, st.session_state["oauth_state"])
            st.link_button("Connect Nolio", auth_url, type="primary")
