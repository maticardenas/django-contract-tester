"""
Configuration module for schema section test.
"""

import configparser
import pathlib
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

import toml


@dataclass
class ValidationSettings:
    """Specific settings for controlling validation behavior."""

    # pylint: disable=too-many-instance-attributes
    # Eight is reasonable in this case as has the required configuration options
    request: bool = True
    request_for_non_successful_responses: bool = False
    response: bool = True
    types: bool = True
    formats: bool = True
    query_parameters: bool = True
    disabled_types: List[str] = field(default_factory=list)
    disabled_formats: List[str] = field(default_factory=list)
    disabled_constraints: List[str] = field(default_factory=list)


@dataclass
class OpenAPITestConfig:
    """Configuration dataclass for schema section test."""

    case_tester: Optional[Callable[[str], None]] = None
    ignore_case: Optional[List[str]] = None
    validators: Any = None
    reference: str = "root"
    http_message: str = "response"
    validation: ValidationSettings = field(default_factory=ValidationSettings)


DEFAULT_CONFIG = OpenAPITestConfig()


def _parse_list_value(value: str) -> List[str]:
    """
    Parse a comma-separated string into a list of strings.
    Handles both single-line and multi-line formats.

    Examples:
        "item1, item2, item3" -> ["item1", "item2", "item3"]
        "item1,item2,item3" -> ["item1", "item2", "item3"]
    """
    if not value or not value.strip():
        return []
    # Split by comma and strip whitespace from each item
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool_value(value: str) -> bool:
    """Parse a string boolean value."""
    return value.lower() in ("true", "1", "yes", "on")


def load_config_from_ini_file(
    config_path: Optional[pathlib.Path] = None,
) -> OpenAPITestConfig:
    """
    Loads configuration from .django-contract-tester INI file.

    Expected format:
        [django-contract-tester]
        ignore_case = ID, API, URL

        [django-contract-tester:validation]
        request = true
        response = true
        types = true
        formats = true
        query_parameters = true
        request_for_non_successful_responses = false
        disabled_types = array
        disabled_formats = date-time, email
        disabled_constraints = enum, pattern, minLength

    Args:
        config_path: Optional path to a .django-contract-tester file. If not provided,
                     searches from the current working directory upwards.

    Returns:
        OpenAPITestConfig instance with loaded settings or DEFAULT_CONFIG if not found.
    """
    ini_path: Optional[pathlib.Path] = None

    if config_path is not None:
        # Use the provided path directly
        if config_path.exists():
            ini_path = config_path
    else:
        # Search from current working directory upwards
        cwd = pathlib.Path.cwd()
        for path in [cwd] + list(cwd.parents):
            potential_path = path / ".django-contract-tester"
            if potential_path.exists():
                ini_path = potential_path
                break

    if not ini_path:
        return DEFAULT_CONFIG

    try:
        config = configparser.ConfigParser()
        config.read(ini_path)

        # Main section
        main_section = "django-contract-tester"
        validation_section = "django-contract-tester:validation"

        # Parse ignore_case
        ignore_case_value = None
        if config.has_option(main_section, "ignore_case"):
            ignore_case_str = config.get(main_section, "ignore_case")
            ignore_case_value = _parse_list_value(ignore_case_str)

        # Parse validation settings
        validation_data: dict[str, bool | List[str]] = {}
        if config.has_section(validation_section):
            for option in config.options(validation_section):
                value = config.get(validation_section, option)

                # Boolean options
                if option in (
                    "request",
                    "response",
                    "types",
                    "formats",
                    "query_parameters",
                    "request_for_non_successful_responses",
                ):
                    validation_data[option] = _parse_bool_value(value)
                # List options
                elif option in (
                    "disabled_types",
                    "disabled_formats",
                    "disabled_constraints",
                ):
                    validation_data[option] = _parse_list_value(value)

        # Build ValidationSettings with proper type casting
        def get_bool(key: str, default: bool) -> bool:
            val = validation_data.get(key, default)
            return val if isinstance(val, bool) else default

        def get_list(key: str) -> List[str]:
            val = validation_data.get(key, [])
            return val if isinstance(val, list) else []

        current_validation_settings = ValidationSettings(
            request=get_bool("request", True),
            request_for_non_successful_responses=get_bool(
                "request_for_non_successful_responses", False
            ),
            response=get_bool("response", True),
            types=get_bool("types", True),
            formats=get_bool("formats", True),
            query_parameters=get_bool("query_parameters", True),
            disabled_types=get_list("disabled_types"),
            disabled_formats=get_list("disabled_formats"),
            disabled_constraints=get_list("disabled_constraints"),
        )

        return OpenAPITestConfig(
            case_tester=DEFAULT_CONFIG.case_tester,
            ignore_case=ignore_case_value
            if ignore_case_value is not None
            else DEFAULT_CONFIG.ignore_case,
            validators=DEFAULT_CONFIG.validators,
            reference=DEFAULT_CONFIG.reference,
            http_message=DEFAULT_CONFIG.http_message,
            validation=current_validation_settings,
        )
    except (configparser.Error, ValueError):
        return DEFAULT_CONFIG


