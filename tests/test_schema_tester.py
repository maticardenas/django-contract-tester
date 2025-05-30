from __future__ import annotations

import glob
import os
from copy import deepcopy
from typing import TYPE_CHECKING
from unittest.mock import patch
from uuid import UUID, uuid1, uuid4

import pytest
from django.core.exceptions import ImproperlyConfigured

from openapi_tester import (
    DrfSpectacularSchemaLoader,
    DrfYasgSchemaLoader,
    SchemaTester,
    StaticSchemaLoader,
    is_pascal_case,
)
from openapi_tester.constants import (
    INIT_ERROR,
    OPENAPI_PYTHON_MAPPING,
    VALIDATE_EXCESS_KEY_ERROR,
    VALIDATE_MISSING_KEY_ERROR,
    VALIDATE_NONE_ERROR,
    VALIDATE_ONE_OF_ERROR,
    VALIDATE_WRITE_ONLY_RESPONSE_KEY_ERROR,
)
from openapi_tester.exceptions import (
    CaseError,
    DocumentationError,
    UndocumentedSchemaSectionError,
)
from openapi_tester.loaders import UrlStaticSchemaLoader
from openapi_tester.response_handler import GenericRequest
from openapi_tester.response_handler_factory import ResponseHandlerFactory
from openapi_tester.schema_tester import OpenAPITestConfig
from test_project.models import Names
from tests import example_object, example_schema_types
from tests.utils import TEST_ROOT, iterate_schema, mock_schema

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

tester = SchemaTester()
name_id = 1234567890
parameterized_path = "/api/{version}/cars/correct"
de_parameterized_path = "/api/v1/cars/correct"
method = "get"
status = "200"
bad_test_data = [
    {
        "url": "/api/v1/cars/incorrect",
        "expected_response": [
            {"name": "Saab", "color": "Yellow", "height": "Medium height"},
            {
                "name": "Volvo",
                "color": "Red",
                "width": "Not very wide",
                "length": "2 meters",
            },
            {
                "name": "Tesla",
                "height": "Medium height",
                "width": "Medium width",
                "length": "2 meters",
            },
        ],
    },
    {
        "url": "/api/v1/trucks/incorrect",
        "expected_response": [
            {"name": "Saab", "color": "Yellow", "height": "Medium height"},
            {
                "name": "Volvo",
                "color": "Red",
                "width": "Not very wide",
                "length": "2 meters",
            },
            {
                "name": "Tesla",
                "height": "Medium height",
                "width": "Medium width",
                "length": "2 meters",
            },
        ],
    },
    {
        "url": "/api/v1/trucks/incorrect",
        "expected_response": [
            {"name": "Saab", "color": "Yellow", "height": "Medium height"},
            {
                "name": "Volvo",
                "color": "Red",
                "width": "Not very wide",
                "length": "2 meters",
            },
            {
                "name": "Tesla",
                "height": "Medium height",
                "width": "Medium width",
                "length": "2 meters",
            },
        ],
    },
]

docs_any_of_example = {
    "type": "object",
    "anyOf": [
        {
            "required": ["age"],
            "properties": {
                "age": {"type": "integer"},
                "nickname": {"type": "string"},
            },
        },
        {
            "required": ["pet_type"],
            "properties": {
                "pet_type": {"type": "string", "enum": ["Cat", "Dog"]},
                "hunts": {"type": "boolean"},
            },
        },
    ],
}
# Excluded schemas files for test_example_schemas as they include expected validation errors.
EXCLUDED_SCHEMA_FILES = [
    "openapi_v3_reference_schema.yaml",
]


def test_loader_inference(settings):
    # Test drf-spectacular
    assert isinstance(SchemaTester().loader, DrfSpectacularSchemaLoader)

    # Test drf-yasg
    settings.INSTALLED_APPS.pop(settings.INSTALLED_APPS.index("drf_spectacular"))
    settings.INSTALLED_APPS.append("drf_yasg")
    assert isinstance(SchemaTester().loader, DrfYasgSchemaLoader)

    # Test static loader
    assert isinstance(SchemaTester(schema_file_path="test").loader, StaticSchemaLoader)

    # Test url static loader
    assert isinstance(
        SchemaTester(schema_file_path="http://test.url:8080/schema.yaml").loader,
        UrlStaticSchemaLoader,
    )

    # Test no loader
    settings.INSTALLED_APPS = []
    with pytest.raises(ImproperlyConfigured, match=INIT_ERROR):
        SchemaTester()


