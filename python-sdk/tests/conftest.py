"""Pytest configuration for Midscene tests."""

import pytest


@pytest.fixture
def sample_screenshot_base64():
    """A minimal valid PNG image as base64 for testing."""
    # 1x1 transparent PNG
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
