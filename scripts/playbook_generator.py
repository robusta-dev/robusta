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
    ss["trigger_name"] = trigger
    ss["action_name"] = action
    ss["action_ready"] = False
    # TODO: trigger_ready
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
    st.header("Start from Scratch")
    st.button(":point_right: Create a custom playbook", key="playbook_builder_btn", on_click=go_to_playbook_builder)
    st.header("Start from Template", anchor=None)

    if "trigger_name" not in ss:
        ss["trigger_name"] = "on_helm_release_fail"

    st.subheader("Take action...")
    alert_remediation_expander = st.expander(":zap: Run a K8s Job in response to a Prometheus alert", expanded=False)

    st.subheader("Get notified...")
    release_fail_expander = st.expander(":zap: Get notified when a Helm release fails", expanded=False)
    deployment_change_expander = st.expander(":zap: Get notified when a deployment changes", expanded=False)
    ingress_change_expander = st.expander(":zap: Get notified when an ingress changes", expanded=False)
    hpa_max_expander = st.expander(":zap: Get notified when a HPA reaches max replicas", expanded=False)

    with alert_remediation_expander:
        st.markdown(
            "*Trigger:* on_prometheus_alert\n\n*Action:* alert_handling_job"
        )
        st.image("./docs/images/alert-handling-job.png")
        st.button(
            "Use Playbook",
            key="but_prometheus_remediation",
            on_click=lambda: update_changes("on_prometheus_alert", "alert_handling_job"),
        )

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
    with hpa_max_expander:
        st.markdown(
            "When a HPA reaches its maximum replicas, the on_horizontalpodautoscaler_update trigger is fired. An alert is sent using alert_on_hpa_reached_limit action asking you to increase the value of maxReplicas."
            
        )
        st.image("./docs/images/alert_on_hpa_reached_limit1.png")
        st.button(
            "Use Playbook",
            key="but_hpa_max",
            on_click=lambda: update_changes("on_horizontalpodautoscaler_update", "alert_on_hpa_reached_limit"),
        )


@st.cache_data
def get_examples_generator():
    return ExamplesGenerator()


generator = get_examples_generator()
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
        # we need to do things this way and not with st.rerun() because st.rerun() terminates execution immediately
        # meaning this run will not complete and we won't parse the input properly before st.rerun() happens
        # so we essentially do a deferred rerun
        ss.rerun_necessary = True


POPULAR_TRIGGERS = ["on_prometheus_alert"]
POPULAR_ACTIONS = ["pod_bash_enricher"]


def format_combobox_option(option_name, popular_options):
    if option_name in popular_options:
        return f":fire: {option_name}"
    return option_name


def sort_combobox_options(options, popular_options):
    relevant_popular_options = [t for t in options if t in popular_options]
    other_options = [t for t in options if t not in popular_options]
    return relevant_popular_options + other_options


def custom_selectbox(
        label,
        options,
        default_option,
        popular_options,
        key):
    sorted_options = sort_combobox_options(options, popular_options)
    if default_option is not None:
        index = sorted_options.index(default_option)
    else:
        index = 0
    value = st.selectbox(label, sorted_options, key=key, placeholder="Type to search", index=index)

    # for some reason without this, after making a choice the combobox is not updated to show the new choice
    # instead it keeps the old value - this possibly is a result of the default_option parameter... not sure
    if value != default_option:
        ss.rerun_necessary = True
    return value


def display_triggers():
    trigger_names = list(triggers.keys())
    st.info(":zap: Triggers are events that cause a playbook to start running")

    ss["trigger_name"] = custom_selectbox(
        "Choose a trigger",
        trigger_names,
        ss.get("trigger_name"),
        POPULAR_TRIGGERS,
        "triggers-combo"
    )
    if ss["trigger_name"] is None:
        return

    trigger_model = triggers[ss["trigger_name"]]
    # we don't actually have docs on the triggers today, so no point in outputing docs
    #if trigger_model.__doc__:
    #    with st.expander(f"Docs for {trigger_model}"):
    #        st.markdown(trigger_model.__doc__)

    ss["trigger_data"] = modified_pydantic_form(
        key=f"trigger_form-{ss['trigger_name']}",
        model=trigger_model,
        initial_data=ss.get("trigger_data"),
        ignore_empty_values=True,
        group_optional_fields="expander",
        title=f"*{ss['trigger_name']}* settings",
        submit_label="Continue",
        on_submit=lambda: Screens.set_current_screen(Screens.ACTION)
    )


