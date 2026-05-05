import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import agent.research_topic as research_module


class _FakeStructuredLLM:
    def __init__(self, response):
        self.response = response
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return self.response


class _FakeLLM:
    def __init__(self, response):
        self.structured = _FakeStructuredLLM(response)

    def with_structured_output(self, schema):
        return self.structured


def test_build_search_queries_trims_and_limits_results(monkeypatch) -> None:
    fake_llm = _FakeLLM(
        {"queries": [" nasa apollo 11 timeline ", "", "apollo 11 trajectory", "moon landing press kit", "extra"]}
    )
    monkeypatch.setattr(research_module, "llm", fake_llm)

    queries = research_module._build_search_queries(
        "Explain Apollo 11",
        {
            "route": "named_real_world_event",
            "needs_external_grounding": True,
            "named_entities": ["Apollo 11"],
            "time_sensitive": False,
            "domain": "space",
            "ambiguity_notes": [],
        },
    )

    assert queries == [
        "nasa apollo 11 timeline",
        "apollo 11 trajectory",
        "moon landing press kit",
        "extra",
    ]


def test_build_search_queries_falls_back_to_prompt_and_entities(monkeypatch) -> None:
    fake_llm = _FakeLLM({"queries": ["", "   "]})
    monkeypatch.setattr(research_module, "llm", fake_llm)

    queries = research_module._build_search_queries(
        "Explain methane combustion",
        {
            "route": "reaction_or_pathway",
            "needs_external_grounding": True,
            "named_entities": ["methane"],
            "time_sensitive": False,
            "domain": "chemistry",
            "ambiguity_notes": [],
        },
    )

    assert queries == ["Explain methane combustion methane"]
