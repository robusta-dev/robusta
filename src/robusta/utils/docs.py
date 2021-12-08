from typing import List
from xml.etree import ElementTree

from docutils.core import publish_doctree


class DocstringField:
    """
    Represents a docstring field like ":var xyz: abc"
    For the above example, field_type is "var", field_target is "xyz", and field_value is "abc"
    """

    def __init__(self, name: str, body: str):
        field_type, field_target = name.split()
        self.field_type = field_type
        self.field_target = field_target
        self.field_value = body


class Docstring:
    def __init__(self, docstring: str):
        """
        Parse docutils/sphinx-style docs from a docstring.

        For example, given the following docstring:

            '''
            This is the description

            :var x: abc
            :example x: efg
            '''

        We parse:
        - description="This is the description"
        - fields:
            - var field
            - example field

        :param docstring: the docstring to parse
        """
        dom = publish_doctree(docstring).asdom()
        tree = ElementTree.fromstring(dom.toxml())
        self.fields = []

        for field in tree.iter(tag="field"):
            name = next(field.iter(tag="field_name"))
            body = next(field.iter(tag="field_body"))
            self.fields.append(DocstringField(name.text, "".join(body.itertext())))

        # we select all the docutils paragraphs which are under a root <block_quote> element
        # this is essentially all the lines in the docstring which don't contain :field:
        self.description = "\n\n".join(
            ["".join(p.itertext()) for p in tree.findall("./block_quote/paragraph")]
        )
