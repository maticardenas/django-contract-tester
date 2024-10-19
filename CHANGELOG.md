# Changelog

## v1.5.0 2024-10-19

* Adding `readOnly` properties validation for requests.

## v1.4.0 2024-06-10

* Adding support for Django Ninja test client.

## v1.3.2 2024-05-07

* Fixing serialization for date values.
* Adding support for validation of string type schemas with numerical values.
* Refactor tests and serialization.

## v1.3.1 2024-04-04

* Adding support for Django 5.0 (it was limited at the dependency configuration)
* Improving error messages.
* Serializing json requests data when application/json header is passed.
* Replacing black and isort linters with ruff (https://github.com/astral-sh/ruff)

## v1.2.0 2024-03-01

* Adding support for Django Ninja.
* Allowing to use OpenAPIClient against Django Ninja API endpoints, handling HttpResponse objects for OpenAPI validation.
* Adding small Django Ninja test project.

## v1.1.0 2024-02-29

* Update openapi-spec-validator to lastest version.
* Fix deprecated imports and libraries used.
* Drop python 3.7 support as minimum support from openapi-spec-validator is now 3.8.

## v1.0.0 2024-02-29

* Package refactored and renamed from `drf-contract-tester` to `django-contract-tester`
* Added support for validating request payloads
