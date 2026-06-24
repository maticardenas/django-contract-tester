# ruff: noqa: ARG001

from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect
from rest_framework.request import Request


def index(
    request: Request,
) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """
    Redirects traffic from / to /swagger.
    """
    return redirect("schema-swagger-ui")
