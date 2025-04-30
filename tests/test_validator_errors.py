from typing import Union

import pytest

from openapi_tester import SchemaTester
from openapi_tester.exceptions import CaseError, DocumentationError
from openapi_tester.schema_tester import OpenAPITestConfig
from openapi_tester.validators import (
    validate_enum,
    validate_format,
    validate_max_items,
    validate_max_length,
    validate_max_properties,
    validate_maximum,
    validate_min_items,
    validate_min_length,
    validate_min_properties,
    validate_minimum,
    validate_multiple_of,
    validate_pattern,
    validate_type,
    validate_unique_items,
)

tester = SchemaTester()


def test_case_error_message():
    error = CaseError(key="test-key", case="camelCase", expected="testKey")
    assert (
        error.args[0].strip()
        == "The response key `test-key` is not properly camelCase. Expected value: testKey"
    )


def test_validate_min_properties_error():
    message = validate_min_properties({"minProperties": 2}, {})
    assert (
        message
        == "The number of properties in {} is fewer than the specified minimum number of properties of 2"
    )


def test_validate_max_properties_error():
    message = validate_max_properties({"maxProperties": 1}, {"one": 1, "two": 2})
    assert (
        message
        == "The number of properties in {'one': 1, 'two': 2} exceeds the specified maximum number of properties"
        " of 1"
    )


def test_validate_max_items_error():
    message = validate_max_items({"maxItems": 1}, [1, 2])
    assert (
        message
        == "The length of the array [1, 2] exceeds the specified maximum length of 1"
    )


def test_validate_min_items_error():
    message = validate_min_items({"minItems": 1}, [])
    assert (
        message
        == "The length of the array [] is shorter than the specified minimum length of 1"
    )


def test_validate_max_length_error():
    message = validate_max_length({"maxLength": 1}, "test")
    assert message == 'The length of "test" exceeds the specified maximum length of 1'


def test_validate_min_length_error():
    message = validate_min_length({"minLength": 5}, "test")
    assert (
        message
        == 'The length of "test" is shorter than the specified minimum length of 5'
    )


def test_validate_unique_items_error():
    message = validate_unique_items({"uniqueItems": True}, [1, 2, 1])
    assert message == "The array [1, 2, 1] must contain unique items only"


def test_validate_minimum_error():
    message = validate_minimum({"minimum": 2}, 0)
    assert message == "The value 0 is lower than the specified minimum of 2"


def test_validate_exclusive_minimum_error():
    message = validate_minimum({"minimum": 2, "exclusiveMinimum": True}, 2)
    assert message == "The value 2 is lower than the specified minimum of 3"

    message = validate_minimum({"minimum": 2, "exclusiveMinimum": False}, 2)
    assert message is None


def test_validate_maximum_error():
    message = validate_maximum({"maximum": 2}, 3)
    assert message == "The value 3 exceeds the maximum allowed value of 2"


def test_validate_exclusive_maximum_error():
    message = validate_maximum({"maximum": 2, "exclusiveMaximum": True}, 2)
    assert message == "The value 2 exceeds the maximum allowed value of 1"

    message = validate_maximum({"maximum": 2, "exclusiveMaximum": False}, 2)
    assert message is None


def test_validate_multiple_of_error():
    message = validate_multiple_of({"multipleOf": 2}, 3)
    assert message == "The value 3 should be a multiple of 2"


def test_validate_pattern_error():
    message = validate_pattern({"pattern": "^[a-z]$"}, "3")
    assert message == 'The string "3" does not match the specified pattern: ^[a-z]$'


# Formatted errors


def test_validate_enum_error():
    message = validate_enum({"enum": ["Cat"]}, "Turtle")
    assert message == "Expected: a member of the enum ['Cat']\n\nReceived: \"Turtle\""


@pytest.mark.parametrize(
    "schema, data",
    [
        ({"format": "byte"}, "not byte"),
        ({"format": "base64"}, "not byte"),
        ({"format": "date"}, "not date"),
        ({"format": "date-time"}, "not date-time"),
        ({"format": "double"}, "not double"),
        ({"format": "email"}, "not email"),
        ({"format": "float", "type": "string"}, "not float"),
        ({"format": "number", "type": "string"}, "not number"),
        ({"format": "float"}, "not float"),
        ({"format": "ipv4"}, "not ipv4"),
        ({"format": "ipv6"}, "not ipv6"),
        ({"format": "time"}, "not time"),
        ({"format": "uri"}, "not uri"),
        ({"format": "url"}, "not url"),
    ],
)
def test_validate_format_error(schema: dict, data: str):
    message = validate_format(schema, data)
    schema_type = schema["type"] if "type" in schema else "object"
    assert (
        message
        == f'''Expected: a "{schema['format']}" formatted "{schema_type}" value\n\nReceived: "{data}"'''
    )


