import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agent.regenerate_code import route_code_recovery


pytestmark = pytest.mark.anyio


def test_route_code_recovery_ends_on_success() -> None:
    assert route_code_recovery({"sandbox_error": "No error"}) == "__end__"


def test_route_code_recovery_uses_direct_repairs_before_simplifying() -> None:
    assert route_code_recovery({"sandbox_error": "boom", "render_failures": 1}) == "correct_code"
    assert route_code_recovery({"sandbox_error": "boom", "render_failures": 2}) == "correct_code"


def test_route_code_recovery_switches_to_simplify_after_three_failures() -> None:
    assert route_code_recovery(
        {"sandbox_error": "still failing", "render_failures": 3, "simplification_attempted": False}
    ) == "simplify_code"


def test_route_code_recovery_stops_after_max_failures() -> None:
    assert route_code_recovery(
        {"sandbox_error": "still failing", "render_failures": 5, "simplification_attempted": True}
    ) == "__end__"
