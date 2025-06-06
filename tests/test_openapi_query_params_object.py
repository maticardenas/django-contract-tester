import pytest

from openapi_tester import SchemaTester
from openapi_tester.config import OpenAPITestConfig
from openapi_tester.exceptions import DocumentationError


def test_openapi_query_params_object():
    schema_section = {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}},
            "limit": {"type": "integer", "format": "int32"},
        },
    }

    query_params = {
        "tags": ["dog", "cat"],
        "limit": 10,
    }

    tester = SchemaTester()

    tester.test_openapi_query_params_object(
        schema_section=schema_section,
        data=query_params,
        test_config=OpenAPITestConfig(
            reference="GET /endpoint > query_params", http_message="request"
        ),
    )


def test_openapi_query_params_object_no_query_params():
    schema_section = {
        "type": "object",
        "properties": {},
    }

    query_params = {}

    tester = SchemaTester()

    tester.test_openapi_query_params_object(
        schema_section=schema_section,
        data=query_params,
        test_config=OpenAPITestConfig(
            reference="GET /endpoint > query_params", http_message="request"
        ),
    )


def test_openapi_query_params_object_missing_required_query_param():
    expected_error_message = (
        'The following query parameter was found in the schema definition, but is missing from the request data: "tags"'
        "\n\nReference:\n\nGET /endpoint > query_params > tags\n\nRequest Query param:\n  {}\nSchema section:"
        '\n  {\n  "tags": {\n    "type": "array",\n    "items": {\n      "type": "string"\n    }\n  }\n}\n\n'
        "Hint: Remove the key from your OpenAPI docs, or include it in your API request"
    )
    schema_section = {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["tags"],
    }

    query_params = {}

    tester = SchemaTester()

    with pytest.raises(DocumentationError, match=expected_error_message):
        tester.test_openapi_query_params_object(
            schema_section=schema_section,
            data=query_params,
            test_config=OpenAPITestConfig(
                reference="GET /endpoint > query_params", http_message="request"
            ),
        )


def test_excess_query_param_in_request():
    expected_error_message = (
        'The following query parameter was found in the request, but is missing from the schema definition: "new_tag"'
        '\n\nReference:\n\nGET /endpoint > query_params > new_tag\n\nRequest query parameters:\n  {\n  "new_tag": "new_tag_value"\n}'
        '\n\nQuery parameters\' Schema section:\n  {\n  "tags": {\n    "type": "array",\n    "items": {\n      "type": "string"\n    }\n  },'
        '\n  "limit": {\n    "type": "integer",\n    "format": "int32"\n  }\n}\n\nHint: Remove the query parameter from your API request, or include it in your OpenAPI docs'
    )

    tester = SchemaTester()

    schema_section = {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}},
            "limit": {"type": "integer", "format": "int32"},
        },
        "required": [],
    }

    query_params = {
        "new_tag": "new_tag_value",
    }

    with pytest.raises(DocumentationError, match=expected_error_message):
        tester.test_openapi_query_params_object(
            schema_section=schema_section,
            data=query_params,
            test_config=OpenAPITestConfig(
                reference="GET /endpoint > query_params", http_message="request"
            ),
        )


def test_openapi_query_params_object_invalid_query_param_type():
    expected_error_message = (
        '\n\nExpected: an "integer" type value\n\nReceived: "not_an_integer"\n\nReference: \n\n'
        "GET /endpoint > query_params > limit\n\n Request value:\n  not_an_integer\n "
        "Schema description:\n  {'type': 'integer', 'format': 'int32'}"
    )

    tester = SchemaTester()

    schema_section = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "format": "int32"},
        },
    }

    query_params = {"limit": "not_an_integer"}

    with pytest.raises(DocumentationError, match=expected_error_message):
        tester.test_openapi_query_params_object(
            schema_section=schema_section,
            data=query_params,
            test_config=OpenAPITestConfig(
                reference="GET /endpoint > query_params", http_message="request"
            ),
        )


def test_openapi_query_params_object_email_format():
    expected_error_message = (
        '\n\nExpected: a "email" formatted "string" value\n\nReceived: "not_an_email"\n\nReference: \n\n'
        "GET /endpoint > query_params > email\n\n Request value:\n  not_an_email\n "
        "Schema description:\n  {'type': 'string', 'format': 'email'}"
    )

    tester = SchemaTester()

    schema_section = {
        "type": "object",
        "properties": {
            "email": {"type": "string", "format": "email"},
        },
    }

    query_params = {
        "email": "valid_test_email@example.com",
    }

    tester.test_openapi_query_params_object(
        schema_section=schema_section,
        data=query_params,
        test_config=OpenAPITestConfig(
            reference="GET /endpoint > query_params", http_message="request"
        ),
    )

    query_params = {
        "email": "not_an_email",
    }

    with pytest.raises(DocumentationError, match=expected_error_message):
        tester.test_openapi_query_params_object(
            schema_section=schema_section,
            data=query_params,
            test_config=OpenAPITestConfig(
                reference="GET /endpoint > query_params", http_message="request"
            ),
        )


def test_openapi_query_params_object_string_type_schema_section_integer_query_param():
    tester = SchemaTester()

    schema_section = {
        "type": "object",
        "properties": {
            "key": {"type": "string"},
        },
    }

    query_params = {"key": 1234}

    tester.test_openapi_query_params_object(
        schema_section=schema_section,
        data=query_params,
        test_config=OpenAPITestConfig(
            reference="GET /endpoint > query_params", http_message="request"
        ),
    )


def test_openapi_params_object_string_type_schema_section_with_format_string_query_param():
    tester = SchemaTester()

    schema_section = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "format": "email"},
        },
    }

    query_params = {"key": "test@test.com"}

    tester.test_openapi_query_params_object(
        schema_section=schema_section,
        data=query_params,
        test_config=OpenAPITestConfig(
            reference="GET /endpoint > query_params", http_message="request"
        ),
    )

    query_params = {"key": "1234"}

    with pytest.raises(DocumentationError):
        tester.test_openapi_query_params_object(
            schema_section=schema_section,
            data=query_params,
            test_config=OpenAPITestConfig(
                reference="GET /endpoint > query_params", http_message="request"
            ),
        )