def display_actions():
    st.info(":zap: Actions are what the playbook *does* - they can collect data or execute remediations")
    relevant_actions = [a.action_name for a in triggers_to_actions[ss["trigger_name"]]]

    # if the user changed triggers and the action is no longer relevant - discard it
    if ss.get("action_name") not in relevant_actions:
        ss["action_name"] = None

    ss["action_name"] = custom_selectbox(
        "Choose an action",
        relevant_actions,
        ss.get("action_name"),
        POPULAR_ACTIONS,
        key="actions-combo"
    )

    if ss["action_name"] is None:
        return

    action_obj = actions_by_name[ss["action_name"]]
    if action_obj.func.__doc__:
        with st.expander(f"Docs for {ss['action_name']}"):
            st.markdown(action_obj.func.__doc__)

    if not hasattr(action_obj, "params_type") or not hasattr(action_obj.params_type, "schema"):
        st.markdown("This action doesn't have any parameters")
        ss["action_data"] = None
        ss["action_ready"] = True
        st.button("Continue", key="actions-continue-no-params", on_click=Screens.set_current_screen, args=[Screens.YAML])
        return

    ss["action_data"] = modified_pydantic_form(
        key=f"action_form-{ss['action_name']}",
        model=action_obj.params_type,
        initial_data=ss.get("action_data"),
        ignore_empty_values=True,
        group_optional_fields="expander",
        title=f"*{ss['action_name']}* settings",
        submit_label="Continue",
        on_submit=lambda: Screens.set_current_screen(Screens.YAML),
    )
    ss["action_ready"] = True


def display_playbook_builder():
    st.button(":point_left: Choose a Playbook template", key="choose_playbook_btn", on_click=go_to_demo_playbooks)
    st.title(":wrench: Playbook Builder", anchor=None)

    current_screen = Screens.get_current_screen()

    step = sac.steps(
        items=[
            sac.StepsItem(title=Screens.TRIGGER),
            sac.StepsItem(title=Screens.ACTION),
            sac.StepsItem(title=Screens.YAML),
        ],
        index=current_screen.to_index(),
        format_func='title',
    )

    new_screen = Screens(step)
    if new_screen != current_screen:
        Screens.set_current_screen(new_screen)

    if new_screen == Screens.TRIGGER:
        display_triggers()
    elif new_screen == Screens.ACTION:
        display_actions()
    elif new_screen == Screens.YAML:
        st.info(":scroll: Add this YAML to Robusta's Helm values to configure your playbook")
        if not ss['trigger_data']:
            st.warning("Error: mandatory Trigger fields are missing!")
        if not ss['action_ready']:
            st.warning("Error: mandatory Action fields are missing!")

        st.markdown(
            "Add this code to your **generated_values.yaml** and [upgrade Robusta](https://docs.robusta.dev/external-prom-docs/setup-robusta/upgrade.html)"
        )

        trigger_dict = ss["trigger_data"].dict(exclude_defaults=True)
        action_dict = ss["action_data"].dict(exclude_defaults=True) if ss["action_data"] else {}
        playbook = {
            "customPlaybooks": [
                OrderedDict([("triggers", [{ss['trigger_name']: trigger_dict}]), ("actions", [{ss['action_name']: action_dict}])])
            ]
        }
        yaml.add_representer(
            OrderedDict, lambda dumper, data: dumper.represent_mapping("tag:yaml.org,2002:map", data.items())
        )

        st.code(yaml.dump(playbook))


if __name__ == "__main__":

    if "current_page" not in ss:
        ss.current_page = "demo_playbooks"

    if "rerun_necessary" not in ss:
        ss.rerun_necessary = False

    if ss.current_page == "demo_playbooks":
        display_demo_playbook()

    elif ss.current_page == "playbook_builder":
        display_playbook_builder()

    if ss.rerun_necessary:
        ss.rerun_necessary = False
        st.rerun()