@pytest.mark.parametrize(
    "schema, data",
    [
        ({"format": "double", "type": "string"}, "3.12"),
        ({"format": "integer", "type": "string"}, "312"),
        ({"format": "float", "type": "string"}, "3.12"),
        ({"format": "number", "type": "string"}, "3.12"),
    ],
)
def test_format_validation_passes_for_string_type_with_numeric_format(
    schema: dict, data: str
):
    message = validate_format(schema, data)
    assert message is None


@pytest.mark.parametrize(
    "schema, data, article",
    [
        ({"type": "string"}, 1, "a"),
        ({"type": "file"}, 1, "a"),
        ({"type": "boolean"}, 1, "a"),
        ({"type": "integer"}, True, "an"),
        ({"type": "number"}, "string", "a"),
        ({"type": "object"}, "string", "an"),
        ({"type": "array"}, "string", "an"),
    ],
)
def test_validate_type_error(schema: dict, data: Union[str, int, bool], article: str):
    # string
    message = validate_type(schema, data)
    data = f'"{data}"' if isinstance(data, str) else data
    assert (
        message
        == f"Expected: {article} \"{schema['type']}\" type value\n\nReceived: {data}"
    )


def test_null_error():
    expected_error_message = (
        "A property received a null value in the response data, but is a non-nullable object in the schema definition"
        "\n\nReference:"
        "\n\nPOST /endpoint > response > nonNullableObject"
        '\n\nSchema description:\n  {\n    "type": "object"\n}'
        "\n\nHint: Return a valid type, or document the value as nullable"
    )
    tester = SchemaTester()
    with pytest.raises(DocumentationError, match=expected_error_message):
        tester.test_schema_section(
            {"type": "object"},
            None,
            OpenAPITestConfig(
                reference="POST /endpoint > response > nonNullableObject"
            ),
        )


def test_any_of_error():
    expected_error_message = (
        "Expected data to match one or more of the documented anyOf schema types, but found no matches\n\n"
        "Reference: init.anyOf"
    )
    tester = SchemaTester()
    with pytest.raises(DocumentationError, match=expected_error_message):
        tester.test_schema_section(
            {"anyOf": []}, {}, OpenAPITestConfig(reference="init")
        )


def test_one_of_error():
    expected_error_message = "Expected data to match one and only one of the oneOf schema types; found 0 matches\n\nReference: init.oneOf"
    tester = SchemaTester()
    with pytest.raises(DocumentationError, match=expected_error_message):
        tester.test_schema_section(
            {"oneOf": []}, {}, OpenAPITestConfig(reference="init")
        )


@pytest.mark.parametrize(
    "input_value",
    [
        "abcd",
        7,
        "1234",
        "abc",
    ],
)
def test_string_integer_pattern_multiple_of_invalid(input_value):
    """Test invalid cases for string and integer type with pattern and multiple of restrictions."""
    schema = {"type": ["string", "integer"], "pattern": "^[A-Z]{1,3}$", "multipleOf": 5}
    with pytest.raises(DocumentationError):
        tester.test_schema_section(schema, input_value)


@pytest.mark.parametrize(
    "input_value",
    [
        "abcd",
        -1,
        11,
        True,
    ],
)
def test_string_number_multiple_restrictions_invalid(input_value):
    """Test invalid cases for string and number type with multiple restrictions."""
    schema = {"type": ["string", "number"], "maxLength": 3, "minimum": 0, "maximum": 10}
    with pytest.raises(DocumentationError):
        tester.test_schema_section(schema, input_value)


@pytest.mark.parametrize(
    "input_value",
    [
        "test1",
        1,
        0,
    ],
)
def test_string_integer_length_minimum_restrictions_invalid(input_value):
    """Test invalid cases for string and integer type with length and minimum restrictions."""
    schema = {"type": ["string", "integer"], "maxLength": 4, "minimum": 2}
    with pytest.raises(DocumentationError):
        tester.test_schema_section(schema, input_value)
