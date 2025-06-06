"""Schema Tester"""

from __future__ import annotations

import json
import re
from copy import copy
from itertools import chain
from typing import TYPE_CHECKING, Any, Callable, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import URLValidator

from openapi_tester.config import OpenAPITestConfig
from openapi_tester.constants import (
    INIT_ERROR,
    UNDOCUMENTED_SCHEMA_SECTION_ERROR,
    VALIDATE_ANY_OF_ERROR,
    VALIDATE_EXCESS_KEY_ERROR,
    VALIDATE_EXCESS_QUERY_PARAM_ERROR,
    VALIDATE_MISSING_KEY_ERROR,
    VALIDATE_MISSING_QUERY_PARAM_ERROR,
    VALIDATE_NONE_ERROR,
    VALIDATE_ONE_OF_ERROR,
    VALIDATE_READ_ONLY_RESPONSE_KEY_ERROR,
    VALIDATE_WRITE_ONLY_RESPONSE_KEY_ERROR,
)
from openapi_tester.exceptions import (
    DocumentationError,
    OpenAPISchemaError,
    UndocumentedSchemaSectionError,
)
from openapi_tester.loaders import (
    DrfSpectacularSchemaLoader,
    DrfYasgSchemaLoader,
    StaticSchemaLoader,
    UrlStaticSchemaLoader,
)
from openapi_tester.utils import (
    get_required_keys,
    lazy_combinations,
    normalize_schema_section,
    query_params_to_object,
    serialize_schema_section_data,
    should_validate_query_param,
)
from openapi_tester.validators import (
    validate_enum,
    validate_format,
    validate_max_items,
    validate_max_length,
    validate_max_properties,
    validate_maximum,
    validate_min_items,
    validate_min_length,
    validate_min_properties,
    validate_minimum,
    validate_multiple_of,
    validate_pattern,
    validate_type,
    validate_unique_items,
)

if TYPE_CHECKING:
    from typing import Optional

    from openapi_tester.response_handler import GenericRequest, ResponseHandler


