import pytest

from openapi_tester import SchemaTester
from openapi_tester.config import OpenAPITestConfig
from openapi_tester.exceptions import DocumentationError


def test_missing_response_key_error():
    expected_error_message = (
        'The following property was found in the schema definition, but is missing from the response data: "one"'
        "\n\nReference:\n\nPOST /endpoint > response > one"
        '\n\nResponse body:\n  {\n    "two": 2\n}'
        '\nSchema section:\n  {\n    "one": {\n        "type": "int"\n    }\n}'
        "\n\nHint: Remove the key from your OpenAPI docs, or include it in your API response"
    )
    tester = SchemaTester()
    with pytest.raises(DocumentationError, match=expected_error_message):
        tester.test_openapi_object(
            {"required": ["one"], "properties": {"one": {"type": "int"}}},
            {"two": 2},
            OpenAPITestConfig(reference="POST /endpoint > response"),
        )


def test_missing_schema_key_error():
    expected_error_message = (
        'The following property was found in the response data, but is missing from the schema definition: "two"'
        "\n\nReference:"
        "\n\nPOST /endpoint > response > two"
        '\n\nResponse body:\n  {\n    "one": 1,\n    "two": 2\n}'
        '\n\nSchema section:\n  {\n    "one": {\n        "type": "int"\n    }\n}'
        "\n\nHint: Remove the key from your API response, or include it in your OpenAPI docs"
    )
    tester = SchemaTester()
    with pytest.raises(DocumentationError, match=expected_error_message):
        tester.test_openapi_object(
            {"required": ["one"], "properties": {"one": {"type": "int"}}},
            {"one": 1, "two": 2},
            OpenAPITestConfig(reference="POST /endpoint > response"),
        )


def test_key_in_write_only_properties_error():
    expected_error_message = (
        'The following property was found in the response, but is documented as being "writeOnly": "one"'
        "\n\nReference:"
        "\n\nPOST /endpoint > response > one"
        '\n\nResponse body:\n  {\n    "one": 1\n}'
        '\nSchema section:\n  {\n    "one": {\n        "type": "int",\n        "writeOnly": true\n    }\n}'
        '\n\nHint: Remove the key from your API response, or remove the "WriteOnly" restriction'
    )
    tester = SchemaTester()
    with pytest.raises(DocumentationError, match=expected_error_message):
        tester.test_openapi_object(
            {"properties": {"one": {"type": "int", "writeOnly": True}}},
            {"one": 1},
            OpenAPITestConfig(reference="POST /endpoint > response"),
        )
