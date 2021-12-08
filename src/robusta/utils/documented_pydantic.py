import inspect
import json
import logging
from pydantic import BaseModel
from pydantic.fields import ModelField
from .docs import Docstring, DocstringField


class DocumentedModel(BaseModel):
    """
    Extends pydantic.BaseModel so that you can document models with docstrings and not using
        Field(..., description="foo")

    You write docs in the docstring and behind the scenes the actual Fields()  will be updated
    This way pydantic's introspection and schema-generation works like normal and includes those docs

    """

    # warning: __init_subclass__ only works on Python 3.6 and above
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        docs = inspect.getdoc(cls)
        if docs is not None:
            cls.__update_fields_from_docstring(docs)

    @classmethod
    def __update_fields_from_docstring(cls, docstring):
        """
        Updates pydantic fields according to the docstring so that:

        1. you can document individual fields with ":var fieldname: description" in the model's docstring
        2. you can provide examples for individual fields with ":example fieldname: value" in the model's docstring
        3. docs about individual fields (like :var: and :example:) are removed from the root docs
        """
        docs = Docstring(docstring)
        for doc_field in docs.fields:
            if doc_field.field_target not in cls.__fields__:
                logging.warning(
                    f"Docstring contains description of {doc_field.field_target} which is not a field on the model"
                )
                continue

            f: ModelField = cls.__fields__[doc_field.field_target]
            if doc_field.field_type == "example":
                f.field_info.extra["example"] = cls.__parse_example(
                    doc_field.field_value
                )
            if doc_field.field_type == "var":
                if f.field_info.description:
                    logging.warning(
                        f"Overriding existing field description '{f.field_info.description}' with '{doc_field.field_value}'"
                    )
                f.field_info.description = doc_field.field_value
        cls.__doc__ = docs.description

    @staticmethod
    def __parse_example(example: str):
        try:
            return json.loads(example)
        except json.JSONDecodeError:
            return example
