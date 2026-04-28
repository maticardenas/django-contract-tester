from __future__ import annotations

from collections.abc import Callable, Generator
from copy import deepcopy
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.response import Response

import openapi_tester
from openapi_tester.config import OpenAPITestConfig, load_config_from_pyproject_toml
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
def openapi_v32_pets_schema() -> Path:
    return TEST_ROOT / "schemas" / "openapi_v3.2_pets_schema.yaml"


@pytest.fixture
def pets_post_request() -> GenericRequest:
    request_body = MagicMock()
    request_body.read.return_value = b'{"name": "doggie", "tag": "dog"}'
    return GenericRequest(
        method="post",
        path="/api/pets",
        data={"name": "doggie", "tag": "dog"},
        headers={"Content-Type": "application/json"},
    )


@pytest.fixture
def pets_delete_request() -> GenericRequest:
    return GenericRequest(
        method="delete",
        path="/api/pets/1",
        headers={"Content-Type": "application/json"},
    )


@pytest.fixture
def pets_get_request():
    return GenericRequest(
        method="get",
        path="/api/pets",
        data={},
        headers={"Content-Type": "application/json"},
        query_params={"tags": ["dog", "cat"]},
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
                    query_params=request.query_params,
                )
            }
        else:
            response.renderer_context = {  # type: ignore[attr-defined]
                "request": MagicMock(
                    path=url_fragment,
                    method=method,
                    data={},
                    headers={},
                    query_params={},
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


def custom_test_config_factory(
    config_path: Path,
) -> Generator[OpenAPITestConfig]:
    test_config = load_config_from_pyproject_toml(config_path=config_path)
    with patch("openapi_tester.config.settings", test_config):
        # Also need to patch it in validators module since it's already imported
        with patch("openapi_tester.validators.settings", test_config):
            yield test_config


@pytest.fixture
def custom_test_config():
    yield from custom_test_config_factory(
        TEST_ROOT / "data" / "config" / "pyproject.toml"
    )


@pytest.fixture
def custom_test_config_no_response_validation():
    yield from custom_test_config_factory(
        TEST_ROOT / "data" / "config" / "pyproject_no_response_validation.toml"
    )


@pytest.fixture
def custom_test_config_excluded_endpoints():
    yield from custom_test_config_factory(
        TEST_ROOT / "data" / "config" / "django-contract-tester-excluded-endpoints.toml"
    )
