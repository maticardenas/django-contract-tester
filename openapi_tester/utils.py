"""
Utils Module - this file contains utility functions used in multiple places.
"""

from __future__ import annotations

from copy import deepcopy
from itertools import chain, combinations
from typing import TYPE_CHECKING

import orjson

if TYPE_CHECKING:
    from typing import Any, Iterator, Sequence


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
