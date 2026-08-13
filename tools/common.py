#!/usr/bin/env python3
"""common.py — общий код для validate.py и query.py.
Архитектура: ARCHITECTURE_v3_1_1.md (заморожена arch-freeze-v3.1.1).
Принцип: без LLM внутри, детерминированно, fail-closed [T2].
"""
import re
import sys
import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
RAW_DIR = REPO_ROOT / "raw"
OUTPUTS_DIR = REPO_ROOT / "outputs"
TOOLS_DIR = REPO_ROOT / "tools"
REGISTRY_PATH = REPO_ROOT / "sources" / "registry.yaml"
LINT_FINDINGS_PATH = WIKI_DIR / "lint-findings.yaml"
CONFIG_PATH = TOOLS_DIR / "config.yaml"
IMPACT_TIERS_PATH = TOOLS_DIR / "impact_tiers.yaml"

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Персистентные семантические причины блокировки [§4.1]
ALLOWED_BLOCK_REASONS = {
    "contradiction_pending",
    "human_flag",
    "extraction_manual_review",
}
ALLOWED_REVIEW_STATUS = {"draft", "active"}
ALLOWED_PROVENANCE = {"source", "human"}

# Грамматика commit-сообщений [§5.1, FIN-CGPT-010, AUD2-026]
COMMIT_RE = re.compile(
    r"^\[(INGEST|PROMOTE|QUERY|LINT|LINT-FIX|MIGRATE|HUMAN-EDIT|RAW-ADMIN)\] .+"
)


def load_yaml(path: Path, default=None):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or default


def load_config():
    cfg = load_yaml(CONFIG_PATH, {})
    if not cfg:
        die(f"FATAL: не найден или пуст {CONFIG_PATH} — fail-closed, работа невозможна")
    return cfg


def die(msg: str):
    print(msg, file=sys.stderr)
    sys.exit(2)


class Card:
    """Карточка: canonical YAML frontmatter + рендер-тело [Q5, T5]."""

    def __init__(self, path: Path):
        self.path = path
        self.errors: list[str] = []
        self.meta: dict = {}
        self.body: str = ""
        self.is_candidate = path.name.endswith(".candidate.md")
        text = path.read_text(encoding="utf-8")
        m = FRONTMATTER_RE.match(text)
        if not m:
            self.errors.append("нет YAML frontmatter (--- ... ---)")
            return
        try:
            self.meta = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            self.errors.append(f"битый YAML frontmatter: {e}")
            return
        self.body = text[m.end():]

    # --- удобные свойства -------------------------------------------------
    @property
    def card_id(self):
        return self.meta.get("card_id")

    @property
    def revision_id(self):
        return self.meta.get("revision_id")

    @property
    def review_status(self):
        return self.meta.get("review_status")

    @property
    def persisted_block_reasons(self):
        return list(self.meta.get("block_reasons") or [])

    def claim_fields(self, domain_fields: list[str]):
        """Итератор (имя_поля, список_claims) только по доменным полям схемы."""
        for field in domain_fields:
            claims = self.meta.get(field)
            if claims is None:
                continue
            if not isinstance(claims, list):
                yield field, None  # сигнал ошибки формата
                continue
            yield field, claims


def load_cards(only_active=False) -> list[Card]:
    cards = []
    if not WIKI_DIR.exists():
        return cards
    for p in sorted(WIKI_DIR.glob("*.md")):
        if p.name in ("contradictions.md",):
            continue
        c = Card(p)
        if only_active and c.review_status != "active":
            continue
        cards.append(c)
    return cards


def open_lint_findings() -> dict:
    """finding_id -> запись; только открытые findings [FIN-CGPT-006]."""
    data = load_yaml(LINT_FINDINGS_PATH, {}) or {}
    return {
        fid: rec
        for fid, rec in data.items()
        if isinstance(rec, dict) and rec.get("status") == "open"
    }


def derived_block_reasons(card: Card, registry: dict, findings: dict, cfg: dict) -> list[str]:
    """Вычисляемые блокировки [T6]: НЕ хранятся в карточке.
    newer_source_loaded — информационный флаг, НЕ блокирует [FIN-CGPT-005]."""
    reasons = []
    # Открытые семантические LINT-findings по этой карточке
    for fid, rec in findings.items():
        if rec.get("card_id") == card.card_id:
            reasons.append(f"lint_finding_open:{fid}")
    # Несовпадение schema_version с текущей production-схемой
    prod_schema = cfg.get("schema_version")
    if card.meta.get("schema_version") != prod_schema:
        # exp-* карточки Фазы A валидны, но по определению не eligible [§8-A]
        reasons.append("schema_version_mismatch")
    # exp-pipeline никогда не eligible [FIN-CGPT-004]
    pv = str(card.meta.get("pipeline_version") or "")
    if pv.startswith("exp-"):
        reasons.append("experimental_pipeline")
    return reasons


def effective_block_reasons(card: Card, registry: dict, findings: dict, cfg: dict) -> list[str]:
    return card.persisted_block_reasons + derived_block_reasons(card, registry, findings, cfg)


def is_eligible(card: Card, registry: dict, findings: dict, cfg: dict) -> bool:
    """QUERY-eligibility [§4.1]."""
    return (
        card.review_status == "active"
        and not card.is_candidate
        and not effective_block_reasons(card, registry, findings, cfg)
    )


def newer_source_loaded(card: Card, registry: dict) -> bool:
    """Информационный флаг [FIN-CGPT-005]: у какого-то source этой карточки
    в registry появился наследник (supersedes указывает на него)."""
    my_sources = set(card.meta.get("sources") or [])
    for sid, rec in (registry or {}).items():
        if isinstance(rec, dict) and rec.get("supersedes") in my_sources:
            return True
    return False


def json_out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))
