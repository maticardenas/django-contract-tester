import json
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import orjson
import pytest

from openapi_tester import SchemaTester
from openapi_tester.clients import OpenAPINinjaClient
from openapi_tester.exceptions import DocumentationError, UndocumentedSchemaSectionError
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


def test_get_user_by_name(client: OpenAPINinjaClient):
    query_params = {"name": "John Doe"}
    response = client.get(f"/1?{urlencode(query_params)}")
    assert response.status_code == 200


def test_get_user_with_undocumented_query_param(client: OpenAPINinjaClient):
    query_params = {"name": "John Doe", "date_of_birth": "12/12/1990"}

    with pytest.raises(DocumentationError) as error:
        client.get(f"/1?{urlencode(query_params)}")

    assert (
        'The following query parameter was found in the request, but is missing from the schema definition: "date_of_birth"'
        in str(error.value)
    )


def test_get_user_profile(client: OpenAPINinjaClient):
    query_params = {"membership_level": 3}
    response = client.get(f"/profiles?{urlencode(query_params)}")
    assert response.status_code == 200


def test_get_user_profile_undocumented_query_param(client: OpenAPINinjaClient):
    query_params = {"membership_level": 3, "date_of_birth": "12/12/1990"}
    with pytest.raises(DocumentationError) as error:
        client.get(f"/profiles?{urlencode(query_params)}")

    assert (
        'The following query parameter was found in the request, but is missing from the schema definition: "date_of_birth"'
        in str(error.value)
    )


def test_get_user_profile_with_documented_query_param_incompatible_format(
    client: OpenAPINinjaClient,
):
    query_params = {
        "membership_level": 3,
        "is_active": "yes",
    }  # defined as boolean in schema
    with pytest.raises(DocumentationError) as error:
        client.get(f"/profiles?{urlencode(query_params)}")

    assert 'Expected: a "boolean" type value' in str(error.value)


def test_get_user_with_larger_than_int64_integer(client: OpenAPINinjaClient):
    with pytest.raises(DocumentationError) as error:
        client.get("/2")

    assert 'Expected: a "int64" formatted "integer" value' in str(error.value)


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


def test_update_user_with_int_fields(client: OpenAPINinjaClient):
    payload = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 35,
        "is_active": True,
        "total_points_earned": 1000,
        "membership_level": 3,
    }

    response = client.put(
        path="/1",
        data=orjson.dumps(payload).decode("utf-8"),
        content_type="application/json",
    )

    assert response.status_code == 200


def test_update_user_with_int_fields_out_of_range(client: OpenAPINinjaClient):
    payload = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 35,
        "is_active": True,
        "total_points_earned": 2**64,
        "membership_level": 6,
    }

    with pytest.raises(DocumentationError):
        client.put(
            path="/1",
            data=json.dumps(
                payload
            ),  # using json.dumps as orjson doesn't support integer value types > int64 - https://github.com/ijl/orjson/issues/301
            content_type="application/json",
        )


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
