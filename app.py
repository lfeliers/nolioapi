import streamlit as st

from auth.nolio_auth import get_athletes
from components.nolio_auth_widget import render_navbar
from db.mongo import upsert_athlete

st.set_page_config(page_title="Nolio Integration", page_icon="🔗", layout="wide")

st.markdown(
    "<style>[data-testid='stSidebarNav'], [data-testid='stSidebar'] { display: none; }</style>",
    unsafe_allow_html=True,
)

render_navbar()

st.title("Nolio Integration")

token = st.session_state.get("nolio_token")


@st.cache_data(ttl=300, show_spinner="Fetching athletes…")
def fetch_and_sync_athletes(token: str) -> list[dict]:
    athletes = get_athletes(token)
    for athlete in athletes:
        upsert_athlete(athlete)
    return athletes


if not token:
    st.info("Link your Nolio account using the button above.")
else:
    try:
        athletes = fetch_and_sync_athletes(token)

        col_list, col_detail = st.columns([1, 3])

        with col_list:
            st.subheader("Athletes")
            for athlete in athletes:
                if st.button(athlete.get("name"), key=f"athlete_{athlete['nolio_id']}", use_container_width=True):
                    st.session_state["selected_athlete_id"] = athlete["nolio_id"]

        with col_detail:
            selected_id = st.session_state.get("selected_athlete_id")
            if not selected_id:
                st.info("Select an athlete to see their details.")
            else:
                athlete = next((a for a in athletes if a["nolio_id"] == selected_id), None)
                if athlete:
                    st.subheader(athlete.get("name"))
                    st.markdown(f"**Nolio ID:** `{athlete.get('nolio_id')}`")
                    teams = athlete.get("teams", [])
                    if teams:
                        st.markdown("**Teams:**")
                        for team in teams:
                            st.markdown(f"- {team.get('name')} (ID: `{team.get('id')}`)")
                    else:
                        st.markdown("**Teams:** —")

    except Exception as e:
        st.error(f"Failed to fetch athletes: {e}")
