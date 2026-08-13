#!/usr/bin/env python3
"""validate.py — детерминированный контролёр [Q2, T2, §5.1].
Fail-closed: любое сомнение = блокировка (exit code 1), не пропуск.

Режимы:
  validate.py                 полная проверка wiki/ + registry + outputs
  validate.py --pre-commit    то же + правило raw/ по git-status [FIN-CGPT-003]
  validate.py --commit-msg F  проверка грамматики сообщения из файла F [FIN-CGPT-010]
  validate.py --eligibility   JSON: eligibility и effective_block_reasons всех карточек
  validate.py --raw-admin SID --reason "..."   owner-only режим для M/D/R в raw/ [§5.1]
"""
import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    ALLOWED_BLOCK_REASONS, ALLOWED_PROVENANCE, ALLOWED_REVIEW_STATUS,
    COMMIT_RE, RAW_DIR, REGISTRY_PATH, REPO_ROOT,
    Card, effective_block_reasons, is_eligible, json_out, load_cards,
    load_config, load_yaml, newer_source_loaded, open_lint_findings,
)

ERRORS: list[str] = []


def err(where: str, msg: str):
    ERRORS.append(f"ERROR [{where}]: {msg}")


# ---------------------------------------------------------------- claims ---
def check_claim(card: Card, field: str, i: int, claim: dict, cfg, registry):
    where = f"{card.path.name}:{field}[{i}]"
    if not isinstance(claim, dict):
        err(where, "claim не является объектом")
        return
    cid = claim.get("claim_id")
    if not cid:
        err(where, "нет claim_id [V-CGPT-001]")
    ptype = claim.get("provenance_type", "source")
    if ptype not in ALLOWED_PROVENANCE:
        err(where, f"недопустимый provenance_type: {ptype}")
    if ptype == "source":
        sid = claim.get("source_id")
        anchor = claim.get("anchor")
        if not sid:
            err(where, "provenance_type=source, но нет source_id [4.3.3→§4.2]")
        elif sid not in (registry or {}):
            err(where, f"source_id {sid} отсутствует в sources/registry.yaml [FIN-CGPT-008]")
        if not (isinstance(anchor, dict) and ("page" in anchor)):
            err(where, "нет anchor.page (или anchor.manual) [C2]")
    else:  # human assertion [FIN-CGPT-007]
        for req in ("asserted_by", "asserted_at", "justification"):
            if not claim.get(req):
                err(where, f"human assertion без обязательного поля {req}")
    if "value_raw" not in claim:
        err(where, "нет value_raw (дословное значение источника) [4.3]")
    mb = claim.get("measurement_basis")
    vocab = cfg.get("measurement_basis_vocab") or []
    if mb is not None and vocab and mb not in vocab:
        err(where, f"measurement_basis '{mb}' вне controlled vocabulary [FIN-CGPT-002]")
    cons = claim.get("constraints")
    if cons is not None:
        if not isinstance(cons, dict):
            err(where, "constraints должны быть объектом предикатов [FIN-CGPT-002]")
        else:
            allowed_keys = set(cfg.get("constraint_keys") or [])
            if allowed_keys:
                for k in cons:
                    if k not in allowed_keys and k != "unmodeled":
                        err(where, f"constraint-предикат '{k}' вне замороженного словаря")


