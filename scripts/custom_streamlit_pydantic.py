# based on code in streamlit_pydantic.pydantic_form but with extra modifications for our use case
import streamlit as st
from typing import Type, Optional, TypeVar, Callable
from pydantic import BaseModel, ValidationError, parse_obj_as
from streamlit_pydantic import pydantic_input
from streamlit_pydantic.ui_renderer import GroupOptionalFieldsStrategy

# Define generic type to allow autocompletion for the model fields
T = TypeVar("T", bound=BaseModel)


def modified_pydantic_form(
    key: str,
    model: Type[T],
    submit_label: str = "Submit",
    clear_on_submit: bool = False,
    group_optional_fields: GroupOptionalFieldsStrategy = "no",  # type: ignore
    lowercase_labels: bool = False,
    ignore_empty_values: bool = False,
    title: str = None,
    on_submit: Callable = None
) -> Optional[T]:
    """Auto-generates a Streamlit form based on the given (Pydantic-based) input class.

    Args:
        key (str): A string that identifies the form. Each form must have its own key.
        model (Type[BaseModel]): The input model. Either a class or instance based on Pydantic `BaseModel` or Python `dataclass`.
        submit_label (str): A short label explaining to the user what this button is for. Defaults to “Submit”.
        clear_on_submit (bool): If True, all widgets inside the form will be reset to their default values after the user presses the Submit button. Defaults to False.
        group_optional_fields (str, optional): If `sidebar`, optional input elements will be rendered on the sidebar.
            If `expander`,  optional input elements will be rendered inside an expander element. Defaults to `no`.
        lowercase_labels (bool): If `True`, all input element labels will be lowercased. Defaults to `False`.
        ignore_empty_values (bool): If `True`, empty values for strings and numbers will not be stored in the session state. Defaults to `False`.

    Returns:
        Optional[BaseModel]: An instance of the given input class,
            if the submit button is used and the input data passes the Pydantic validation.
    """
    # TODO: replace with a visual container from streamlit_extras due to https://github.com/LukasMasuch/streamlit-pydantic/issues/39
    with st.form(key=key, clear_on_submit=clear_on_submit):
        if title is not None:
            st.header(title)

        input_state = pydantic_input(
            key,
            model,
            group_optional_fields=group_optional_fields,
            lowercase_labels=lowercase_labels,
            ignore_empty_values=ignore_empty_values,
        )
        submit_button = st.form_submit_button(label=submit_label)

        if submit_button:
            try:
                result = None
                # check if the model is an instance before parsing
                if isinstance(model, BaseModel):
                    result = parse_obj_as(model.__class__, input_state)
                else:
                    result = parse_obj_as(model, input_state)

                if on_submit is not None:
                    on_submit()
                    return result

            except ValidationError as ex:
                error_text = "**Whoops! There were some problems with your input:**"
                for error in ex.errors():
                    if "loc" in error and "msg" in error:
                        location = ".".join(error["loc"]).replace("__root__.", "")  # type: ignore
                        error_msg = f"**{location}:** " + error["msg"]
                        error_text += "\n\n" + error_msg
                    else:
                        # Fallback
                        error_text += "\n\n" + str(error)
                st.error(error_text)
                return None
    return None
