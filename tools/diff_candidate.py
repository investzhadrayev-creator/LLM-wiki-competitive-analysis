#!/usr/bin/env python3
"""diff_candidate.py <card_id> — структурированная дельта active↔candidate [F1, §6.2].
Оператор НЕ сравнивает YAML глазами: показываются новые / изменённые /
удалённые claims с value_raw обеих версий.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import json_out, load_cards, load_config  # noqa: E402


def claims_map(card, domain_fields):
    out = {}
    for field, claims in card.claim_fields(domain_fields):
        for cl in (claims or []):
            if isinstance(cl, dict) and cl.get("claim_id"):
                out[(field, cl["claim_id"])] = cl
    return out


def brief(cl):
    return {"value_raw": cl.get("value_raw"),
            "value_normalized": cl.get("value_normalized"),
            "unit": cl.get("unit"),
            "constraints": cl.get("constraints"),
            "measurement_basis": cl.get("measurement_basis"),
            "provenance_type": cl.get("provenance_type", "source")}


def main():
    if len(sys.argv) != 2:
        print("Использование: diff_candidate.py <card_id>", file=sys.stderr)
        sys.exit(2)
    card_id = sys.argv[1]
    cfg = load_config()
    fields = cfg.get("domain_fields") or []
    active = candidate = None
    for c in load_cards():
        if c.card_id != card_id:
            continue
        if c.is_candidate:
            candidate = c
        elif c.review_status == "active":
            active = c
    if candidate is None:
        print(f"ERROR: candidate для {card_id} не найден", file=sys.stderr)
        sys.exit(1)
    a = claims_map(active, fields) if active else {}
    b = claims_map(candidate, fields)
    added = [{"field": f, "claim_id": cid, "candidate": brief(cl)}
             for (f, cid), cl in sorted(b.items()) if (f, cid) not in a]
    removed = [{"field": f, "claim_id": cid, "active": brief(cl)}
               for (f, cid), cl in sorted(a.items()) if (f, cid) not in b]
    # одинаковый claim_id при валидной базе = семантически идентичен [V-CGPT-001],
    # поэтому "changed" в норме пуст; непустой = сигнал прогнать validate.py
    changed = [{"field": f, "claim_id": cid,
                "active": brief(a[(f, cid)]), "candidate": brief(cl),
                "warning": "одинаковый claim_id при разном содержимом — "
                           "нарушение V-CGPT-001, прогоните validate.py"}
               for (f, cid), cl in sorted(b.items())
               if (f, cid) in a and brief(a[(f, cid)]) != brief(cl)]
    json_out({
        "card_id": card_id,
        "active_revision": active.revision_id if active else None,
        "candidate_revision": candidate.revision_id,
        "added_claims": added,
        "removed_claims": removed,
        "invalid_same_id_changes": changed,
        "summary": f"+{len(added)} / -{len(removed)} claims",
    })


if __name__ == "__main__":
    main()
