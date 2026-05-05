from __future__ import annotations

import json
import re
from urllib.parse import urlparse

import requests
from langchain_core.messages import AIMessage
from typing_extensions import TypedDict

from agent.graph_state import RouteInfo, State, TopicBrief
from agent.llm import make_llm
from agent.source_registry import get_domain_config


llm = make_llm("openai:gpt-5.4")

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
MAX_SEARCH_RESULTS = 5
MAX_FETCHED_PAGES = 3


class SearchQueries(TypedDict):
    queries: list[str]


QUERY_PROMPT = """
You are preparing research queries for an educational animation system.

Given the user prompt, its route classification, and the domain, generate 2 to 4 focused
web search queries that will retrieve factual, visualizable, educational information.

Rules:
- For real-world named events or systems, include the exact entity name.
- Prefer queries that retrieve official sources, mission profiles, process breakdowns,
  timelines, mechanisms, or quantitative facts.
- Keep queries compact.
""".strip()


SYNTHESIS_PROMPT = """
You are building a factual topic brief for an educational animation pipeline.

Your output will drive scene planning for a math/science explainer video, so it must be:
- fact-focused,
- visually oriented,
- explicit about quantitative data when available,
- explicit about uncertainty or missing evidence.

Rules:
- Use the supplied web evidence as primary factual grounding when it exists.
- Do not invent specific dates, numbers, or named facts if the evidence does not support them.
- Prefer concrete process steps over vague summaries.
- recommended_visual_mode must be one of: conceptual, quantitative, hybrid.
- source_registry should contain the URLs you relied on most.
- source_snippets should contain short evidence-backed fact statements, not raw HTML.
""".strip()


INTERNAL_BRIEF_PROMPT = """
You are building a factual topic brief for a concept-focused educational animation.

Use strong general scientific knowledge, but avoid pretending to know specific recent
facts or measurements unless they are canonical and stable.

The brief must optimize for clear visual explanation:
- key facts,
- process steps,
- what objects need to be shown,
- common misconceptions,
- and what the narration should cover.

recommended_visual_mode must be one of: conceptual, quantitative, hybrid.
""".strip()


def _invoke_structured(schema, system_prompt: str, payload: dict):
    return llm.with_structured_output(schema).invoke(
        [
            ("system", system_prompt),
            ("human", json.dumps(payload, ensure_ascii=False)),
        ],
    )


def _build_search_queries(prompt: str, route_info: RouteInfo) -> list[str]:
    domain_config = get_domain_config(route_info["domain"])
    response = _invoke_structured(
        SearchQueries,
        QUERY_PROMPT,
        {
            "prompt": prompt,
            "route_info": route_info,
            "query_hints": list(domain_config.query_hints),
        },
    )
    queries = [query.strip() for query in response.get("queries", []) if query.strip()]
    if queries:
        return queries[:4]

    fallback = f"{prompt} {' '.join(route_info.get('named_entities', []))}".strip()
    return [fallback or prompt]


def _search_with_duckduckgo(query: str) -> list[dict]:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return []

    try:
        with DDGS() as ddgs:
            return [
                {
                    "title": item.get("title", ""),
                    "href": item.get("href", ""),
                    "body": item.get("body", ""),
                }
                for item in ddgs.text(query, max_results=MAX_SEARCH_RESULTS)
            ]
    except Exception:
        return []


def _prioritize_results(results: list[dict], route_info: RouteInfo) -> list[dict]:
    preferred_domains = get_domain_config(route_info["domain"]).preferred_domains
    if not preferred_domains:
        return results[:MAX_SEARCH_RESULTS]

    preferred: list[dict] = []
    fallback: list[dict] = []
    for result in results:
        hostname = urlparse(result.get("href", "")).hostname or ""
        target = preferred if any(hostname.endswith(domain) for domain in preferred_domains) else fallback
        target.append(result)

    return (preferred + fallback)[:MAX_SEARCH_RESULTS]


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _fetch_page_excerpt(url: str) -> str:
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return ""

    if "html" not in response.headers.get("content-type", ""):
        return ""

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return _clean_text(response.text)[:1500]

    soup = BeautifulSoup(response.text, "html.parser")
    title = _clean_text(soup.title.get_text(" ", strip=True)) if soup.title else ""
    chunks: list[str] = []

    for tag in soup.find_all(["p", "li"]):
        text = _clean_text(tag.get_text(" ", strip=True))
        if len(text) < 40:
            continue
        chunks.append(text)
        if sum(len(chunk) for chunk in chunks) > 1800:
            break

    excerpt = " ".join(chunks)[:1800]
    return f"Title: {title}\nExcerpt: {excerpt}" if title else excerpt


def _collect_web_evidence(prompt: str, route_info: RouteInfo) -> tuple[list[str], list[str]]:
    if not route_info.get("needs_external_grounding"):
        return [], []

    queries = _build_search_queries(prompt, route_info)
    evidence_blocks: list[str] = []
    seen_urls: set[str] = set()
    excerpted_urls: set[str] = set()

    for query in queries:
        for result in _prioritize_results(_search_with_duckduckgo(query), route_info):
            href = result.get("href", "").strip()
            if not href or href in seen_urls:
                continue

            seen_urls.add(href)
            evidence = (
                f"URL: {href}\n"
                f"Title: {result.get('title', '').strip()}\n"
                f"Snippet: {result.get('body', '').strip()}"
            )

            if len(excerpted_urls) < MAX_FETCHED_PAGES:
                excerpt = _fetch_page_excerpt(href)
                if excerpt:
                    evidence += f"\nPage Excerpt: {excerpt}"
                    excerpted_urls.add(href)

            evidence_blocks.append(evidence)
            if len(evidence_blocks) >= MAX_SEARCH_RESULTS:
                return queries, evidence_blocks

    return queries, evidence_blocks


def _synthesize_topic_brief(
    prompt: str,
    route_info: RouteInfo,
    queries: list[str],
    evidence_blocks: list[str],
) -> TopicBrief:
    if evidence_blocks:
        system_prompt = SYNTHESIS_PROMPT
        payload = {
            "prompt": prompt,
            "route_info": route_info,
            "search_queries": queries,
            "web_evidence": evidence_blocks,
        }
    else:
        system_prompt = INTERNAL_BRIEF_PROMPT
        payload = {
            "prompt": prompt,
            "route_info": route_info,
        }

    return _invoke_structured(TopicBrief, system_prompt, payload)


def build_topic_brief(state: State) -> dict:
    prompt = state["prompt"]
    route_info = state["route_info"]
    queries, evidence_blocks = _collect_web_evidence(prompt, route_info)
    topic_brief = _synthesize_topic_brief(prompt, route_info, queries, evidence_blocks)

    summary = topic_brief.get("factual_summary", "").strip()
    message = summary or f"Built topic brief for {topic_brief.get('topic_title', 'the topic')}."
    return {
        "messages": [AIMessage(content=message)],
        "topic_brief": topic_brief,
    }
