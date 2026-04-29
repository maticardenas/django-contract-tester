import functools
from typing import TYPE_CHECKING

import orjson
import pytest
from django.test.testcases import SimpleTestCase
from rest_framework import status

from openapi_tester.clients import OpenAPIClient, OpenAPINinjaClient
from openapi_tester.exceptions import (
    APIFrameworkNotInstalledError,
    DocumentationError,
    UndocumentedSchemaSectionError,
)
from openapi_tester.schema_tester import SchemaTester

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def openapi_client(settings) -> OpenAPIClient:
    """Sample ``OpenAPIClient`` instance to use in tests."""
    # use `drf-yasg` schema loader in tests
    settings.INSTALLED_APPS = [
        app for app in settings.INSTALLED_APPS if app != "drf_spectacular"
    ]
    return OpenAPIClient()


def test_init_schema_tester_passed():
    """Ensure passed ``SchemaTester`` instance is used."""
    schema_tester = SchemaTester()

    client = OpenAPIClient(schema_tester=schema_tester)

    assert client.schema_tester is schema_tester


def test_init_schema_tester_passed_ninja():
    """Ensure passed ``SchemaTester`` instance is used."""
    schema_tester = SchemaTester()

    client = OpenAPINinjaClient(router_or_app=None, schema_tester=schema_tester)

    assert client.schema_tester is schema_tester


def test_get_request(cars_api_schema: "Path"):
    schema_tester = SchemaTester(schema_file_path=str(cars_api_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)
    response = openapi_client.get(path="/api/v1/cars/correct")

    assert response.status_code == status.HTTP_200_OK


def test_post_request(openapi_client):
    response = openapi_client.post(
        path="/api/v1/vehicles",
        data={"vehicle_type": "suv"},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_201_CREATED


def test_post_request_no_content_type(openapi_client):
    response = openapi_client.post(
        path="/api/v1/vehicles",
        data={"vehicle_type": "suv"},
    )

    assert response.status_code == status.HTTP_201_CREATED


def test_request_validation_is_not_triggered_for_bad_requests(pets_api_schema: "Path"):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)
    response = openapi_client.post(path="/api/pets", data={})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_request_body_extra_non_documented_field(pets_api_schema: "Path"):
    """Ensure ``SchemaTester`` raises exception when request is successful but an
    extra field non-documented was sent."""
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)

    with pytest.raises(DocumentationError):
        openapi_client.post(
            path="/api/pets",
            data={"name": "doggie", "age": 1},
            content_type="application/json",
        )


def test_request_with_write_only_field(pets_api_schema: "Path"):
    """Ensure validation doesn't raise exception when request a write-only field is
    included in the request, and not in the response."""
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)

    openapi_client.post(
        path="/api/pets",
        data={"name": "doggie", "tag": "Bulldog"},
        content_type="application/json",
    )


def test_request_with_read_only_field(pets_api_schema: "Path"):
    """Ensure validation doesn't raise exception when request a write-only field is
    included in the request, and not in the response."""
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)

    with pytest.raises(DocumentationError):
        openapi_client.post(
            path="/api/pets",
            data={"id": 1, "name": "doggie", "tag": "Bulldog"},
            content_type="application/json",
        )


def test_response_with_write_only_field(pets_api_schema: "Path"):
    """Ensure validation raises exception when response includes a write-only field."""
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)

    with pytest.raises(DocumentationError):
        openapi_client.get(path="/api/pets")


def test_request_body_non_null_fields(pets_api_schema: "Path"):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)

    with pytest.raises(DocumentationError):
        openapi_client.post(
            path="/api/pets",
            data={"name": "doggie", "tag": None},
            content_type="application/json",
        )


def test_request_multiple_types_supported(pets_api_schema: "Path"):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)

    openapi_client.post(path="/api/pets", data={"name": "doggie", "tag": "pet"})


def test_request_multiple_types_null_type_allowed(pets_api_schema: "Path"):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)

    openapi_client.post(path="/api/pets", data={"name": None, "tag": "pet"})


