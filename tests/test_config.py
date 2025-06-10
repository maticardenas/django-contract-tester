from openapi_tester.config import ValidationSettings


def test_default_validation_settings():
    settings = ValidationSettings()
    assert settings.response is True
    assert settings.request is True
    assert settings.types is True
    assert settings.formats is True
    assert settings.query_parameters is True
    assert settings.disabled_types == []
    assert settings.disabled_formats == []
    assert settings.disabled_constraints == []
