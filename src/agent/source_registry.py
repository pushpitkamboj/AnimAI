from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainSourceConfig:
    domain: str
    preferred_domains: tuple[str, ...]
    query_hints: tuple[str, ...]


DOMAIN_SOURCE_REGISTRY: dict[str, DomainSourceConfig] = {
    "space": DomainSourceConfig(
        domain="space",
        preferred_domains=(
            "nasa.gov",
            "jpl.nasa.gov",
            "ssd-api.jpl.nasa.gov",
            "svs.gsfc.nasa.gov",
            "esa.int",
            "asc-csa.gc.ca",
        ),
        query_hints=("mission profile", "trajectory", "timeline", "press kit", "ephemeris"),
    ),
    "physics": DomainSourceConfig(
        domain="physics",
        preferred_domains=("physics.nist.gov", "nist.gov", "cern.ch", "aps.org"),
        query_hints=("mechanism", "equation", "measured values"),
    ),
    "chemistry": DomainSourceConfig(
        domain="chemistry",
        preferred_domains=("pubchem.ncbi.nlm.nih.gov", "webbook.nist.gov", "nist.gov"),
        query_hints=("mechanism", "reaction steps", "conditions", "molecule data"),
    ),
    "biology": DomainSourceConfig(
        domain="biology",
        preferred_domains=("reactome.org", "ncbi.nlm.nih.gov", "nih.gov"),
        query_hints=("pathway", "mechanism", "step by step"),
    ),
    "math": DomainSourceConfig(
        domain="math",
        preferred_domains=("sympy.org", "docs.sympy.org", "mit.edu", "stanford.edu"),
        query_hints=("derivation", "identity", "visual interpretation"),
    ),
    "engineering": DomainSourceConfig(
        domain="engineering",
        preferred_domains=("nasa.gov", "nist.gov", "energy.gov", "ieee.org"),
        query_hints=("system overview", "process steps", "working principle"),
    ),
    "general_science": DomainSourceConfig(
        domain="general_science",
        preferred_domains=("nasa.gov", "nist.gov", "nih.gov", "wikipedia.org"),
        query_hints=("overview", "mechanism", "timeline"),
    ),
}


def get_domain_config(domain: str) -> DomainSourceConfig:
    return DOMAIN_SOURCE_REGISTRY.get(domain, DOMAIN_SOURCE_REGISTRY["general_science"])
