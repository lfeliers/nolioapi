import streamlit as st

from auth.nolio_auth import get_athletes
from components.nolio_auth_widget import render_navbar
from db.mongo import upsert_athlete

st.set_page_config(page_title="Nolio Integration", page_icon="🔗", layout="wide")

render_navbar()

st.title("Nolio Integration")

token = st.session_state.get("nolio_token")


@st.cache_data(ttl=300, show_spinner="Fetching athletes…")
def fetch_athletes(token: str) -> list[dict]:
    return get_athletes(token)


if not token:
    st.info("Link your Nolio account using the button above.")
else:
    st.subheader("Athletes")
    try:
        athletes = fetch_athletes(token)
        for athlete in athletes:
            upsert_athlete(athlete)
            if st.button(athlete.get("name"), key=f"athlete_{athlete['nolio_id']}"):
                st.session_state["selected_athlete_id"] = athlete["nolio_id"]
                st.switch_page("pages/athlete.py")
    except Exception as e:
        st.error(f"Failed to fetch athletes: {e}")
