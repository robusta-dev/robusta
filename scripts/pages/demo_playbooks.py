import streamlit as st
from streamlit import session_state as ss


def update_changes(trigger, action):
    ss.trigger = trigger
    ss.action = action
    ss.current_page = "playbook_builder"
    ss.playbook_chosen = True


def display_demo_playbook():

    st.set_page_config(
        page_title="Demo Playbooks",
        page_icon=":wrench:",
    )
    st.title("Demo Playbooks", anchor=None)

    if "trigger" not in ss:
        ss.trigger = ""
    if "action" not in ss:
        ss.action = ""

    release_fail_expander = st.expander(":zap: Get notified when a Helm release fails", expanded=False)
    deployment_change_expander = st.expander(":zap: Get notified when a deployment changes", expanded=False)
    ingress_change_expander = st.expander(":zap: Get notified when an ingress changes", expanded=False)

    with release_fail_expander:
        st.markdown(
            "When a Helm release enters failed state the on_helm_release_fail trigger is fired. Using the information from the trigger, helm_status_enricher is run to add more information to the alert"
        )
        st.image("./docs/images/helm-release-failed.png")
        st.button(
            "Use Playbook",
            key="but_release_fail",
            on_click=lambda: update_changes("on_helm_release_fail", "helm_status_enricher"),
        )

    with deployment_change_expander:
        st.markdown(
            "When a deployment changes, the on_deployment_update trigger is fired. An alert is sent with data from the resource_babysitter action based on your customization."
        )
        st.image("./docs/images/deployment-image-change.png")
        st.button(
            "Use Playbook",
            key="but_deploy_change",
            on_click=lambda: update_changes("on_deployment_update", "resource_babysitter"),
        )

    with ingress_change_expander:
        st.markdown(
            "When an ingress changes, the on_ingress_all_changes trigger is fired. An alert is sent with data from the resource_babysitter action based on your customization."
        )
        st.image("./docs/images/ingress-image-change.png")
        st.button(
            "Use Playbook",
            key="but_ingress_change",
            on_click=lambda: update_changes("on_ingress_all_changes", "resource_babysitter"),
        )
