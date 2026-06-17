import streamlit as st

from auth.nolio_auth import get_athletes
from components.nolio_auth_widget import render_navbar

st.set_page_config(page_title="Nolio Integration", page_icon="🔗", layout="wide")

render_navbar()

st.title("Nolio Integration")

token = st.session_state.get("nolio_token")

if not token:
    st.info("Link your Nolio account using the button above.")
else:
    st.subheader("Athletes")
    try:
        athletes = get_athletes(token)
        if athletes:
            for athlete in athletes:
                st.write(f"**{athlete.get('first_name', '')} {athlete.get('last_name', '')}** — ID: `{athlete.get('id')}`")
        else:
            st.write("No athletes found.")
    except Exception as e:
        st.error(f"Failed to fetch athletes: {e}")
