"""Tests for the custom drf-spectacular hooks in ``test_project``."""

from __future__ import annotations

import pytest
from rest_framework.views import APIView

from test_project.spectacular_hooks import build_mock_request


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def test_build_mock_request_handles_standard_methods(method):
    """Standard HTTP methods use the matching ``APIRequestFactory`` helper."""
    view = APIView()

    request = build_mock_request(method, "/api/pets", view, original_request=None)

    assert request.method == method


def test_build_mock_request_handles_query_method():
    """Non-standard HTTP methods fall back to ``factory.generic()``."""
    view = APIView()

    request = build_mock_request("QUERY", "/api/pets", view, original_request=None)

    assert request.method == "QUERY"
    assert request.path == "/api/pets"
