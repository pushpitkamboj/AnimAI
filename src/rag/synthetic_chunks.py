from __future__ import annotations

import re
from pathlib import Path
from typing import Any


LOWERCASE_CORE_SYMBOLS = {"always_redraw"}


CORE_SYMBOL_REGISTRY: dict[str, dict[str, Any]] = {
    "Create": {
        "qualified_name": "manim.animation.creation.Create",
        "module": "manim.animation.creation",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.creation.Create.html",
        "summary": "Incrementally show a VMobject.",
        "category": "animation",
        "import_path": "from manim import Create",
        "patterns": ["introduce_object", "draw_shape"],
        "example_code": "self.play(Create(circle))",
    },
    "Write": {
        "qualified_name": "manim.animation.creation.Write",
        "module": "manim.animation.creation",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.creation.html",
        "summary": "Simulate hand-writing a Text or hand-drawing a VMobject.",
        "category": "animation",
        "import_path": "from manim import Write",
        "patterns": ["write_label", "draw_text"],
        "example_code": 'self.play(Write(Text("Hello")))',
    },
    "FadeIn": {
        "qualified_name": "manim.animation.fading.FadeIn",
        "module": "manim.animation.fading",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.fading.html",
        "summary": "Fade a mobject into view.",
        "category": "animation",
        "import_path": "from manim import FadeIn",
        "patterns": ["soft_reveal", "focus_shift"],
        "example_code": "self.play(FadeIn(label))",
    },
    "FadeOut": {
        "qualified_name": "manim.animation.fading.FadeOut",
        "module": "manim.animation.fading",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.fading.html",
        "summary": "Fade a mobject out of view.",
        "category": "animation",
        "import_path": "from manim import FadeOut",
        "patterns": ["remove_object", "declutter_scene"],
        "example_code": "self.play(FadeOut(label))",
    },
    "Transform": {
        "qualified_name": "manim.animation.transform.Transform",
        "module": "manim.animation.transform",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.transform.Transform.html",
        "summary": "Transform a mobject into a target mobject.",
        "category": "animation",
        "import_path": "from manim import Transform",
        "patterns": ["morph_shape", "state_change"],
        "example_code": "self.play(Transform(source, target))",
    },
    "ReplacementTransform": {
        "qualified_name": "manim.animation.transform.ReplacementTransform",
        "module": "manim.animation.transform",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.transform.html",
        "summary": "Replace one mobject with another while morphing between them.",
        "category": "animation",
        "import_path": "from manim import ReplacementTransform",
        "patterns": ["swap_object", "replace_state"],
        "example_code": "self.play(ReplacementTransform(old_mob, new_mob))",
    },
    "MoveAlongPath": {
        "qualified_name": "manim.animation.movement.MoveAlongPath",
        "module": "manim.animation.movement",
        "source_url": "https://docs.manim.community/en/stable/reference.html",
        "summary": "Move a mobject along a given path.",
        "category": "animation",
        "import_path": "from manim import MoveAlongPath",
        "patterns": ["path_motion", "trajectory"],
        "example_code": "self.play(MoveAlongPath(dot, orbit_path))",
    },
    "AnimationGroup": {
        "qualified_name": "manim.animation.composition.AnimationGroup",
        "module": "manim.animation.composition",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.composition.html",
        "summary": "Play a group or series of animations together.",
        "category": "animation",
        "import_path": "from manim import AnimationGroup",
        "patterns": ["parallel_motion", "coordinated_reveal"],
        "example_code": "self.play(AnimationGroup(Create(a), FadeIn(b), lag_ratio=0.0))",
    },
    "LaggedStart": {
        "qualified_name": "manim.animation.composition.LaggedStart",
        "module": "manim.animation.composition",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.composition.html",
        "summary": "Stagger a series of animations using lag_ratio.",
        "category": "animation",
        "import_path": "from manim import LaggedStart",
        "patterns": ["staggered_reveal", "sequenced_build"],
        "example_code": "self.play(LaggedStart(*animations, lag_ratio=0.15))",
    },
    "Succession": {
        "qualified_name": "manim.animation.composition.Succession",
        "module": "manim.animation.composition",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.composition.html",
        "summary": "Play animations one after another in order.",
        "category": "animation",
        "import_path": "from manim import Succession",
        "patterns": ["sequential_motion", "timeline_build"],
        "example_code": "self.play(Succession(Create(a), Transform(a, b), FadeOut(b)))",
    },
    "Indicate": {
        "qualified_name": "manim.animation.indication.Indicate",
        "module": "manim.animation.indication",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.indication.html",
        "summary": "Draw attention to a mobject.",
        "category": "animation",
        "import_path": "from manim import Indicate",
        "patterns": ["highlight_relation", "focus_attention"],
        "example_code": "self.play(Indicate(term))",
    },
    "Circumscribe": {
        "qualified_name": "manim.animation.indication.Circumscribe",
        "module": "manim.animation.indication",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.indication.html",
        "summary": "Highlight a mobject by drawing around it.",
        "category": "animation",
        "import_path": "from manim import Circumscribe",
        "patterns": ["highlight_boundary", "callout"],
        "example_code": "self.play(Circumscribe(term))",
    },
    "Flash": {
        "qualified_name": "manim.animation.indication.Flash",
        "module": "manim.animation.indication",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.indication.html",
        "summary": "Create a brief flash around a point or mobject.",
        "category": "animation",
        "import_path": "from manim import Flash",
        "patterns": ["pulse_highlight", "attention_signal"],
        "example_code": "self.play(Flash(dot.get_center()))",
    },
    "Text": {
        "qualified_name": "manim.mobject.text.text_mobject.Text",
        "module": "manim.mobject.text.text_mobject",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.text.text_mobject.Text.html",
        "summary": "Render plain text labels for explanations and annotations.",
        "category": "mobject",
        "import_path": "from manim import Text",
        "patterns": ["label", "annotation"],
        "example_code": 'title = Text("Mission Profile").to_edge(UP)',
    },
    "MarkupText": {
        "qualified_name": "manim.mobject.text.text_mobject.MarkupText",
        "module": "manim.mobject.text.text_mobject",
        "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.text.text_mobject.MarkupText.html",
        "summary": "Render styled inline text using Pango markup.",
        "category": "mobject",
        "import_path": "from manim import MarkupText",
        "patterns": ["styled_label", "inline_emphasis"],
        "example_code": 'label = MarkupText("<b>Burn 1</b>").scale(0.7)',
    },
    "TracedPath": {
        "qualified_name": "manim.animation.changing.TracedPath",
        "module": "manim.animation.changing",
        "source_url": "https://docs.manim.community/en/stable/reference.html",
        "summary": "Trace the path of a moving point over time.",
        "category": "mobject",
        "import_path": "from manim import TracedPath",
        "patterns": ["trajectory_trace", "orbit_path"],
        "example_code": "trail = TracedPath(dot.get_center, stroke_color=YELLOW)",
    },
    "always_redraw": {
        "qualified_name": "manim.animation.updaters.mobject_update_utils.always_redraw",
        "module": "manim.animation.updaters.mobject_update_utils",
        "source_url": "https://docs.manim.community/en/stable/reference.html",
        "summary": "Recreate a mobject every frame from a callable for dynamic updates.",
        "category": "updater",
        "import_path": "from manim import always_redraw",
        "patterns": ["dynamic_updaters", "live_geometry"],
        "example_code": "moving_label = always_redraw(lambda: Dot(point_tracker.get_center()))",
    },
    "VoiceoverScene": {
        "qualified_name": "manim_voiceover.VoiceoverScene",
        "module": "manim_voiceover",
        "source_url": "https://voiceover.manim.community/en/stable/quickstart.html",
        "summary": "Scene mixin that adds self.voiceover(...) and speech-service support.",
        "category": "voiceover",
        "import_path": "from manim_voiceover import VoiceoverScene",
        "patterns": ["voiceover_scene", "timed_narration"],
        "example_code": (
            "class MissionScene(VoiceoverScene):\n"
            "    def construct(self):\n"
            "        with self.voiceover(text=\"This circle is drawn as I speak.\") as tracker:\n"
            "            self.play(Create(Circle()), run_time=tracker.duration)"
        ),
    },
    "GTTSService": {
        "qualified_name": "manim_voiceover.services.gtts.GTTSService",
        "module": "manim_voiceover.services.gtts",
        "source_url": "https://voiceover.manim.community/en/stable/quickstart.html",
        "summary": "Speech service wrapper around gTTS for fast cross-platform voiceover generation.",
        "category": "voiceover",
        "import_path": "from manim_voiceover.services.gtts import GTTSService",
        "patterns": ["speech_service", "narration_runtime"],
        "example_code": 'self.set_speech_service(GTTSService(lang="en", tld="com"))',
    },
}


