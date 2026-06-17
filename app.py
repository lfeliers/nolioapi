from datetime import date, timedelta

import streamlit as st

from auth.nolio_auth import get_athletes, get_trainings
from components.nolio_auth_widget import render_navbar
from db.mongo import get_trainings_for_athlete, upsert_athlete, upsert_training

st.set_page_config(page_title="Nolio Integration", page_icon="🔗", layout="wide")

st.markdown(
    "<style>[data-testid='stSidebarNav'], [data-testid='stSidebar'] { display: none; }</style>",
    unsafe_allow_html=True,
)

render_navbar()

st.title("Nolio Integration")

token = st.session_state.get("nolio_token")


def week_bounds() -> tuple[str, str]:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat(), today.isoformat()


def fmt_duration(seconds: int) -> str:
    h, m = divmod(seconds // 60, 60)
    return f"{h}h{m:02d}" if h else f"{m}min"


@st.cache_data(ttl=300, show_spinner="Fetching athletes…")
def fetch_and_sync_athletes(token: str) -> list[dict]:
    athletes = get_athletes(token)
    for athlete in athletes:
        upsert_athlete(athlete)
    return athletes


@st.cache_data(ttl=300, show_spinner="Fetching trainings…")
def fetch_and_sync_trainings(token: str, athlete_id: int, from_date: str, to_date: str) -> list[dict]:
    trainings = get_trainings(token, athlete_id, from_date, to_date)
    for training in trainings:
        upsert_training(training, athlete_id)
    return trainings


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
                        st.markdown("**Teams:** " + ", ".join(t.get("name", "") for t in teams))

                    st.divider()
                    st.markdown("**This week's trainings**")

                    from_date, to_date = week_bounds()
                    trainings = fetch_and_sync_trainings(token, selected_id, from_date, to_date)

                    if not trainings:
                        st.caption("No trainings recorded this week.")
                    else:
                        for t in trainings:
                            with st.container(border=True):
                                c1, c2 = st.columns([3, 1])
                                with c1:
                                    st.markdown(f"**{t.get('name', '—')}**")
                                    st.caption(f"{t.get('sport', '')} · {t.get('date_start', '')}")
                                with c2:
                                    st.metric("Duration", fmt_duration(t.get("duration", 0)))
                                if t.get("distance"):
                                    st.caption(f"Distance: {t['distance']:.1f} km · Elevation: {t.get('elevation_gain', 0):.0f} m")

    except Exception as e:
        st.error(f"Error: {e}")
