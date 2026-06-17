import streamlit as st

from components.nolio_auth_widget import render_navbar
from db.mongo import get_athlete

st.set_page_config(page_title="Athlete", page_icon="🏃", layout="wide")

render_navbar()

if st.button("← Back"):
    st.switch_page("app.py")

athlete_id = st.session_state.get("selected_athlete_id")

if not athlete_id:
    st.warning("No athlete selected.")
    st.stop()

athlete = get_athlete(athlete_id)

if not athlete:
    st.error("Athlete not found.")
    st.stop()

st.title(athlete.get("name", "Unknown Athlete"))

st.markdown(f"**Nolio ID:** `{athlete.get('nolio_id')}`")

teams = athlete.get("teams", [])
if teams:
    st.markdown("**Teams:**")
    for team in teams:
        st.markdown(f"- {team.get('name')} (ID: `{team.get('id')}`)")
else:
    st.markdown("**Teams:** —")

st.markdown(f"*Last synced: {athlete.get('synced_at', 'N/A')}*")