def check_card(card: Card, cfg, registry, id_pairs: Counter, cards_by_cardid: dict):
    where = card.path.name
    for e in card.errors:
        err(where, e)
    if card.errors:
        return
    # обязательные служебные поля [§4.1]
    for req in ("card_id", "revision_id", "schema_version", "review_status", "pipeline_version"):
        if not card.meta.get(req):
            err(where, f"нет обязательного поля {req}")
    if card.review_status not in ALLOWED_REVIEW_STATUS:
        err(where, f"review_status '{card.review_status}' вне {sorted(ALLOWED_REVIEW_STATUS)}")
    for br in card.persisted_block_reasons:
        if br not in ALLOWED_BLOCK_REASONS:
            err(where, f"персистентный block_reason '{br}' вне допустимых "
                       f"(вычисляемые причины НЕ хранятся [T6])")
    # candidate не может быть active
    if card.is_candidate and card.review_status == "active":
        err(where, "candidate-файл не может иметь review_status: active [§6.2]")
    # exp-* только draft [FIN-CGPT-004]
    pv = str(card.meta.get("pipeline_version") or "")
    if pv.startswith("exp-") and card.review_status != "draft":
        err(where, "pipeline_version exp-* допускает только review_status: draft [FIN-CGPT-004]")
    # уникальность (card_id, revision_id) [V-CGPT-001]
    pair = (card.card_id, card.revision_id)
    id_pairs[pair] += 1
    cards_by_cardid.setdefault(card.card_id, []).append(card)
    # sources: только ссылки
    for sid in card.meta.get("sources") or []:
        if sid not in (registry or {}):
            err(where, f"sources[] ссылается на {sid}, отсутствующий в registry")
    # claims
    domain_fields = cfg.get("domain_fields") or []
    for field, claims in card.claim_fields(domain_fields):
        if claims is None:
            err(where, f"поле {field} должно быть списком claims [C1]")
            continue
        seen_cids = set()
        for i, claim in enumerate(claims):
            check_claim(card, field, i, claim, cfg, registry)
            cid = isinstance(claim, dict) and claim.get("claim_id")
            if cid:
                if cid in seen_cids:
                    err(f"{where}:{field}", f"дубль claim_id {cid} внутри ревизии")
                seen_cids.add(cid)


def check_claim_inheritance(cards_by_cardid: dict, cfg):
    """Инвариант наследования claim_id между active и candidate [V-CGPT-001]:
    одинаковый claim_id => семантическая идентичность."""
    sem_keys = ("value_raw", "constraints", "measurement_basis", "source_id")
    domain_fields = cfg.get("domain_fields") or []
    for card_id, group in cards_by_cardid.items():
        if len(group) < 2:
            continue
        claims_by_cid: dict = {}
        for card in group:
            for field, claims in card.claim_fields(domain_fields):
                for claim in (claims or []):
                    if not isinstance(claim, dict):
                        continue
                    cid = claim.get("claim_id")
                    if not cid:
                        continue
                    sig = tuple(repr(claim.get(k)) for k in sem_keys)
                    prev = claims_by_cid.get(cid)
                    if prev and prev != sig:
                        err(card.path.name,
                            f"claim_id {cid} повторён между ревизиями {card_id}, "
                            f"но claim изменён — изменённый claim обязан получить "
                            f"НОВЫЙ claim_id [V-CGPT-001]")
                    claims_by_cid[cid] = sig


