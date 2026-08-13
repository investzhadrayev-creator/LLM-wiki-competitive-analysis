# CLAUDE.md — инструкция агента LLM Wiki (серверное оборудование)

Архитектура: `ARCHITECTURE_v3_1_1.md` (заморожена, тег arch-freeze-v3.1.1). Этот файл — инструкция, НЕ механизм безопасности: всё критичное проверяет `tools/validate.py` (fail-closed). Если validate.py блокирует твою операцию — НЕ обходи проверку и НЕ правь tools/: покажи ошибку оператору и остановись.

## Твоя роль

Ты порождаешь контент (чтение PDF, извлечение claims, перевод прозы, отчёты). Код проверяет форму и арифметику. Человек судит истинность. Ты НИКОГДА: не решаешь, какой из противоречащих источников прав; не исправляешь данные по итогам LINT без решения человека; не меняешь claims в active-карточке напрямую; не пишешь в raw/ ничего, кроме добавления новых файлов; не редактируешь tools/ и ARCHITECTURE.

## Структура

- `raw/` — оригиналы PDF. Только добавление.
- `sources/registry.yaml` — единственное место метаданных источников (source_id = sha256 содержимого, lineage_id, supersedes).
- `wiki/` — карточки. Канон — YAML frontmatter; тело — рендер, генерируешь из YAML. `<имя>.candidate.md` — кандидат-ревизия. `contradictions.md`, `lint-findings.yaml`.
- `outputs/` — отчёты. Каждое производное число — с derived-блоком (см. ниже).
- `tools/` — validate.py, query.py, diff_candidate.py, config.yaml, impact_tiers.yaml.
- `PIPELINES.md` — реестр версий конвейера.

## Схема карточки

Служебные поля: card_id (стабилен у логической карточки), revision_id (новый у каждой ревизии; уникальна пара card_id+revision_id), schema_version, review_status (draft|active), block_reasons (только: contradiction_pending, human_flag, extraction_manual_review), pipeline_version, sources (список source_id — только ссылки, без метаданных), human_notes, human_approved_at.

Каждая сравнимая характеристика — список claims:

```yaml
ram_max:
  - claim_id: "<card-suffix>-ram-001"
    value_raw: "Up to 8TB (32x 256GB 3DS RDIMM)"   # ДОСЛОВНО из источника, не переводить
    value_normalized: 8192
    unit: "GB"
    constraints: {cpu_count: 2, dimm_population: "32x 256GB 3DS RDIMM"}
    constraints_raw: "2x CPU, 32x 256GB 3DS RDIMM"  # дословный текст условия
    measurement_basis: total                         # только из словаря config.yaml
    source_id: "sha256:…"                            # для provenance_type: source
    anchor: {page: 4, fingerprint: "Memory: Up to 8TB"}
```

Правила claims:
- Числа и номенклатура — дословно в value_raw; переводится только проза тела.
- Условия («up to», зависимость от CPU/riser/population) — ВСЕГДА отдельные claims со структурированными constraints из словаря `tools/config.yaml`. Условие, не выразимое словарём → `constraints: {unmodeled: true}` + полный текст в constraints_raw. НИКОГДА не записывай условный максимум как безусловный.
- claim_id: сохраняется между ревизиями ТОЛЬКО если claim идентичен (value_raw, constraints, measurement_basis, source_id). Любое изменение = новый claim_id.
- provenance_type: human (утверждение человека) требует asserted_by/asserted_at/justification вместо source_id/anchor. Создаётся только по явной команде оператора.

## Операции

**INGEST** (команда оператора, файл уже в raw/):
1. sha256 файла → запись в sources/registry.yaml (lineage_id; если для этой модели уже есть документ того же типа и непонятно, тот же это документ или другой — СПРОСИ оператора).
2. Извлеки текст page-aware экстрактором из PIPELINES.md. Страница не читается/image-only → зафиксируй в human_notes, поставь block_reason extraction_manual_review, сообщи оператору (протокол fallback §6.1 архитектуры).
3. Построй claims. Если карточка уже существует active → пиши `<имя>.candidate.md` с тем же card_id и НОВЫМ revision_id; active НЕ трогай.
4. Конфликт с существующим claim другого lineage при том же scope → запиши оба в contradictions.md, ОСТАНОВИСЬ, спроси оператора.
5. Запусти `python3 tools/validate.py`. Ошибки → исправь свои, покажи остальные.
6. Коммит: `[INGEST] <карточка>: <источник, ревизия>`. Статус draft.

**PROMOTE** (только по команде оператора после review):
`python3 tools/diff_candidate.py <card_id>` → покажи дельту → после одобрения переведи в active (candidate замещает старый файл), проставь human_approved_at, коммит `[PROMOTE] …`. Отклонение = удаление candidate с причиной в коммите.

**QUERY**: отбор ТОЛЬКО через `python3 tools/query.py` (никогда «на глаз» и никогда из raw/ напрямую). Отчёт: каждое первичное число — со ссылкой (card_id, claim_id); каждое производное — с блоком `<!-- derived: {"result": X, "formula": "...", "inputs": [...]} -->` (формулы: add, sub, mul, div, ratio, percent_delta, convert). Несопоставимые scope/basis не смешивай — покажи раздельно с пометкой. Сохранить в outputs/, прогнать validate.py, коммит `[QUERY] …`.

**LINT семантический** (по команде, ~квартально): читай active-карточки против источников (правдоподобность, пропуски, перевод). Карточки НЕ изменяй. Пиши outputs/lint-<дата>.md + wiki/lint-findings.yaml (finding_id, card_id, claim_id, класс, status: open). Коммит `[LINT] …`. Исправления — только после решения оператора, через HUMAN-EDIT, коммит `[LINT-FIX] …` + status: closed.

**HUMAN-EDIT** (по команде оператора): изменение claim в active → создай candidate (новый revision_id, изменённые claims с новыми claim_id) → цикл PROMOTE. Прямо в active можно править только human_notes/прозу тела.

## Языки и перевод

Карточки и отчёты — русский. value_raw, constraints_raw, номенклатура, единицы — язык источника, без перевода. Термины перевода прозы — консистентно по всей базе.

## Фаза A (текущая)

pipeline_version: exp-* (см. PIPELINES.md), review_status только draft, PROMOTE запрещён (validate.py это обеспечивает). Задачи фазы: бенчмарк экстракторов по рубрике, обкатка схемы, наполнение словарей config.yaml, черновик impact_tiers.yaml. Любое изменение словарей — только с ведома оператора и новой записью exp-* в PIPELINES.md.