def load_config_from_pyproject_toml(
    config_path: Optional[pathlib.Path] = None,
) -> OpenAPITestConfig:
    """
    Loads configuration from pyproject.toml.
    Top-level settings under [tool.django-contract-tester].
    Validation behavior settings under [tool.django-contract-tester.validation].
    Returns an OpenAPITestConfig instance.
    Falls back to default values if pyproject.toml is not found or sections are missing.

    Args:
        config_path: Optional path to a pyproject.toml file. If not provided,
                     searches from the current working directory upwards.
    """
    pyproject_path: Optional[pathlib.Path] = None

    if config_path is not None:
        # Use the provided path directly
        if config_path.exists():
            pyproject_path = config_path
    else:
        # Search from current working directory upwards
        cwd = pathlib.Path.cwd()
        for path in [cwd] + list(cwd.parents):
            potential_path = path / "pyproject.toml"
            if potential_path.exists():
                pyproject_path = potential_path
                break

    if not pyproject_path:
        return DEFAULT_CONFIG

    try:
        data = toml.load(pyproject_path)
        tool_config = data.get("tool", {}).get("django-contract-tester", {})

        if not tool_config:
            return DEFAULT_CONFIG

        ignore_case_from_toml = tool_config.get("ignore_case")
        if ignore_case_from_toml is not None and not isinstance(
            ignore_case_from_toml, list
        ):
            ignore_case_from_toml = DEFAULT_CONFIG.ignore_case

        validation_data = tool_config.get("validation", {})

        disabled_types_from_toml = validation_data.get("disabled_types")
        if disabled_types_from_toml is not None and not isinstance(
            disabled_types_from_toml, list
        ):
            disabled_types_from_toml = []

        disabled_formats_from_toml = validation_data.get("disabled_formats")
        if disabled_formats_from_toml is not None and not isinstance(
            disabled_formats_from_toml, list
        ):
            disabled_formats_from_toml = []

        disabled_constraints_from_toml = validation_data.get("disabled_constraints")
        if disabled_constraints_from_toml is not None and not isinstance(
            disabled_constraints_from_toml, list
        ):
            disabled_constraints_from_toml = []

        current_validation_settings = ValidationSettings(
            request=validation_data.get("request", True),
            request_for_non_successful_responses=validation_data.get(
                "request_for_non_successful_responses", False
            ),
            response=validation_data.get("response", True),
            types=validation_data.get("types", True),
            formats=validation_data.get("formats", True),
            query_parameters=validation_data.get("query_parameters", True),
            disabled_types=disabled_types_from_toml
            if disabled_types_from_toml is not None
            else [],
            disabled_formats=disabled_formats_from_toml
            if disabled_formats_from_toml is not None
            else [],
            disabled_constraints=disabled_constraints_from_toml
            if disabled_constraints_from_toml is not None
            else [],
        )

        return OpenAPITestConfig(
            case_tester=DEFAULT_CONFIG.case_tester,
            ignore_case=ignore_case_from_toml
            if ignore_case_from_toml is not None
            else DEFAULT_CONFIG.ignore_case,
            validators=DEFAULT_CONFIG.validators,
            reference=tool_config.get("reference", DEFAULT_CONFIG.reference),
            http_message=tool_config.get("http_message", DEFAULT_CONFIG.http_message),
            validation=current_validation_settings,
        )
    except toml.TomlDecodeError:
        return DEFAULT_CONFIG


def load_config() -> OpenAPITestConfig:
    """
    Loads configuration from available sources.
    Priority order (first found wins):
    1. .django-contract-tester (INI file)
    2. pyproject.toml
    3. DEFAULT_CONFIG

    Returns:
        OpenAPITestConfig instance with loaded settings.
    """
    # Try .django-contract-tester first
    ini_config = load_config_from_ini_file()
    if ini_config != DEFAULT_CONFIG:
        return ini_config

    # Fall back to pyproject.toml
    toml_config = load_config_from_pyproject_toml()
    if toml_config != DEFAULT_CONFIG:
        return toml_config

    # Return defaults if nothing found
    return DEFAULT_CONFIG


settings = load_config()
