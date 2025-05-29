"""
Configuration module for schema section test.
"""

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


def load_config_from_pyproject_toml() -> OpenAPITestConfig:
    """
    Loads configuration from pyproject.toml.
    Top-level settings under [tool.django-contract-tester].
    Validation behavior settings under [tool.django-contract-tester.validation].
    Returns an OpenAPITestConfig instance.
    Falls back to default values if pyproject.toml is not found or sections are missing.
    """
    cwd = pathlib.Path.cwd()
    pyproject_path: Optional[pathlib.Path] = None

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


settings = load_config_from_pyproject_toml()
