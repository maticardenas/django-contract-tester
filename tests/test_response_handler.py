from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from openapi_tester.response_handler import (
    DjangoNinjaResponseHandler,
    ResponseHandler,
)


@pytest.fixture
def normalize():
    return ResponseHandler._normalize_query_params


@pytest.fixture
def build_ninja_handler():
    def _build(path: str) -> DjangoNinjaResponseHandler:
        return DjangoNinjaResponseHandler(
            "GET",
            path,
            None,
            response=MagicMock(),
        )

    return _build


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"page": "1"}, {"page": 1}),
        ({"count": "10", "price": "9.5"}, {"count": 10, "price": 9.5}),
        ({"temperature": "-3.14"}, {"temperature": -3.14}),
        ({"amount": "2.0"}, {"amount": 2}),
    ],
)
def test_normalize_query_params_casts_numeric_strings(normalize, raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"active": "true"}, {"active": True}),
        ({"active": "false"}, {"active": False}),
        ({"value": "null"}, {"value": None}),
        ({"name": "doggie"}, {"name": "doggie"}),
    ],
)
def test_normalize_query_params_handles_special_and_plain_strings(
    normalize, raw, expected
):
    assert normalize(raw) == expected


def test_django_ninja_handler_parses_and_normalizes_query_string(build_ninja_handler):
    handler = build_ninja_handler("/api/pets?page=1&active=true&name=doggie")

    assert handler.request.query_params == {
        "page": 1,
        "active": True,
        "name": "doggie",
    }


def test_django_ninja_handler_returns_empty_query_params_when_missing(
    build_ninja_handler,
):
    handler = build_ninja_handler("/api/pets")

    assert handler.request.query_params == {}
