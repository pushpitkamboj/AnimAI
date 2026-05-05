import sys
from pathlib import Path

from langgraph.pregel import Pregel


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agent.graph import workflow_app


def test_graph_compiles() -> None:
    assert isinstance(workflow_app, Pregel)
