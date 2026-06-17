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


# Handle athlete card click via query param
if "select_athlete" in st.query_params:
    st.session_state["selected_athlete_id"] = int(st.query_params["select_athlete"])
    st.query_params.clear()
    st.switch_page("pages/athlete.py")

if not token:
    st.info("Link your Nolio account using the button above.")
else:
    st.subheader("Athletes")
    try:
        athletes = fetch_athletes(token)
        for athlete in athletes:
            upsert_athlete(athlete)

        cards_html = "".join(
            f"""
            <a href="?select_athlete={a['nolio_id']}" style="text-decoration:none;">
              <div style="
                min-width: 140px;
                background: #1e2130;
                border: 1px solid #2d2d2d;
                border-radius: 10px;
                padding: 1rem;
                text-align: center;
                color: #fff;
                font-size: 0.9rem;
                font-weight: 500;
                transition: border-color 0.2s;
                cursor: pointer;
              "
              onmouseover="this.style.borderColor='#4f8ef7'"
              onmouseout="this.style.borderColor='#2d2d2d'"
              >
                {a.get('name', '—')}
              </div>
            </a>
            """
            for a in athletes
        )

        st.markdown(
            f"""
            <div style="
              display: flex;
              flex-direction: row;
              gap: 1rem;
              overflow-x: auto;
              padding: 0.5rem 0 1rem 0;
            ">
              {cards_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.error(f"Failed to fetch athletes: {e}")
