"""
This module contains the concrete response handlers for both DRF and Django Ninja responses.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Union

import orjson

if TYPE_CHECKING:
    from django.http.response import HttpResponse
    from rest_framework.response import Response


@dataclass
class GenericRequest:
    """Generic request class for both DRF and Django Ninja."""

    path: str
    method: str
    data: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)


class ResponseHandler(ABC):
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
    @abstractmethod
    def request(self) -> GenericRequest: ...

    @property
    @abstractmethod
    def data(self) -> Optional[dict]: ...


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
    def request(self) -> GenericRequest:
        return GenericRequest(
            path=self.response.renderer_context["request"].path,  # type: ignore[attr-defined]
            method=self.response.renderer_context["request"].method,  # type: ignore[attr-defined]
            data=self.response.renderer_context["request"].data,  # type: ignore[attr-defined]
            headers=self.response.renderer_context["request"].headers,  # type: ignore[attr-defined]
        )


class DjangoNinjaResponseHandler(ResponseHandler):
    """
    Handles the response and request data from Django Ninja responses.
    """

    def __init__(
        self, *request_args, response: "HttpResponse", path_prefix: str = "", **kwargs
    ) -> None:
        super().__init__(response)
        self._request_method = request_args[0]
        self._request_path = f"{path_prefix}{request_args[1]}"
        self._request_data = self._build_request_data(request_args[2])
        self._request_headers = kwargs

    @property
    def data(self) -> Optional[dict]:
        return self.response.json() if self.response.content else None  # type: ignore[attr-defined]

    @property
    def request(self) -> GenericRequest:
        return GenericRequest(
            path=self._request_path,
            method=self._request_method,
            data=self._request_data,
            headers=self._request_headers,
        )

    def _build_request_data(self, request_data: Any) -> dict:
        try:
            return orjson.loads(request_data)
        except (orjson.JSONDecodeError, TypeError, ValueError):
            return {}
