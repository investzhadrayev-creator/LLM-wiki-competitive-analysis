#!/usr/bin/env python3
"""query.py — детерминированный отбор для QUERY [Q2, T2, §5.2].
Один запрос к одной версии базы = один результат. Ссылки только по
card_id/claim_id [FIN-CGPT-001]. Только eligible-карточки.
Сопоставимость — только по структурированным предикатам [FIN-CGPT-002].

Примеры:
  query.py --field ram_max --constraint cpu_count=2 --basis total
  query.py --card-meta vendor=lenovo --field drive_bays
  query.py --list-eligible
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    REGISTRY_PATH, is_eligible, json_out, load_cards, load_config,
    load_yaml, open_lint_findings,
)


def parse_kv(pairs):
    out = {}
    for p in pairs or []:
        if "=" not in p:
            print(f"ERROR: ожидается key=value, получено '{p}'", file=sys.stderr)
            sys.exit(2)
        k, v = p.split("=", 1)
        out[k] = int(v) if v.isdigit() else v
    return out


def claim_matches(claim, want_constraints, want_basis):
    if not isinstance(claim, dict):
        return False
    cons = claim.get("constraints") or {}
    if cons.get("unmodeled"):
        return False  # unmodeled исключён из автосравнения [§4.2]
    if want_basis and claim.get("measurement_basis") != want_basis:
        return False
    for k, v in want_constraints.items():
        if cons.get(k) != v:
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--field", help="доменное поле схемы (например ram_max)")
    ap.add_argument("--constraint", action="append",
                    help="предикат key=value, можно несколько")
    ap.add_argument("--basis", help="требуемый measurement_basis")
    ap.add_argument("--card-meta", action="append",
                    help="фильтр по служебному полю карточки key=value")
    ap.add_argument("--list-eligible", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    registry = load_yaml(REGISTRY_PATH, {}) or {}
    findings = open_lint_findings()
    want_c = parse_kv(args.constraint)
    want_m = parse_kv(args.card_meta)

    eligible = [c for c in load_cards()
                if is_eligible(c, registry, findings, cfg)]
    # детерминированный порядок [§5.2]
    eligible.sort(key=lambda c: (str(c.card_id), str(c.revision_id)))

    if args.list_eligible:
        json_out({"criteria": {"list_eligible": True},
                  "cards": [{"card_id": c.card_id, "revision_id": c.revision_id}
                            for c in eligible]})
        return

    if not args.field:
        print("ERROR: требуется --field или --list-eligible", file=sys.stderr)
        sys.exit(2)
    if args.field not in (cfg.get("domain_fields") or []):
        print(f"ERROR: поле '{args.field}' вне domain_fields схемы (fail-closed)",
              file=sys.stderr)
        sys.exit(1)

    results, excluded = [], []
    for card in eligible:
        if any(card.meta.get(k) != v for k, v in want_m.items()):
            continue
        claims = card.meta.get(args.field) or []
        matched = [cl for cl in claims if claim_matches(cl, want_c, args.basis)]
        unmod = [cl.get("claim_id") for cl in claims
                 if isinstance(cl, dict) and (cl.get("constraints") or {}).get("unmodeled")]
        for cl in matched:
            results.append({
                "card_id": card.card_id,
                "revision_id": card.revision_id,
                "claim_id": cl.get("claim_id"),
                "value_raw": cl.get("value_raw"),
                "value_normalized": cl.get("value_normalized"),
                "unit": cl.get("unit"),
                "constraints": cl.get("constraints"),
                "measurement_basis": cl.get("measurement_basis"),
                "provenance_type": cl.get("provenance_type", "source"),
            })
        if unmod:
            excluded.append({"card_id": card.card_id,
                             "unmodeled_claim_ids": unmod,
                             "note": "требует ручного сопоставления [§4.2]"})
    results.sort(key=lambda r: (str(r["card_id"]), str(r["claim_id"])))
    json_out({
        "criteria": {"field": args.field, "constraints": want_c,
                     "measurement_basis": args.basis, "card_meta": want_m},
        "results": results,
        "excluded_unmodeled": excluded,
    })


if __name__ == "__main__":
    main()