def test_request_on_empty_list(openapi_client):
    """Ensure ``SchemaTester`` doesn't raise exception when response is empty list."""
    response = openapi_client.generic(
        method="GET",
        path="/api/v1/empty-names",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK, response.data


@pytest.mark.parametrize(
    ("generic_kwargs", "raises_kwargs"),
    [
        (
            {
                "method": "POST",
                "path": "/api/v1/vehicles",
                "data": orjson.dumps({"vehicle_type": "1" * 50}).decode("utf-8"),
                "content_type": "application/json",
            },
            {
                "expected_exception": UndocumentedSchemaSectionError,
                "match": "Undocumented status code: 400",
            },
        ),
        (
            {"method": "PUT", "path": "/api/v1/animals"},
            {
                "expected_exception": UndocumentedSchemaSectionError,
                "match": "Undocumented method: put",
            },
        ),
    ],
)
def test_request_invalid_response(
    openapi_client,
    generic_kwargs,
    raises_kwargs,
):
    """Ensure ``SchemaTester`` raises an exception when response is invalid."""
    with pytest.raises(**raises_kwargs):  # noqa: PT010
        openapi_client.generic(**generic_kwargs)


@pytest.mark.parametrize(
    "openapi_client_class",
    [
        OpenAPIClient,
        functools.partial(OpenAPIClient, schema_tester=SchemaTester()),
    ],
)
def test_django_testcase_client_class(openapi_client_class):
    """Ensure example from README.md about Django test case works fine."""

    class DummyTestCase(SimpleTestCase):
        """Django ``TestCase`` with ``OpenAPIClient`` client."""

        client_class = openapi_client_class

    test_case = DummyTestCase()
    test_case._pre_setup()

    assert isinstance(test_case.client, OpenAPIClient)


def test_ninja_not_installed(ninja_not_installed):
    OpenAPIClient()

    with pytest.raises(APIFrameworkNotInstalledError):
        OpenAPINinjaClient(router_or_app=None)


def test_openapi_v32_schema_loads(openapi_v32_pets_schema: "Path"):
    """Test that schemas with OpenAPI 3.2 features are properly loaded and supported."""
    schema_tester = SchemaTester(schema_file_path=str(openapi_v32_pets_schema))
    assert schema_tester.get_openapi_schema() == "3.2.0"


def test_openapi_v32_get_request(openapi_v32_pets_schema: "Path"):
    """Test GET request with OpenAPI 3.2 schema."""
    schema_tester = SchemaTester(schema_file_path=str(openapi_v32_pets_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)
    response = openapi_client.get(path="/api/pets")

    assert response.status_code == status.HTTP_200_OK


def test_openapi_v32_post_request(openapi_v32_pets_schema: "Path"):
    """Test POST request with OpenAPI 3.2 schema."""
    schema_tester = SchemaTester(schema_file_path=str(openapi_v32_pets_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)
    response = openapi_client.post(
        path="/api/pets",
        data={"name": "doggie", "tag": "pet"},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_201_CREATED


def test_openapi_v32_query_request(openapi_v32_pets_schema: "Path"):
    """Test POST request with OpenAPI 3.2 schema."""
    schema_tester = SchemaTester(schema_file_path=str(openapi_v32_pets_schema))
    openapi_client = OpenAPIClient(schema_tester=schema_tester)

    response = openapi_client.query(
        path="/api/pets",
        data={"names": ["doggie", "max"], "tags": ["pet", "dog"]},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK


def test_openapi_v32_enhanced_tags_recognized(openapi_v32_pets_schema: "Path"):
    """Test that OpenAPI 3.2 enhanced tags are properly recognized."""
    schema_tester = SchemaTester(schema_file_path=str(openapi_v32_pets_schema))
    schema = schema_tester.loader.get_schema()

    tags = schema.get("tags", [])
    assert len(tags) > 0

    pets_tag = next((t for t in tags if t["name"] == "pets"), None)
    assert pets_tag is not None
    assert pets_tag.get("summary") == "Pet Management"
    assert pets_tag.get("kind") == "nav"


def test_openapi_v32_server_names(openapi_v32_pets_schema: "Path"):
    """Test that OpenAPI 3.2 server names are properly recognized."""
    schema_tester = SchemaTester(schema_file_path=str(openapi_v32_pets_schema))
    schema = schema_tester.loader.get_schema()

    servers = schema.get("servers", [])
    assert len(servers) > 0
    assert servers[0].get("name") == "Production"
    assert servers[0].get("description") == "Main production server"


def test_openapi_v32_example_data_value(openapi_v32_pets_schema: "Path"):
    """Test that OpenAPI 3.2 examples with dataValue field are present."""
    schema_tester = SchemaTester(schema_file_path=str(openapi_v32_pets_schema))
    schema = schema_tester.loader.get_schema()

    pets_get = schema["paths"]["/api/pets"]["get"]
    examples = pets_get["responses"]["200"]["content"]["application/json"]["examples"]

    assert "simple" in examples
    assert "dataValue" in examples["simple"]
    assert isinstance(examples["simple"]["dataValue"], list)
