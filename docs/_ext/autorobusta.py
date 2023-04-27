import inspect
import json
import pydoc
import textwrap
import typing
from pathlib import Path
from typing import List, Optional, Type

import pydantic.fields
import sphinx.addnodes
import yaml
from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from PIL import Image
from pydantic import BaseModel
from pydantic.fields import ModelField
from sphinx.application import Sphinx
from sphinx.util import nested_parse_with_titles
from sphinx.util.docutils import SphinxDirective

from robusta.api import Action
from robusta.core.playbooks.generation import ExamplesGenerator, get_possible_types
from robusta.integrations.kubernetes.autogenerated.triggers import K8sTriggers

# creating this is slightly expensive so we create one global instance and re-use it
generator = ExamplesGenerator()


class PydanticModelDirective(SphinxDirective):
    """
    Document the fields of any pydantic model.

    Example:

        .. pydantic-model:: foo.MyModel
            :show-code:
            :show-optionality:

    Supports two optional flags:

        :show-code: will show yaml code under each setting with a sample configuration

        :show-optionality: will show for each setting if it is optional/required.
                           regardless of the setting, this is always done for inner fields inside another field.
    """

    option_spec = {"show-code": directives.flag, "show-optionality": directives.flag}
    has_content = False
    required_arguments = 1
    final_argument_whitespace = True

    def run(self) -> List[Node]:
        objpath = self.arguments[0]
        obj = pydoc.locate(objpath)
        if obj is None:
            raise Exception(f"Cannot document None: {objpath}")
        if not issubclass(obj, BaseModel):
            raise Exception(f"not a pydantic model: {obj}")
        return self.__document_model(obj, "show-code" in self.options, "show-optionality" in self.options)

    @classmethod
    def __document_model(cls, model: Type[BaseModel], show_code: bool, show_optionality: bool):
        node = nodes.section()

        all_fields = model.__fields__.values()
        required_fields = list(filter(lambda f: f.required, all_fields))
        optional_fields = list(filter(lambda f: not f.required, all_fields))

        if not show_optionality and len(required_fields) > 0:
            node.append(nodes.strong(text="required:"))
        node.extend(cls.__document_fields(required_fields, show_code, show_optionality))

        if not show_optionality and len(optional_fields) > 0:
            node.append(nodes.strong(text="optional:"))
        node.extend(cls.__document_fields(optional_fields, show_code, show_optionality))

        return node.children

    @classmethod
    def __document_fields(cls, fields: List[ModelField], show_code: bool, show_optionality: bool) -> List[Node]:
        node = nodes.section()

        for field in fields:
            desc = sphinx.addnodes.desc()
            node.append(desc)
            desc["domain"] = "robusta"
            desc["objtype"] = "model"
            desc.extend(cls.__document_field_signature(field, show_optionality))
            desc.extend(cls.__document_field_content(field, show_code, show_optionality))

        return node.children

    @classmethod
    def __document_field_signature(cls, field: ModelField, show_optionality: bool) -> List[Node]:
        sig = sphinx.addnodes.desc_signature()

        if show_optionality:
            if field.required:
                sig.append(nodes.strong(text="required: "))
            else:
                sig.append(nodes.emphasis(text="optional: "))

        sig.append(sphinx.addnodes.desc_name(text=field.name))
        sig.append(sphinx.addnodes.desc_sig_space())
        sig.append(sphinx.addnodes.desc_sig_element(text=f"({cls.__get_readable_field_type(field)})"))

        if field.default:
            sig.append(sphinx.addnodes.desc_sig_space())
            sig.append(sphinx.addnodes.desc_sig_element(text=f"= {field.default}"))
        return [sig]

    @classmethod
    def __document_field_content(cls, field: ModelField, show_code: bool, show_optionality: bool) -> List[Node]:
        content = sphinx.addnodes.desc_content()

        if field.field_info.description:
            content.append(nodes.paragraph(text=field.field_info.description))

        if show_code:
            content.extend(cls.__document_field_example(field))

        if typing.get_origin(field.type_) == typing.Union:
            possible_types = get_possible_types(field.type_)
            paragraph = nodes.paragraph(text="each entry is one of the following:")
            content.append(paragraph)
            for t in possible_types:
                if isinstance(None, t):
                    continue
                content.extend(cls.__document_model(t, show_code, show_optionality))

        elif issubclass(field.type_, BaseModel):
            paragraph = nodes.paragraph(text="each entry contains:")
            content.append(paragraph)
            # when documenting an inner model, we always show "required"/"optional" inline
            content.extend(cls.__document_model(field.type_, show_code, show_optionality))

        return [content]

    @classmethod
    def __document_field_example(cls, field: ModelField):
        if "example" in field.field_info.extra:
            value = yaml.dump({field.name: field.field_info.extra["example"]})
        elif field.default:
            value = "# default\n" + yaml.dump({field.name: field.default})
        else:
            value = yaml.dump({field.name: cls.__get_sample_value(field)})
        return [nodes.literal_block(text=value)]

    @staticmethod
    def __get_readable_field_type(field: pydantic.fields.ModelField):
        if typing.get_origin(field.type_) == typing.Union:
            inner_type_name = "complex"
        else:
            inner_type_name = field.type_.__name__.lower()
            if inner_type_name == "secretstr":
                inner_type_name = "str"
            if issubclass(field.type_, BaseModel):
                inner_type_name = "complex"

        if field.shape == pydantic.fields.SHAPE_SINGLETON:
            return inner_type_name
        elif field.shape == pydantic.fields.SHAPE_LIST:
            return f"{inner_type_name} list"
        elif field.shape == pydantic.fields.SHAPE_DICT:
            return f"{inner_type_name} dict"
        return repr(field)

    @staticmethod
    def __get_sample_value(field: pydantic.fields.ModelField):
        if field.shape == pydantic.fields.SHAPE_LIST:
            return ["<value1>", "<value2>"]
        elif field.shape == pydantic.fields.SHAPE_DICT:
            return {"key1": "value1", "key2": "value2"}
        return "<value>"


