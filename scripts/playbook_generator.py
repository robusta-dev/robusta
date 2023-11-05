# run with poetry run streamlit run scripts/playbook_generator.py or use the streamlit.Dockerfile
# to get streamlit-pydantic to not show something, it needs to be a Literal or a PrivateAttr
# if a Literal, it still must have a default value
# TODO: filter out BaseExecutionEvent actions that don't make sense like `add_silence`
# TODO: perhaps mark certain actions as recommended

from collections import OrderedDict
from typing import List, Set, Optional, Literal
from enum import Enum

import streamlit as st
import streamlit_pydantic as sp
import yaml
from streamlit import session_state as ss
from pydantic import BaseModel
from robusta.core.playbooks.generation import ExamplesGenerator, find_playbook_actions

st.set_page_config(
    page_title="Playbook Generator",
    page_icon=":wrench:",
)


def update_changes(trigger, action):
    ss.trigger = trigger
    ss.action = action
    ss.current_page = "playbook_builder"
    ss.playbook_chosen = True


def go_to_playbook_builder():
    for key in st.session_state.keys():
        if key != "current_page":
            del st.session_state[key]
        ss.current_page = "playbook_builder"


def go_to_demo_playbooks():
    for key in st.session_state.keys():
        if key != "current_page":
            del st.session_state[key]
        ss.current_page = "demo_playbooks"


def display_demo_playbook():

    st.button(":point_right: Create a custom Playbooks ", key="playbook_builder_btn", on_click=go_to_playbook_builder)

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


generator = ExamplesGenerator()
triggers = generator.get_all_triggers()
actions = find_playbook_actions("./playbooks/robusta_playbooks")
actions_by_name = {a.action_name: a for a in actions}
triggers_to_actions = generator.get_triggers_to_actions(actions)


class ExpanderState(Enum):
    TRIGGER = 1
    TRIGGER_PARAMS = 2
    ACTION = 3
    ACTION_PARAMS = 4
    YAML = 5


def set_expander_state(state: ExpanderState):
    ss.expander_state = state


def display_playbook_builder():
    st.button(":point_left: Choose a Playbook template", key="choose_playbook_btn", on_click=go_to_demo_playbooks)
    st.title(":wrench: Playbook Builder", anchor=None)
    if "expander_state" not in ss:
        ss.expander_state = ExpanderState.TRIGGER

    # there seems to be a streamlit bug with how enums are stored in session state
    # we work around by recreating the enum. without this, equality checks on the enum always return False
    expander_state = ExpanderState(ss.expander_state.value)

    # initialize expanders
    trigger_expander = st.expander(
        ":zap: Trigger - A trigger is an event that starts your Playbook",
        expanded=expander_state == ExpanderState.TRIGGER,
    )
    trigger_parameter_expander = st.expander(
        "Configure Trigger", expanded=expander_state == ExpanderState.TRIGGER_PARAMS
    )
    action_expander = st.expander(
        ":boom: Action - An action is an event a Playbook performs after it starts",
        expanded=expander_state == ExpanderState.ACTION,
    )
    action_parameter_expander = st.expander(
        "Configure Action", expanded=expander_state == ExpanderState.ACTION_PARAMS
    )
    playbook_expander = st.expander(":scroll: Playbook", expanded=expander_state == ExpanderState.YAML)

    trigger_ready = False
    action_ready = False

    # TRIGGER
    with trigger_expander:
        trigger_name = st.selectbox("Type to search", triggers.keys(), key="trigger")
        st.button("Continue", key="button1", on_click=set_expander_state, args=[ExpanderState.TRIGGER_PARAMS])

    # TRIGGER PARAMETER
    with trigger_parameter_expander:
        # st.header("Available Parameters")
        trigger_data = sp.pydantic_input(key=f"trigger_form-{trigger_name}", model=triggers[trigger_name], ignore_empty_values=True)

        try:
            trigger_data = triggers[trigger_name](**trigger_data).dict(exclude_defaults=True)
            trigger_ready = True
        except:
            pass
        st.button("Continue", key="button2", on_click=set_expander_state, args=[ExpanderState.ACTION])

    # ACTION
    with action_expander:
        relevant_actions = [a.action_name for a in triggers_to_actions[trigger_name]]
        action_name = st.selectbox("Choose an action", relevant_actions, key="action")
        st.button("Continue", key="button3", on_click=set_expander_state, args=[ExpanderState.ACTION_PARAMS])

    # ACTION PARAMETER
    with action_parameter_expander:
        action_obj = actions_by_name.get(action_name, None)
        if action_obj and hasattr(action_obj, "params_type") and hasattr(action_obj.params_type, "schema"):
            action_data = sp.pydantic_input(key=f"action_form-{action_name}", model=action_obj.params_type, ignore_empty_values=True)
            try:
                action_data = action_obj.params_type(**action_data).dict(exclude_defaults=True)
                action_ready = True
            except:
                pass
        else:
            st.markdown("This action doesn't have any parameters")
            action_data = None
            action_ready = True

        st.button("Continue", key="button4", on_click=set_expander_state, args=[ExpanderState.YAML])

    # DISPLAY PLAYBOOK
    with playbook_expander:
        if not trigger_ready:
            st.warning("Error: mandatory Trigger fields are missing!")
        if not action_ready:
            st.warning("Error: mandatory Action fields are missing!")

        st.markdown(
            "Add this code to your **generated_values.yaml** and [upgrade Robusta](https://docs.robusta.dev/external-prom-docs/setup-robusta/upgrade.html)"
        )

        if action_data is None:
            playbook = {
                "customPlaybooks": [
                    OrderedDict([("triggers", [{trigger_name: trigger_data}]), ("actions", [{action_name: {}}])])
                ]
            }
        else:
            playbook = {
                "customPlaybooks": [
                    OrderedDict(
                        [("triggers", [{trigger_name: trigger_data}]), ("actions", [{action_name: action_data}])]
                    )
                ]
            }

        yaml.add_representer(
            OrderedDict, lambda dumper, data: dumper.represent_mapping("tag:yaml.org,2002:map", data.items())
        )

        st.code(yaml.dump(playbook))


if __name__ == "__main__":

    if "current_page" not in ss:
        ss.current_page = "demo_playbooks"

    if ss.current_page == "demo_playbooks":
        display_demo_playbook()

    elif ss.current_page == "playbook_builder":
        display_playbook_builder()
