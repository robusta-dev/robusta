import streamlit as st
from streamlit import session_state as ss


def update_changes(trigger, action):
    ss.trigger = trigger
    ss.action = action
    ss.current_page = "playbook_builder"
    ss.expander_state = [False, False, False, False, True]
    ss.playbook_chosen = True


def display_demo_playbook():

    st.set_page_config(
        page_title="Demo Playbooks",
        page_icon=":wrench:",
    )
    st.title("Demo Playbooks", anchor=None)

    if "expander_state" not in ss:
        ss.expander_state = [True, False, False, False, False]
    if "trigger" not in ss:
        ss.trigger = ""
    if "action" not in ss:
        ss.action = ""

    release_fail_expander = st.expander(":zap: Get notified when a Helm release fails", expanded=False)
    deployment_change_expander = st.expander(":zap: Get notified when a deployment changes", expanded=False)
    ingress_change_expander = st.expander(":zap: Get notified when an ingress changes", expanded=False)

    with release_fail_expander:
        st.markdown(
            "on_helm_release_fail is triggered when a Helm release enters a failed state. This is a one-time trigger, meaning that it only fires once when the release fails."
        )
        st.image("./docs/images/helm-release-failed.png")
        st.button(
            "Use Playbook",
            key="but_release_fail",
            on_click=lambda: update_changes("on_helm_release_fail", "helm_status_enricher"),
        )

    with deployment_change_expander:
        st.markdown(
            "on_deployment_update is triggered for every deployment updated. When this happens the resource_babysitter action sends you the changed field and details of what changed."
        )
        st.image("./docs/images/deployment-image-change.png")
        st.button(
            "Use Playbook",
            key="but_deploy_change",
            on_click=lambda: update_changes("on_deployment_update", "resource_babysitter"),
        )

    with ingress_change_expander:
        st.markdown(
            "on_ingress_all_changes is triggered for every change in an ingress. The resource_babysitter action sends you the changed field and details of what changed."
        )
        st.image("./docs/images/ingress-image-change.png")
        st.button(
            "Use Playbook",
            key="but_ingress_change",
            on_click=lambda: update_changes("on_ingress_all_changes", "resource_babysitter"),
        )
