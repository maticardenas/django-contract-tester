"""
This module contains the concrete response handlers for both DRF and Django Ninja responses.
"""

import json
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from django.http.response import HttpResponse
    from rest_framework.response import Response


class ResponseHandler:
    """
    This class is used to handle the response and request data
    from both DRF and Django HTTP (Django Ninja) responses.
    """

    def __init__(self, response: Union["Response", "HttpResponse"]) -> None:
        self._response = response

    @property
    def response(self) -> Union["Response", "HttpResponse"]:
        return self._response

    @property
    def data(self) -> Optional[dict]:
        ...

    @property
    def request_data(self) -> Optional[dict]:
        ...


class DRFResponseHandler(ResponseHandler):
    """
    Handles the response and request data from DRF responses.
    """

    def __init__(self, response: "Response") -> None:
        super().__init__(response)

    @property
    def data(self) -> Optional[dict]:
        return self.response.json() if self.response.data is not None else None  # type: ignore[attr-defined]

    @property
    def request_data(self) -> Optional[dict]:
        return self.response.renderer_context["request"].data  # type: ignore[attr-defined]


class DjangoNinjaResponseHandler(ResponseHandler):
    """
    Handles the response and request data from Django Ninja responses.
    """

    def __init__(self, response: "HttpResponse") -> None:
        super().__init__(response)

    @property
    def data(self) -> Optional[dict]:
        return self.response.json() if self.response.content else None  # type: ignore[attr-defined]

    @property
    def request_data(self) -> Optional[dict]:
        response_body = self.response.wsgi_request.body  # type: ignore[attr-defined]
        return json.loads(response_body) if response_body else None
