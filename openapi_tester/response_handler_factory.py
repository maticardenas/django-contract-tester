# pylint: disable=R0903
"""
Module that contains the factory to create response handlers.
"""

from typing import TYPE_CHECKING, Union

from rest_framework.response import Response

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
        *request_args, response: Union[Response, "HttpResponse"], **kwargs
    ) -> "ResponseHandler":
        if isinstance(response, Response):
            return DRFResponseHandler(response=response)
        return DjangoNinjaResponseHandler(*request_args, response=response, **kwargs)
