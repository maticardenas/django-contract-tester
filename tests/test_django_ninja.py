from typing import TYPE_CHECKING

import orjson
import pytest

from openapi_tester import SchemaTester
from openapi_tester.clients import OpenAPINinjaClient
from openapi_tester.exceptions import UndocumentedSchemaSectionError
from test_project.api.ninja.api import router

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def client(users_ninja_api_schema: "Path") -> OpenAPINinjaClient:
    return OpenAPINinjaClient(
        router_or_app=router,
        path_prefix="/ninja_api/users",
        schema_tester=SchemaTester(schema_file_path=str(users_ninja_api_schema)),
    )


def test_get_users(client: OpenAPINinjaClient):
    response = client.get("/")
    assert response.status_code == 200


def test_get_user(client: OpenAPINinjaClient):
    response = client.get("/1")
    assert response.status_code == 200


def test_create_user(client: OpenAPINinjaClient):
    payload = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 30,
        "is_active": True,
    }
    response = client.post(
        path="/",
        data=orjson.dumps(payload).decode("utf-8"),
        content_type="application/json",
    )
    assert response.status_code == 201


def test_update_user(client: OpenAPINinjaClient):
    payload = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 35,
        "is_active": True,
    }
    response = client.put(
        path="/1",
        data=orjson.dumps(payload).decode("utf-8"),
        content_type="application/json",
    )
    assert response.status_code == 200


def test_delete_user(client: OpenAPINinjaClient):
    response = client.delete(
        path="/1",
    )
    assert response.status_code == 204


def test_patch_user_undocumented_path(client: OpenAPINinjaClient):
    payload = {
        "name": "John Doe",
    }
    with pytest.raises(UndocumentedSchemaSectionError):
        client.patch(
            path="/1",
            data=orjson.dumps(payload).decode("utf-8"),
            content_type="application/json",
        )
