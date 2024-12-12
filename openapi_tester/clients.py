"""Subclass of ``APIClient`` using ``SchemaTester`` to validate responses."""

from __future__ import annotations

import http
from typing import TYPE_CHECKING

try:
    from ninja import NinjaAPI, Router
    from ninja.testing import TestClient
except ImportError:
    NinjaAPI = Router = TestClient = object


from rest_framework.test import APIClient

from .exceptions import APIFrameworkNotInstalledError
from .response_handler_factory import ResponseHandlerFactory
from .schema_tester import SchemaTester
from .utils import serialize_json

if TYPE_CHECKING:
    from rest_framework.response import Response


class OpenAPIClient(APIClient):
    """``APIClient`` validating responses against OpenAPI schema."""

    def __init__(
        self,
        *args,
        schema_tester: SchemaTester | None = None,
        **kwargs,
    ) -> None:
        """Initialize ``OpenAPIClient`` instance."""
        super().__init__(*args, **kwargs)
        self.schema_tester = schema_tester or self._schema_tester_factory()

    def request(self, *args, **kwargs) -> Response:  # type: ignore[override]
        """Validate fetched response against given OpenAPI schema."""
        response = super().request(**kwargs)
        response_handler = ResponseHandlerFactory.create(
            *args, response=response, **kwargs
        )
        if self._is_successful_response(response):
            self.schema_tester.validate_request(response_handler=response_handler)
        self.schema_tester.validate_response(response_handler=response_handler)
        return response

    @serialize_json
    def post(
        self,
        *args,
        content_type="application/json",
        **kwargs,
    ):
        return super().post(
            *args,
            content_type=content_type,
            **kwargs,
        )

    @serialize_json
    def put(
        self,
        *args,
        content_type="application/json",
        **kwargs,
    ):
        return super().put(
            *args,
            content_type=content_type,
            **kwargs,
        )

    @serialize_json
    def patch(self, *args, content_type="application/json", **kwargs):
        return super().patch(
            *args,
            content_type=content_type,
            **kwargs,
        )

    @serialize_json
    def delete(
        self,
        *args,
        content_type="application/json",
        **kwargs,
    ):
        return super().delete(
            *args,
            content_type=content_type,
            **kwargs,
        )

    @serialize_json
    def options(
        self,
        *args,
        content_type="application/json",
        **kwargs,
    ):
        return super().options(
            *args,
            content_type=content_type,
            **kwargs,
        )

    @staticmethod
    def _is_successful_response(response: Response) -> bool:
        return response.status_code < http.HTTPStatus.BAD_REQUEST

    @staticmethod
    def _schema_tester_factory() -> SchemaTester:
        """Factory of default ``SchemaTester`` instances."""
        return SchemaTester()


# pylint: disable=R0903
class OpenAPINinjaClient(TestClient):
    """``APINinjaClient`` validating responses against OpenAPI schema."""

    def __init__(
        self,
        *args,
        router_or_app: NinjaAPI | Router,
        path_prefix: str = "",
        schema_tester: SchemaTester | None = None,
        **kwargs,
    ) -> None:
        """Initialize ``OpenAPINinjaClient`` instance."""
        if not isinstance(object, TestClient):
            super().__init__(*args, router_or_app=router_or_app, **kwargs)
        else:
            raise APIFrameworkNotInstalledError("Django-Ninja is not installed.")
        self.schema_tester = schema_tester or self._schema_tester_factory()
        self._ninja_path_prefix = path_prefix

    def request(self, *args, **kwargs) -> Response:
        """Validate fetched response against given OpenAPI schema."""
        response = super().request(*args, **kwargs)
        response_handler = ResponseHandlerFactory.create(
            *args, response=response, path_prefix=self._ninja_path_prefix, **kwargs
        )
        if self._is_successful_response(response):
            self.schema_tester.validate_request(response_handler=response_handler)
        self.schema_tester.validate_response(response_handler)
        return response

    @staticmethod
    def _is_successful_response(response: Response) -> bool:
        return response.status_code < http.HTTPStatus.BAD_REQUEST

    @staticmethod
    def _schema_tester_factory() -> SchemaTester:
        """Factory of default ``SchemaTester`` instances."""
        return SchemaTester()