@pytest.mark.usefixtures("db")
@pytest.mark.parametrize(
    "url",
    [
        f"/api/v1/{name_id}/names",
        "/api/v1/router_generated/names/",
        f"/api/v1/router_generated/names/{name_id}/",
    ],
)
def test_drf_coerced_model_primary_key(client, url):
    Names.objects.create(custom_id_field=name_id)
    schema_tester = SchemaTester()
    response = client.get(url)
    schema_tester.validate_response(ResponseHandlerFactory.create(response=response))


@pytest.mark.parametrize(
    "filename",
    [
        filename
        for filename in glob.iglob(str(TEST_ROOT) + "/schemas/**/**", recursive=True)
        if os.path.isfile(filename)
        and "metadata" not in filename
        and filename.split("/")[-1] not in EXCLUDED_SCHEMA_FILES
    ],
)
def test_example_schemas(filename):
    """
    This is an automated integration test template, for each schema in the "../schemas" folder a test is generated
    """
    schema_tester = SchemaTester(schema_file_path=filename)
    schema = schema_tester.loader.load_schema()
    schema_tester.loader.schema = schema_tester.loader.de_reference_schema(schema)
    for schema_section, response, url_fragment in iterate_schema(
        schema_tester.loader.schema
    ):
        if schema_section and response:
            with patch.object(
                StaticSchemaLoader,
                "resolve_path",
                side_effect=lambda *args, **kwargs: (url_fragment, None),  # noqa
            ):
                response_handler = ResponseHandlerFactory.create(response=response)
                schema_tester.validate_response(response_handler=response_handler)
                assert sorted(
                    schema_tester.get_response_schema_section(
                        response_handler=response_handler,
                        test_config=OpenAPITestConfig(case_tester=is_pascal_case),
                    )
                ) == sorted(schema_section)


def test_validate_response_failure_scenario_with_predefined_data(client):
    for item in bad_test_data:
        response = client.get(item["url"])
        assert response.status_code == 200
        assert response.json() == item["expected_response"]
        with pytest.raises(
            DocumentationError,
            match=(
                "The following property was found in the schema definition, "
                'but is missing from the response data: "width"'
            ),
        ):
            tester.validate_response(ResponseHandlerFactory.create(response=response))


def test_validate_response_failure_scenario_undocumented_path(
    monkeypatch, response_factory
):
    schema = deepcopy(tester.loader.get_schema())
    schema_section = schema["paths"][parameterized_path][method]["responses"][status][
        "content"
    ]["application/json"]["schema"]
    del schema["paths"][parameterized_path]
    monkeypatch.setattr(tester.loader, "get_schema", mock_schema(schema))
    response = response_factory(schema_section, de_parameterized_path, method, status)
    with pytest.raises(
        UndocumentedSchemaSectionError,
        match=f"Unsuccessfully tried to index the OpenAPI schema by `{parameterized_path}`.",
    ):
        tester.validate_response(ResponseHandlerFactory.create(response=response))


def test_validate_response_failure_scenario_undocumented_method(
    monkeypatch, response_factory
):
    schema = deepcopy(tester.loader.get_schema())
    schema_section = schema["paths"][parameterized_path][method]["responses"][status][
        "content"
    ]["application/json"]["schema"]
    del schema["paths"][parameterized_path][method]
    monkeypatch.setattr(tester.loader, "get_schema", mock_schema(schema))
    response = response_factory(schema_section, de_parameterized_path, method, status)
    with pytest.raises(
        UndocumentedSchemaSectionError,
        match=f"Unsuccessfully tried to index the OpenAPI schema by `{method}`.",
    ):
        tester.validate_response(ResponseHandlerFactory.create(response=response))


