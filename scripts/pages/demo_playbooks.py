import streamlit as st
from streamlit import session_state as ss


def update_changes():
    ss.current_page = "playbook_builder"
    ss.expander_state = [False, False, False, False, True]
    ss.playbook_choosen = True


def release_fail_options():
    ss.trigger = "on_helm_release_fail"
    ss.actions = "helm_status_enricher"
    update_changes()


def deployment_change_options():
    ss.trigger = "on_deployment_update"
    ss.actions = "resource_babysitter"
    update_changes()


def ingress_change_options():
    ss.trigger = "on_ingress_all_changes"
    ss.actions = "resource_babysitter"
    update_changes()


def display_demo_playbook():

    st.set_page_config(
        page_title="Demo Playbooks",
        page_icon=":wrench:",
    )
    st.title("Demo Playbooks", anchor=None)

    if "expander_state" not in st.session_state:
        ss.expander_state = [True, False, False, False, False]
    if "triggers" not in ss:
        ss.triggers = ""
    if "actions" not in ss:
        ss.actions = ""

    release_fail_expander = st.expander(":zap: Get notified when a Helm release fails", expanded=False)
    deployment_change_expander = st.expander(":zap: Get notified when a deployment changes", expanded=False)
    ingress_change_expander = st.expander(":zap: Get notified when an ingress changes", expanded=False)

    with release_fail_expander:
        st.markdown(
            "on_helm_release_fail is triggered when a Helm release enters a failed state. This is a one-time trigger, meaning that it only fires once when the release fails."
        )
        st.image("./docs/images/helm-release-failed.png")
        st.button("Use Playbook", key="but_release_fail", on_click=release_fail_options)

    with deployment_change_expander:
        st.markdown(
            "on_deployment_update is triggered for every deployment updated. When this happens the resource_babysitter action sends you the changed field and details of what changed."
        )
        st.image("./docs/images/deployment-image-change.png")
        st.button("Use Playbook", key="but_deploy_change", on_click=deployment_change_options)

    with ingress_change_expander:
        st.markdown(
            "on_ingress_all_changes is triggered for every change in an ingress. The resource_babysitter action sends you the changed field and details of what changed."
        )
        st.image("./docs/images/ingress-image-change.png")
        st.button("Use Playbook", key="but_ingress_change", on_click=ingress_change_options)
