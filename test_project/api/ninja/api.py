from typing import List, Optional

from ninja import NinjaAPI, Query, Router

from test_project.api.ninja.schemas import (
    UserIn,
    UserOut,
    UserProfileFilter,
    UserProfileOut,
)

ninja_api = NinjaAPI()

router = Router()


@router.post("/", response={201: UserOut})
def create_user(request, user: UserIn):
    return {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 30,
        "is_active": True,
    }


@router.get("/profiles", response={200: List[UserProfileOut]})
def get_user_profile(request, query: Query[UserProfileFilter]):
    return [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "membership_level": 3,
            "points": 1000,
            "join_date": "2021-01-01",
            "is_active": True,
            "last_login": "2021-01-01",
        }
    ]


@router.get("/{user_id}", response={200: UserOut})
def get_user(request, user_id: int, name: Optional[str] = ""):
    if user_id == 1:
        return {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "is_active": True,
        }
    else:
        return {
            "id": 2,
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "age": 25,
            "is_active": True,
            "total_points_earned": 2**64,
            "membership_level": 3,
        }


@router.put("/{user_id}", response={200: UserOut})
def update_user(request, user_id: int, user: UserIn):
    return {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 35,
        "is_active": True,
    }


@router.delete("/{user_id}", response={204: None})
def delete_user(request, user_id: int):
    return


@router.get("/", response={200: List[UserOut]})
def get_users(request):
    return [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "is_active": True,
        },
        {
            "id": 1,
            "name": "Jay May",
            "email": "jay.may@example.com",
            "age": 23,
            "is_active": True,
        },
    ]


@router.patch("/{user_id}", response={200: UserOut})
def patch_user(request, user_id: int, user: UserIn):
    return {"id": 1, "name": "John Doe", "email": "john.doe@example.com"}


ninja_api.add_router("/users", router)
