from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Callable
from unittest.mock import MagicMock

import pytest
from rest_framework.response import Response

import openapi_tester
from openapi_tester.response_handler import GenericRequest
from tests.schema_converter import SchemaToPythonConverter
from tests.utils import TEST_ROOT

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def pets_api_schema() -> Path:
    return TEST_ROOT / "schemas" / "openapi_v3_reference_schema.yaml"


@pytest.fixture
def pets_api_schema_prefix_in_server() -> Path:
    return TEST_ROOT / "schemas" / "openapi_v3_prefix_in_server.yaml"


@pytest.fixture
def cars_api_schema() -> Path:
    return TEST_ROOT / "schemas" / "spectactular_reference_schema.yaml"


@pytest.fixture
def pets_post_request():
    request_body = MagicMock()
    request_body.read.return_value = b'{"name": "doggie", "tag": "dog"}'
    return GenericRequest(
        method="post",
        path="/api/pets",
        data={"name": "doggie", "tag": "dog"},
        headers={"Content-Type": "application/json"},
    )


@pytest.fixture
def invalid_pets_post_request():
    request_body = MagicMock()
    request_body.read.return_value = b'{"surname": "doggie", "species": "dog"}'
    return GenericRequest(
        method="post",
        path="/api/pets",
        data={"surname": "doggie", "species": "dog"},
        headers={"Content-Type": "application/json"},
    )


@pytest.fixture
def response_factory() -> Callable:
    def response(
        schema: dict | None,
        url_fragment: str,
        method: str,
        status_code: int | str = 200,
        response_body: str | None = None,
        request: GenericRequest | None = None,
    ) -> Response:
        converted_schema = None
        if schema:
            converted_schema = SchemaToPythonConverter(deepcopy(schema)).result
        response = Response(status=int(status_code), data=converted_schema)
        response.request = {"REQUEST_METHOD": method, "PATH_INFO": url_fragment}  # type: ignore

        if request:
            response.renderer_context = {  # type: ignore[attr-defined]
                "request": MagicMock(
                    path=request.path,
                    method=request.method,
                    data=request.data,
                    headers=request.headers,
                )
            }
        else:
            response.renderer_context = {  # type: ignore[attr-defined]
                "request": MagicMock(
                    path=url_fragment,
                    method=method,
                    data={},
                    headers={},
                )
            }

        if schema:
            response.json = lambda: converted_schema  # type: ignore
        elif response_body:
            response.request["CONTENT_LENGTH"] = len(response_body)  # type: ignore
            response.request["CONTENT_TYPE"] = "application/json"  # type: ignore
            response.request["wsgi.input"] = response_body  # type: ignore
        return response

    return response


@pytest.fixture
def users_ninja_api_schema() -> Path:
    return TEST_ROOT / "schemas" / "users_django_api_schema.yaml"


@pytest.fixture
def ninja_not_installed():
    former_client = openapi_tester.clients.TestClient
    openapi_tester.clients.TestClient = object
    yield
    openapi_tester.clients.TestClient = former_client
