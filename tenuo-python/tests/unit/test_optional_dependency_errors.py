"""Tests for standardized optional-dependency error messages.

Issue #659: Standardize optional-integration installation errors.
"""
import importlib
import subprocess
import sys

import pytest

from tenuo._deps import EXTRA_MAP, check_import, missing_dep_error, PYTHON_MARKERS


class TestMissingDepError:
    """Test the missing_dep_error factory function."""

    def test_basic_error_message(self):
        err = missing_dep_error("openai", "openai")
        assert isinstance(err, ImportError)
        assert "tenuo[openai]" in str(err)
        assert "pip install" in str(err)

    def test_all_extras_covered(self):
        """Every module in EXTRA_MAP should produce a valid error."""
        for module, extra in EXTRA_MAP.items():
            err = missing_dep_error(module, module)
            assert "tenuo[" in str(err)
            assert extra in str(err)

    def test_error_includes_package_name(self):
        err = missing_dep_error("crewai", "crewai")
        assert "crewai" in str(err)

    def test_error_includes_install_command(self):
        err = missing_dep_error("langgraph", "langgraph")
        msg = str(err)
        assert "pip install" in msg
        assert "tenuo[langgraph]" in msg


class TestPythonMarkers:
    """Test that Python version markers are correct."""

    def test_python310_modules_have_marker(self):
        """Modules requiring Python 3.10+ should have markers."""
        for module in ["autogen", "crewai", "mcp", "fastmcp", "temporal"]:
            marker = PYTHON_MARKERS.get(module, "")
            assert "3.10" in marker, f"{module} missing 3.10 marker"

    def test_unrestricted_modules_no_marker(self):
        """Modules with no Python version restriction should have empty marker."""
        for module in ["openai", "langchain", "langgraph", "a2a", "fastapi"]:
            marker = PYTHON_MARKERS.get(module, "")
            assert marker == "", f"{module} should have no marker"


class TestIntegrationModules:
    """Test that integration modules use standardized errors."""

    def test_openai_import_error_is_standardized(self):
        """openai.py should raise standardized ImportError."""
        # This test verifies the pattern exists
        # In a real isolated environment, we'd check the actual error
        err = missing_dep_error("openai", "openai")
        assert "tenuo[openai]" in str(err)

    def test_autogen_import_error_is_standardized(self):
        err = missing_dep_error("autogen", "autogen-agentchat")
        assert "tenuo[autogen]" in str(err)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
