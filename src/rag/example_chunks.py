from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path
from typing import Any

from rag.synthetic_chunks import LOWERCASE_CORE_SYMBOLS


def _extract_doc_examples(docstring: str) -> list[str]:
    examples: list[str] = []
    lines = docstring.splitlines()
    index = 0

    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith(".. manim::") or stripped.startswith(".. code-block:: python"):
            index += 1
            while index < len(lines) and (
                not lines[index].strip() or lines[index].strip().startswith(":")
            ):
                index += 1

            block: list[str] = []
            while index < len(lines):
                raw_line = lines[index]
                if raw_line.strip() and not raw_line.startswith(("    ", "\t")):
                    break
                block.append(raw_line)
                index += 1

            candidate = textwrap.dedent("\n".join(block)).strip()
            if "class " in candidate and "construct" in candidate:
                examples.append(candidate)
            continue
        index += 1

    return examples


def _detect_symbols(example_code: str) -> list[str]:
    tokens = set(re.findall(r"\b[A-Z][A-Za-z0-9_]+\b", example_code))
    for symbol in LOWERCASE_CORE_SYMBOLS:
        if re.search(rf"\b{re.escape(symbol)}\b", example_code):
            tokens.add(symbol)
    return sorted({token for token in tokens if token not in {"Scene", "VoiceoverScene"}})


def _infer_tags(file_path: str, example_code: str) -> tuple[list[str], list[str]]:
    stem = Path(file_path).stem.lower()
    domain_tags: set[str] = set()
    visual_patterns: set[str] = set()

    if "graph" in stem or "axes" in example_code.lower():
        domain_tags.add("graphing")
        visual_patterns.add("persistent_axes")
    if "three_d" in stem:
        domain_tags.add("3d")
    if "probability" in stem:
        domain_tags.add("probability")
    if "vector" in stem:
        domain_tags.add("vectors")
    if "text" in stem:
        domain_tags.add("text")
    if "Transform" in example_code:
        visual_patterns.add("transforms")
    if "MoveAlongPath" in example_code:
        visual_patterns.add("path_motion")
    if "LaggedStart" in example_code:
        visual_patterns.add("staggered_reveal")
    if "always_redraw" in example_code:
        visual_patterns.add("dynamic_updaters")

    return sorted(domain_tags), sorted(visual_patterns)


def _summary_chunk(
    file_path: str,
    scene_name: str,
    example_code: str,
    doc_summary: str,
) -> dict[str, Any]:
    symbols_used = _detect_symbols(example_code)
    domain_tags, visual_patterns = _infer_tags(file_path, example_code)
    content = (
        f"Scene example: {scene_name}\n"
        f"Summary: {doc_summary or 'Example Manim scene from documentation.'}\n"
        f"Symbols: {', '.join(symbols_used)}\n"
        f"Patterns: {', '.join(visual_patterns)}\n"
        f"Code excerpt:\n{example_code[:1200]}"
    )
    return {
        "id": f"{scene_name}#summary",
        "content": content,
        "metadata": {
            "source_type": "example",
            "chunk_kind": "scene_summary",
            "scene_name": scene_name,
            "example_kind": "official_docs",
            "domain_tags": domain_tags,
            "visual_patterns": visual_patterns,
            "symbols_used": symbols_used,
            "layout_patterns": visual_patterns,
            "animation_patterns": visual_patterns,
            "teaching_patterns": ["explanatory_scene"],
            "file_path": file_path,
        },
    }


def _scene_chunk(file_path: str, scene_name: str, example_code: str) -> dict[str, Any]:
    symbols_used = _detect_symbols(example_code)
    domain_tags, visual_patterns = _infer_tags(file_path, example_code)
    return {
        "id": f"{scene_name}#scene",
        "content": example_code,
        "metadata": {
            "source_type": "example",
            "chunk_kind": "scene_code",
            "scene_name": scene_name,
            "example_kind": "official_docs",
            "domain_tags": domain_tags,
            "visual_patterns": visual_patterns,
            "symbols_used": symbols_used,
            "layout_patterns": visual_patterns,
            "animation_patterns": visual_patterns,
            "teaching_patterns": ["scene_code"],
            "file_path": file_path,
        },
    }


def _action_chunk(file_path: str, scene_name: str, example_code: str) -> dict[str, Any] | None:
    action_lines = [
        line
        for line in example_code.splitlines()
        if "self.play(" in line or "self.add(" in line or "self.wait(" in line
    ]
    if not action_lines:
        return None

    symbols_used = _detect_symbols(example_code)
    domain_tags, visual_patterns = _infer_tags(file_path, example_code)
    return {
        "id": f"{scene_name}#actions",
        "content": "\n".join(action_lines),
        "metadata": {
            "source_type": "example",
            "chunk_kind": "animation_block",
            "scene_name": scene_name,
            "example_kind": "official_docs",
            "domain_tags": domain_tags,
            "visual_patterns": visual_patterns,
            "symbols_used": symbols_used,
            "layout_patterns": visual_patterns,
            "animation_patterns": visual_patterns,
            "teaching_patterns": ["animation_sequence"],
            "file_path": file_path,
        },
    }


def extract_example_chunks(file_path: str) -> list[dict[str, Any]]:
    source_path = Path(file_path)
    source_code = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source_code)
    module_docstring = ast.get_docstring(tree) or ""

    examples: list[dict[str, Any]] = []
    docstrings = [module_docstring]
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node) or ""
            if doc:
                docstrings.append(doc)

    seen_scene_ids: set[str] = set()
    for docstring in docstrings:
        for example_code in _extract_doc_examples(docstring):
            match = re.search(r"class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", example_code)
            if not match:
                continue
            scene_name = match.group(1)
            if scene_name in seen_scene_ids:
                continue
            seen_scene_ids.add(scene_name)

            summary = " ".join(docstring.split())[:300]
            examples.append(_summary_chunk(str(source_path), scene_name, example_code, summary))
            examples.append(_scene_chunk(str(source_path), scene_name, example_code))
            action_chunk = _action_chunk(str(source_path), scene_name, example_code)
            if action_chunk is not None:
                examples.append(action_chunk)

    return examples
