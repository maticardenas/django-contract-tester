"""
This module contains the concrete response handlers for both DRF and Django Ninja responses.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Union
from urllib.parse import parse_qsl

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
    query_params: dict = field(default_factory=dict)


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

    @staticmethod
    def _normalize_query_params(query_params: dict) -> dict:
        """
        Normalize the query params to be validated against the schema.
        This is necessary because the query params are always strings in the request.
        """
        normalized_query_params = {}
        for query_param in query_params.keys():
            try:
                normalized_query_params[query_param] = float(query_params[query_param])
                if normalized_query_params[query_param].is_integer():
                    normalized_query_params[query_param] = int(
                        normalized_query_params[query_param]
                    )
            except ValueError:
                if query_param.lower() == "true":
                    normalized_query_params[query_param] = True
                elif query_param.lower() == "false":
                    normalized_query_params[query_param] = False
                elif query_param.lower() == "null":
                    normalized_query_params[query_param] = None  # type: ignore[assignment]
                else:
                    normalized_query_params[query_param] = query_params[query_param]
        return normalized_query_params


class DRFResponseHandler(ResponseHandler):
    """
    Handles the response and request data from DRF responses.
    """

    def __init__(self, response: "Response") -> None:
        super().__init__(response)
        self._request_path = self.response.renderer_context["request"].path  # type: ignore[attr-defined]
        self._request_method = self.response.renderer_context["request"].method  # type: ignore[attr-defined]
        self._request_data = self.response.renderer_context["request"].data  # type: ignore[attr-defined]
        self._request_headers = self.response.renderer_context["request"].headers  # type: ignore[attr-defined]
        self._request_query_params = self._normalize_query_params(
            self.response.renderer_context["request"].query_params  # type: ignore[attr-defined]
        )

    @property
    def data(self) -> Optional[dict]:
        return self.response.json() if self.response.data is not None else None  # type: ignore[attr-defined]

    @property
    def request(self) -> GenericRequest:
        return GenericRequest(
            path=self._request_path,
            method=self._request_method,
            data=self._request_data,
            headers=self._request_headers,
            query_params=self._request_query_params,
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
        self._request_path = self._build_request_path(request_args[1], path_prefix)
        self._request_query_params = self._build_request_query_params(request_args[1])
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
            query_params=self._request_query_params,
        )

    def _build_request_path(self, request_path: str, path_prefix: str) -> str:
        request_path = request_path.split("?")[0]
        return f"{path_prefix}{request_path}"

    def _build_request_query_params(self, request_path: str) -> dict:
        try:
            query_params = dict(parse_qsl(request_path.split("?")[1]))
            return self._normalize_query_params(query_params)
        except IndexError:
            return {}

    def _build_request_data(self, request_data: Any) -> dict:
        try:
            return json.loads(request_data)
        except (json.JSONDecodeError, TypeError, ValueError):
            return {}