def test_validate_response_failure_scenario_undocumented_status_code(
    monkeypatch, response_factory
):
    schema = deepcopy(tester.loader.get_schema())
    schema_section = schema["paths"][parameterized_path][method]["responses"][status][
        "content"
    ]["application/json"]["schema"]
    del schema["paths"][parameterized_path][method]["responses"][status]
    monkeypatch.setattr(tester.loader, "get_schema", mock_schema(schema))
    response = response_factory(schema_section, de_parameterized_path, method, status)
    with pytest.raises(
        UndocumentedSchemaSectionError,
        match=f"Unsuccessfully tried to index the OpenAPI schema by `{status}`.",
    ):
        tester.validate_response(ResponseHandlerFactory.create(response=response))


def test_validate_response_failure_scenario_undocumented_content(client, monkeypatch):
    schema = deepcopy(tester.loader.get_schema())
    del schema["paths"][parameterized_path][method]["responses"][status]["content"]
    monkeypatch.setattr(tester.loader, "get_schema", mock_schema(schema))
    response = client.get(de_parameterized_path)
    with pytest.raises(
        UndocumentedSchemaSectionError,
        match=(
            "Error: Unsuccessfully tried to index the OpenAPI schema by `content`. \n\nNo `content` defined for this response: get, path: /api/{version}/cars/correct"
        ),
    ):
        tester.validate_response(ResponseHandlerFactory.create(response=response))


def test_validate_request(
    response_factory, pets_api_schema: Path, pets_post_request: dict[str, Any]
):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    response = response_factory(
        schema=None,
        url_fragment="/api/pets",
        method="POST",
        status_code=201,
        response_body={"name": "doggie", "tag": "dog"},
    )
    schema_tester.validate_request(ResponseHandlerFactory.create(response=response))


def test_validate_request_with_config(
    response_factory, pets_api_schema: Path, pets_post_request: dict[str, Any]
):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    response = response_factory(
        schema=None,
        url_fragment="/api/pets",
        method="POST",
        status_code=201,
        response_body={"name": "doggie", "tag": "dog"},
    )
    schema_tester.validate_request(
        ResponseHandlerFactory.create(response=response),
        OpenAPITestConfig(case_tester=is_pascal_case, ignore_case=["name", "tag"]),
    )


def test_validate_request_invalid(
    response_factory, pets_api_schema: Path, pets_post_request: GenericRequest
):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    pets_post_request.data.pop("name")
    response = response_factory(
        schema=None,
        url_fragment="/api/pets",
        method="POST",
        status_code=201,
        request=pets_post_request,
    )
    response_handler = ResponseHandlerFactory.create(response=response)
    with pytest.raises(DocumentationError):
        schema_tester.validate_request(response_handler=response_handler)


def test_validate_request_no_application_json(
    response_factory, pets_api_schema: Path, pets_post_request: GenericRequest
):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    response = response_factory(
        schema=None,
        url_fragment="/api/pets",
        method="POST",
        status_code=201,
        response_body={"tag": "dog"},
    )
    response.renderer_context["request"].headers["CONTENT_TYPE"] = "application/xml"
    schema_tester.validate_request(ResponseHandlerFactory.create(response=response))


def test_validate_request_schema_with_prefix_in_server(
    response_factory,
    pets_api_schema_prefix_in_server: Path,
    pets_post_request: dict[str, Any],
):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema_prefix_in_server))
    response = response_factory(
        schema=None,
        url_fragment="/api/pets",
        method="POST",
        status_code=201,
        response_body={"name": "Doggie"},
    )

    with pytest.raises(UndocumentedSchemaSectionError) as error:
        schema_tester.validate_request(ResponseHandlerFactory.create(response=response))

    assert "Undocumented route /api/pets" in str(error.value)


def test_validate_request_schema_with_prefix_in_server_path_prefix(
    response_factory,
    pets_api_schema_prefix_in_server: Path,
    pets_post_request: dict[str, Any],
):
    schema_tester = SchemaTester(
        schema_file_path=str(pets_api_schema_prefix_in_server), path_prefix="/api"
    )
    response = response_factory(
        schema=None,
        url_fragment="/api/pets",
        method="POST",
        status_code=201,
        response_body={"name": "Doggie"},
    )
    schema_tester.validate_request(ResponseHandlerFactory.create(response=response))


def test_get_openapi_schema(pets_api_schema: Path):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    assert schema_tester.get_openapi_schema() == "3.1.0"


