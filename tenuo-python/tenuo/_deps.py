"""Standardized optional-dependency error messages for Tenuo integrations.

Port of the Tenuo 0.3.0 DX improvement (#659): every missing-dependency
error now points to the correct ``tenuo[<extra>]`` installation command.
"""
from __future__ import annotations

from typing import Optional

# Map module names to their pyproject.toml extras
EXTRA_MAP = {
    "openai": "openai",
    "autogen": "autogen",
    "langchain": "langchain",
    "langgraph": "langgraph",
    "crewai": "crewai",
    "google_adk": "google_adk",
    "a2a": "a2a",
    "mcp": "mcp",
    "fastmcp": "fastmcp",
    "fastapi": "fastapi",
    "temporal": "temporal",
}

# Python version markers from pyproject.toml
PYTHON_MARKERS = {
    "autogen": "; python_version >= '3.10'",
    "crewai": "; python_version >= '3.10'",
    "mcp": "; python_version >= '3.10'",
    "fastmcp": "; python_version >= '3.10'",
    "google_adk": "",
    "openai": "",
    "langchain": "",
    "langgraph": "",
    "a2a": "",
    "fastapi": "",
    "temporal": "; python_version >= '3.10'",
}


def missing_dep_error(
    module: str,
    package: str,
    extra: Optional[str] = None,
) -> ImportError:
    """Build a standardized missing-dependency error.

    Args:
        module: The Tenuo integration module name (e.g. "openai", "crewai")
        package: The PyPI package that's missing (e.g. "openai", "crewai")
        extra: Override the extras name (defaults to module name)

    Returns:
        ImportError with a clear installation instruction
    """
    extra_name = extra or EXTRA_MAP.get(module, module)
    marker = PYTHON_MARKERS.get(module, "")
    return ImportError(
        f"The '{package}' package is required for tenuo[{extra_name}] "
        f"but is not installed.\n\n"
        f"Install it with:\n"
        f'    pip install "tenuo[{extra_name}]"\n\n'
        f"Or install directly:\n"
        f"    pip install {package}{marker}"
    )


def check_import(module: str, package: str) -> None:
    """Raise standardized error if package is not importable.

    Args:
        module: Tenuo integration module name
        package: PyPI package name to attempt import

    Raises:
        ImportError: If package is not importable
    """
    try:
        __import__(package)
    except ImportError:
        raise missing_dep_error(module, package) from None
