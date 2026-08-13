# ARCHITECTURE v3.1.1 — LLM Wiki: Competitive Analysis of Server Hardware

**Статус:** кандидат на заморозку; точечный патч по верификации
**Дата:** 2026-08-13
**Предыдущие версии:** v1.0 (`7940f3a`), v2.0, v3.0 (финальный аудит), v3.1 (верификация: Grok — F1–F4/F6 CLOSED, не блокирует; ChatGPT — блок по V-CGPT-001, PARTIAL по FIN-CGPT-003/007)
**Основания:** вся цепочка audits/ и deliberation/; данный патч закрывает audits/verification-chatgpt.md
**Критерий заморозки:** автор находок (ChatGPT) подтверждает закрытие V-CGPT-001 и остатков FIN-CGPT-003/007; новых critical/high нет

---

## 0.0. Changelog v3.1 → v3.1.1 (патч по верификации)

| Находка | Исправление | Раздел |
|---|---|---|
| V-CGPT-001 (уникальность ID vs active+candidate) | Revision-aware identity: `revision_id`; уникальность `(card_id, revision_id)`; правила наследования claim_id между ревизиями | §4.1, §4.2, §5.1 |
| FIN-CGPT-003 (остаток: owner-only режим raw/ не специфицирован) | Операция RAW-ADMIN: явный режим validate.py с проверкой ссылочной целостности и audit trail | §3.1, §5.1 |
| FIN-CGPT-007 (остаток: human assertion vs registry) | `provenance_type: source | human`; для human — собственный контракт полей, освобождение от registry/anchor-проверок, обязательная маркировка в отчётах | §4.2, §5.1, §6.6 |

---

## 0.1. Changelog v3.0 → v3.1 (закрытие находок финального аудита)

| Находка | Исправление | Раздел |
|---|---|---|
| FIN-CGPT-001 | Введены неизменяемые `card_id` и `claim_id`; query.py и DSL ссылаются только на них | §4.1, §4.2, §5.2 |
| FIN-CGPT-002 | scope/conditions — структурированные предикаты + controlled vocabulary; raw-текст условия хранится отдельно для provenance | §4.2, §8-A |
| FIN-CGPT-003 | Правило raw/ формализовано по git-status: A разрешён, M/D/R запрещены; owner-only исключение | §3.1, §5.1 |
| FIN-CGPT-004 | Bootstrap-протокол Фазы A: exp-* pipeline, только draft, не eligible; p1 — по завершении | §8-A |
| FIN-CGPT-005 | Новая ревизия источника = информационный флаг; supersession активируется атомарно при PROMOTE | §3.3, §4.1 |
| FIN-CGPT-006 | Семантический LINT пишет findings-реестр (отдельный файл); блокировки — derived через validate.py; карточки LINT не трогает | §6.4 |
| FIN-CGPT-007 | Введена операция HUMAN-EDIT: правка claims в active → candidate + PROMOTE; прямые правки active — только human_notes | §6.6 |
| FIN-CGPT-008 | Канонический source registry (`sources/registry.yaml`) + lineage_id; карточки не копируют метаданные | §3.2 |
| FIN-CGPT-010 | Грамматика коммитов — commit-msg hook (не pre-commit) | §5.1 |
| F1 (Grok) | Naming candidate-файлов, tools/diff_candidate.py, правило отклонения | §6.1, §6.2 |
| F2 (Grok) | Операционное определение cohort для эскалации | §9 |
| F3 (Grok) | Протокол fallback-экстракции | §6.1 |
| F4 (Grok) | Артефакт pilot/phase-b-results + шаг калибровки | §8-B |
| F6 (Grok) | tools/impact_tiers.yaml — реестр tier'ов, читается validate.py | §9 |
| FIN-CGPT-009, 011; F5 | Backlog (не блокируют по критерию) | Приложение B |

---

## 0. Changelog v2.0 → v3.0

