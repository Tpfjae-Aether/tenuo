"""Tests for GrantBuilder.tool() / tools() fix (issue #674)."""
import pytest
from unittest.mock import MagicMock, patch
from tenuo import SigningKey, Pattern, Warrant
from tenuo.builder import GrantBuilder


@pytest.fixture
def root_key():
    return SigningKey.generate()


@pytest.fixture
def parent_warrant(root_key):
    """Create a parent warrant with some capabilities."""
    sup = SigningKey.generate()
    with patch('tenuo.builder._delegation_receipts', {}):
        tw = (Warrant.mint_builder()
              .capability("lookup_order", order_id=Pattern("A-*"))
              .tool("search_knowledge_base")
              .holder(sup.public_key)
              .ttl(600)
              .mint(root_key))
    return tw, sup


def test_grant_with_tool_only(parent_warrant):
    """GrantBuilder.tool() alone should produce a valid warrant."""
    tw, sup = parent_warrant
    res = SigningKey.generate()
    
    with patch('tenuo.builder._delegation_receipts', {}):
        child = tw.grant_builder().holder(res.public_key).tool("search_knowledge_base").ttl(120).grant(sup)
    
    assert "search_knowledge_base" in child.capabilities


def test_grant_with_tools_list(parent_warrant):
    """GrantBuilder.tools() should produce a valid warrant."""
    tw, sup = parent_warrant
    res = SigningKey.generate()
    
    with patch('tenuo.builder._delegation_receipts', {}):
        child = tw.grant_builder().holder(res.public_key).tools(["lookup_order", "search_knowledge_base"]).ttl(120).grant(sup)
    
    assert "lookup_order" in child.capabilities
    assert "search_knowledge_base" in child.capabilities


def test_grant_with_capability(parent_warrant):
    """GrantBuilder.capability() should still work."""
    tw, sup = parent_warrant
    res = SigningKey.generate()
    
    with patch('tenuo.builder._delegation_receipts', {}):
        child = tw.grant_builder().holder(res.public_key).capability("lookup_order", order_id=Pattern("A-*")).ttl(120).grant(sup)
    
    assert "lookup_order" in child.capabilities


if __name__ == "__main__":
    test_grant_with_tool_only(parent_warrant(SigningKey.generate()))
    test_grant_with_tools_list(parent_warrant(SigningKey.generate()))
    test_grant_with_capability(parent_warrant(SigningKey.generate()))
    print("All tests passed!")
