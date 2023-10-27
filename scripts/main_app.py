from pages import demo_playbooks, playbook_builder
from streamlit import session_state as ss

if "current_page" not in ss:
    ss.current_page = "demo_playbooks"

if "playbook_chosen" not in ss:
    ss.playbook_chosen = False

if ss.current_page == "demo_playbooks" and not ss.playbook_chosen:
    demo_playbooks.display_demo_playbook()

elif ss.current_page == "playbook_builder":
    playbook_builder.display_playbook_builder()
