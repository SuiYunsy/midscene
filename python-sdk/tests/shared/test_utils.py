"""Tests for utility functions."""

import pytest

from midscene.shared.utils import (
    uuid,
    generate_hash_id,
    assert_condition,
    escape_script_tag,
    anti_escape_script_tag,
    replace_illegal_path_chars_and_space,
)


def test_uuid_generates_valid_uuid():
    """Test that uuid generates a valid UUID string."""
    result = uuid()
    assert isinstance(result, str)
    assert len(result) == 36  # Standard UUID length with hyphens
    assert result.count("-") == 4


def test_generate_hash_id_returns_string():
    """Test that generate_hash_id returns a string."""
    result = generate_hash_id({"x": 10, "y": 20}, "test content")
    assert isinstance(result, str)
    assert len(result) >= 5


def test_generate_hash_id_same_input_same_output():
    """Test that same input produces same output."""
    rect = {"x": 10, "y": 20}
    content = "test"
    result1 = generate_hash_id(rect, content)
    result2 = generate_hash_id(rect, content)
    assert result1 == result2


def test_assert_condition_passes_on_truthy():
    """Test that assert_condition passes on truthy values."""
    assert_condition(True)
    assert_condition(1)
    assert_condition("string")
    assert_condition([1])


def test_assert_condition_raises_on_falsy():
    """Test that assert_condition raises on falsy values."""
    with pytest.raises(AssertionError, match="Assertion failed"):
        assert_condition(False)
    
    with pytest.raises(AssertionError, match="Custom message"):
        assert_condition(None, "Custom message")


def test_escape_script_tag():
    """Test HTML escaping."""
    html = "<script>alert('xss')</script>"
    escaped = escape_script_tag(html)
    assert "<" not in escaped
    assert ">" not in escaped


def test_anti_escape_script_tag():
    """Test HTML unescaping."""
    escaped = "__midscene_lt__script__midscene_gt__"
    unescaped = anti_escape_script_tag(escaped)
    assert "<script>" in unescaped


def test_replace_illegal_path_chars():
    """Test path character replacement."""
    path = "file:name*with?illegal<chars>"
    result = replace_illegal_path_chars_and_space(path)
    assert ":" not in result
    assert "*" not in result
    assert "?" not in result
    assert "<" not in result
    assert ">" not in result
