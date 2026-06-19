from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from test_project.api.serializers import PetsSerializer

if TYPE_CHECKING:
    from rest_framework.request import Request


class Pet(APIView):
    http_method_names = [*APIView.http_method_names, "query"]

    def get(self, request: Request, petId: int = 0) -> Response:
        pet = {
            "id": petId if petId else 1,
            "name": "doggie",
            "tag": "Bulldog",
        }
        return Response(pet, HTTP_200_OK)

    def post(self, request) -> Response:
        serializer = PetsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"id": 1, "name": request.data["name"]}, 201)

    def query(self, request: Request) -> Response:
        names = request.data.get("names", [])
        tags = request.data.get("tags", [])

        filtered_pets = [
            {
                "id": i * len(tags) + j,
                "name": name,
                "tag": tag,
            }
            for i, name in enumerate(names)
            for j, tag in enumerate(tags)
        ]

        return Response(filtered_pets, HTTP_200_OK)
