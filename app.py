import streamlit as st

from components.nolio_auth_widget import render_navbar

st.set_page_config(page_title="Nolio Integration", page_icon="🔗", layout="wide")

render_navbar()

st.title("Nolio Integration")
st.write("Your app content goes here.")
