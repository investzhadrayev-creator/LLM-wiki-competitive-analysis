# VERIFICATION PATCH — ChatGPT / аудитор 1

**Дата:** 2026-08-13  
**Объект:** `ARCHITECTURE_v3_1_1.md`  
**Рамка:** только V-CGPT-001, остаток FIN-CGPT-003, остаток FIN-CGPT-007 + проверка новых defect critical/high, внесённых этими исправлениями.

| Пункт | Вердикт | Проверка |
|---|---|---|
| **V-CGPT-001** | **CLOSED** | Введён `revision_id`; `card_id` остаётся стабильным между active/candidate, а уникальность проверяется по `(card_id, revision_id)`. Для claims явно задан инвариант: повтор `claim_id` между ревизиями разрешён только при семантической идентичности, изменённый claim получает новый ID; validator проверяет эти правила вместо глобальной уникальности. Самоблокировка candidate→PROMOTE/HUMAN-EDIT устранена. |
| **FIN-CGPT-003 (остаток)** | **CLOSED** | Owner-only исключение реализовано отдельным режимом `validate.py --raw-admin`; обычные режимы по-прежнему блокируют M/D/R. RAW-ADMIN проверяет ссылочную целостность, требует причину и `[RAW-ADMIN]` audit trail, сохраняет registry-запись удалённого source_id. Прежняя недоопределённость exceptional workflow устранена. |
| **FIN-CGPT-007 (остаток)** | **CLOSED** | Введён `provenance_type: source | human`. Для source сохраняется registry+anchor контракт; для human действует отдельный обязательный контракт `asserted_by/asserted_at/justification`, без проверки против raw/registry. HUMAN-EDIT по-прежнему создаёт candidate и требует PROMOTE, а отчёты явно маркируют human assertions. Конфликт с validator устранён. |

## Проверка новых critical/high дефектов от патча v3.1.1

Новых critical/high дефектов, непосредственно внесённых этими тремя исправлениями, не обнаружено. Revision-aware identity согласована с параллельным active+candidate workflow; RAW-ADMIN сохраняет fail-closed обычного контура; разделение provenance source/human не создаёт обхода candidate→PROMOTE и не позволяет human assertion выглядеть как vendor-sourced fact.

Заморозку не блокирую