import json
from typing import TYPE_CHECKING

import pytest

from openapi_tester import OpenAPIClient, SchemaTester
from openapi_tester.exceptions import UndocumentedSchemaSectionError
from tests.utils import TEST_ROOT

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def users_ninja_api_schema() -> "Path":
    return TEST_ROOT / "schemas" / "users_django_api_schema.yaml"


@pytest.fixture
def client(users_ninja_api_schema: "Path") -> OpenAPIClient:
    return OpenAPIClient(
        schema_tester=SchemaTester(schema_file_path=str(users_ninja_api_schema))
    )


def test_get_users(client: OpenAPIClient):
    response = client.get("/ninja_api/users/")
    assert response.status_code == 200


def test_get_user(client: OpenAPIClient):
    response = client.get("/ninja_api/users/1")
    assert response.status_code == 200


def test_create_user(client: OpenAPIClient):
    payload = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 30,
        "is_active": True,
    }
    response = client.post(
        path="/ninja_api/users/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201


def test_update_user(client: OpenAPIClient):
    payload = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 35,
        "is_active": True,
    }
    response = client.put(
        path="/ninja_api/users/1",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200


def test_delete_user(client: OpenAPIClient):
    response = client.delete(
        path="/ninja_api/users/1",
    )
    assert response.status_code == 204


def test_patch_user_undocumented_path(client: OpenAPIClient):
    payload = {
        "name": "John Doe",
    }
    with pytest.raises(UndocumentedSchemaSectionError):
        client.patch(
            path="/ninja_api/users/1",
            data=json.dumps(payload),
            content_type="application/json",
        )