# ---------------------------------------------------------------- raw/ -----
def git_status_raw():
    out = subprocess.run(
        ["git", "status", "--porcelain", "--", "raw/"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).stdout
    return [line for line in out.splitlines() if line.strip()]


def check_raw_rule():
    """A разрешён; M/D/R запрещены в обычных режимах [FIN-CGPT-003]."""
    for line in git_status_raw():
        code = line[:2]
        path = line[3:]
        if any(c in code for c in ("M", "D", "R")):
            err("raw/", f"запрещённая операция '{code.strip()}' над {path}; "
                        f"используйте validate.py --raw-admin [FIN-CGPT-003]")


def raw_admin(source_id: str, reason: str, cfg, registry):
    """Owner-only режим [§5.1]: ссылочная целостность + audit trail."""
    if not reason:
        err("raw-admin", "обязателен --reason")
        return
    if source_id not in (registry or {}):
        err("raw-admin", f"{source_id} не найден в registry")
        return
    # ссылочная целостность: active-claims не должны ссылаться
    findings = open_lint_findings()
    for card in load_cards():
        if card.review_status != "active":
            continue
        for field, claims in card.claim_fields(cfg.get("domain_fields") or []):
            for claim in (claims or []):
                if isinstance(claim, dict) and claim.get("source_id") == source_id:
                    err("raw-admin",
                        f"{card.path.name}:{field} (active) ссылается на {source_id} — "
                        f"сначала HUMAN-EDIT/supersession [§5.1]")
    if not ERRORS:
        print(f"OK: RAW-ADMIN разрешён для {source_id}.")
        print(f"Обязательные действия: (1) в registry добавить removed_at и "
              f"removal_reason: \"{reason}\" (запись НЕ удалять); "
              f"(2) commit message начать с [RAW-ADMIN] {reason}")


# ---------------------------------------------------------------- outputs --
def recompute_derived():
    """Пересчёт derived-значений отчётов по DSL [T8, Q8].
    Формат блока в outputs/*.md:
      <!-- derived: {"result": 12.5, "formula": "percent_delta", "inputs": [8192, 7282]} -->
    Whitelist: add sub mul div ratio percent_delta convert."""
    import json as _json
    import re as _re
    tol = 0.005  # относительная погрешность 0.5%
    cfg = load_config()
    conv = cfg.get("unit_conversion") or {}
    block_re = _re.compile(r"<!--\s*derived:\s*(\{.*?\})\s*-->", _re.DOTALL)
    from common import OUTPUTS_DIR
    if not OUTPUTS_DIR.exists():
        return
    for p in sorted(OUTPUTS_DIR.glob("*.md")):
        for m in block_re.finditer(p.read_text(encoding="utf-8")):
            try:
                d = _json.loads(m.group(1))
            except _json.JSONDecodeError as e:
                err(p.name, f"битый derived-блок: {e}")
                continue
            f, ins, res = d.get("formula"), d.get("inputs", []), d.get("result")
            try:
                if f == "add":
                    calc = sum(ins)
                elif f == "sub":
                    calc = ins[0] - ins[1]
                elif f == "mul":
                    calc = ins[0] * ins[1]
                elif f in ("div", "ratio"):
                    calc = ins[0] / ins[1]
                elif f == "percent_delta":
                    calc = (ins[0] - ins[1]) / ins[1] * 100
                elif f == "convert":
                    factor = conv.get(d.get("units", ""))
                    if factor is None:
                        err(p.name, f"convert: неизвестная пара единиц "
                                    f"'{d.get('units')}' в unit_conversion")
                        continue
                    calc = ins[0] * factor
                else:
                    err(p.name, f"формула '{f}' вне whitelist DSL [T8]")
                    continue
            except (IndexError, ZeroDivisionError, TypeError) as e:
                err(p.name, f"ошибка вычисления {f}({ins}): {e}")
                continue
            ref = abs(res) if res else 1.0
            if abs(calc - res) / ref > tol:
                err(p.name, f"derived-значение {res} ≠ пересчёту {round(calc, 4)} "
                            f"({f}{ins}) — отчёт заблокирован [T8]")


# ---------------------------------------------------------------- main -----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pre-commit", action="store_true")
    ap.add_argument("--commit-msg", metavar="FILE")
    ap.add_argument("--eligibility", action="store_true")
    ap.add_argument("--raw-admin", metavar="SOURCE_ID")
    ap.add_argument("--reason", default="")
    args = ap.parse_args()

    if args.commit_msg:  # [FIN-CGPT-010]
        msg = Path(args.commit_msg).read_text(encoding="utf-8").strip()
        if not COMMIT_RE.match(msg):
            print(f"ERROR: commit message не соответствует грамматике "
                  f"[INGEST|PROMOTE|QUERY|LINT|LINT-FIX|MIGRATE|HUMAN-EDIT|RAW-ADMIN]: "
                  f"'{msg}'", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    cfg = load_config()
    registry = load_yaml(REGISTRY_PATH, {}) or {}
    findings = open_lint_findings()

    if args.raw_admin:
        raw_admin(args.raw_admin, args.reason, cfg, registry)
    elif args.eligibility:
        out = []
        for card in load_cards():
            out.append({
                "file": card.path.name,
                "card_id": card.card_id,
                "revision_id": card.revision_id,
                "review_status": card.review_status,
                "eligible": is_eligible(card, registry, findings, cfg),
                "effective_block_reasons":
                    effective_block_reasons(card, registry, findings, cfg),
                "newer_source_loaded": newer_source_loaded(card, registry),
            })
        json_out(out)
        sys.exit(0)
    else:
        id_pairs: Counter = Counter()
        by_cardid: dict = {}
        for card in load_cards():
            check_card(card, cfg, registry, id_pairs, by_cardid)
        for (cid, rid), n in id_pairs.items():
            if n > 1:
                err("wiki/", f"пара (card_id={cid}, revision_id={rid}) неуникальна "
                             f"({n} файлов) [V-CGPT-001]")
        check_claim_inheritance(by_cardid, cfg)
        recompute_derived()
        if args.pre_commit:
            check_raw_rule()

    if ERRORS:
        print("\n".join(ERRORS), file=sys.stderr)
        print(f"\nFAIL: {len(ERRORS)} нарушений — коммит/операция заблокированы "
              f"(fail-closed).", file=sys.stderr)
        sys.exit(1)
    print("OK: нарушений не найдено.")


if __name__ == "__main__":
    main()
