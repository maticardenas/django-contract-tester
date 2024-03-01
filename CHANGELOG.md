# Changelog

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
