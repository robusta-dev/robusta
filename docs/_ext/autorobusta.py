import inspect
import pydoc
import textwrap
import typing
from pathlib import Path
from typing import List, Type

import pydantic.fields
import sphinx.addnodes
import yaml
from PIL import Image
from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from pydantic import BaseModel
from pydantic.fields import ModelField
from sphinx.application import Sphinx
from sphinx.ext.autodoc.directive import DummyOptionSpec
from sphinx.util import nested_parse_with_titles
from sphinx.util.docutils import SphinxDirective

from robusta.api import Action
from robusta.core.playbooks.generation import ExamplesGenerator, get_possible_types

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
        return self.__document_model(
            obj, "show-code" in self.options, "show-optionality" in self.options
        )

    @classmethod
    def __document_model(
        cls, model: Type[BaseModel], show_code: bool, show_optionality: bool
    ):
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
    def __document_fields(
        cls, fields: List[ModelField], show_code: bool, show_optionality: bool
    ) -> List[Node]:
        node = nodes.section()

        for field in fields:
            desc = sphinx.addnodes.desc()
            node.append(desc)
            desc.extend(cls.__document_field_signature(field, show_optionality))
            desc.extend(
                cls.__document_field_content(field, show_code, show_optionality)
            )

        return node.children

    @classmethod
    def __document_field_signature(
        cls, field: ModelField, show_optionality: bool
    ) -> List[Node]:
        sig = sphinx.addnodes.desc_signature()

        if show_optionality:
            if field.required:
                sig.append(nodes.strong(text="required: "))
            else:
                sig.append(nodes.emphasis(text="optional: "))

        sig.append(sphinx.addnodes.desc_name(text=field.name))
        sig.append(sphinx.addnodes.desc_sig_space())
        sig.append(
            sphinx.addnodes.desc_sig_element(
                text=f"({cls.__get_readable_field_type(field)})"
            )
        )

        if field.default:
            sig.append(sphinx.addnodes.desc_sig_space())
            sig.append(sphinx.addnodes.desc_sig_element(text=f"= {field.default}"))
        return [sig]

    @classmethod
    def __document_field_content(
        cls, field: ModelField, show_code: bool, show_optionality: bool
    ) -> List[Node]:
        content = sphinx.addnodes.desc_content()

        if field.field_info.description:
            content.append(nodes.paragraph(text=field.field_info.description))

        if show_code:
            content.extend(cls.__document_field_example(field))

        if typing.get_origin(field.type_) == typing.Union:
            possible_types = get_possible_types(field.type_)
            paragraph = nodes.paragraph(text=f"each entry is one of the following:")
            content.append(paragraph)
            for t in possible_types:
                if isinstance(None, t):
                    continue
                content.extend(cls.__document_model(t, show_code, show_optionality))

        elif issubclass(field.type_, BaseModel):
            paragraph = nodes.paragraph(text=f"each entry contains:")
            content.append(paragraph)
            # when documenting an inner model, we always show "required"/"optional" inline
            content.extend(
                cls.__document_model(field.type_, show_code, show_optionality)
            )

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


class RobustaActionDirective(SphinxDirective):

    option_spec = DummyOptionSpec()
    has_content = True
    required_arguments = 1
    final_argument_whitespace = True

    def run(self) -> List[Node]:
        objpath = self.arguments[0]
        obj = pydoc.locate(objpath)
        if obj is None:
            raise Exception(f"Cannot document None: {objpath}")
        action_definition = Action(obj)
        return self.__generate_rst(action_definition)

    def __generate_rst(self, action_definition: Action):
        node = nodes.section()
        node.document = self.state.document

        example_yaml = generator.generate_example_config(action_definition.func)
        params_cls = action_definition.params_type
        params_cls_path = ""
        if params_cls is not None:
            params_cls_path = f"{params_cls.__module__}.{params_cls.__name__}"

        code = self.__get_source_code(action_definition.func)
        description = self.__get_description(action_definition)
        # possible_triggers = get_possible_triggers(action_definition.event_type)
        possible_triggers = [
            generator.get_highest_possible_trigger(action_definition.event_type)
        ]

        indented_code = "\n".join(" " * 32 + l for l in code)
        indented_description = "\n".join(" " * 28 + l for l in description.split("\n"))
        indented_example = "\n".join(" " * 32 + l for l in example_yaml.split("\n"))
        indented_triggers = "\n".join(" " * 28 + " * " + l for l in possible_triggers)

        content = textwrap.dedent(
            f"""\
            {action_definition.action_name}
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            
            .. admonition:: Playbook Action
            
                .. tab-set::
            
                    .. tab-item:: Description\n\n{indented_description}\n\n
            
                    .. tab-item:: Parameters
                        
                        .. pydantic-model:: {params_cls_path}
                       
                    .. tab-item:: Supported Triggers\n\n{indented_triggers}
                    
                    .. tab-item:: Example YAML
            
                        .. code-block:: yaml \n\n{indented_example}
                        
                    .. tab-item:: Code
            
                        .. code-block:: python \n\n{indented_code}
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
        MAX_WIDTH = 500.0
        MAX_HEIGHT = 250.0
        if width > MAX_WIDTH:
            resize_ratio = MAX_WIDTH / width
            width *= resize_ratio
            height *= resize_ratio
        if height > MAX_HEIGHT:
            resize_ratio = MAX_HEIGHT / height
            width *= resize_ratio
            height *= resize_ratio
        return width, height

    def __get_description(self, action_definition: Action):
        description = ""

        docs = inspect.getdoc(action_definition.func)
        if docs:
            description += docs
        if self.content:
            description += "\n".join(l for l in self.content)
        if not description:
            description += "*No description*"

        image_dir = Path(inspect.getfile(action_definition.func)).parent / Path(
            "images"
        )
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