def test_get_request_body_schema_section(
    pets_post_request: GenericRequest, pets_api_schema: Path
):
    test_config = OpenAPITestConfig(case_tester=is_pascal_case)
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    schema_section = schema_tester.get_request_body_schema_section(
        request=pets_post_request, test_config=test_config
    )
    assert schema_section == {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": ["string", "null"]},
            "tag": {"type": "string", "writeOnly": True},
        },
    }


def test_get_request_body_schema_section_content_type_no_application_json(
    pets_post_request: GenericRequest, pets_api_schema: Path
):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    test_config = OpenAPITestConfig(case_tester=is_pascal_case)
    pets_post_request.headers["Content-Type"] = "application/xml"
    schema_section = schema_tester.get_request_body_schema_section(
        request=pets_post_request, test_config=test_config
    )
    assert schema_section == {}


def test_get_request_body_schema_section_no_content_request(
    pets_post_request: GenericRequest, pets_api_schema: Path
):
    test_config = OpenAPITestConfig(case_tester=is_pascal_case)
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    pets_post_request.data = {}
    schema_section = schema_tester.get_request_body_schema_section(
        request=pets_post_request, test_config=test_config
    )
    assert schema_section == {}


def test_get_query_params_schema_section(
    pets_get_request: GenericRequest, pets_api_schema: Path
):
    test_config = OpenAPITestConfig(case_tester=is_pascal_case)
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    schema_section = schema_tester.get_request_query_params_schema_section(
        request=pets_get_request, test_config=test_config
    )

    assert schema_section == {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}},
            "limit": {"type": "integer", "format": "int32"},
        },
    }


def test_get_request_query_params_schema_section_no_query_params(
    pets_post_request: GenericRequest, pets_api_schema: Path
):
    test_config = OpenAPITestConfig(case_tester=is_pascal_case)
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    schema_section = schema_tester.get_request_query_params_schema_section(
        request=pets_post_request, test_config=test_config
    )
    assert schema_section == {}


def test_validate_response_global_case_tester(client):
    response = client.get(de_parameterized_path)
    with pytest.raises(CaseError, match="is not properly PascalCased"):
        SchemaTester(case_tester=is_pascal_case).validate_response(
            ResponseHandlerFactory.create(response=response)
        )


@pytest.mark.parametrize("empty_schema", [None, {}])
def test_validate_response_empty_content(
    empty_schema, client, monkeypatch, response_factory
):
    schema = deepcopy(tester.loader.get_schema())
    del schema["paths"][parameterized_path][method]["responses"][status]["content"]
    monkeypatch.setattr(tester.loader, "get_schema", mock_schema(schema))
    response = response_factory(empty_schema, de_parameterized_path, method, status)
    tester.validate_response(ResponseHandlerFactory.create(response=response))


def test_validate_response_global_ignored_case(client):
    response = client.get(de_parameterized_path)
    SchemaTester(
        case_tester=is_pascal_case,
        ignore_case=["name", "color", "height", "width", "length"],
    ).validate_response(ResponseHandlerFactory.create(response=response))


def test_validate_response_passed_in_case_tester(client):
    response = client.get(de_parameterized_path)
    with pytest.raises(
        CaseError,
        match="The response key `name` is not properly PascalCased. Expected value: Name",
    ):
        tester.validate_response(
            response_handler=ResponseHandlerFactory.create(response=response),
            test_config=OpenAPITestConfig(case_tester=is_pascal_case),
        )


def test_validate_response_passed_in_ignored_case(client):
    response = client.get(de_parameterized_path)
    tester.validate_response(
        response_handler=ResponseHandlerFactory.create(response=response),
        test_config=OpenAPITestConfig(
            case_tester=is_pascal_case,
            ignore_case=["name", "color", "height", "width", "length"],
        ),
    )


def test_nullable_validation():
    for schema in example_schema_types:
        # A null value should always raise an error
        with pytest.raises(
            DocumentationError,
            match=VALIDATE_NONE_ERROR.format(
                expected=OPENAPI_PYTHON_MAPPING[schema["type"]], http_message="response"
            ),
        ):
            tester.test_schema_section(schema, None)

        # Unless the schema specifies it should be nullable

        # OpenAPI 3+
        schema["nullable"] = True
        tester.test_schema_section(schema, None)

        # Swagger 2.0
        del schema["nullable"]
        schema["x-nullable"] = True
        tester.test_schema_section(schema, None)