class SchemaTester:
    """Schema Tester: this is the base class of the library."""

    loader: (
        StaticSchemaLoader
        | DrfSpectacularSchemaLoader
        | DrfYasgSchemaLoader
        | UrlStaticSchemaLoader
    )
    validators: list[Callable[[dict, Any], str | None]]

    def __init__(
        self,
        case_tester: Callable[[str], None] | None = None,
        ignore_case: list[str] | None = None,
        schema_file_path: str | None = None,
        validators: list[Callable[[dict, Any], str | None]] | None = None,
        field_key_map: dict[str, str] | None = None,
        path_prefix: str | None = None,
    ) -> None:
        """
        Iterates through an OpenAPI schema object and API response to check that they match at every level.

        :param case_tester: An optional callable that validates schema and response keys
        :param ignore_case: An optional list of keys for the case_tester to ignore
        :schema_file_path: The file path to an OpenAPI yaml or json file. Only passed when using a static schema loader
        :param path_prefix: An optional string to prefix the path of the schema file
        :raises: openapi_tester.exceptions.DocumentationError or ImproperlyConfigured
        """
        self.case_tester = case_tester
        self._path_prefix = path_prefix
        self.ignore_case = ignore_case or []
        self.validators = validators or []

        if schema_file_path is not None:
            try:
                URLValidator()(schema_file_path)
                self.loader = UrlStaticSchemaLoader(
                    schema_file_path, field_key_map=field_key_map
                )
            except ValidationError:
                self.loader = StaticSchemaLoader(
                    schema_file_path, field_key_map=field_key_map
                )
        elif "drf_spectacular" in settings.INSTALLED_APPS:
            self.loader = DrfSpectacularSchemaLoader(field_key_map=field_key_map)
        elif "drf_yasg" in settings.INSTALLED_APPS:
            self.loader = DrfYasgSchemaLoader(field_key_map=field_key_map)
        else:
            raise ImproperlyConfigured(INIT_ERROR)

    @staticmethod
    def get_key_value(
        schema: dict[str, dict], key: str, error_addon: str = "", use_regex=False
    ) -> dict:
        """
        Returns the value of a given key
        """
        try:
            if use_regex:
                compiled_pattern = re.compile(key)
                for key_ in schema.keys():
                    if compiled_pattern.match(key_):
                        return schema[key_]
            return schema[key]
        except KeyError as e:
            raise UndocumentedSchemaSectionError(
                UNDOCUMENTED_SCHEMA_SECTION_ERROR.format(
                    key=key, error_addon=error_addon
                )
            ) from e

    @staticmethod
    def get_status_code(
        schema: dict[str | int, dict], status_code: str | int, error_addon: str = ""
    ) -> dict:
        """
        Returns the status code section of a schema, handles both str and int status codes
        """
        if str(status_code) in schema:
            return schema[str(status_code)]
        if int(status_code) in schema:
            return schema[int(status_code)]
        raise UndocumentedSchemaSectionError(
            UNDOCUMENTED_SCHEMA_SECTION_ERROR.format(
                key=status_code, error_addon=error_addon
            )
        )

    @staticmethod
    def get_schema_type(schema: dict[str, str]) -> str | None:
        if "type" in schema:
            return schema["type"]
        if "properties" in schema or "additionalProperties" in schema:
            return "object"
        return None

    def get_paths_object(self) -> dict[str, Any]:
        schema = self.loader.get_schema()
        paths_object = self.get_key_value(schema, "paths")
        if self._path_prefix:
            paths_object = {
                f"{self._path_prefix}{key}": value
                for key, value in paths_object.items()
            }

        return paths_object

    def get_response_schema_section(
        self, response_handler: ResponseHandler, test_config: OpenAPITestConfig
    ) -> dict[str, Any]:
        """
        Fetches the response section of a schema, wrt. the route, method, status code, and schema version.

        :param response: DRF Response Instance
        :return dict
        """
        response = response_handler.response
        schema = self.loader.get_schema()

        response_method = response_handler.request.method.lower()
        parameterized_path, _ = self.loader.resolve_path(
            response_handler.request.path,
            method=response_method,
        )
        paths_object = self.get_paths_object()

        route_object = self.get_key_value(
            paths_object,
            parameterized_path,
            (
                f"\n\n{test_config.reference}\n\nUndocumented route {parameterized_path}.\n\nDocumented routes: "
                + "\n\t• ".join(paths_object.keys())
            ),
        )

        method_object = self.get_key_value(
            route_object,
            response_method,
            (
                f"\n\n{test_config.reference}"
                f"\n\nUndocumented method: {response_method}."
                "\n\nDocumented methods: "
                f"{[method.lower() for method in route_object.keys() if method.lower() != 'parameters']}."
            ),
        )

        responses_object = self.get_key_value(method_object, "responses")
        status_code_object = self.get_status_code(
            responses_object,
            response.status_code,
            (
                f"\n\n{test_config.reference}"
                f"\n\nUndocumented status code: {response.status_code}."
                f"\n\nDocumented status codes: {list(responses_object.keys())}. "
            ),
        )

        if "openapi" not in schema:
            # openapi 2.0, i.e. "swagger" has a different structure than openapi 3.0 status sub-schemas
            return self.get_key_value(status_code_object, "schema")

        if status_code_object.get("content"):
            content_object = self.get_key_value(
                status_code_object,
                "content",
                (
                    f"\n\n{test_config.reference}"
                    f"\n\nNo content documented for method: {response_method}, path: {parameterized_path}"
                ),
            )
            json_object = self.get_key_value(
                content_object,
                r"^application\/.*json$",
                (
                    f"\n\n{test_config.reference}"
                    "\n\nNo `application/json` responses documented for method: "
                    f"{response_method}, path: {parameterized_path}"
                ),
                use_regex=True,
            )
            return self.get_key_value(json_object, "schema")

        if response_handler.data:
            raise UndocumentedSchemaSectionError(
                UNDOCUMENTED_SCHEMA_SECTION_ERROR.format(
                    key="content",
                    error_addon=(
                        f"\n\nNo `content` defined for this response: {response_method}, path: {parameterized_path}"
                    ),
                )
            )
        return {}

    def retrieve_documented_request(
        self, request: GenericRequest, test_config: OpenAPITestConfig
    ) -> tuple[str, str, dict[Any, Any]]:
        request_method = request.method.lower()  # request["REQUEST_METHOD"].lower()

        parametrized_path, _ = self.loader.resolve_path(
            request.path, method=request_method
        )

        paths_object = self.get_paths_object()

        route_object = self.get_key_value(
            paths_object,
            parametrized_path,
            (
                f"\n\n{test_config.reference}\n\nUndocumented route {parametrized_path}.\n\nDocumented routes: "
                + "\n\t• ".join(paths_object.keys())
            ),
        )

        method_object = self.get_key_value(
            route_object,
            request_method,
            (
                f"\n\n{test_config.reference}"
                f"\n\nUndocumented method: {request_method}."
                "\n\nDocumented methods: "
                f"{[method.lower() for method in route_object.keys() if method.lower() != 'parameters']}."
            ),
        )

        return parametrized_path, request_method, method_object

    def get_request_query_params_schema_section(
        self, request: GenericRequest, test_config: OpenAPITestConfig
    ) -> dict[str, Any]:
        """
        Fetches the request query params section of a schema and converts it to an object schema format.
        """
        parametrized_path, request_method, method_object = (
            self.retrieve_documented_request(request, test_config)
        )

        parameters_object: list[dict[str, Any]] = method_object.get("parameters", [])
        query_params = [
            param for param in parameters_object if param.get("in") == "query"
        ]

        if not query_params:
            if request.query_params:
                raise UndocumentedSchemaSectionError(
                    UNDOCUMENTED_SCHEMA_SECTION_ERROR.format(
                        key="parameters",
                        error_addon=f"\n\n{test_config.reference}"
                        f"\n\nNo query parameters documented for method: {request_method}, path: {parametrized_path}",
                    )
                )
            return {}

        # we convert the query params to an object schema in order to be able to validate it within the same flow of test_schema_section
        return query_params_to_object(query_params)

    def get_request_body_schema_section(
        self, request: GenericRequest, test_config: OpenAPITestConfig
    ) -> dict[str, Any]:
        """
        Fetches the request section of a schema.

        :param response: DRF Request Instance
        :return dict
        """

        parametrized_path, request_method, method_object = (
            self.retrieve_documented_request(request, test_config)
        )

        if request.data:
            if not any(
                "application/json" == request.headers.get(content_type)
                for content_type in ["content_type", "CONTENT_TYPE", "Content-Type"]
            ):
                return {}

            request_body_object = self.get_key_value(
                method_object,
                "requestBody",
                (
                    f"\n\n{test_config.reference}"
                    f"\n\nNo request body documented for method: {request_method}, path: {parametrized_path}"
                ),
            )

            content_object = self.get_key_value(
                request_body_object,
                "content",
                (
                    f"\n\n{test_config.reference}"
                    f"\n\nNo content documented for method: {request_method}, path: {parametrized_path}"
                ),
            )

            json_object = self.get_key_value(
                content_object,
                r"^application\/.*json$",
                (
                    f"\n\n{test_config.reference}"
                    "\n\nNo `application/json` requests documented for method: "
                    f"{request_method}, path: {parametrized_path}"
                ),
                use_regex=True,
            )

            return self.get_key_value(json_object, "schema")

        return {}

    def handle_one_of(
        self,
        schema_section: dict,
        data: Any,
        reference: str,
        test_config: OpenAPITestConfig,
    ) -> None:
        matches = 0
        passed_schema_section_formats = set()
        for option in schema_section["oneOf"]:
            try:
                test_config.reference = f"{test_config.reference}.oneOf"
                self.test_schema_section(
                    schema_section=option,
                    data=data,
                    test_config=test_config,
                )
                matches += 1
                passed_schema_section_formats.add(option.get("format"))
            except DocumentationError:
                continue
        if matches == 2 and passed_schema_section_formats == {"date", "date-time"}:
            # With Django v4, the datetime validator now parses normal
            # date formats successfully, so a oneOf: date // datetime section
            # will succeed twice where it used to succeed once.
            return
        if matches != 1:
            raise DocumentationError(
                f"{VALIDATE_ONE_OF_ERROR.format(matches=matches)}\n\nReference: {reference}.oneOf"
            )

    def handle_any_of(
        self,
        schema_section: dict,
        data: Any,
        reference: str,
        test_config: OpenAPITestConfig,
    ) -> None:
        any_of: list[dict[str, Any]] = schema_section.get("anyOf", [])
        for schema in chain(any_of, lazy_combinations(any_of)):
            test_config.reference = f"{test_config.reference}.anyOf"
            try:
                self.test_schema_section(
                    schema_section=schema,
                    data=data,
                    test_config=test_config,
                )
                return
            except DocumentationError:
                continue
        raise DocumentationError(
            f"{VALIDATE_ANY_OF_ERROR}\n\nReference: {reference}.anyOf"
        )

    def get_openapi_schema(self) -> str | None:
        return self.loader.get_schema().get("openapi")

    @staticmethod
    def test_is_nullable(schema_item: dict) -> bool:
        """
        Checks if the item is nullable.

        OpenAPI 3 ref: https://swagger.io/docs/specification/data-models/data-types/#null
        OpenApi 2 ref: https://help.apiary.io/api_101/swagger-extensions/

        :param schema_item: schema item
        :return: whether or not the item can be None
        """
        openapi_schema_3_nullable = "nullable"
        swagger_2_nullable = "x-nullable"

        if "oneOf" in schema_item:
            one_of: list[dict[str, Any]] = schema_item.get("oneOf", [])
            return any(
                nullable_key in schema and schema[nullable_key]
                for schema in one_of
                for nullable_key in [openapi_schema_3_nullable, swagger_2_nullable]
            )

        if "anyOf" in schema_item:
            any_of: list[dict[str, Any]] = schema_item.get("anyOf", [])
            return any(
                nullable_key in schema and schema[nullable_key]
                for schema in any_of
                for nullable_key in [openapi_schema_3_nullable, swagger_2_nullable]
            )

        return any(
            nullable_key in schema_item and schema_item[nullable_key]
            for nullable_key in [openapi_schema_3_nullable, swagger_2_nullable]
        )

    def test_key_casing(
        self,
        key: str,
        case_tester: Callable[[str], None] | None = None,
        ignore_case: list[str] | None = None,
    ) -> None:
        tester = case_tester or getattr(self, "case_tester", None)
        ignore_case = [*self.ignore_case, *(ignore_case or [])]
        if tester and key not in ignore_case:
            tester(key)

    def test_schema_section(
        self,
        schema_section: dict,
        data: Any,
        test_config: OpenAPITestConfig | None = None,
        is_query_params: bool = False,
    ) -> None:
        """
        This method orchestrates the testing of a schema section
        """
        test_config = test_config or OpenAPITestConfig()
        if data is None and "3.1" not in (self.get_openapi_schema() or ""):
            if self.test_is_nullable(schema_section) or not schema_section:
                # If data is None and nullable, we return early
                return
            raise DocumentationError(
                f"{VALIDATE_NONE_ERROR.format(http_message=test_config.http_message)}"
                "\n\nReference:"
                f"\n\n{test_config.reference}"
                f"\n\nSchema description:\n  {json.dumps(schema_section, indent=4)}"
                "\n\nHint: Return a valid type, or document the value as nullable"
            )
        schema_section = normalize_schema_section(schema_section)
        if "oneOf" in schema_section:
            self.handle_one_of(
                schema_section=schema_section,
                data=data,
                reference=test_config.reference,
                test_config=test_config,
            )
            return
        if "anyOf" in schema_section:
            self.handle_any_of(
                schema_section=schema_section,
                data=data,
                reference=test_config.reference,
                test_config=test_config,
            )
            return

        schema_section_type = self.get_schema_type(schema_section)
        if not schema_section_type:
            return
        combined_validators = cast(
            "list[Callable[[dict, Any], Optional[str]]]",
            [
                validate_type,
                validate_format,
                validate_pattern,
                validate_multiple_of,
                validate_minimum,
                validate_maximum,
                validate_unique_items,
                validate_min_length,
                validate_max_length,
                validate_min_items,
                validate_max_items,
                validate_max_properties,
                validate_min_properties,
                validate_enum,
                *self.validators,
                *(test_config.validators or []),
            ],
        )
        for validator in combined_validators:
            error = validator(schema_section, data)
            if error:
                raise DocumentationError(
                    f"\n\n{error}"
                    "\n\nReference: "
                    f"\n\n{test_config.reference}"
                    f"\n\n {test_config.http_message.capitalize()} value:\n  {data}"
                    f"\n Schema description:\n  {schema_section}"
                )
            # Add early return for null data after type validation succeeds
            if data is None and validator.__name__ == "validate_type":
                return

        if is_query_params:
            self.test_openapi_query_params_object(
                schema_section=schema_section, data=data, test_config=test_config
            )
        elif schema_section_type == "object":
            self.test_openapi_object(
                schema_section=schema_section, data=data, test_config=test_config
            )
        elif schema_section_type == "array":
            self.test_openapi_array(
                schema_section=schema_section, data=data, test_config=test_config
            )

    def test_openapi_object(
        self,
        schema_section: dict,
        data: dict,
        test_config: OpenAPITestConfig,
    ) -> None:
        """
        1. Validate that casing is correct for both request/response and schema
        2. Check if any required key is missing from the request/response
        3. Check if any request/response key is not in the schema
        4. Validate sub-schema/nested data
        """
        properties = schema_section.get("properties", {})
        write_only_properties = [
            key for key in properties.keys() if properties[key].get("writeOnly")
        ]
        read_only_properties = [
            key for key in properties.keys() if properties[key].get("readOnly")
        ]
        required_keys = get_required_keys(
            schema_section=schema_section,
            http_message=test_config.http_message,
            write_only_props=write_only_properties,
            read_only_props=read_only_properties,
        )

        request_response_keys = data.keys()
        additional_properties: bool | dict | None = schema_section.get(
            "additionalProperties"
        )
        additional_properties_allowed = additional_properties is not None
        if additional_properties_allowed and not isinstance(
            additional_properties, (bool, dict)
        ):
            raise OpenAPISchemaError("Invalid additionalProperties type")
        for key in properties.keys():
            self.test_key_casing(key, test_config.case_tester, test_config.ignore_case)
            if key in required_keys and key not in request_response_keys:
                raise DocumentationError(
                    f"{VALIDATE_MISSING_KEY_ERROR.format(missing_key=key, http_message=test_config.http_message)}"
                    "\n\nReference:"
                    f"\n\n{test_config.reference} > {key}"
                    f"\n\n{test_config.http_message.capitalize()} body:\n  {serialize_schema_section_data(data=data)}"
                    f"\nSchema section:\n  {serialize_schema_section_data(data=properties)}"
                    "\n\nHint: Remove the key from your OpenAPI docs, or"
                    f" include it in your API {test_config.http_message}"
                )
        for key in request_response_keys:
            self.test_key_casing(key, test_config.case_tester, test_config.ignore_case)
            if key not in properties and not additional_properties_allowed:
                raise DocumentationError(
                    f"{VALIDATE_EXCESS_KEY_ERROR.format(excess_key=key, http_message=test_config.http_message)}"
                    "\n\nReference:"
                    f"\n\n{test_config.reference} > {key}"
                    f"\n\n{test_config.http_message.capitalize()} body:\n  {serialize_schema_section_data(data=data)}"
                    f"\n\nSchema section:\n  {serialize_schema_section_data(data=properties)}"
                    "\n\nHint: Remove the key from your API"
                    f" {test_config.http_message}, or include it in your OpenAPI docs"
                )
            if key in write_only_properties and test_config.http_message == "response":
                raise DocumentationError(
                    f"{VALIDATE_WRITE_ONLY_RESPONSE_KEY_ERROR.format(write_only_key=key)}\n\nReference:"
                    f"\n\n{test_config.reference} > {key}"
                    f"\n\n{test_config.http_message.capitalize()} body:\n  {serialize_schema_section_data(data=data)}"
                    f"\nSchema section:\n  {serialize_schema_section_data(data=properties)}"
                    f"\n\nHint: Remove the key from your API {test_config.http_message}, or"
                    ' remove the "WriteOnly" restriction'
                )
            if key in read_only_properties and test_config.http_message == "request":
                raise DocumentationError(
                    f"{VALIDATE_READ_ONLY_RESPONSE_KEY_ERROR.format(read_only_key=key)}\n\nReference:"
                    f"\n\n{test_config.reference} > {key}"
                    f"\n\n{test_config.http_message.capitalize()} body:\n  {serialize_schema_section_data(data=data)}"
                    f"\nSchema section:\n  {serialize_schema_section_data(data=properties)}"
                    f"\n\nHint: Remove the key from your API {test_config.http_message}, or"
                    ' remove the "ReadOnly" restriction'
                )
        for key, value in data.items():
            if key in properties:
                drill_down_test_config = copy(test_config)
                drill_down_test_config.reference = f"{test_config.reference} > {key}"
                self.test_schema_section(
                    schema_section=properties[key],
                    data=value,
                    test_config=drill_down_test_config,
                )
            elif isinstance(additional_properties, dict):
                drill_down_test_config = copy(test_config)
                drill_down_test_config.reference = f"{test_config.reference} > {key}"
                self.test_schema_section(
                    schema_section=additional_properties,
                    data=value,
                    test_config=drill_down_test_config,
                )

    def test_openapi_query_params_object(
        self,
        schema_section: dict,
        data: dict,
        test_config: OpenAPITestConfig,
    ) -> None:
        properties = schema_section.get("properties", {})
        required_params = schema_section.get("required", [])
        request_params_keys = data.keys()

        for key in properties.keys():
            self.test_key_casing(key, test_config.case_tester, test_config.ignore_case)
            if key in required_params and key not in request_params_keys:
                raise DocumentationError(
                    f"{VALIDATE_MISSING_QUERY_PARAM_ERROR.format(missing_key=key, http_message=test_config.http_message)}"
                    "\n\nReference:"
                    f"\n\n{test_config.reference} > {key}"
                    f"\n\n{test_config.http_message.capitalize()} Query param:\n  {serialize_schema_section_data(data=data)}"
                    f"\nSchema section:\n  {serialize_schema_section_data(data=properties)}"
                    "\n\nHint: Remove the key from your OpenAPI docs, or"
                    f" include it in your API {test_config.http_message}"
                )
        for key in request_params_keys:
            self.test_key_casing(key, test_config.case_tester, test_config.ignore_case)
            if key not in properties:
                raise DocumentationError(
                    f"{VALIDATE_EXCESS_QUERY_PARAM_ERROR.format(excess_key=key, http_message=test_config.http_message)}"
                    "\n\nReference:"
                    f"\n\n{test_config.reference} > {key}"
                    f"\n\n{test_config.http_message.capitalize()} query parameters:\n  {serialize_schema_section_data(data=data)}"
                    f"\n\nQuery parameters' Schema section:\n  {serialize_schema_section_data(data=properties)}"
                    "\n\nHint: Remove the query parameter from your API"
                    f" {test_config.http_message}, or include it in your OpenAPI docs"
                )
        for key, value in data.items():
            if key in properties:
                if not should_validate_query_param(
                    param_schema_section=properties[key], request_value=value
                ):
                    continue
                drill_down_test_config = copy(test_config)
                drill_down_test_config.reference = f"{test_config.reference} > {key}"
                self.test_schema_section(
                    schema_section=properties[key],
                    data=value,
                    test_config=drill_down_test_config,
                )

    def test_openapi_array(
        self, schema_section: dict[str, Any], data: dict, test_config: OpenAPITestConfig
    ) -> None:
        for array_item in data:
            array_item_test_config = copy(test_config)
            array_item_test_config.reference = f"{test_config.reference}"
            self.test_schema_section(
                # the items keyword is required in arrays
                schema_section=schema_section["items"],
                data=array_item,
                test_config=array_item_test_config,
            )

    def validate_request(
        self,
        response_handler: ResponseHandler,
        test_config: OpenAPITestConfig | None = None,
    ) -> None:
        """
        Verifies that an OpenAPI schema definition matches an API request,
        validating both query parameters and request body.

        :param response_handler: The HTTP response handler (can be a DRF or Ninja response)
        :param test_config: Optional object with test configuration
        :raises: ``openapi_tester.exceptions.DocumentationError`` for inconsistencies in the API response and schema.
                 ``openapi_tester.exceptions.CaseError`` for case errors.
        """
        if self.get_openapi_schema() is not None:
            if test_config:
                test_config.http_message = "request"
            else:
                test_config = OpenAPITestConfig(
                    http_message="request",
                    reference=f"{response_handler.request.method} {response_handler.request.path} > request",
                )

            query_params_schema = self.get_request_query_params_schema_section(
                response_handler.request, test_config=test_config
            )

            if query_params_schema:
                test_config.reference = f"{test_config.reference} > query parameter"
                self.test_schema_section(
                    schema_section=query_params_schema,
                    data=response_handler.request.query_params,
                    test_config=test_config,
                    is_query_params=True,
                )

            request_body_schema = self.get_request_body_schema_section(
                response_handler.request, test_config=test_config
            )

            if request_body_schema:
                self.test_schema_section(
                    schema_section=request_body_schema,
                    data=response_handler.request.data,
                    test_config=test_config,
                )

    def validate_response(
        self,
        response_handler: ResponseHandler,
        test_config: OpenAPITestConfig | None = None,
    ) -> None:
        """
        Verifies that an OpenAPI schema definition matches an API response.

        :param response_handler: The HTTP response handler (can be a DRF or Ninja response)
        :param test_config: Optional object with test configuration
        :raises: ``openapi_tester.exceptions.DocumentationError`` for inconsistencies in the API response and schema.
                 ``openapi_tester.exceptions.CaseError`` for case errors.
        """
        if test_config:
            test_config.http_message = "response"
        else:
            request = response_handler.request
            test_config = OpenAPITestConfig(
                http_message="response",
                reference=f"{request.method} {request.path} > response > {response_handler.response.status_code}",
            )
        response_schema = self.get_response_schema_section(
            response_handler, test_config=test_config
        )
        self.test_schema_section(
            schema_section=response_schema,
            data=response_handler.data,
            test_config=test_config,
        )
