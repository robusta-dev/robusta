import streamlit as st
from pages import demo_playbooks, playbook_builder
from streamlit import session_state as ss

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "demo_playbooks"

if "playbook_choosen" not in st.session_state:
    ss.playbook_choosen = False

if st.session_state.current_page == "demo_playbooks" and not ss.playbook_choosen:
    print("Demo PlayBooks")
    demo_playbooks.display_demo_playbook()

elif st.session_state.current_page == "playbook_builder":
    print(st.session_state)
    print("DemoBuilder")
    playbook_builder.display_playbook_builder()
    # st.experimental_rerun()
