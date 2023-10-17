import streamlit as st
from streamlit import session_state as ss


def set_playbook_options():
    print("PLAYBOOK OPTIONS SET")
    print(ss)
    ss.trigger = "on_helm_release_fail"
    ss.actions = "helm_status_enricher"
    ss.current_page = "playbook_builder"
    ss.expander_state = [False, False, False, False, True]
    ss.playbook_choosen = True


def display_demo_playbook():

    st.set_page_config(
        page_title="Demo Playbooks",
        page_icon=":wrench:",
    )
    print("Demo Playbook Running")
    st.title("Demo Playbooks", anchor=None)

    if "expander_state" not in st.session_state:
        ss.expander_state = [True, False, False, False, False]

    if "triggers" not in ss:
        ss.triggers = ""
    if "actions" not in ss:
        ss.actions = ""
    playbook_expander = st.expander(
        ":zap: Get notified when a Helm release fails", expanded=st.session_state.expander_state[0]
    )

    # if "button_clicked" not in st.session_state:
    #     st.session_state.button_clicked = False

    # if not st.session_state.trigger_name or st.session_state.actions or st.session_state.expander_state:
    #     st.session_state.trigger_name = "on_helm_release_fail"
    #     st.session_state.actions = "add_silence"
    #     st.session_state.expander_state = [True, False, False, False, False]

    with playbook_expander:

        st.markdown(
            "on_helm_release_fail is triggered when a Helm release enters a failed state. This is a one-time trigger, meaning that it only fires once when the release fails."
        )
        # st.markdown("**Trigger:** When a Prometheus alert with the name KubePodCrashLooping")
        # st.markdown("**Action:** Gets the logs of the pod")
        # st.markdown("**Sample Alert:**")
        st.image("./docs/images/helm-release-failed.png")
        st.button("Use Playbook", key="buttondemo", on_click=set_playbook_options)
        # if st.button("Use Playbook", key="buttondemo"):
        #     ss.trigger = "on_helm_release_fail"
        #     ss.actions = "helm_status_enricher"
        #     ss.current_page = "playbook_builder"
        #     ss.expander_state = [False, False, False, False, True]
        #     ss.playbook_choosen = True
        #     print(st.session_state)
        #     st.experimental_rerun()
