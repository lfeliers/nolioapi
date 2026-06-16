import os
import secrets

import streamlit as st

from auth.nolio_auth import exchange_code_for_token, get_authorize_url, get_user
from db.mongo import delete_user, upsert_user

REDIRECT_URI = os.environ.get("NOLIO_REDIRECT_URI", "http://localhost:8501")

st.set_page_config(page_title="Nolio Connect", page_icon="🔗")
st.title("Nolio Integration")

# Pre-generate OAuth state so it's ready before the button is clicked
if "oauth_state" not in st.session_state:
    st.session_state["oauth_state"] = secrets.token_urlsafe(16)

params = st.query_params

# Handle OAuth callback (Nolio redirected back with ?code=...)
if "code" in params and "nolio_token" not in st.session_state:
    code = params["code"]
    returned_state = params.get("state", "")
    expected_state = st.session_state.get("oauth_state", "")

    if expected_state and returned_state != expected_state:
        st.error("Invalid state parameter — please try linking again.")
    else:
        with st.spinner("Linking your Nolio account…"):
            try:
                token = exchange_code_for_token(code, REDIRECT_URI)
                user = get_user(token)
                user_id = str(user["id"])
                upsert_user(
                    user_id=user_id,
                    token=token,
                    token_type="Bearer",
                    profile=user,
                )
                st.session_state["nolio_token"] = token
                st.session_state["nolio_user"] = user
                st.session_state["nolio_user_id"] = user_id
                # Rotate state for next session
                st.session_state["oauth_state"] = secrets.token_urlsafe(16)
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to link account: {e}")

# Linked state
if "nolio_user" in st.session_state:
    user = st.session_state["nolio_user"]
    st.success("Nolio account linked!")
    st.json(user)
    if st.button("Unlink Account"):
        user_id = st.session_state.get("nolio_user_id")
        if user_id:
            delete_user(user_id)
        del st.session_state["nolio_token"]
        del st.session_state["nolio_user"]
        st.session_state.pop("nolio_user_id", None)
        st.rerun()
else:
    st.write("Connect your Nolio account to get started.")
    auth_url = get_authorize_url(REDIRECT_URI, st.session_state["oauth_state"])
    st.link_button("Link Nolio Account", auth_url, type="primary")
