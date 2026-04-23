import pytest

from openapi_tester.utils import (
    get_required_keys,
    merge_objects,
    normalize_query_param_value,
    query_params_to_object,
    serialize_schema_section_data,
    should_validate_query_param,
)
from tests.utils import sort_object


def test_documentation_error_sort_data_type():
    assert sort_object([1, 3, 2]) == [1, 2, 3]  # list
    assert sort_object({"1", "3", "2"}) == {"1", "2", "3"}  # set
    assert sort_object({"1": "a", "3": "a", "2": "a"}) == {
        "1": "a",
        "2": "a",
        "3": "a",
    }  # dict

    # Test sort failure scenario - expect the method to succeed and default to no reordering
    assert sort_object(["1", {}, []]) == ["1", {}, []]


def test_merge_objects():
    object_1 = {
        "type": "object",
        "required": ["key1"],
        "properties": {"key1": {"type": "string"}},
    }
    object_2 = {
        "type": "object",
        "required": ["key2"],
        "properties": {"key2": {"type": "string"}},
    }
    test_schemas = [
        object_1,
        object_2,
    ]
    expected = {
        "type": "object",
        "required": ["key1", "key2"],
        "properties": {"key1": {"type": "string"}, "key2": {"type": "string"}},
    }
    assert sort_object(merge_objects(test_schemas)) == sort_object(expected)


def test_serialize_schema_section_data():
    data = {
        "type": "object",
        "required": ["key1", "key2"],
        "properties": {"key1": {"type": "string"}, "key2": {"type": "string"}},
    }
    serialized_data = serialize_schema_section_data(data=data)
    assert serialized_data == (
        "{\n  "
        '"type": "object",'
        '\n  "required": [\n    "key1",\n    "key2"\n  ],\n  '
        '"properties": {\n'
        '    "key1": {\n      "type": "string"\n    },\n'
        '    "key2": {\n      "type": "string"\n    }\n'
        "  }"
        "\n}"
    )


def test_get_required_keys():
    # given
    schema_section = {
        "type": "object",
        "required": ["key1", "key2"],
        "properties": {"key1": {"type": "string"}, "key2": {"type": "string"}},
    }
    read_only_props = []
    write_only_props = []
    http_message = "response"

    # when
    required_keys = get_required_keys(
        schema_section=schema_section,
        http_message=http_message,
        read_only_props=read_only_props,
        write_only_props=write_only_props,
    )

    # then
    assert required_keys == ["key1", "key2"]


def test_get_required_keys_request_with_read_only_field():
    # given
    schema_section = {
        "type": "object",
        "required": ["key1", "key2"],
        "properties": {"key1": {"type": "string"}, "key2": {"type": "string"}},
        "readOnly": ["key2"],
    }
    read_only_props = ["key2"]
    write_only_props = []

    http_message = "request"

    # when
    required_keys = get_required_keys(
        schema_section=schema_section,
        http_message=http_message,
        read_only_props=read_only_props,
        write_only_props=write_only_props,
    )

    # then
    assert required_keys == ["key1"]


def test_get_required_keys_response_with_write_only_field():
    # given
    schema_section = {
        "type": "object",
        "required": ["key1", "key2"],
        "properties": {"key1": {"type": "string"}, "key2": {"type": "string"}},
        "writeOnly": ["key2"],
    }
    write_only_props = ["key2"]
    read_only_props = []
    http_message = "response"

    # when
    required_keys = get_required_keys(
        schema_section=schema_section,
        http_message=http_message,
        write_only_props=write_only_props,
        read_only_props=read_only_props,
    )

    # then
    assert required_keys == ["key1"]


def test_query_params_to_object():
    query_params = [
        {
            "name": "name",
            "in": "query",
            "required": False,
            "schema": {"type": "string"},
        },
        {
            "name": "age",
            "in": "query",
            "required": False,
            "schema": {"type": "integer"},
        },
    ]

    converted_query_params = query_params_to_object(query_params)

    assert converted_query_params == {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
    }


def test_query_params_to_object_with_required_query_params():
    query_params = [
        {"name": "name", "in": "query", "required": True, "schema": {"type": "string"}},
        {
            "name": "age",
            "in": "query",
            "required": False,
            "schema": {"type": "integer"},
        },
    ]

    converted_query_params = query_params_to_object(query_params)

    assert converted_query_params == {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name"],
    }


def test_query_params_to_object_no_query_params():
    query_params = []

    converted_query_params = query_params_to_object(query_params)

    assert converted_query_params == {}


def test_should_validate_query_param():
    assert should_validate_query_param({"type": "string"}, "123") is False
    assert should_validate_query_param({"type": "string"}, 123) is False
    assert (
        should_validate_query_param(
            {"type": "string", "format": "email"}, "test@test.com"
        )
        is True
    )
    assert (
        should_validate_query_param({"type": "string", "format": "email"}, 123) is False
    )


def test_normalize_query_param_value():
    assert normalize_query_param_value({"type": "array"}, "1,2,3") == ["1", "2", "3"]
    assert normalize_query_param_value({"type": "array"}, "1|2|3") == ["1", "2", "3"]
    assert normalize_query_param_value({"type": "array"}, "1;2;3") == ["1", "2", "3"]


@pytest.mark.parametrize(
    ("items_type", "raw", "expected"),
    [
        ("integer", "1,2,3", [1, 2, 3]),
        ("number", "1.5|2.5|3", [1.5, 2.5, 3.0]),
        ("boolean", "true;false;true", [True, False, True]),
        ("integer", "5", [5]),
        ("string", "a,b,c", ["a", "b", "c"]),
    ],
)
def test_normalize_query_param_value_coerces_items_by_items_type(
    items_type, raw, expected
):
    param_schema = {"type": "array", "items": {"type": items_type}}

    assert normalize_query_param_value(param_schema, raw) == expected


@pytest.mark.parametrize(
    ("items_type", "raw", "expected"),
    [
        ("integer", "1,oops,3", [1, "oops", 3]),
        ("number", "1.5,nope", [1.5, "nope"]),
        ("boolean", "true,maybe", [True, "maybe"]),
    ],
)
def test_normalize_query_param_value_falls_back_on_invalid_items(
    items_type, raw, expected
):
    param_schema = {"type": "array", "items": {"type": items_type}}

    assert normalize_query_param_value(param_schema, raw) == expected


@pytest.mark.parametrize(
    ("items_type", "value", "expected"),
    [
        ("integer", 155, [155]),
        ("number", 3.14, [3.14]),
        ("boolean", True, [True]),
        ("boolean", False, [False]),
        ("integer", None, []),
    ],
)
def test_normalize_query_param_value_wraps_precoerced_scalars_as_single_item_array(
    items_type, value, expected
):
    param_schema = {"type": "array", "items": {"type": items_type}}

    assert normalize_query_param_value(param_schema, value) == expected


def test_normalize_query_param_value_leaves_lists_untouched():
    param_schema = {"type": "array", "items": {"type": "integer"}}

    assert normalize_query_param_value(param_schema, [1, 2, 3]) == [1, 2, 3]
