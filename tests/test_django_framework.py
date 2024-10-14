from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from rest_framework.test import APITestCase

from openapi_tester import SchemaTester
from openapi_tester.exceptions import DocumentationError
from openapi_tester.response_handler_factory import ResponseHandlerFactory
from tests.utils import TEST_ROOT

if TYPE_CHECKING:
    from rest_framework.response import Response

schema_tester = SchemaTester(
    schema_file_path=str(TEST_ROOT) + "/schemas/openapi_v3_reference_schema.yaml"
)


class BaseAPITestCase(APITestCase):
    """Base test class for api views including schema validation"""

    @staticmethod
    def assertResponse(response: Response, **kwargs) -> None:
        """helper to run validate_response and pass kwargs to it"""
        response_handler = ResponseHandlerFactory.create(response=response)
        schema_tester.validate_response(response_handler=response_handler, **kwargs)


class PetsAPITests(BaseAPITestCase):
    def test_get_pet_by_id(self):
        response = self.client.get(
            reverse("get-pets"),
            content_type="application/vnd.api+json",
        )
        assert response.status_code == 200
        with pytest.raises(DocumentationError):
            self.assertResponse(response)
