"""Tests for types module."""

import pytest

from midscene.core.types import (
    AgentOpt,
    LocateOption,
    PlanningAction,
    ServiceExtractOption,
)


def test_agent_opt_defaults():
    """Test AgentOpt default values."""
    opts = AgentOpt()
    assert opts.group_name == "Midscene Report"
    assert opts.generate_report is True
    assert opts.auto_print_report_msg is True


def test_locate_option_defaults():
    """Test LocateOption default values."""
    opt = LocateOption()
    assert opt.deep_think is False
    assert opt.timeout_ms is None


def test_planning_action():
    """Test PlanningAction creation."""
    action = PlanningAction(
        type="Tap",
        param={"locate": {"prompt": "click button"}},
        thought="Need to click the button"
    )
    assert action.type == "Tap"
    assert action.param["locate"]["prompt"] == "click button"
    assert action.thought == "Need to click the button"


def test_service_extract_option_defaults():
    """Test ServiceExtractOption default values."""
    opt = ServiceExtractOption()
    assert opt.dom_included is False
    assert opt.screenshot_included is True
