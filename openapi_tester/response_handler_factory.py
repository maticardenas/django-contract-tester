# pylint: disable=R0903
"""
Module that contains the factory to create response handlers.
"""

import contextlib
from typing import TYPE_CHECKING

from openapi_tester.response_handler import (
    DjangoNinjaResponseHandler,
    DRFResponseHandler,
)

if TYPE_CHECKING:
    from django.http.response import HttpResponse

    from openapi_tester.response_handler import ResponseHandler


class ResponseHandlerFactory:
    """
    Response Handler Factory: this class is used to create a response handler
    instance for both DRF and Django HTTP (Django Ninja) responses.
    """

    @staticmethod
    def create(
        *request_args,
        response: "HttpResponse",
        **kwargs,
    ) -> "ResponseHandler":
        with contextlib.suppress(ImportError):
            from rest_framework.response import Response as DRFResponse

            if isinstance(response, DRFResponse):
                return DRFResponseHandler(response=response)
        with contextlib.suppress(ImportError):
            from ninja.testing.client import NinjaResponse

            if isinstance(response, NinjaResponse):
                return DjangoNinjaResponseHandler(
                    *request_args, response=response, **kwargs
                )
        raise TypeError(f"Can't pick response handler for {response}!")
