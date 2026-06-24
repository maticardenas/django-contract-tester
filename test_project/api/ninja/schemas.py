from ninja import FilterSchema, Schema


class UserIn(Schema):
    name: str
    email: str
    age: int
    is_active: bool
    membership_level: int = 0
    total_points_earned: int = 0

    class Config:
        example = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "is_active": True,
            "membership_level": 3,
            "total_points_earned": 1000,
        }


class UserOut(UserIn):
    id: int

    class Config:
        example = {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "is_active": True,
            "membership_level": 3,
            "total_points_earned": 1000,
        }


class UserProfileOut(Schema):
    id: int
    name: str
    email: str
    membership_level: int
    points: int
    join_date: str
    last_login: str
    is_active: bool

    class Config:
        example = {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "membership_level": 3,
            "points": 1000,
            "join_date": "2021-01-01",
            "last_login": "2021-01-01",
            "is_active": True,
        }


class UserProfileFilter(FilterSchema):
    membership_level: int
    min_points: int | None = None
    is_active: str = "yes"
    join_date: str | None = None
    search: str | None = None
    sort_by: str | None = None
    sort_order: str | None = None

    class Config:
        example = {
            "membership_level": 3,
            "min_points": 1000,
        }