def _build_aliases(symbol: str, qualified_name: str, module_name: str) -> list[str]:
    aliases = {
        symbol,
        symbol.lower(),
        qualified_name,
        module_name,
        qualified_name.split(".")[-1],
        qualified_name.replace(".", "_"),
    }
    return sorted(alias for alias in aliases if alias)


def _usage_examples(symbol: str, docs_dir: Path, limit: int = 6) -> list[str]:
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    snippets: list[str] = []
    for source_path in sorted(docs_dir.glob("*.py")):
        lines = source_path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if not pattern.search(line):
                continue
            window = lines[max(0, index - 1) : min(len(lines), index + 2)]
            snippet = "\n".join(item.rstrip() for item in window).strip()
            if not snippet:
                continue
            snippets.append(f"[{source_path.name}]\n{snippet}")
            if len(snippets) >= limit:
                return snippets
    return snippets


def build_synthetic_symbol_chunks(docs_dir: str | Path) -> list[dict[str, Any]]:
    docs_path = Path(docs_dir)
    chunks: list[dict[str, Any]] = []

    for symbol, spec in CORE_SYMBOL_REGISTRY.items():
        usage_examples = _usage_examples(symbol, docs_path)
        content_lines = [
            f"Symbol: {symbol}",
            f"Qualified name: {spec['qualified_name']}",
            f"Category: {spec['category']}",
            f"Preferred import: {spec['import_path']}",
            f"Summary: {spec['summary']}",
            f"Common patterns: {', '.join(spec['patterns'])}",
            "Canonical example:",
            spec["example_code"],
        ]
        if usage_examples:
            content_lines.extend(["", "Local usage evidence:", *usage_examples])

        chunks.append(
            {
                "id": f"synthetic::{symbol}",
                "content": "\n".join(content_lines).strip(),
                "metadata": {
                    "source_type": "api",
                    "chunk_kind": "synthetic_symbol",
                    "symbol": symbol,
                    "module": spec["module"],
                    "file_path": "synthetic://core_symbols",
                    "parent_symbol": None,
                    "children_symbols": [],
                    "imports_hint": [spec["import_path"]],
                    "keywords": sorted(
                        {symbol, spec["category"], *spec["patterns"], spec["qualified_name"].split(".")[-1]}
                    ),
                    "aliases": _build_aliases(symbol, spec["qualified_name"], spec["module"]),
                    "doc_summary": spec["summary"],
                    "source_url": spec["source_url"],
                    "qualified_name": spec["qualified_name"],
                    "animation_patterns": spec["patterns"],
                    "visual_patterns": spec["patterns"],
                },
            }
        )

    return chunks
