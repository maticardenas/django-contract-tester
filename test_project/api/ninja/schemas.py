from ninja import Schema


class UserIn(Schema):
    name: str
    email: str
    age: int
    is_active: bool

    class Config:
        example = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "is_active": True,
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
        }
