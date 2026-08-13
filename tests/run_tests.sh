#!/bin/bash
# Smoke-тесты tools/ [T2]. Запуск из корня репо: bash tests/run_tests.sh
set -u; cd "$(dirname "$0")/.."
# подготовка окружения из эталонов
mkdir -p wiki outputs sources raw
cp examples/registry.example.yaml sources/registry.yaml
cp examples/lenovo-sr650-v3.md examples/lenovo-sr650-v3.candidate.md wiki/
cp examples/derived-block-example.md outputs/
cleanup(){ rm -f sources/registry.yaml wiki/lenovo-sr650-v3.md wiki/lenovo-sr650-v3.candidate.md outputs/derived-block-example.md outputs/_t8.md; }
trap cleanup EXIT
pass=0; fail=0
check () { # $1=описание $2=ожидаемый_код $3...=команда
  desc="$1"; want="$2"; shift 2
  "$@" >/dev/null 2>&1; got=$?
  if [ "$got" -eq "$want" ]; then pass=$((pass+1)); echo "PASS: $desc"
  else fail=$((fail+1)); echo "FAIL: $desc (ожидался код $want, получен $got)"; fi
}
check "валидная база проходит"                    0 python3 tools/validate.py
check "eligibility отдаёт JSON"                   0 python3 tools/validate.py --eligibility
check "query по предикату"                        0 python3 tools/query.py --field ram_max --constraint cpu_count=2
check "query по полю вне схемы блокируется"       1 python3 tools/query.py --field nonexistent_field
echo "fixed stuff" > /tmp/_m1
check "плохой commit-msg блокируется"             1 python3 tools/validate.py --commit-msg /tmp/_m1
echo "[INGEST] test: ok" > /tmp/_m2
check "хороший commit-msg проходит"               0 python3 tools/validate.py --commit-msg /tmp/_m2
# нарушение V-CGPT-001: тот же claim_id, изменённое значение
cp wiki/lenovo-sr650-v3.candidate.md /tmp/_cand_backup
python3 - << 'PY'
p="wiki/lenovo-sr650-v3.candidate.md"
s=open(p).read().replace('"a1b2c3-ram-003"','"a1b2c3-ram-001"')
open(p,"w").write(s)
PY
check "изменённый claim под старым ID блокируется" 1 python3 tools/validate.py
cp /tmp/_cand_backup wiki/lenovo-sr650-v3.candidate.md
# нарушение T8: ложное derived-значение
printf 'x <!-- derived: {"result": 55.0, "formula": "percent_delta", "inputs": [8192, 4096]} -->\n' > outputs/_t8.md
check "ложный derived-расчёт блокируется"          1 python3 tools/validate.py
rm -f outputs/_t8.md
check "diff_candidate работает"                    0 python3 tools/diff_candidate.py "lenovo-sr650-v3#a1b2c3"
echo "----------------------------------------"
echo "ИТОГ: $pass PASS, $fail FAIL"
[ "$fail" -eq 0 ]