def test_write_only_validation():
    test_schema_section = {
        "type": "object",
        "properties": {
            "test": {
                "type": "string",
                "writeOnly": False,
            },
        },
    }
    test_response = {"test": "testString"}
    tester.test_schema_section(test_schema_section, test_response)
    test_schema_section["properties"]["test"]["writeOnly"] = True
    with pytest.raises(
        DocumentationError,
        match=VALIDATE_WRITE_ONLY_RESPONSE_KEY_ERROR.format(write_only_key="test"),
    ):
        tester.test_schema_section(test_schema_section, test_response)


def test_any_of_validation():
    """
    This test makes sure our anyOf implementation works as described in the official example docs:
    https://swagger.io/docs/specification/data-models/oneof-anyof-allof-not/#anyof
    """
    tester.test_schema_section(docs_any_of_example, {"age": 50})
    tester.test_schema_section(docs_any_of_example, {"pet_type": "Cat", "hunts": True})
    tester.test_schema_section(
        docs_any_of_example, {"nickname": "Fido", "pet_type": "Dog", "age": 44}
    )

    with pytest.raises(DocumentationError):
        tester.test_schema_section(
            docs_any_of_example, {"nickname": "Mr. Paws", "hunts": False}
        )


def test_one_of_validation():
    all_types = [
        {"type": "string"},
        {"type": "number"},
        {"type": "integer"},
        {"type": "boolean"},
        {"type": "array", "items": {}},
        {"type": "object"},
    ]

    # Make sure integers are validated correctly
    non_int_types = all_types[:1] + all_types[3:]
    int_types = all_types[1:3]
    int_value = 1
    for t in non_int_types:
        with pytest.raises(
            DocumentationError, match=VALIDATE_ONE_OF_ERROR.format(matches=0)
        ):
            tester.test_schema_section({"oneOf": [t]}, int_value)
    for t in int_types:
        tester.test_schema_section({"oneOf": [t]}, int_value)

    # Make sure strings are validated correctly
    non_string_types = all_types[1:]
    string_types = all_types[:1]
    string_value = "test"
    for t in non_string_types:
        with pytest.raises(
            DocumentationError, match=VALIDATE_ONE_OF_ERROR.format(matches=0)
        ):
            tester.test_schema_section({"oneOf": [t]}, string_value)
    for t in string_types:
        tester.test_schema_section({"oneOf": [t]}, string_value)

    # Make sure booleans are validated correctly
    non_boolean_types = all_types[:3] + all_types[4:]
    boolean_types = [all_types[3]]
    boolean_value = False
    for t in non_boolean_types:
        with pytest.raises(
            DocumentationError, match=VALIDATE_ONE_OF_ERROR.format(matches=0)
        ):
            tester.test_schema_section({"oneOf": [t]}, boolean_value)
    for t in boolean_types:
        tester.test_schema_section({"oneOf": [t]}, boolean_value)

    # Make sure arrays are validated correctly
    non_array_types = all_types[:4] + all_types[5:]
    array_types = [all_types[4]]
    array_value = []
    for t in non_array_types:
        with pytest.raises(
            DocumentationError, match=VALIDATE_ONE_OF_ERROR.format(matches=0)
        ):
            tester.test_schema_section({"oneOf": [t]}, array_value)
    for t in array_types:
        tester.test_schema_section({"oneOf": [t]}, array_value)

    # Make sure arrays are validated correctly
    non_object_types = all_types[:5]
    object_types = [all_types[5]]
    object_value = {}
    for t in non_object_types:
        with pytest.raises(
            DocumentationError, match=VALIDATE_ONE_OF_ERROR.format(matches=0)
        ):
            tester.test_schema_section({"oneOf": [t]}, object_value)
    for t in object_types:
        tester.test_schema_section({"oneOf": [t]}, object_value)

    # Make sure we raise the appropriate error when we find several matches
    with pytest.raises(
        DocumentationError, match=VALIDATE_ONE_OF_ERROR.format(matches=2)
    ):
        tester.test_schema_section(
            {
                "oneOf": [
                    {"type": "string"},
                    {"type": "number"},
                    {"type": "integer"},
                    {"type": "boolean"},
                    {"type": "array", "items": {}},
                    {"type": "object"},
                ]
            },
            1,
        )

    # Make sure we raise the appropriate error when we find no matches
    with pytest.raises(
        DocumentationError, match=VALIDATE_ONE_OF_ERROR.format(matches=0)
    ):
        tester.test_schema_section(
            {
                "oneOf": [
                    {"type": "number"},
                    {"type": "integer"},
                    {"type": "boolean"},
                    {"type": "array", "items": {}},
                    {"type": "object"},
                ]
            },
            "test",
        )


