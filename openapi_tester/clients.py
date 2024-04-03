"""Subclass of ``APIClient`` using ``SchemaTester`` to validate responses."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from rest_framework.test import APIClient

from .schema_tester import SchemaTester

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

    def request(self, **kwargs) -> Response:  # type: ignore[override]
        """Validate fetched response against given OpenAPI schema."""
        response = super().request(**kwargs)
        if self._is_successful_response(response):
            self.schema_tester.validate_request(response)
        self.schema_tester.validate_response(response)
        return response

    # pylint: disable=W0622
    def post(self, path, data=None, format=None, content_type="application/json", follow=False, **extra):
        if data and content_type == "application/json":
            data = self._serialize(data)
        return super().post(path, data=data, format=format, content_type=content_type, follow=follow, **extra)

    # pylint: disable=W0622
    def put(self, path, data=None, format=None, content_type="application/json", follow=False, **extra):
        if data and content_type == "application/json":
            data = self._serialize(data)
        return super().put(path, data=data, format=format, content_type=content_type, follow=follow, **extra)

    # pylint: disable=W0622
    def patch(self, path, data=None, format=None, content_type="application/json", follow=False, **extra):
        if data and content_type == "application/json":
            data = self._serialize(data)
        return super().patch(path, data=data, format=format, content_type=content_type, follow=follow, **extra)

    # pylint: disable=W0622
    def delete(self, path, data=None, format=None, content_type="application/json", follow=False, **extra):
        if data and content_type == "application/json":
            data = self._serialize(data)
        return super().delete(path, data=data, format=format, content_type=content_type, follow=follow, **extra)

    # pylint: disable=W0622
    def options(self, path, data=None, format=None, content_type="application/json", follow=False, **extra):
        if data and content_type == "application/json":
            data = self._serialize(data)
        return super().options(path, data=data, format=format, content_type=content_type, follow=follow, **extra)

    @staticmethod
    def _is_successful_response(response: Response) -> bool:
        return response.status_code < 400

    @staticmethod
    def _schema_tester_factory() -> SchemaTester:
        """Factory of default ``SchemaTester`` instances."""
        return SchemaTester()

    @staticmethod
    def _serialize(data):
        try:
            return json.dumps(data)
        except (TypeError, OverflowError):
            """Data is already serialized"""
            return data
