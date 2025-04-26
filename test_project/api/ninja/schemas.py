from ninja import Schema


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
