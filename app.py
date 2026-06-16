import hashlib
import os
import secrets

import streamlit as st

from auth.nolio_auth import exchange_code_for_token, get_authorize_url
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

    with st.spinner("Linking your Nolio account…"):
            try:
                token_data = exchange_code_for_token(code, REDIRECT_URI)
                access_token = token_data["access_token"]
                user_id = hashlib.sha256(access_token.encode()).hexdigest()[:16]
                upsert_user(
                    user_id=user_id,
                    token=access_token,
                    token_type=token_data.get("token_type", "Bearer"),
                    profile={},
                )
                st.session_state["nolio_token"] = access_token
                st.session_state["nolio_user_id"] = user_id
                st.session_state["oauth_state"] = secrets.token_urlsafe(16)
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to link account: {e}")

# Linked state
if "nolio_token" in st.session_state:
    st.success("Nolio account linked!")
    if st.button("Unlink Account"):
        user_id = st.session_state.get("nolio_user_id")
        if user_id:
            delete_user(user_id)
        st.session_state.pop("nolio_token", None)
        st.session_state.pop("nolio_user_id", None)
        st.rerun()
else:
    st.write("Connect your Nolio account to get started.")
    auth_url = get_authorize_url(REDIRECT_URI, st.session_state["oauth_state"])
    st.link_button("Link Nolio Account", auth_url, type="primary")
