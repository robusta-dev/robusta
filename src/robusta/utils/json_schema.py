# Based on https://github.com/sphinx-contrib/openapi/blob/4f78db9c8ca2cefc4e4c1eeb46552a8d9d432855/sphinxcontrib/openapi/schema_utils.py
#
# Copyright (c) 2016, Igor Kalnitsky <igor@kalnitsky.org>.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from io import StringIO


_DEFAULT_EXAMPLES = {
    "string": "string",
    "integer": 1,
    "number": 1.0,
    "boolean": True,
    "array": [],
}


_DEFAULT_STRING_EXAMPLES = {
    "date": "2020-01-01",
    "date-time": "2020-01-01T01:01:01Z",
    "password": "********",
    "byte": "QG1pY2hhZWxncmFoYW1ldmFucw==",
    "ipv4": "127.0.0.1",
    "ipv6": "::1",
}


def example_from_schema(schema):
    """
    Generates an example request/response body from the provided schema.

    >>> schema = {
    ...     "type": "object",
    ...     "required": ["id", "name"],
    ...     "properties": {
    ...         "id": {
    ...             "type": "integer",
    ...             "format": "int64"
    ...         },
    ...         "name": {
    ...             "type": "string",
    ...             "example": "John Smith"
    ...         },
    ...         "tag": {
    ...             "type": "string"
    ...         }
    ...     }
    ... }
    >>> example = example_from_schema(schema)
    >>> assert example == {
    ...     "id": 1,
    ...     "name": "John Smith",
    ...     "tag": "string"
    ... }
    """

    if "example" in schema:
        return schema["example"]

    elif "default" in schema:
        return schema["default"]

    elif "oneOf" in schema:
        return example_from_schema(schema["oneOf"][0])

    elif "anyOf" in schema:
        return example_from_schema(schema["anyOf"][0])

    elif "allOf" in schema:
        # Combine schema examples
        example = {}
        for sub_schema in schema["allOf"]:
            example.update(example_from_schema(sub_schema))
        return example

    elif "enum" in schema:
        return schema["enum"][0]

    elif "type" not in schema:
        # Any type
        return _DEFAULT_EXAMPLES["integer"]

    elif schema["type"] == "object" or "properties" in schema:
        example = {}
        required = schema.get("required", [])
        for prop, prop_schema in schema.get("properties", {}).items():
            has_example = "example" in prop_schema
            # skip optional properties unless they have an explicit example
            if prop not in required and not has_example:
                continue
            example[prop] = example_from_schema(prop_schema)
        return example

    elif schema["type"] == "array":
        items = schema["items"]
        min_length = schema.get("minItems", 0)
        max_length = schema.get("maxItems", max(min_length, 2))
        assert min_length <= max_length
        # Try generate at least 2 example array items
        gen_length = min(2, max_length) if min_length <= 2 else min_length

        example_items = []
        if items == {}:
            # Any-type arrays
            example_items.extend(_DEFAULT_EXAMPLES.values())
        elif isinstance(items, dict) and "oneOf" in items:
            # Mixed-type arrays
            example_items.append(_DEFAULT_EXAMPLES[sorted(items["oneOf"])[0]])
        else:
            example_items.append(example_from_schema(items))

        # Generate array containing example_items and satisfying min_length and max_length
        return [example_items[i % len(example_items)] for i in range(gen_length)]

    elif schema["type"] == "string":
        example_string = _DEFAULT_STRING_EXAMPLES.get(
            schema.get("format", None), _DEFAULT_EXAMPLES["string"]
        )
        min_length = schema.get("minLength", 0)
        max_length = schema.get("maxLength", max(min_length, len(example_string)))
        gen_length = (
            min(len(example_string), max_length)
            if min_length <= len(example_string)
            else min_length
        )
        assert 0 <= min_length <= max_length
        if min_length <= len(example_string) <= max_length:
            return example_string
        else:
            example_builder = StringIO()
            for i in range(gen_length):
                example_builder.write(example_string[i % len(example_string)])
            example_builder.seek(0)
            return example_builder.read()

    elif schema["type"] in ("integer", "number"):
        example = _DEFAULT_EXAMPLES[schema["type"]]
        if "minimum" in schema and "maximum" in schema:
            # Take average
            example = schema["minimum"] + (schema["maximum"] - schema["minimum"]) / 2
        elif "minimum" in schema and example <= schema["minimum"]:
            example = schema["minimum"] + 1
        elif "maximum" in schema and example >= schema["maximum"]:
            example = schema["maximum"] - 1
        return float(example) if schema["type"] == "number" else int(example)

    else:
        return _DEFAULT_EXAMPLES[schema["type"]]
