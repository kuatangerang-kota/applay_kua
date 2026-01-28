import streamlit as st

def hide_sidebar():
    with st.sidebar:
        st.empty()

def top_actions(show_back=True, back_target="dashboard"):
    col1, col2 = st.columns([1,1])

    if show_back:
        if col1.button("⬅ Kembali", use_container_width=True):
            st.session_state.menu_selected = back_target
            st.rerun()

    if col2.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()
