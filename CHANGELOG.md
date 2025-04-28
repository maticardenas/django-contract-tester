# Changelog

## 1.5.3 2025-04-28

* Adding `int32` and `int64` format validation support for `integer` values.
* Adding `null` type (OpenAPI `3.1.x`) validation support.

## v1.5.2 2024-12-12

* Improving response handlers creation, by checking supported frameworks and ensuring failure in case response type is not handled.
* Remove unnecessary log entry at `clients` module when `django-ninja` is not installed.

## v1.5.0 2024-10-19

* Adding `readOnly` properties validation for requests.

## v1.4.0 2024-06-10

* Adding support for Django Ninja test client.

## v1.3.2 2024-05-07

* Fixing serialization for date values.
* Adding support for validation of string type schemas with numerical values.
* Refactor tests and serialization.

## v1.3.1 2024-04-04

* Adding support for `Django 5.0` (it was limited at the dependency configuration)
* Improving error messages.
* Serializing `json` requests data when `application/json` header is passed.
* Replacing black and isort linters with `ruff` (https://github.com/astral-sh/ruff)

## v1.2.0 2024-03-01

* Adding support for Django Ninja.
* Allowing to use `OpenAPIClient` against `Django Ninja` API endpoints, handling `HttpResponse` objects for `OpenAPI` validation.
* Adding small `Django Ninja` test project.

## v1.1.0 2024-02-29

* Update `openapi-spec-validator` to lastest version.
* Fix deprecated imports and libraries used.
* Drop python 3.7 support as minimum support from `openapi-spec-validator` is now `3.8`.

## v1.0.0 2024-02-29

* Package refactored and renamed from `drf-contract-tester` to `django-contract-tester`
* Added support for validating request payloads
