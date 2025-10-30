import pathlib

from openapi_tester.config import (
    DEFAULT_CONFIG,
    OpenAPITestConfig,
    ValidationSettings,
    load_config_from_ini_file,
    load_config_from_pyproject_toml,
)


def test_default_validation_settings():
    settings = ValidationSettings()
    assert settings.response is True
    assert settings.request is True
    assert settings.request_for_non_successful_responses is False
    assert settings.types is True
    assert settings.formats is True
    assert settings.query_parameters is True
    assert settings.disabled_types == []
    assert settings.disabled_formats == []
    assert settings.disabled_constraints == []


def test_load_config_from_pyproject_toml_with_valid_config():
    """Test loading a valid configuration from pyproject.toml."""
    config_path = pathlib.Path("tests/data/config/pyproject.toml")
    config = load_config_from_pyproject_toml(config_path=config_path)

    # Check top-level settings
    assert config.ignore_case == ["name", "color", "height", "width", "length"]

    # Check validation settings
    assert config.validation.request is False
    assert config.validation.request_for_non_successful_responses is False
    assert config.validation.response is True
    assert config.validation.types is True
    assert config.validation.formats is True
    assert config.validation.query_parameters is True
    assert config.validation.disabled_types == ["integer", "array"]
    assert config.validation.disabled_formats == ["date-time", "email"]
    assert config.validation.disabled_constraints == [
        "enum",
        "pattern",
        "minLength",
        "maxLength",
        "minimum",
        "maximum",
        "multipleOf",
        "uniqueItems",
        "minItems",
        "maxItems",
        "minProperties",
        "maxProperties",
    ]


def test_load_config_from_pyproject_toml_with_nonexistent_file():
    """Test that nonexistent config file returns default config."""
    config_path = pathlib.Path("tests/data/config/nonexistent.toml")
    config = load_config_from_pyproject_toml(config_path=config_path)

    # Should return default config
    assert config.ignore_case == DEFAULT_CONFIG.ignore_case
    assert config.validation.request is True
    assert config.validation.request_for_non_successful_responses is False
    assert config.validation.response is True
    assert config.validation.types is True
    assert config.validation.formats is True
    assert config.validation.query_parameters is True
    assert config.validation.disabled_types == []
    assert config.validation.disabled_formats == []
    assert config.validation.disabled_constraints == []


def test_load_config_from_pyproject_toml_without_path_parameter():
    """Test that function works without config_path parameter (searches from cwd)."""
    # This should search from current working directory upwards
    # and should find the project's root pyproject.toml
    config = load_config_from_pyproject_toml()

    # Should be an OpenAPITestConfig instance
    assert isinstance(config, OpenAPITestConfig)
    # The function should at least return something (default or loaded)
    assert config.validation is not None


def test_config_fixture_integration(custom_test_config):
    """Test that the custom_test_config fixture properly patches settings."""
    from openapi_tester.validators import settings as validator_settings

    # Verify that the patched settings match our test config
    assert validator_settings.validation.disabled_types == ["integer", "array"]
    assert validator_settings.validation.disabled_formats == ["date-time", "email"]
    assert validator_settings.ignore_case == [
        "name",
        "color",
        "height",
        "width",
        "length",
    ]

    # Verify it's the same instance
    assert validator_settings == custom_test_config


def test_load_config_from_pyproject_toml_with_wrong_configs():
    """Test that function works with wrong configs."""
    config_path = pathlib.Path("tests/data/config/pyproject_wrong_configs.toml")
    config = load_config_from_pyproject_toml(config_path=config_path)

    assert config.validation.disabled_types == []
    assert config.validation.disabled_formats == []
    assert config.validation.disabled_constraints == []


def test_load_config_from_pyproject_toml_with_wrong_formatted_configs():
    """Test that function works with wrong formatted configs."""
    config_path = pathlib.Path("tests/data/config/wrong_pyproject.toml")
    config = load_config_from_pyproject_toml(config_path=config_path)

    assert config.validation.disabled_types == []
    assert config.validation.disabled_formats == []
    assert config.validation.disabled_constraints == []


def test_load_config_from_pyproject_toml_with_no_response_validation():
    """Test that function works with no response validation."""
    config_path = pathlib.Path(
        "tests/data/config/pyproject_no_response_validation.toml"
    )
    config = load_config_from_pyproject_toml(config_path=config_path)

    assert config.validation.response is False
    assert config.validation.request_for_non_successful_responses is False
    assert config.validation.types is False
    assert config.validation.formats is False
    assert config.validation.query_parameters is False


def test_load_config_from_ini_file_with_valid_config():
    config_path = pathlib.Path("tests/data/config/.django-contract-tester")
    config = load_config_from_ini_file(config_path=config_path)

    assert config.ignore_case == ["name", "color", "height", "width", "length"]

    assert config.validation.request is False
    assert config.validation.request_for_non_successful_responses is False
    assert config.validation.response is True
    assert config.validation.types is True
    assert config.validation.formats is True
    assert config.validation.query_parameters is True
    assert config.validation.disabled_types == ["integer", "array"]
    assert config.validation.disabled_formats == ["date-time", "email"]
    assert config.validation.disabled_constraints == [
        "enum",
        "pattern",
        "minLength",
        "maxLength",
        "minimum",
        "maximum",
        "multipleOf",
        "uniqueItems",
        "minItems",
        "maxItems",
        "minProperties",
        "maxProperties",
    ]


def test_load_config_from_ini_file_with_nonexistent_file():
    config_path = pathlib.Path("tests/data/config/.nonexistent-ini")
    config = load_config_from_ini_file(config_path=config_path)

    assert config.ignore_case == DEFAULT_CONFIG.ignore_case
    assert config.validation.request is True
    assert config.validation.request_for_non_successful_responses is False
    assert config.validation.response is True
    assert config.validation.types is True
    assert config.validation.formats is True
    assert config.validation.query_parameters is True
    assert config.validation.disabled_types == []
    assert config.validation.disabled_formats == []
    assert config.validation.disabled_constraints == []


def test_load_config_from_ini_file_without_path_parameter():
    config = load_config_from_ini_file()
    assert isinstance(config, OpenAPITestConfig)
    assert config.validation is not None


def test_load_config_from_ini_file_with_no_response_validation():
    config_path = pathlib.Path("tests/data/config/.django-contract-tester-no-response")
    config = load_config_from_ini_file(config_path=config_path)

    assert config.validation.response is False
    assert config.validation.request_for_non_successful_responses is False
    assert config.validation.types is False
    assert config.validation.formats is False
    assert config.validation.query_parameters is False


def test_load_config_from_ini_file_with_wrong_configs():
    config_path = pathlib.Path("tests/data/config/.django-contract-tester-wrong")
    config = load_config_from_ini_file(config_path=config_path)

    assert config.validation.disabled_types == ["not_a_list_but_string"]
    assert config.validation.disabled_formats == ["12345"]
