"""drf-spectacular customisation hooks for the test project.

Lives here so the override path is short and easy to understand; the project's
``SPECTACULAR_SETTINGS`` points at the callables defined in this module.
"""

from __future__ import annotations

from rest_framework.test import APIRequestFactory


def build_mock_request(method, path, view, original_request, **kwargs):
    """Drop-in replacement for ``drf_spectacular.plumbing.build_mock_request``.

    The upstream helper assumes every entry in ``view.http_method_names`` matches
    a convenience method on ``APIRequestFactory`` (``get``/``post``/``put``/...).
    That breaks for non-standard HTTP methods such as ``QUERY`` (OpenAPI 3.2),
    where the factory has no dedicated helper. We fall back to ``generic()`` for
    those cases so schema generation succeeds for any verb DRF can dispatch.
    """
    factory = APIRequestFactory()
    method_lower = method.lower()
    if hasattr(factory, method_lower):
        request = getattr(factory, method_lower)(path=path)
    else:
        request = factory.generic(method, path)

    request = view.initialize_request(request)

    if original_request:
        request.user = original_request.user
        request.auth = original_request.auth
        for name, value in original_request.META.items():
            if not name.startswith("HTTP_"):
                continue
            if name in ("HTTP_ACCEPT", "HTTP_COOKIE", "HTTP_AUTHORIZATION"):
                continue
            request.META[name] = value
    return request
