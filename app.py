from datetime import date, timedelta

import streamlit as st

from auth.nolio_auth import get_athletes, get_planned_trainings, get_trainings
from components.nolio_auth_widget import render_navbar
from db.mongo import upsert_athlete, upsert_training

st.set_page_config(page_title="Nolio Integration", page_icon="🔗", layout="wide")

st.markdown(
    "<style>[data-testid='stSidebarNav'], [data-testid='stSidebar'] { display: none; }</style>",
    unsafe_allow_html=True,
)

render_navbar()

st.title("Nolio Integration")

token = st.session_state.get("nolio_token")


def week_bounds() -> tuple[str, str, str, str]:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    tomorrow = today + timedelta(days=1)
    return (
        monday.isoformat(),
        today.isoformat(),
        tomorrow.isoformat(),
        sunday.isoformat(),
    )


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
def fetch_and_sync_trainings(
    token: str, athlete_id: int, from_date: str, to_date: str
) -> list[dict]:
    trainings = get_trainings(token, athlete_id, from_date, to_date)
    for training in trainings:
        upsert_training(training, athlete_id)
    return trainings


@st.cache_data(ttl=300, show_spinner="Fetching planned trainings…")
def fetch_planned_trainings(
    token: str, athlete_id: int, from_date: str, to_date: str
) -> list[dict]:
    return get_planned_trainings(token, athlete_id, from_date, to_date)


if not token:
    st.info("Link your Nolio account using the button above.")
else:
    try:
        athletes = fetch_and_sync_athletes(token)

        col_list, col_detail = st.columns([1, 4])

        with col_list:
            st.subheader("Athletes")
            with st.container(height=600):
                for athlete in athletes:
                    if st.button(
                        athlete.get("name"),
                        key=f"athlete_{athlete['nolio_id']}",
                        use_container_width=True,
                    ):
                        st.session_state["selected_athlete_id"] = athlete["nolio_id"]

        with col_detail:
            selected_id = st.session_state.get("selected_athlete_id")
            if not selected_id:
                st.info("Select an athlete to see their details.")
            else:
                athlete = next(
                    (a for a in athletes if a["nolio_id"] == selected_id), None
                )
                if athlete:
                    st.subheader(athlete.get("name"))
                    st.markdown(f"**Nolio ID:** `{athlete.get('nolio_id')}`")

                    teams = athlete.get("teams", [])
                    if teams:
                        st.markdown(
                            "**Teams:** " + ", ".join(t.get("name", "") for t in teams)
                        )

                    st.divider()
                    st.markdown("**This week's trainings**")

                    monday_date = date.today() - timedelta(days=date.today().weekday())
                    from_date, to_date, tomorrow, sunday = week_bounds()

                    trainings = fetch_and_sync_trainings(
                        token, selected_id, from_date, to_date
                    )
                    planned = fetch_planned_trainings(
                        token, selected_id, tomorrow, sunday
                    )

                    # Group by date
                    done_by_day: dict[str, list] = {}
                    for t in trainings:
                        done_by_day.setdefault(t["date_start"], []).append(t)

                    planned_by_day: dict[str, list] = {}
                    for t in planned:
                        planned_by_day.setdefault(t["date_start"], []).append(t)

                    day_cols = st.columns(7)
                    for i, col in enumerate(day_cols):
                        day = monday_date + timedelta(days=i)
                        day_str = day.isoformat()
                        with col:
                            st.markdown(f"**{day.strftime('%a')}**")
                            st.caption(day.strftime("%d %b"))

                            for t in done_by_day.get(day_str, []):
                                distance = (
                                    f"<div style='font-size:0.75rem;color:#fca5a5;'>{t['distance']:.1f} km</div>"
                                    if t.get("distance")
                                    else ""
                                )
                                st.markdown(
                                    f"""
                                    <div style="
                                        background:#450a0a;
                                        border:1px solid #7f1d1d;
                                        border-radius:8px;
                                        padding:0.6rem 0.75rem;
                                        margin-bottom:0.5rem;
                                    ">
                                        <div style="font-size:0.85rem;font-weight:600;color:#fecaca;">{t.get("name", "—")}</div>
                                        <div style="font-size:0.75rem;color:#fca5a5;">{t.get("sport", "")}</div>
                                        <div style="font-size:0.75rem;color:#fca5a5;">{fmt_duration(t.get("duration", 0))}</div>
                                        {distance}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            for t in planned_by_day.get(day_str, []):
                                distance = (
                                    f"<div style='font-size:0.75rem;color:#fca5a5;'>{t['distance']:.1f} km</div>"
                                    if t.get("distance")
                                    else ""
                                )
                                duration = (
                                    fmt_duration(t["duration"])
                                    if t.get("duration")
                                    else ""
                                )
                                st.markdown(
                                    f"""
                                    <div style="
                                        background:transparent;
                                        border:1px dashed #7f1d1d;
                                        border-radius:8px;
                                        padding:0.6rem 0.75rem;
                                        margin-bottom:0.5rem;
                                    ">
                                        <div style="font-size:0.85rem;font-weight:600;color:#fecaca;">{t.get("name", "—")}</div>
                                        <div style="font-size:0.75rem;color:#fca5a5;">{t.get("sport", "")}</div>
                                        <div style="font-size:0.75rem;color:#fca5a5;">{duration}</div>
                                        {distance}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

    except Exception as e:
        st.error(f"Error: {e}")