1. **Введён слой tools/** — детерминированные Python-инструменты validate.py и query.py [Q2, T2]. Система больше не «zero-code»; это осознанное решение: правила без исполняемого enforcement гниют (консенсус обоих аудитов).
2. **Модель claims**: сравнимые характеристики — не скаляры, а структуры с областью применимости `{value_raw, value_normalized, unit, scope, conditions, measurement_basis, source_id}` [C1].
3. **Канон данных — YAML frontmatter**; тело карточки — детерминированно генерируемый рендер, не редактируется независимо [Q5, T5].
4. **Идентичность источника — content hash**, не имя файла; карточка несёт `sources[]`, каждый claim ссылается на source_id [AUD2-003, 013].
5. **Экстрактор PDF**: markitdown заменён page-aware кандидатами (PyMuPDF4LLM, Marker), выбор — по бенчмарку Фазы A; fallback-протокол для плохой экстракции [Q4, T4].
6. **Статусы**: `review_status` (draft/active) + персистентные `block_reasons[]`; freshness и валидационные блокировки — вычисляемые [Q6, T6].
7. **INGEST через candidate-файлы**: существующая active-версия никогда не перезаписывается до promotion [AUD2-007]; ревизия того же документа = supersession, не contradiction [AUD2-020].
8. **Риск-ярусный review** с калибровкой по пилоту и автоэскалацией на cohort [Q7, T7].
9. **LINT разделён**: машинный (validate.py, непрерывно) и семантический (LLM, квартально) с безопасным режимом отказа [A2-mod].
10. **OUTPUT-validation в MVP**: derived-значения отчётов пересчитываются validate.py по ограниченному DSL [Q8, T8] — решение делиберации 2:1 против позиции архитектора.
11. **Двухфазный пилот** с предрегистрированным составом validation set (Lenovo + HP/HPE, тяжёлые layout) [Q3, T3].
12. **Wikilinks — best-effort, вне контрольного контура** [Q1, T1].
13. **Обязательный private GitHub remote** как off-host backup; формулировки «неизменяемость» заменены на versioning/rollback/tamper-evidence [C6].
14. **`pipeline_version`** в каждой карточке; изменение pipeline → прогон sentinel-набора [AUD2-018].

---

## 1. Концепция и роли

Персональная база знаний для каталогизации и конкурентного анализа серверного оборудования (Lenovo vs HP/HPE и др.). Паттерн «LLM Wiki» (Karpathy): инкрементальная персистентная база плоских Markdown-файлов вместо RAG.

| Роль | Отвечает за |
|---|---|
| Человек-оператор (владелец) | Загрузка первоисточников; бизнес-задачи (ТЗ, сравнения); review по риск-ярусной схеме (§9); разрешение противоречий; вето на любое изменение данных |
| LLM-агент (Claude Code) | Извлечение, перевод прозы, создание candidate-карточек, линковка, отчёты, git-коммиты |
| tools/ (детерминированный код) | Валидация схемы/provenance/переходов; воспроизводимый отбор карточек; пересчёт derived-значений; блокировка брака (fail-closed) |

**Принцип разделения:** LLM порождает контент, код проверяет форму и арифметику, человек судит истинность. Ни один из трёх не совмещает две роли. Ни один критичный механизм не держится на дисциплине человека (проектный критерий из A11).

---

## 2. Технологический стек

| Компонент | Инструмент | Статус |
|---|---|---|
| Хранилище/интерфейс | Obsidian (Markdown) | Базовый |
| Версионирование | Git + **обязательный private GitHub remote** (off-host backup, внешняя копия истории) | Базовый |
| Агент | Claude Code | Базовый |
| Enforcement/QUERY-отбор | **tools/validate.py, tools/query.py** (Python; см. §5) | Базовый |
| Извлечение PDF | **PyMuPDF4LLM (кандидат по умолчанию) / Marker (кандидат для тяжёлых таблиц)** — финальный выбор по бенчмарку Фазы A [T4] | Базовый |
| Витрина для человека | Dataview (Obsidian) — только визуализация; агент Dataview не использует [AUD2-005] | Базовый |
| Текстовый поиск | grep / поиск Obsidian | Базовый |
| Гибридный поиск (qmd и аналоги) | — | Отложен. Сигнал ввода: падение recall на known-answer QUERY-бенчмарке ЛИБО оператор чаще 1 из 5 запросов вручную дополняет candidate set [C5]. Порог по количеству карточек удалён |
| markitdown | — | Допустим только как вторичное «читабельное» представление; в конвейере извлечения не участвует |

---

## 3. Архитектура данных

### 3.1. Слои

| Слой | Содержимое | Права | Enforcement |
|---|---|---|---|
| `raw/` | Оригиналы PDF (даташиты, гайды, support matrices), брифы ТЗ | Только добавление | pre-commit hook по git-status: статус `A` (новый файл) — разрешён; `M`/`D`/`R` (изменение/удаление/переименование закоммиченного) — блокируются [FIN-CGPT-003]. Исключительное удаление/замена — отдельная owner-only операция с явной записью в commit message. Git + remote — откат и внешняя история; OS chmod не применяется [A12] |
| `wiki/` | Карточки (canonical YAML + рендер-тело), candidate-файлы, `contradictions.md`, `lint-findings.yaml` | Агент — через workflows §6; человек — нефактические поля напрямую, claims только через HUMAN-EDIT §6.6 [FIN-CGPT-007], всегда отдельным коммитом до операций агента [C4] | validate.py на pre-commit + commit-msg hook; clean-worktree preflight каждой операции |
| `outputs/` | Отчёты сравнения, подборки под ТЗ, отчёты семантического LINT | Агент пишет, validate.py пересчитывает derived, человек валидирует | DSL-пересчёт [T8] |
| `tools/` | validate.py, query.py, миграционные скрипты, тесты | Изменения — только через явное решение владельца | Тесты; версия фиксируется в pipeline_version |
| `audits/`, `deliberation/` | Процесс развития системы | Каждый участник пишет только свои файлы | Git-история; проверка коммитов владельцем |

**Терминология [C6]:** git даёт versioning, rollback и tamper-evidence (через remote), но не «неизменяемость» — слово из v2 изъято как преувеличение.

### 3.2. Идентичность источников и канонический реестр [AUD2-013, FIN-CGPT-008]

При INGEST вычисляется `source_id = SHA256(содержимое файла)` и создаётся/обновляется запись в **едином каноническом реестре `sources/registry.yaml`** — единственном месте хранения метаданных источника:

```yaml
"sha256:ab12…":
  file: "raw/lenovo-sr650-v3_2026-03.pdf"   # отображение
  doc_type: datasheet
  doc_date: "2026-03"
  revision: "1.4"
  imported_at: "2026-08-13"
  lineage_id: "lenovo-sr650-v3:datasheet:main"   # стабильный ID семейства документа
  supersedes: "sha256:cd34…"                      # предыдущая ревизия того же lineage (или null)
```

`lineage_id` присваивается при INGEST явно (человек подтверждает при неоднозначности) — это решает случай нескольких независимых документов одного doc_type у одной модели: разные support matrices получают разные lineage_id и не могут ошибочно supersede друг друга. Карточки ссылаются на source_id и НЕ копируют авторитетные метаданные; validate.py запрещает конфликт метаданных для одного source_id. Provenance = source_id + page index + текстовый fingerprint; переименование или подмена файла не ломает и не подделывает provenance.

### 3.3. Lineage и supersession [AUD2-020, FIN-CGPT-005]

Новая ревизия документа того же lineage = **supersession**: создаётся candidate-версия карточки (§6.1). **Загрузка новой ревизии в raw/ — информационное событие, не блокирующее:** текущая active-карточка остаётся полностью eligible на весь период review candidate (derived-флаг `newer_source_loaded` виден человеку, но не входит в effective_block_reasons). Замещение старой версии становится действующим **атомарно в момент успешного PROMOTE candidate** — так система никогда не остаётся без последней подтверждённой версии. Исключение — отзыв документа вендором (retraction): отдельная owner-only операция немедленной блокировки. **Contradiction** — только несовместимые claims с одинаковым scope из разных lineage; фиксируется в `contradictions.md`, решает человек.

---

## 4. Схема данных

### 4.1. Служебный frontmatter карточки

```yaml
card_id: "lenovo-sr650-v3#a1b2c3"   # СТАБИЛЬНЫЙ ID логической карточки: одинаков у active
                                     # и её candidate, переживает supersession, MIGRATE,
                                     # переименования [FIN-CGPT-001, V-CGPT-001]
revision_id: "r3"                    # ID ревизии карточки; НОВЫЙ у каждого candidate.
                                     # Глобально уникальна ПАРА (card_id, revision_id) —
                                     # именно её проверяет validate.py [V-CGPT-001]
schema_version: "3.1.1"
review_status: draft            # draft | active
block_reasons: []               # ТОЛЬКО персистентные семантические причины
                                # (contradiction_pending, human_flag, extraction_manual_review)
pipeline_version: "p1"          # ссылка на запись в PIPELINES.md (в Фазе A — exp-*, см. §8-A)
sources: ["sha256:ab12…"]       # только ссылки на sources/registry.yaml;
                                # метаданные НЕ дублируются [FIN-CGPT-008]
human_notes: ""
human_approved_at: null         # ставится при promotion
```

**Вычисляемое, не хранимое [T6]:** информационный флаг `newer_source_loaded` (из registry.supersedes против active-карточек; НЕ блокирует — см. §3.3 [FIN-CGPT-005]), валидационные блокировки (unsourced claims, schema mismatch, открытые LINT-findings — §6.4). QUERY-eligibility = `review_status == active` AND `effective_block_reasons == []`, где effective = persisted + derived; derived вычисляет validate.py на каждом прогоне.

### 4.2. Claims — сравнимые характеристики [C1]

Каждая сравнимая характеристика — список claims (не скаляр):

```yaml
ram_max:
  - claim_id: "a1b2c3-ram-001"          # уникален внутри ревизии; между ревизиями одной
                                         # карточки СОХРАНЯЕТСЯ при семантической идентичности
                                         # и МЕНЯЕТСЯ при изменении утверждения [V-CGPT-001]
    value_raw: "Up to 8TB (32x 256GB 3DS RDIMM)"   # дословно из источника
    value_normalized: 8192
    unit: "GB"
    constraints:                          # СТРУКТУРИРОВАННЫЕ предикаты [FIN-CGPT-002] —
      cpu_count: 2                        # типы и словарь замораживаются в Фазе A
      dimm_population: "32x 256GB 3DS RDIMM"
    constraints_raw: "2x CPU, 32x 256GB 3DS RDIMM"  # исходный текст условия — для provenance
    measurement_basis: "total"            # controlled vocabulary: total | per_socket | per_channel …
    source_id: "sha256:ab12…"
    anchor: {page: 4, fingerprint: "Memory: Up to 8TB"}
  - claim_id: "a1b2c3-ram-002"
    value_raw: "Up to 4TB"
    value_normalized: 4096
    unit: "GB"
    constraints: {cpu_count: 1}
    constraints_raw: "single-processor configurations"
    measurement_basis: "total"
    source_id: "sha256:ab12…"
    anchor: {page: 4, fingerprint: "single-processor configurations"}
```

Правила: (1) value_raw и constraints_raw — дословно, переводится только проза; (2) канонические единицы фиксирует схема; конверсия — явная; (3) claim без claim_id и без валидного provenance (см. ниже) = ERROR валидации; (4) **сопоставимость решает query.py детерминированно и только по структурированным полям**: constraints-предикаты и measurement_basis из controlled vocabulary, зафиксированного в Фазе A [FIN-CGPT-002]. Свободный текст в сравнении не участвует; «2x CPU» и «dual processor» становятся одним предикатом `cpu_count: 2` на этапе извлечения. Несопоставимость отражается в отчёте явно, а не молча усредняется. Claim с constraints, не выразимыми словарём, получает предикат `unmodeled: true` и исключается из автоматического сравнения (попадает в отчёт как «требует ручного сопоставления»).

**Идентичность claims между ревизиями [V-CGPT-001]:** claim_id уникален внутри ревизии; **между ревизиями одной карточки (active ↔ candidate) повтор claim_id разрешён и обязателен, если claim семантически идентичен** (совпадают value_raw, constraints, measurement_basis, source_id, anchor); **изменённый или заменённый claim получает новый claim_id**. Ссылки из outputs/ и lint-findings на `(card_id, claim_id)` тем самым остаются валидными для неизменённых значений и корректно инвалидируются для изменённых. Инварианты проверяет validate.py; глобальной уникальности claim_id не требуется.

**Provenance двух типов [FIN-CGPT-007-остаток]:** каждый claim несёт `provenance_type: source | human`. Для `source` (по умолчанию): обязательны source_id (существующий в registry) + anchor. Для `human` (typed human assertion из §6.6): source_id и anchor НЕ требуются и не проверяются против registry; вместо них обязательны `asserted_by: owner`, `asserted_at: <дата>`, `justification: <текст>`; query.py при конфликте предпочитает human assertion, все такие значения в отчётах маркируются явно.

### 4.3. Доменные поля

Черновой перечень v2 (§4.4) сохраняется как гипотеза; финальный состав, канонические единицы и impact-tier каждого поля [T7a] фиксируются по итогам Фазы A пилота, ДО Фазы B [C3].

### 4.4. Версионирование схемы

`schema_version` в каждой карточке. Миграция = детерминированный скрипт в tools/ (может быть написан агентом, исполняется как код) + dry-run + validate.py до коммита [AUD2-014]. Сосуществование версий в active запрещено.

---

## 5. Слой tools/ [Q2, T2]

Требования к обоим инструментам: **без LLM внутри; фиксированные вход/выход; fail-closed** (сомнение = блокировка, не пропуск); покрыты тестами; изменение — только решением владельца с фиксацией новой версии в pipeline_version.

### 5.1. validate.py

**Разделение hook'ов [FIN-CGPT-010]:** проверки данных/схемы — pre-commit; грамматика commit-сообщений `[INGEST|PROMOTE|QUERY|LINT|LINT-FIX|MIGRATE|HUMAN-EDIT|RAW-ADMIN]` — **commit-msg hook** (pre-commit не видит итогового сообщения), оба вызывают соответствующие режимы validate.py.

Проверяет (pre-commit и по команде): соответствие claims схеме и schema_version; **уникальность пары (card_id, revision_id); стабильность card_id между active и candidate; инварианты наследования claim_id между ревизиями (повтор = семантическая идентичность; изменение = новый ID) [V-CGPT-001]**; для `provenance_type: source` — существование source_id в `sources/registry.yaml` и файла в raw/ (по hash) + синтаксис anchor; для `provenance_type: human` — обязательность asserted_by/asserted_at/justification, registry-проверка не применяется [FIN-CGPT-007]; отсутствие конфликта метаданных registry [FIN-CGPT-008]; принадлежность constraints и measurement_basis замороженному словарю [FIN-CGPT-002]; допустимость переходов review_status; git-status правило raw/ (A разрешён, M/D/R блок в обычных режимах) [FIN-CGPT-003]; целостность рендер-тела против YAML [T5]; **пересчёт derived-значений в outputs/ по DSL** (whitelist: + − × ÷, ratio, percent_delta, unit-конверсия по фиксированной таблице; расхождение = блокировка отчёта) [T8]; чтение `wiki/lint-findings.yaml` и включение открытых findings в derived-блокировки [FIN-CGPT-006]; чтение `tools/impact_tiers.yaml` для риск-ярусного review [F6]; счётчики эскалации review [T7b,c].

**Режим RAW-ADMIN [FIN-CGPT-003-остаток]:** единственный путь для M/D/R в raw/ — явный вызов `validate.py --raw-admin` владельцем. Режим: (1) проверяет ссылочную целостность — если удаляемый/заменяемый source_id упоминается в claims active-карточек, операция блокируется до перевода этих claims через HUMAN-EDIT или до supersession; (2) требует причину, которая пишется в registry (`removed_at`, `removal_reason`) и в commit message `[RAW-ADMIN] …`; (3) запись registry для удалённого source_id не удаляется никогда (историческая целостность provenance). Обычные режимы validate.py продолжают блокировать M/D/R безусловно.

### 5.2. query.py

Вход: критерии отбора (поля, constraint-предикаты). Выход: воспроизводимый candidate set — JSON со списком **card_id/claim_id** [FIN-CGPT-001] + применённые критерии. Ссылки только по неизменяемым ID, никогда по имени файла или индексу массива. Один запрос к одной версии базы = один результат. Отбирает только eligible-карточки; сопоставимость — только по структурированным предикатам (§4.2). Dataview агентом не используется — только человеком как витрина.

---

## 6. Workflows

Триггер всех операций — человек запускает сессию (агент — не демон). **Preflight каждой операции: clean git worktree** [C4]; незакоммиченные правки человека сначала фиксируются его отдельным коммитом.

### 6.1. INGEST

1. Оператор кладёт PDF в raw/, даёт команду.
2. Скрипт вычисляет source_id, создаёт запись в `sources/registry.yaml` с lineage_id (при неоднозначности lineage — вопрос человеку) [FIN-CGPT-008]. Переименование файлов не требуется — идентичность по hash [A1-mod].
3. Page-aware экстракция. **Fallback-протокол [F3]:** страница с quality ниже порога или image-only → (а) команда re-extract с альтернативным backend (Marker вместо PyMuPDF4LLM — список допустимых путей в PIPELINES.md); (б) если и он не справился — ручной ввод значений человеком с anchor вида `{page: N, manual: true}` и записью в human_notes; (в) до разрешения — block_reason `extraction_manual_review`, promotion невозможен [T4].
4. Агент строит claims с constraint-предикатами (перевод — только проза), генерирует рендер-тело, ставит best-effort wikilinks [Q1].
5. Существует active-версия карточки? → пишется **candidate-файл `<имя-карточки>.candidate.md`** рядом [F1], active не трогается [AUD2-007]. Supersession vs contradiction — по §3.3; contradiction → запись в contradictions.md, стоп, вопрос человеку.
6. validate.py; коммит `[INGEST] …`. Карточка/candidate в review_status: draft.

### 6.2. PROMOTE (отдельная операция)

1. Для candidate: оператор запускает `tools/diff_candidate.py <card_id>` — структурированная дельта по claims (новые / изменённые / удалённые, с value_raw обеих версий) [F1]. Сравнение YAML глазами не предполагается.
2. Review по риск-ярусной схеме §9 → человек одобряет → validate.py финальный прогон → draft/candidate становится active; для candidate замещение старой версии происходит **атомарно в этом шаге** [FIN-CGPT-005]; `human_approved_at` проставляется; коммит `[PROMOTE] …`.
3. **Отклонение candidate** — явный коммит удаления candidate-файла с причиной в commit message [F1]; молчаливого «зависания» кандидатов протокол не допускает (очередь и возраст кандидатов — backlog-инструмент, Приложение B).
4. Изменение уже approved claims — review обязателен всегда [AUD2-008]; выборочность применима только к новым карточкам.

### 6.3. QUERY

Обязательная цепочка: только через INGEST→PROMOTE; ad-hoc анализ raw/ в обход не существует [AUD2-021]. Отбор — query.py; синтез отчёта — агент; каждое первичное число наследует provenance claim'а; каждое derived-число несёт inputs (claim refs) + формулу DSL; validate.py пересчитывает; отчёт в outputs/, коммит `[QUERY] …`, валидация человеком.

### 6.4. LINT (двухконтурный) [A2-mod, FIN-CGPT-006]

**Машинный контур** — validate.py: непрерывно (pre-commit) и полным прогоном по команде; человека не требует.
**Семантический контур** — LLM, квартально: правдоподобность значений против источников, качество перевода, пропущенные в извлечении поля. **READ-ONLY по отношению к карточкам без исключений.** Результат — два артефакта: человекочитаемый отчёт `outputs/lint-*.md` и машиночитаемый реестр находок `wiki/lint-findings.yaml` (finding_id, card_id/claim_id, класс, статус open/closed). Карточки LINT не изменяет; блокировка достигается иначе: **validate.py читает реестр и включает открытые findings в derived-часть effective_block_reasons** — карточка выпадает из QUERY без единой мутации её файла. Безопасный режим отказа сохранён: неразобранный отчёт = «меньше карточек в выдаче». Закрытие finding — решение человека: либо исправление коммитом `[LINT-FIX] …` (для claims — через HUMAN-EDIT §6.6), либо отклонение находки; статус в реестре меняется соответствующим коммитом.

### 6.5. MIGRATE

По §4.4. Коммит `[MIGRATE] …`.

### 6.6. HUMAN-EDIT [FIN-CGPT-007]

Прямые правки active-карточки человеком разрешены **только для нефактических полей**: human_notes, wikilinks, проза рендер-тела, не связанная со значениями. **Любое изменение machine-readable claim в active-карточке идёт через candidate:** операция HUMAN-EDIT создаёт candidate (новый revision_id, тот же card_id [V-CGPT-001]) с изменённым claim, сбрасывает approval для затронутых значений и требует полного цикла PROMOTE (включая provenance нового значения). Намеренный override источника человеком («в даташите опечатка, я знаю правильное значение») не переписывает sourced claim, а добавляет **typed human assertion** — отдельный claim с `provenance_type: human` и обязательными asserted_by/asserted_at/justification (§4.2) [FIN-CGPT-007]; query.py при конфликте предпочитает human assertion, отчёт помечает такие значения явно. validate.py блокирует коммит, изменяющий claims active-карточки в обход HUMAN-EDIT.

---

## 7. CLAUDE.md и PIPELINES.md

**CLAUDE.md** — инструкция агенту: схема, контракты, протоколы workflows, стандарты перевода. НЕ механизм безопасности — всё критичное продублировано в tools/ [из v2, подтверждено].
**PIPELINES.md** — реестр версий конвейера: p1 = {модель, экстрактор+версия, SHA CLAUDE.md, версия tools/}. Любое изменение состава → новая запись + прогон фиксированного sentinel-набора документов; регресс = откат изменения [AUD2-018].

---

## 8. Пилот (двухфазный) [Q3, C3, T3]

**Фаза A — schema discovery + бенчмарк экстракции (5 документов).**

*Bootstrap-протокол [FIN-CGPT-004]:* до создания p1 действует экспериментальный режим — pipeline versions `exp-1, exp-2, …` регистрируются в PIPELINES.md как experiment runs (состав фиксируется, но меняется свободно); карточки Фазы A несут `pipeline_version: exp-*` и experimental schema_version, могут существовать **только в review_status: draft** и никогда не eligible для QUERY и PROMOTE — validate.py это обеспечивает. Гейты системы не обходятся: они формально выполняются, просто production-ветка ещё пуста.

Содержание: PyMuPDF4LLM vs Marker на реальных Lenovo/HPE PDF с матричными таблицами — по **зафиксированной до первого прогона scoring-рубрике** (полнота таблиц, сохранность связей строка/столбец, привязка footnotes, page anchoring, детекция image-only; единица оценки и порог fallback — часть рубрики; результаты — benchmark-артефакт) [FIN-CGPT-011→частично, остальное Приложение B]. Параллельно: финализация доменных полей, канонических единиц, **constraint-словаря и controlled vocabulary measurement_basis [FIN-CGPT-002]**, impact-tiers (→ `tools/impact_tiers.yaml` [F6]). По завершении — **заморозка схемы и pipeline: создаётся запись p1; только p1+ допускает promotion**. Карточки exp-* пересоздаются на p1 или удаляются.

**Фаза B — blind validation (16 документов: 10 Lenovo + 6 HP/HPE).**
Состав фиксируется ДО начала: оба вендора; классы rack 1U/2U, tower, edge; обязательные классы сложности — matrix-таблицы конфигураций, footnotes «see Note N», multi-configuration «up to», image-содержащие страницы [T3]. Сплошная ручная сверка всех полей. **Результаты фиксируются структурированно в `pilot/phase-b-results.yaml`** (card_id, поле/claim_id, expected, extracted, error_class, impact_tier_proposed) [F4]; по завершении — явный шаг калибровки: из phase-b-results выводятся N выборки, порог эскалации и итоговые impact-tiers, записываются в конфиг tools/ — «ощущение качества» без чисел результатом пилота не является.

**Предрегистрированные метрики (фиксируются до Фазы B):**
- eligibility-критичные поля (по impact-tier из Фазы A): ошибки = **0** (отдельный gate);
- completeness/recall: доля полей источника, пропущенных извлечением — порог фиксируется в Фазе A [AUD2-016];
- claims без provenance: **0** (обеспечивает validate.py);
- ошибки перевода, искажающие смысл: 0;
- агрегатная ошибка числовых значений ≤2% — вторичная метрика.

Провал → разбор класса ошибок, правка pipeline, повтор Фазы B на новых документах. Результат пилота = adversarial coverage, не статистическая гарантия [T3]. Калибровка N и порога эскалации для §9 — из данных Фазы B [T7b].

---

## 9. Риск-ярусный review [Q7, T7]

- **Tier 1 (eligibility-критичные):** поля, способные изменить включение модели в shortlist или итог сравнения (определяются по impact, не статическим списком; классификация — из Фазы A, хранится в **`tools/impact_tiers.yaml`**, читается validate.py; обновление реестра — только по итогам пилота или явным решением владельца) [F6]. Проверка человеком — всегда, при INGEST и PROMOTE.
- **Tier 2 (остальные):** выборка 1 из N (N — из phase-b-results).
- **Эскалация (автоматика validate.py):** ошибка в выборке → сплошная проверка текущей карточки И всех карточек того же cohort до восстановления чистой серии [T7c]. **Операционное определение cohort [F2]: одинаковый pipeline_version + одинаковый doc_type + одинаковый layout-class** (классификация layout — из бенчмарк-рубрики Фазы A, фиксируется в записи источника при INGEST). Размер cohort и поведение при превышении разумного объёма сплошной проверки (например, cohort > 15 карточек → эскалация ставит cohort в очередь с приоритизацией по impact) — параметры конфига tools/. Счётчики ведёт код, не человек.

---

## 10. Заимствования и отклонения от доноров

| Компонент | Донор | Статус |
|---|---|---|
| Скелет структуры, workflow-паттерн, symlink для Obsidian | SamurAIGPT/llm-wiki-agent (MIT) | Принято |
| Zero Hallucination (provenance), contradictions + human-in-the-loop, lifecycle, git-native | JPeetz/MeMex-Zero-RAG (MIT) | Принято, расширено (claims/scope, tools/) |
| markitdown-конвертация | llm-wiki-agent | **Отклонено** решением делиберации [Q4]: разрушает таблицы, теряет пагинацию |
| Гибридный поиск | tobi/qmd и производные | Отложен, сигнальный критерий §2 |

Доменный слой (claims со scope, схема серверных спецификаций, impact-tiers, RU-перевод) — собственная разработка.

---

## Приложение A. Реестр решений

| Решение | Основание | Раздел v3 |
|---|---|---|
| Q1: wikilinks best-effort | Делиберация, единогласно | §6.1, T1 |
| Q2: tools/ в базовом стеке | Делиберация, единогласно | §5 |
| Q3: полный двухфазный пилот | Делиберация, единогласно | §8 |
| Q4: page-aware экстрактор | Делиберация, единогласно | §2, §6.1, §8-A |
| Q5: YAML канон | Делиберация, единогласно | §4, T5 |
| Q6: 2 поля статуса + вычисляемое | Делиберация, единогласно | §4.1, T6 |
| Q7: риск-ярусный review | Делиберация, единогласно | §9 |
| Q8: OUTPUT-пересчёт в MVP | Делиберация 2:1 (архитектор уступил) | §5.1, §6.3, T8 |
| Полные диспозиции 30 находок | disposition-v2.md | по тексту |
| Ратификация Q1–Q8 | Владелец, 2026-08-13 | — |
| Закрытие FIN-CGPT-001…008, 010; F1–F4, F6 | Финальный аудит → v3.1 | §0.1 |

## Приложение B. Backlog (не блокирует запуск)

| # | Источник | Суть | Когда закрыть |
|---|---|---|---|
| B1 | FIN-CGPT-009 | Machine-readable правило нормализации единиц (conversion_rule / parsed raw numeric+unit; нормализация детерминированным кодом по versioned unit table) | Фаза A, вместе с заморозкой схемы — до Фазы B |
| B2 | FIN-CGPT-011 (остаток) | Полный benchmark-артефакт с воспроизводимым скорингом обоих экстракторов | До завершения Фазы A |
| B3 | F5 | tools/status.py или Dataview-очередь кандидатов на PROMOTE с возрастом | По мере роста базы |