def to_name(action_name: str) -> str:
    parts = action_name.split("_")
    parts[0] = parts[0].capitalize()
    return " ".join(parts)


class RobustaActionDirective(SphinxDirective):
    """
     Document a Robusta playbook action

     Example:

         .. robusta-action:: playbooks.robusta_playbooks.some_module.some_playbook

     Optionally, a second parameter can be given, recommending a relevant trigger to show in the documentation:

         .. robusta-action:: playbooks.robusta_playbooks.some_module.some_playbook on_deployment_update

    Finally, there are optional flags:

         :reference-label: Change the Sphinx reference (anchor) that is generated here - see https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#role-ref
                           This is useful when a playbook action is documented in multiple locations and you want to avoid duplicate labels

         :manual-trigger-only: For actions that are expected to be used as manual triggers only. Hides the example YAML config.

         :trigger-params: Extra trigger parameters that should be shown in autogenerated YAML. For example `{ "alert_name": "Foo" }`

    """

    option_spec = {
        "reference-label": str,
        "manual-trigger-only": directives.flag,
        "trigger-params": str,
    }
    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self) -> List[Node]:
        objpath = self.arguments[0]
        if len(self.arguments) < 2:
            recommended_trigger = None
        else:
            recommended_trigger = self.arguments[1]
        obj = pydoc.locate(objpath)
        if obj is None:
            raise Exception(f"Cannot document None: {objpath}")
        action_definition = Action(obj)
        return self.__generate_rst(action_definition, recommended_trigger)

    def __generate_rst(self, action_definition: Action, recommended_trigger: Optional[str]):
        node = nodes.section()
        node.document = self.state.document

        trigger_params = json.loads(self.options.get("trigger-params", "{}"))

        example_yaml = generator.generate_example_config(action_definition.func, recommended_trigger, trigger_params)
        params_cls = action_definition.params_type
        params_cls_path = ""
        if params_cls is not None:
            params_cls_path = f"{params_cls.__module__}.{params_cls.__name__}"

        # code = self.__get_source_code(action_definition.func)
        description = self.__get_description(action_definition)
        triggers = self.__get_triggers(generator.get_supported_triggers(action_definition), recommended_trigger)
        cli_trigger = generator.get_manual_trigger_cmd(action_definition)

        # indented_code = "\n".join(" " * 32 + line for line in code)
        indented_description = "\n".join(" " * 28 + line for line in description.split("\n"))
        indented_example = "\n".join(" " * 32 + line for line in example_yaml.split("\n"))
        indented_triggers = "\n".join(" " * 24 + line for line in triggers)

        reference_label = self.options.get("reference-label", action_definition.action_name)
        manual_trigger_only = "manual-trigger-only" in self.options

        indented_cli_trigger_example = ""
        if cli_trigger:
            indented_cli_trigger_example = f"""\

                        This action can be :ref:`manually triggered <Manual Triggers>` using the Robusta CLI:

                        .. code-block:: bash \n\n{" " * 32 + cli_trigger}

            """

        if manual_trigger_only:
            example_config = """\

                        This action is typically used via manual triggers and **not** predefined YAML triggers. An example config is not shown because it is not relevant for this action.
                        """
        else:
            example_config = f"""\

                        Add this to your :ref:`Robusta configuration (Helm values.yaml) <Defining playbooks>`:

                        .. code-block:: yaml \n\n{indented_example}

                        The above is an example. Try customizing the trigger and parameters.
                        """

        content = textwrap.dedent(
            f"""\
            .. _{reference_label}:

            {to_name(action_definition.action_name)}
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

            .. admonition:: Playbook Action: {action_definition.action_name}

                .. tab-set::

                    .. tab-item:: Description\n\n{indented_description}\n\n

                    .. tab-item:: Example Config\n\n{example_config}

                    .. tab-item:: Parameters

                        {".. pydantic-model:: " + params_cls_path if params_cls_path else "**No action parameters**"}

                    .. tab-item:: Supported Triggers\n\n{indented_triggers}\n
                        {indented_cli_trigger_example}
            """
        )
        nested_parse_with_titles(self.state, StringList(content.split("\n")), node)
        return node.children

    @staticmethod
    def __get_source_code(obj) -> List[str]:
        lines = inspect.getsourcelines(obj)[0]
        return [line.replace("\n", "") for line in lines]

    @staticmethod
    def __get_image_size(width, height):
        """
        Returns new image sizes such that the image fits inside a 600x300 bounding box.
        If the image already fits inside that box then the original size is returned.
        """
        MAX_WIDTH = 1200.0
        MAX_HEIGHT = 400.0
        if width > MAX_WIDTH:
            resize_ratio = MAX_WIDTH / width
            width *= resize_ratio
            height *= resize_ratio
        if height > MAX_HEIGHT:
            resize_ratio = MAX_HEIGHT / height
            width *= resize_ratio
            height *= resize_ratio
        return width, height

    @staticmethod
    def __get_ref_for_trigger(trigger_name):
        if trigger_name == ExamplesGenerator.ANY_TRIGGER_MARKER:
            return "any_trigger"
        if trigger_name in K8sTriggers.__fields__:
            return "kubernetes_triggers"
        else:
            return trigger_name

    @classmethod
    def __get_triggers(cls, supported_triggers: List[str], recommended_trigger: Optional[str]):
        if recommended_trigger is not None and recommended_trigger not in supported_triggers:
            supported_triggers.insert(0, recommended_trigger)

        rst = [f"* :ref:`{t} <{cls.__get_ref_for_trigger(t)}>`" for t in supported_triggers]
        return rst

    def __get_description(self, action_definition: Action):
        description = ""

        docs = inspect.getdoc(action_definition.func)
        if docs:
            description += docs + "\n\n"
        if self.content:
            description += "\n".join(line for line in self.content)
        if not description:
            description += "*No description*"

        image_dir = Path(inspect.getfile(action_definition.func)).parent / Path("images")
        image_paths = list(image_dir.glob(f"{action_definition.action_name}*"))
        for path in image_paths:
            # sphinx handles image paths in a weird way
            # we want the path to look like an absolute paths, but really be relative to the docs/ directory
            root_docs_dir = Path(__file__).parent.parent.parent
            relative_path = "/../" + str(path.relative_to(root_docs_dir))
            image = Image.open(path.resolve())
            width, height = self.__get_image_size(*image.size)

            description += textwrap.dedent(
                f"""

                .. thumbnail:: {relative_path}
                    :align: center
                    :width: {width}
                    :height: {height}

                """
            )

        return description


def setup(app: Sphinx) -> None:
    app.setup_extension("sphinx.ext.autodoc")  # Require autodoc extension
    app.add_directive("pydantic-model", PydanticModelDirective)
    app.add_directive("robusta-action", RobustaActionDirective)
