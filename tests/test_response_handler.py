from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import pytest

from openapi_tester.response_handler import (
    DjangoNinjaResponseHandler,
    DRFResponseHandler,
    ResponseHandler,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"page": "1"}, {"page": 1}),
        ({"count": "10", "price": "9.5"}, {"count": 10, "price": 9.5}),
        ({"temperature": "-3.14"}, {"temperature": -3.14}),
        ({"amount": "2.0"}, {"amount": 2}),
    ],
)
def test_normalize_query_params_casts_numeric_strings(raw: dict, expected: dict):
    assert ResponseHandler._normalize_query_params(raw) == expected


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
    raw: dict, expected: dict
):
    assert ResponseHandler._normalize_query_params(raw) == expected


def test_django_ninja_handler_parses_and_normalizes_query_string():
    handler = DjangoNinjaResponseHandler(
        "GET",
        "/api/pets?page=1&active=true&name=doggie",
        None,
        response=MagicMock(),
    )

    assert handler.request.query_params == {
        "page": 1,
        "active": True,
        "name": "doggie",
    }


def test_django_ninja_handler_returns_empty_query_params_when_missing():
    handler = DjangoNinjaResponseHandler(
        "GET",
        "/api/pets",
        None,
        response=MagicMock(),
    )

    assert handler.request.query_params == {}


def _drf_response_handler(*, response_data, parsed_json):
    response = MagicMock()
    response.renderer_context = {
        "request": MagicMock(
            path="/api/pets",
            method="GET",
            data={},
            headers={},
            query_params={},
        )
    }
    response.data = response_data
    response.json.return_value = parsed_json
    return DRFResponseHandler(response=response)


def test_drf_response_handler_data_returns_parsed_json():
    handler = _drf_response_handler(
        response_data={"id": 1, "name": "doggie"},
        parsed_json={"id": 1, "name": "doggie"},
    )

    assert handler.data == {"id": 1, "name": "doggie"}


def test_drf_response_handler_data_returns_none_when_response_data_is_none():
    handler = _drf_response_handler(response_data=None, parsed_json=None)

    assert handler.data is None


def test_django_ninja_handler_data_returns_parsed_json():
    response = MagicMock()
    response.content = b'{"id": 1, "name": "doggie"}'
    response.json.return_value = {"id": 1, "name": "doggie"}
    handler = DjangoNinjaResponseHandler(
        "GET",
        "/api/pets",
        None,
        response=response,
    )

    assert handler.data == {"id": 1, "name": "doggie"}


def test_django_ninja_handler_data_returns_none_when_content_is_empty():
    response = MagicMock()
    response.content = b""
    handler = DjangoNinjaResponseHandler(
        "GET",
        "/api/pets",
        None,
        response=response,
    )

    assert handler.data is None


def _drf_request_mock(*, method="GET", path="/api/pets", data_property=None):
    request = MagicMock(path=path, method=method, headers={}, query_params={})
    type(request).data = data_property or PropertyMock(return_value={})
    return request


def test_drf_response_handler_does_not_read_request_data_on_init():
    """`request.data` is a lazy property in DRF, reading it parses the request body."""
    data_property = PropertyMock(return_value={"name": "doggie"})
    response = MagicMock()
    response.renderer_context = {
        "request": _drf_request_mock(data_property=data_property)
    }

    handler = DRFResponseHandler(response=response)

    data_property.assert_not_called()
    assert handler.method == "GET"
    assert handler.path == "/api/pets"
    assert handler.endpoint() == "GET /api/pets"
    data_property.assert_not_called()


def test_drf_response_handler_reads_request_data_lazily():
    data_property = PropertyMock(return_value={"name": "doggie"})
    response = MagicMock()
    response.renderer_context = {
        "request": _drf_request_mock(method="POST", data_property=data_property)
    }

    handler = DRFResponseHandler(response=response)

    assert handler.request.data == {"name": "doggie"}
    data_property.assert_called_once()
