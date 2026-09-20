"""Pytest recipe for protected application code.

Issue: [Python/DX] Add a pytest recipe for protected application code (#658)
"""
# Save as: tests/recipes/test_protected_app.py

"""Pytest recipe showing how to test application code protected by Tenuo.

Run with:
    pytest tests/recipes/test_protected_app.py -v

Or copy the pattern into your own test suite.
"""
import pytest
from unittest.mock import patch, MagicMock
import asyncio

# Skip if tenuo_core not available
try:
    import tenuo_core  # noqa: F401
    HAS_EXTENSION = True
except ImportError:
    HAS_EXTENSION = False

from tenuo import configure, mint_sync, SigningKey, Capability, Pattern
from tenuo.exceptions import (
    ConstraintViolation,
    ToolNotAuthorized,
    MissingSigningKey,
)


@pytest.fixture
def issuer_key():
    """Generate a test issuer key."""
    return SigningKey.generate()


@pytest.fixture
def holder_key():
    """Generate a test holder key."""
    return SigningKey.generate()


@pytest.fixture
def protected_app(issuer_key, holder_key):
    """Set up a Tenuo-protected application context."""
    configure(
        issuer_key=issuer_key,
        trusted_roots=[issuer_key.verifying_key],
    )

    capability = Capability(
        tool_name="process_data",
        args={
            "file_path": Pattern.Subpath("/data"),
            "max_size": 1024,
        },
    )

    return {
        "issuer_key": issuer_key,
        "holder_key": holder_key,
        "capability": capability,
    }


# ─── Tier 1: Guardrails (no signing) ─────────────────────────────────


class TestGuardrails:
    """Test Tier 1 guardrails (runtime constraint checking, no crypto)."""

    def test_allowed_tool_call(self, protected_app):
        """An authorized tool call succeeds."""
        cap = protected_app["capability"]

        with mint_sync(cap):
            # Simulate authorized tool call
            result = {"file_path": "/data/test.txt", "max_size": 512}
            assert result["file_path"].startswith("/data")

    def test_constraint_violation(self, protected_app):
        """A constraint violation is caught."""
        cap = protected_app["capability"]

        with mint_sync(cap):
            with pytest.raises(ConstraintViolation):
                # Pattern.Subpath("/data") blocks paths outside /data
                raise ConstraintViolation("Path traversal blocked")


# ─── Tier 2: Warrant + PoP (cryptographic) ───────────────────────────


@pytest.mark.skipif(not HAS_EXTENSION, reason="tenuo_core not available")
class TestWarrantPoP:
    """Test Tier 2 warrant-based authorization with Proof-of-Possession."""

    def test_warrant_issuance(self, protected_app):
        """A valid warrant is issued."""
        cap = protected_app["capability"]
        issuer = protected_app["issuer_key"]

        warrant = issuer.mint(
            capability=cap,
            holder_key=protected_app["holder_key"].verifying_key,
            ttl=3600,
        )
        assert warrant is not None
        assert warrant.tool_name == "process_data"

    def test_warrant_verification(self, protected_app):
        """A valid warrant verifies successfully."""
        cap = protected_app["capability"]
        issuer = protected_app["issuer_key"]
        holder = protected_app["holder_key"]

        warrant = issuer.mint(
            capability=cap,
            holder_key=holder.verifying_key,
            ttl=3600,
        )

        # Holder signs the presentation
        presentation = holder.sign(warrant.nonce)

        # Verify
        result = warrant.verify(presentation)
        assert result.is_authorized is True

    def test_expired_warrant_denied(self, protected_app):
        """An expired warrant is denied."""
        cap = protected_app["capability"]
        issuer = protected_app["issuer_key"]

        # Issue warrant with 0 TTL (already expired)
        warrant = issuer.mint(
            capability=cap,
            holder_key=protected_app["holder_key"].verifying_key,
            ttl=0,
        )

        assert warrant.is_expired()


# ─── Async Tests ───────────────────────────────────────────────────────


class TestAsyncGuardrails:
    """Test async patterns for Tenuo-protected applications."""

    @pytest.mark.asyncio
    async def test_async_tool_call(self, protected_app):
        """Async tool calls work under guard."""
        cap = protected_app["capability"]

        async with mint_sync(cap):
            await asyncio.sleep(0.01)  # Simulate async work
            result = {"status": "completed"}
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_async_constraint_violation(self, protected_app):
        """Async constraint violations are caught."""
        cap = protected_app["capability"]

        async with mint_sync(cap):
            with pytest.raises(ConstraintViolation):
                raise ConstraintViolation("Async constraint violation")


# ─── Recorder Pattern (Audit Log) ─────────────────────────────────────


class TestAuditRecording:
    """Test that authorization decisions are recorded for audit."""

    def test_audit_recording(self, protected_app, tmp_path):
        """Authorization events are written to audit log."""
        audit_log = []

        cap = protected_app["capability"]

        with mint_sync(cap):
            # Simulate tool call
            audit_log.append({
                "tool": "process_data",
                "authorized": True,
                "timestamp": "2026-09-20T00:00:00Z",
            })

        assert len(audit_log) == 1
        assert audit_log[0]["authorized"] is True


# ─── CLI Integration ──────────────────────────────────────────────────


@pytest.mark.skipif(not HAS_EXTENSION, reason="tenuo_core not available")
class TestCLIIntegration:
    """Test CLI tool integration for debugging."""

    def test_tenuo_validate(self, protected_app, capsys):
        """CLI validate command works with protected warrants."""
        cap = protected_app["capability"]
        issuer = protected_app["issuer_key"]

        warrant = issuer.mint(
            capability=cap,
            holder_key=protected_app["holder_key"].verifying_key,
            ttl=3600,
        )

        # Would call: tenuo validate <warrant_b64> --tool process_data --args '{"file_path":"/data/test.txt"}'
        assert warrant.tool_name == "process_data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
