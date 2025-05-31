[![PyPI](https://img.shields.io/pypi/v/django-contract-tester.svg)](https://pypi.org/project/django-contract-tester/)
[![Coverage](https://codecov.io/gh/maticardenas/django-contract-tester/graph/badge.svg)](https://app.codecov.io/gh/maticardenas/django-contract-tester)
[![Python versions](https://img.shields.io/badge/Python-3.8%2B-blue)](https://pypi.org/project/django-contract-tester/)
[![Django versions](https://img.shields.io/badge/Django-4.2%2B-blue)](https://pypi.org/project/django-contract-tester/)


# Django Contract Tester

This is a test utility to validate `DRF (Django REST Framework)` and `Django Ninja` test requests & responses against `OpenAPI` versions 2.x and 3.x schemas.

It has built-in support for `OpenAPI`version `2.0`, `3.0.x` and `3.1.x`, both `yaml` or `json` schema files.

## Installation

```shell script
pip install django-contract-tester
```

## Usage

Instantiate one or more instances of `SchemaTester`:

```python
from openapi_tester import SchemaTester

schema_tester = SchemaTester()
```

If you are using either [drf-yasg](https://github.com/axnsan12/drf-yasg)
or [drf-spectacular](https://github.com/tfranzel/drf-spectacular) this will be auto-detected, and the schema will be
loaded by the `SchemaTester` automatically.

If you are using schema files, you will need to pass the file path:

```python
from openapi_tester import SchemaTester

# path should be a string
schema_tester = SchemaTester(schema_file_path="./schemas/publishedSpecs.yaml")
```

Once you've instantiated a tester, you can use it to test responses and request bodies:

```python
from openapi_tester.schema_tester import SchemaTester

schema_tester = SchemaTester()


def test_response_documentation(client):
    response = client.get('api/v1/test/1')
    assert response.status_code == 200
    schema_tester.validate_response(response=response)


def test_request_documentation(client):
    response = client.get('api/v1/test/1')
    assert response.status_code == 200
    schema_tester.validate_request(response=response)
```

If you are using the Django testing framework, you can create a base `APITestCase` that incorporates schema validation:

```python
from rest_framework.response import Response
from rest_framework.test import APITestCase

from openapi_tester.schema_tester import SchemaTester

schema_tester = SchemaTester()


class BaseAPITestCase(APITestCase):
    """ Base test class for api views including schema validation """

    @staticmethod
    def assertResponse(response: Response, **kwargs) -> None:
        """ helper to run validate_response and pass kwargs to it """
        schema_tester.validate_response(response=response, **kwargs)
```

Then use it in a test file:

```python
from shared.testing import BaseAPITestCase


class MyAPITests(BaseAPITestCase):
    def test_some_view(self):
        response = self.client.get("...")
        self.assertResponse(response)
```

## Options

You can pass options either globally, when instantiating a `SchemaTester`, or locally, when
invoking `validate_response`:

```python
from openapi_tester import SchemaTester, is_camel_case
from tests.utils import my_uuid_4_validator

schema_test_with_case_validation = SchemaTester(
    case_tester=is_camel_case,
    ignore_case=["IP"],
    validators=[my_uuid_4_validator]
)

```

Or

```python
from openapi_tester import SchemaTester, is_camel_case
from tests.utils import my_uuid_4_validator

schema_tester = SchemaTester()


def my_test(client):
    response = client.get('api/v1/test/1')
    assert response.status_code == 200
    schema_tester.validate_response(
        response=response,
        case_tester=is_camel_case,
        ignore_case=["IP"],
        validators=[my_uuid_4_validator]
    )
```

### case_tester

The case tester argument takes a callable that is used to validate the key case of both schemas and responses. If
nothing is passed, case validation is skipped.

The library currently has 4 built-in case testers:

- `is_pascal_case`
- `is_snake_case`
- `is_camel_case`
- `is_kebab_case`

You can use one of these, or your own.

### ignore_case

List of keys to ignore when testing key case. This setting only applies when case_tester is not `None`.

### validators

List of custom validators. A validator is a function that receives two parameters: schema_section and data, and returns
either an error message or `None`, e.g.:

```python
from typing import Any, Optional
from uuid import UUID


def my_uuid_4_validator(schema_section: dict, data: Any) -> Optional[str]:
    schema_format = schema_section.get("format")
    if schema_format == "uuid4":
        try:
            result = UUID(data, version=4)
            if not str(result) == str(data):
                return f"Expected uuid4, but received {data}"
        except ValueError:
            return f"Expected uuid4, but received {data}"
    return None
```

### field_key_map

You can pass an optional dictionary that maps custom url parameter names into values, for situations where this cannot be
inferred by the DRF `EndpointEnumerator`. A concrete use case for this option is when
the [django i18n locale prefixes](https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#language-prefix-in-url-patterns).

```python
from openapi_tester import SchemaTester

schema_tester = SchemaTester(field_key_map={
  "language": "en",
})
```

## Schema Validation

When the SchemaTester loads a schema, it parses it using an
[OpenAPI spec validator](https://github.com/p1c2u/openapi-spec-validator). This validates the schema.
In case of issues with the schema itself, the validator will raise the appropriate error.

## Django testing client

The library includes an `OpenAPIClient`, which extends Django REST framework's
[`APIClient` class](https://www.django-rest-framework.org/api-guide/testing/#apiclient).
If you wish to validate each request and response against OpenAPI schema when writing
unit tests - `OpenAPIClient` is what you need!

To use `OpenAPIClient` simply pass `SchemaTester` instance that should be used
to validate requests and responses and then use it like regular Django testing client:

```python
schema_tester = SchemaTester()
client = OpenAPIClient(schema_tester=schema_tester)
response = client.get('/api/v1/tests/123/')
```

To force all developers working on the project to use `OpenAPIClient` simply
override the `client` fixture (when using `pytest` with `pytest-django`):

```python
from pytest_django.lazy_django import skip_if_no_django

from openapi_tester.schema_tester import SchemaTester


@pytest.fixture
def schema_tester():
    return SchemaTester()


@pytest.fixture
def client(schema_tester):
    skip_if_no_django()

    from openapi_tester.clients import OpenAPIClient

    return OpenAPIClient(schema_tester=schema_tester)
```

If you are using plain Django test framework, we suggest to create custom
test case implementation and use it instead of original Django one:

```python
import functools

from django.test.testcases import SimpleTestCase
from openapi_tester.clients import OpenAPIClient
from openapi_tester.schema_tester import SchemaTester

schema_tester = SchemaTester()


class MySimpleTestCase(SimpleTestCase):
    client_class = OpenAPIClient
    # or use `functools.partial` when you want to provide custom
    # ``SchemaTester`` instance:
    # client_class = functools.partial(OpenAPIClient, schema_tester=schema_tester)
```

This will ensure you all newly implemented views will be validated against
the OpenAPI schema.

> It is worth noting that for the case of clients the request validation is only performed for **successful** response scenarios. This is to avoid having the package interfering with your functional negative test case suite.
> You can still use `schema_tester.validate_request` method separately for the negative cases in which you would like to validate the request as well.


### Django Ninja Test Client

In case you are using `Django Ninja` and its corresponding [test client](https://github.com/vitalik/django-ninja/blob/master/ninja/testing/client.py#L159), you can use the `OpenAPINinjaClient`, which extends from it, in the same way as the `OpenAPIClient`:

```python
schema_tester = SchemaTester()
client = OpenAPINinjaClient(
        router_or_app=router,
        schema_tester=schema_tester,
    )
response = client.get('/api/v1/tests/123/')
```

Given that the Django Ninja test client works separately from the django url resolver, you can pass the `path_prefix` argument to the `OpenAPINinjaClient` to specify the prefix of the path that should be used to look into the OpenAPI schema.

```python
client = OpenAPINinjaClient(
        router_or_app=router,
        path_prefix='/api/v1',
        schema_tester=schema_tester,
    )
```

## Known Issues

* We are using [prance](https://github.com/jfinkhaeuser/prance) as a schema resolver, and it has some issues with the
  resolution of (very) complex OpenAPI 2.0 schemas.

## Contributing

Contributions are welcome. Please see the [contributing guide](https://github.com/maticardenas/django-contract-tester/blob/master/CONTRIBUTING.md)
