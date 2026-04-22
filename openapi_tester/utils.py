"""
Utils Module - this file contains utility functions used in multiple places.
"""

from __future__ import annotations

from copy import deepcopy
from itertools import chain, combinations
from typing import TYPE_CHECKING

import orjson

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from typing import Any


def merge_objects(dictionaries: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """
    Deeply merge objects.
    """
    output: dict[str, Any] = {}
    for dictionary in dictionaries:
        for key, value in dictionary.items():
            if key not in output:
                output[key] = value
                continue
            current_value = output[key]
            if isinstance(current_value, list) and isinstance(value, list):
                output[key] = list(chain(output[key], value))
                continue
            if isinstance(current_value, dict) and isinstance(value, dict):
                output[key] = merge_objects([current_value, value])
                continue
    return output


def normalize_schema_section(schema_section: dict[str, Any]) -> dict[str, Any]:
    """
    Remove allOf and handle edge uses of oneOf.
    """
    output: dict[str, Any] = deepcopy(schema_section)
    if output.get("allOf"):
        all_of = output.pop("allOf")
        output = {**output, **merge_objects(all_of)}
    if output.get("oneOf") and all(item.get("enum") for item in output["oneOf"]):
        # handle the way drf-spectacular is doing enums
        one_of = output.pop("oneOf")
        output = {**output, **merge_objects(one_of)}
    for key, value in output.items():
        if isinstance(value, dict):
            output[key] = normalize_schema_section(value)
        elif isinstance(value, list):
            output[key] = [
                normalize_schema_section(entry) if isinstance(entry, dict) else entry
                for entry in value
            ]
    return output


def serialize_schema_section_data(data: dict[str, Any]) -> str:
    return orjson.dumps(data, option=orjson.OPT_INDENT_2, default=str).decode("utf-8")


def lazy_combinations(options_list: Sequence[dict[str, Any]]) -> Iterator[dict]:
    """
    Lazily evaluate possible combinations.
    """
    for i in range(2, len(options_list) + 1):
        for combination in combinations(options_list, i):
            yield merge_objects(combination)


def serialize_json(func):
    def wrapper(*args, content_type="application/json", **kwargs):
        data = kwargs.get("data")
        if data and content_type == "application/json":
            try:
                kwargs["data"] = orjson.dumps(data)
            except (TypeError, OverflowError):
                kwargs["data"] = data
        return func(*args, **kwargs)

    return wrapper


def get_required_keys(
    schema_section: dict,
    http_message: str,
    write_only_props: list[str],
    read_only_props: list[str],
) -> list[str]:
    if http_message == "request":
        return [
            key
            for key in schema_section.get("required", [])
            if key not in read_only_props
        ]
    if http_message == "response":
        return [
            key
            for key in schema_section.get("required", [])
            if key not in write_only_props
        ]
    return []


def query_params_to_object(query_params: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Convert the query parameters of a request to an object schema,
    in order to be able to be validated.
    """
    properties = {}
    required = []

    for param in query_params:
        param_name = param["name"]
        properties[param_name] = param.get("schema", {})
        if param.get("required", False):
            required.append(param_name)

    if properties:
        query_params_object = {
            "type": "object",
            "properties": properties,
        }

        if len(required) > 0:
            query_params_object["required"] = required

        return query_params_object

    return {}


def should_validate_query_param(param_schema_section: dict, request_value: Any) -> bool:
    """
    Checks if query parameter should be validated.
    If the query parameter is a raw string (without any format or constraints) it should not be validated.
    If the query parameter is a string and has a format or constraints, it should be validated if the request value (after normalization) is a string.
    """

    if param_schema_section.get("type") == "string":
        if len(param_schema_section) == 1:
            return False
        return isinstance(request_value, str)

    return True


def _coerce_scalar(schema_type: str | None, raw: str) -> Any:
    """
    Best-effort coercion of a raw string to the Python type implied by an
    OpenAPI scalar schema type. Falls back to the raw string on failure or
    when the target type is unknown.
    """
    if schema_type == "integer":
        try:
            return int(raw)
        except ValueError:
            return raw
    if schema_type == "number":
        try:
            return float(raw)
        except ValueError:
            return raw
    if schema_type == "boolean":
        lowered = raw.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return raw
    return raw


def normalize_query_param_value(param_schema: dict, value: Any) -> Any:
    """
    Normalize query parameter values based on their schema type.

    Specifically handles the case where an array-type parameter comes as a
    delimited string (e.g., "a,b,c" or "a|b|c"). When the schema declares an
    ``items.type`` (integer / number / boolean), each parsed item is coerced
    to the corresponding Python type so the downstream validator receives
    values of the expected type.

    Args:
        param_schema: The OpenAPI schema for the parameter
        value: The actual value from the request

    Returns:
        Normalized value (converted to array if needed)
    """
    schema_type = param_schema.get("type")

    if schema_type == "array" and not isinstance(value, list):
        items_type = param_schema.get("items", {}).get("type")

        if isinstance(value, str):
            for delimiter in [",", "|", ";"]:
                if delimiter in value:
                    items = [
                        item.strip() for item in value.split(delimiter) if item.strip()
                    ]
                    return [_coerce_scalar(items_type, item) for item in items]

            if not value:
                return []
            return [_coerce_scalar(items_type, value)]

        if value is None:
            return []
        return [value]

    return value
