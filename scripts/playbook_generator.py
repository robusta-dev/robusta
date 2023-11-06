# run with poetry run streamlit run scripts/playbook_generator.py or use the streamlit.Dockerfile
# to get streamlit-pydantic to not show something, it needs to be a Literal or a PrivateAttr
# if a Literal, it still must have a default value
# TODO: filter out BaseExecutionEvent actions that don't make sense like `add_silence`
# TODO: perhaps mark certain actions as recommended

from collections import OrderedDict
from typing import List, Set, Optional, Literal
from enum import Enum, StrEnum

import streamlit_antd_components as sac
import streamlit as st
import streamlit_pydantic as sp
import yaml
from streamlit import session_state as ss
from pydantic import BaseModel

from robusta.core.playbooks.generation import ExamplesGenerator, find_playbook_actions
from custom_streamlit_pydantic import modified_pydantic_form, GroupOptionalFieldsStrategy

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


class Screens(StrEnum):
    TRIGGER = "Choose Trigger"
    ACTION = "Choose Action"
    YAML = "Apply Configuration"

    def to_index(self):
        return [Screens.TRIGGER, Screens.ACTION, Screens.YAML].index(self)

    @classmethod
    def get_current_screen(cls):
        if "current_screen" not in ss:
            return cls.TRIGGER

        # there seems to be a streamlit bug with how enums are stored in session state
        # we work around by recreating the enum. without this, equality checks on the enum always return False
        return cls(ss.current_screen.value)

    @classmethod
    def set_current_screen(cls, new_screen):
        old_screen = ss.get("current_screen")
        ss.current_screen = new_screen
        if new_screen != old_screen:
            st.rerun()


def display_triggers():
    trigger_names = list(triggers.keys())
    if ss.get("trigger_name") is not None:
        index = trigger_names.index(ss["trigger_name"])
    else:
        index = None

    st.info(":zap: Triggers are events that cause a playbook to start running")
    ss["trigger_name"] = st.selectbox(
        "Choose a trigger",
        trigger_names,
        key="trigger",
        placeholder="Type to search",
        index=index
    )
    if ss["trigger_name"] is None:
        return

    # use an instance with previous form data if it exists, otherwise use the model class
    trigger_data = ss.get("trigger_data") or triggers[ss["trigger_name"]]

    ss["trigger_data"] = modified_pydantic_form(
        key=f"trigger_form-{ss['trigger_name']}",
        model=triggers[ss['trigger_name']],
        ignore_empty_values=True,
        group_optional_fields="expander",
        title=f"*{ss['trigger_name']}* settings",
        submit_label="Continue",
        on_submit=lambda: Screens.set_current_screen(Screens.ACTION)
    )


def display_playbook_builder():
    st.button(":point_left: Choose a Playbook template", key="choose_playbook_btn", on_click=go_to_demo_playbooks)
    st.title(":wrench: Playbook Builder", anchor=None)

    current_screen = Screens.get_current_screen()

    step = sac.steps(
        items=[
            sac.StepsItem(title=Screens.TRIGGER),
            sac.StepsItem(title=Screens.ACTION),
            sac.StepsItem(title=Screens.YAML),
        ], index=current_screen.to_index(), format_func='title'
    )

    if step == Screens.TRIGGER:
        print("display triggers")
        display_triggers()


    # TODO: move this part to a function like display_triggers(). this requires not just moving it to a function, but updating the code to use modified_pydantic_form etc
    elif step == Screens.ACTION:
        print("display actions")
        st.info(":zap: Actions are what the playbook *does* - they can collect data or execute remediations")
        relevant_actions = [a.action_name for a in triggers_to_actions[ss['trigger_name']]]
        ss['action_name'] = st.selectbox("Choose an action", relevant_actions, key="action")
        action_obj = actions_by_name.get(ss['action_name'], None)
        if action_obj and hasattr(action_obj, "params_type") and hasattr(action_obj.params_type, "schema"):
            action_data = sp.pydantic_form(
                key=f"action_form-{ss['action_name']}",
                model=action_obj.params_type,
                ignore_empty_values=True,
                group_optional_fields="expander"
            )
            try:
                ss['action_data'] = action_obj.params_type(**action_data).dict(exclude_defaults=True)
                ss['action_ready'] = True
            except:
                pass
        else:
            st.markdown("This action doesn't have any parameters")
            ss['action_data'] = None
            ss['action_ready'] = True
        st.button("Continue", key="button2", on_click=Screens.set_current_screen, args=[Screens.YAML])

    elif step == Screens.YAML:
        st.info(":scroll: Add this YAML to Robusta's Helm values to configure your playbook")
        if not ss['trigger_data']:
            st.warning("Error: mandatory Trigger fields are missing!")
        if not ss['action_ready']:
            st.warning("Error: mandatory Action fields are missing!")

        st.markdown(
            "Add this code to your **generated_values.yaml** and [upgrade Robusta](https://docs.robusta.dev/external-prom-docs/setup-robusta/upgrade.html)"
        )

        trigger_dict = ss["trigger_data"].dict(exclude_defaults=True)
        if ss['action_data'] is None:
            playbook = {
                "customPlaybooks": [
                    OrderedDict([("triggers", [{ss['trigger_name']: ss['trigger_data']}]), ("actions", [{ss['action_name']: {}}])])
                ]
            }
        else:
            playbook = {
                "customPlaybooks": [
                    OrderedDict(
                        [("triggers", [{ss['trigger_name']: ss['trigger_data']}]), ("actions", [{ss['action_name']: ss['action_data']}])]
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
