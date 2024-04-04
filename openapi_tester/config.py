"""
Configuration module for schema section test.
"""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional


@dataclass
class OpenAPITestConfig:
    """Configuration dataclass for schema section test."""

    case_tester: Optional[Callable[[str], None]] = None
    ignore_case: Optional[List[str]] = None
    validators: Any = None
    reference: str = "root"
    http_message: str = "response"
