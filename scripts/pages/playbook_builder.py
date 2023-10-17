# run with poetry run streamlit run scripts/playbook_builder.py
from collections import OrderedDict

import streamlit as st
import streamlit_pydantic as sp
import yaml

# from robusta.api import Action
from robusta.core.playbooks.generation import ExamplesGenerator, find_playbook_actions

# from streamlit import session_state as ss


# from typing import List, Optional
# from pydantic import BaseModel, Field
generator = ExamplesGenerator()
triggers = generator.get_all_triggers()
actions = find_playbook_actions("./playbooks/robusta_playbooks")
actions_by_name = {a.action_name: a for a in actions}
triggers_to_actions = generator.get_triggers_to_actions(actions)


def display_playbook_builder():

    # if "current_page" not in st.session_state:
    #     st.session_state.current_page = "playbook_builder"

    # if ss.get('button_clicked', False):  # If button was clicked
    #     ss.button_clicked = False  # Reset the flag
    # if "buttondemo" in st.session_state:
    #     st.session_state.buttondemo = False

    st.title(":wrench: Playbook Builder", anchor=None)
    print("TITLE IS HERE")
    if "expander_state" not in st.session_state:
        st.session_state.expander_state = [True, False, False, False, False]

    # INITIALIZING ALL EXPANDERS
    trigger_expander = st.expander(
        ":zap: Trigger - A trigger is an event that starts your Playbook", expanded=st.session_state.expander_state[0]
    )
    trigger_parameter_expander = st.expander("Configure Trigger", expanded=st.session_state.expander_state[1])
    action_expander = st.expander(
        ":boom: Action - An action is an event a Playbook performs after it starts",
        expanded=st.session_state.expander_state[2],
    )
    action_parameter_expander = st.expander("Configure Action", expanded=st.session_state.expander_state[3])
    playbook_expander = st.expander(":scroll: Playbook", expanded=st.session_state.expander_state[4])

    print("PLAYBOOK BUILDER POST EXPANDERS")

    # TRIGGER
    with trigger_expander:
        print("TRIGGERS")

        trigger_name = st.selectbox("Type to search", triggers.keys(), key="trigger")
        # st.markdown(triggers[trigger_name]["about"])

        if st.button("Continue", key="button1"):
            st.session_state.expander_state = [False, True, False, False, False]
            st.experimental_rerun()

    # TRIGGER PARAMETER
    with trigger_parameter_expander:
        print("TRIGGER PARAMETERS")
        # st.header("Available Parameters")
        trigger_data = sp.pydantic_input(key=f"trigger_form-{trigger_name}", model=triggers[trigger_name])

        if st.button("Continue", key="button2"):
            st.session_state.expander_state = [False, False, True, False, False]
            st.experimental_rerun()

    # ACTION
    with action_expander:
        print("DEMO ACTIONS")
        relevant_actions = [a.action_name for a in triggers_to_actions[trigger_name]]
        action_name = st.selectbox("Choose an action", relevant_actions, key="actions")

        # st.markdown(actions[action_name]["about"])

        if st.button("Continue", key="button3"):
            st.session_state.expander_state = [False, False, False, True, False]
            st.experimental_rerun()

    # ACTION PARAMETER
    with action_parameter_expander:
        action_obj = actions_by_name.get(action_name, None)

        if action_obj and hasattr(action_obj, "params_type") and hasattr(action_obj.params_type, "schema"):
            action_data = sp.pydantic_input(key=f"action_form-{action_name}", model=action_obj.params_type)
            if st.button("Continue", key="button4"):
                st.session_state.expander_state = [False, False, False, False, True]
                st.experimental_rerun()
        else:
            st.markdown("This action doesn't have any parameters")
            st.session_state.expander_state = [False, False, False, False, True]
            action_data = None
            # st.experimental_rerun()          <----------------------------BUG

    # DISPLAY PLAYBOOK
    with playbook_expander:
        print("Display Playbooks")

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
        # st.experimental_rerun()