def test_missing_keys_validation():
    # If a required key is missing, we should raise an error
    required_key = {
        "type": "object",
        "properties": {"value": {"type": "integer"}},
        "required": ["value"],
    }
    with pytest.raises(
        DocumentationError,
        match=VALIDATE_MISSING_KEY_ERROR.format(
            http_message="response", missing_key="value"
        ),
    ):
        tester.test_schema_section(required_key, {})

    # If not required, it should pass
    optional_key = {"type": "object", "properties": {"value": {"type": "integer"}}}
    tester.test_schema_section(optional_key, {})


def test_excess_keys_validation():
    schema = {"type": "object", "properties": {}}
    with pytest.raises(
        DocumentationError,
        match=VALIDATE_EXCESS_KEY_ERROR.format(
            http_message="response", excess_key="value"
        ),
    ):
        tester.test_schema_section(schema, example_object)


def test_custom_validators():
    def uuid_4_validator(schema_section: dict, data: Any) -> str | None:
        schema_format = schema_section.get("format")
        if schema_format == "uuid4":
            result = UUID(data, version=4)
            if str(result) != str(data):
                return f"Expected uuid4, but received {data}"
        return None

    def uuid_1_validator(
        schema_section: dict, data: Any
    ) -> str | None:  # pragma: no cover
        schema_format = schema_section.get("format")
        if schema_format == "uuid1":  #
            try:
                result = UUID(data, version=1)
                if str(result) != str(data):
                    return f"Expected uuid1, but received {data}"
            except ValueError:
                return f"Expected uuid1, but received {data}"
        return None

    tester_with_custom_validator = SchemaTester(validators=[uuid_4_validator])

    uid1_schema = {"type": "string", "format": "uuid1"}
    uid4_schema = {"type": "string", "format": "uuid4"}
    uid1 = str(uuid1())
    uid4 = str(uuid4())

    assert tester_with_custom_validator.test_schema_section(uid4_schema, uid4) is None

    with pytest.raises(
        DocumentationError,
        match=f"Expected uuid4, but received {uid1}",
    ):
        tester_with_custom_validator.test_schema_section(uid4_schema, uid1)

    assert (
        tester_with_custom_validator.test_schema_section(
            uid1_schema,
            uid1,
            test_config=OpenAPITestConfig(validators=[uuid_1_validator]),
        )
        is None
    )

    with pytest.raises(
        DocumentationError,
        match=f"Expected uuid1, but received {uid4}",
    ):
        tester_with_custom_validator.test_schema_section(
            uid1_schema,
            uid4,
            test_config=OpenAPITestConfig(validators=[uuid_1_validator]),
        )


def test_get_paths_object():
    schema = tester.loader.get_schema()
    paths = tester.get_paths_object()
    assert paths == schema["paths"]


def test_get_paths_object_no_path_prefix(pets_api_schema: Path):
    schema_tester = SchemaTester(schema_file_path=str(pets_api_schema))
    paths_object = schema_tester.get_paths_object()

    assert list(paths_object.keys()) == ["/api/pets", "/api/pets/{petId}"]


def test_get_paths_object_path_prefix(pets_api_schema_prefix_in_server: Path):
    path_prefix = "/api"
    schema_tester = SchemaTester(
        schema_file_path=str(pets_api_schema_prefix_in_server), path_prefix=path_prefix
    )
    paths_object = schema_tester.get_paths_object()

    assert list(paths_object.keys()) == ["/api/pets", "/api/pets/{id}"]
