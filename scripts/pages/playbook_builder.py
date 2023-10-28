# run with poetry run streamlit run scripts/main_app.py or use the streamlit.Dockerfile
from collections import OrderedDict
from enum import Enum

import streamlit as st
import streamlit_pydantic as sp
import yaml
from streamlit import session_state as ss

from robusta.core.playbooks.generation import ExamplesGenerator, find_playbook_actions

generator = ExamplesGenerator()
triggers = generator.get_all_triggers()
actions = find_playbook_actions("./playbooks/robusta_playbooks")
actions_by_name = {a.action_name: a for a in actions}
triggers_to_actions = generator.get_triggers_to_actions(actions)


def go_back():
    for key in st.session_state.keys():
        if key != "current_page":
            del st.session_state[key]
        ss.current_page = "demo_playbooks"


class ExpanderState (Enum):
    TRIGGER = 1
    TRIGGER_PARAMS = 2
    ACTION = 3
    ACTION_PARAMS = 4
    YAML = 5


def set_expander_state(state: ExpanderState):
    ss.expander_state=state


def display_playbook_builder():
    st.button(":point_left: Choose a Playbook", key="choose_playbook", on_click=go_back)
    st.title(":wrench: Playbook Builder", anchor=None)
    if "expander_state" not in ss:
        ss.expander_state = ExpanderState.TRIGGER

    print("expander_state is", ss.expander_state)
    # initialize expanders
    trigger_expander = st.expander(
        ":zap: Trigger - A trigger is an event that starts your Playbook",
        expanded=ss.expander_state == ExpanderState.TRIGGER
    )
    trigger_parameter_expander = st.expander(
        "Configure Trigger",
        expanded=ss.expander_state == ExpanderState.TRIGGER_PARAMS
    )
    action_expander = st.expander(
        ":boom: Action - An action is an event a Playbook performs after it starts",
        expanded=ss.expander_state == ExpanderState.ACTION
    )
    action_parameter_expander = st.expander(
        "Configure Action",
        expanded=ss.expander_state == ExpanderState.ACTION_PARAMS
    )
    playbook_expander = st.expander(
        ":scroll: Playbook",
        expanded=ss.expander_state == ExpanderState.YAML
    )

    # TRIGGER
    with trigger_expander:
        trigger_name = st.selectbox("Type to search", triggers.keys(), key="trigger")
        st.button("Continue", key="button1", on_click=set_expander_state, args=[ExpanderState.TRIGGER_PARAMS])

    # TRIGGER PARAMETER
    with trigger_parameter_expander:
        st.header("Available Parameters")
        trigger_data = sp.pydantic_input(key=f"trigger_form-{trigger_name}", model=triggers[trigger_name])
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
            action_data = sp.pydantic_input(key=f"action_form-{action_name}", model=action_obj.params_type)
        else:
            st.markdown("This action doesn't have any parameters")
            action_data = None
        st.button("Continue", key="button4", on_click=set_expander_state, args=[ExpanderState.YAML])

    # DISPLAY PLAYBOOK
    with playbook_expander:
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
