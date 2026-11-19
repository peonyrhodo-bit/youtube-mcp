# Director 3.0 — проект памяти: контракт реализации v1

Дата: 2026-11-19. **Статус: проект архитектуры для согласования, без изменения production.** Основание: `MEMORY_INTELLIGENCE_2_DESIGN.md`, `MEMORY_2_BOUNDED_CONTEXT_CONTRACT.md`, `MEMORY_2_ACCESS_MAP.md`, неизменяемое ТЗ Director 3.0. Этот документ отделяет проект памяти от общего аудита M01–M40.

## 1. Три уровня памяти и владельцы данных

| Уровень | Содержимое | Источник истины | Допустимые действия |
|---|---|---|---|
| L0 — долговременная память | исходные исследования и снимки, прогнозы/факты, решения, согласования, рекомендации, задачи, планы, история статусов, provenance | существующий Supabase, без миграции на первом этапе | append/update по текущим контрактам; никакого автоматического удаления |
| L1 — индекс/представление | ID, project_id, тип, created_at, status, короткое резюме, evidence IDs, полнота и версия | вычисляемая проекция из L0; не замена L0 | безопасное чтение и воспроизводимое пересоздание |
| L2 — рабочий контекст | последние релевантные факты, открытые обязательства, компактные сигналы, ссылки на L0 | временный объект одного цикла Director | ограничить по байтам и времени жизни; не сериализовать внутрь нового L0 result |

**Принцип:** полный исторический результат никогда не вкладывается в следующий результат целиком. Цикл хранит собственный итог и **ссылки** на источники; при необходимости читает конкретный источник отдельно.

## 2. Контракт L1: ResultRef (проект API, не утверждение о существовании endpoint)

```json
{
  "source_table": "director_results",
  "source_record_id": 9,
  "project_id": "<validated project scope>",
  "run_id": 79,
  "result_type": "autonomous_cycle",
  "created_at": "<UTC timestamp>",
  "status": "<existing status or null>",
  "summary": "<bounded plain text>",
  "evidence_ids": [],
  "details_omitted": true,
  "read_completeness": "complete"
}
```

IDs и поля должны проверяться по реальной схеме и legacy project matching; пример не является миграцией. Никаких секретов, full `data_json`, рекурсивного `memory_state`, вложенного `work_plan.basis` в ResultRef. Неизвестное поле = явное null/unknown, не выдумывать.

## 3. Контракт L2: ContextEnvelope

Поля: `schema_version`, `project_id`, `as_of`, `completeness` (`complete|partial|error|unavailable`), `limits` (byte cap, row cap, actual bytes), `source_counts`, `omitted_counts`, `protected_open_items` (IDs и статусы), `recent_result_refs`, `evidence_refs`, `last_successful_cycle_ref`, `errors`. Статус `partial` никогда не маскируется под пустую успешную память.

**Лимиты — предложения для offline тестов, не production настройки:** общий сериализованный L2 <=64 KiB, `recent_result_refs` <=20, `summary` <=512 UTF-8 bytes на объект. Считать именно `len(json.dumps(..., ensure_ascii=False).encode('utf-8'))`; если ограничение не выдержано, детерминированно убирать необязательные элементы и показывать omitted counts. Если защищённые открытые решения/согласования не помещаются, выставить `partial` и запретить автономные действия, зависящие от невидимых условий; **не отбрасывать тихо**. Числа согласовать по измерениям до внедрения.

## 4. Точки изменения (только будущий patch, после разрешения)

1. `memory/supabase.py:get_context/get_recent_results`: добавить отдельный bounded projection/read method, сохранить существующий full read API для drill-down и совместимости; фильтрация project_id и порядок неизменны.
2. `memory/memory.py:_build_memory_context`: заменить `memory_state.recent_results=results` и raw `context.results` на ResultRef в operational ветке; не мутировать исходные записи. `Memory.snapshot` должен выдавать тот же компактный envelope.
3. `director/director.py:_memory_state_summary` и `_merge_context`: принимать только bounded envelope, не копировать full `data_json` в `work_plan.basis` или `project_assessment`.
4. `director/director.py:_autonomy_assess` и `server.py` логирование: печатать counts, IDs, completeness, sizes, а не полные work_plan/assessment JSON.
5. `server.py:run_director_autonomous_cycle` и `memory/supabase.py:update_run`: сохранить все защищённые решения, статусы и ссылки; оптимизацию write path и миграцию схемы **не смешивать** с первым исправлением bounded context.

## 5. Чтение полной истории без переполнения RAM

Будущий read-only drill-down по `source_table + source_record_id + project_id`, с проверкой принадлежности проекту и явным `not_found|forbidden|unavailable`. Для истории — cursor/keyset страницы и заданные time/project фильтры, без массовой материализации `data_json`. До реализации endpoint не обещать, что он существует; полный источник уже хранится в Supabase.

## 6. Тесты и критерии готовности проекта

Использовать BC-01…BC-10 из `MEMORY_2_BOUNDED_CONTEXT_CONTRACT.md`: synthetic 2.34 MB, 5–20 вложенных результатов, project isolation, protected approvals, partial/error, snapshot, logs, ×2/×5 рост, full retrieval. Дополнительно сравнить hash L0 до/после, полные counts и ссылки, статусы failed/partial/success, legacy совместимость. Gate: 0 необъяснённых потерь данных, 0 скрытых защищённых ограничений, детерминированный byte cap; peak RSS измерять отдельно, не заявлять его снижение без профиля.

## 7. Последовательность и отдельные согласования

**A.** Offline contract tests + fixture + измерение размера L2. **B.** Малый обратимый code patch под feature flag (L1/L2), без schema change. **C.** Offline parity + нагрузочные тесты и проверка на Render только с отдельным разрешением deploy. **D.** Затем отдельный проект incremental analytics и retention/archive, без автоматической очистки. Точки согласования: (1) byte cap, (2) разрешение code patch, (3) deploy/canary, (4) любые миграции/удаления/внешние расходы. Отдельный аудит quota/M15 не должен блокировать завершение **дизайна памяти**, но ошибки исследовательских вызовов учитываются в автономном режиме.

**Итог:** архитектурный контракт памяти подготовлен; **не реализован и не принят**. 0/40 общих контрольных этапов формально принято.

## 8. Обязательная поправка: output cap != peak RSS (верификация live SHA)

Повторная проверка live `site-insight-engine@09ceb05f`: `memory/memory.py:Memory.get_context` (267–325) **сначала** вызывает `backend.get_context` (289–323), **затем** `_build_memory_context` (325); последний на 339 получает полные `results`, на 399–408 копирует их в `memory_state`. Следовательно, **постфактум-проекция** в Python ограничит размер сериализованного ответа/повторное сохранение, но **не гарантирует снижение peak RSS**, поскольку full `data_json` уже материализован backend. Также в `_build_memory_context` защищённые lists (constraints/recommendations/actions/decisions) передаются как полные dict; общий лимит только results недостаточен.

**Два независимых acceptance gate:**

- **Gate A (anti-amplification):** L2 и work_plan/logs/новые результаты не содержат full historical JSON; BC/BM тесты подтверждают byte cap, immutable L0, статус incomplete и сохранность защищённых ссылок. Это не считается доказательством решения OOM.
- **Gate B (bounded read/RSS):** отдельный read-model метод backend выбирает только нужные колонки, применяет project scope и детерминированный pagination, **не загружая full data_json** для списка; если требуемый summary существует только внутри data_json, нужно проектировать безопасную ограниченную серверную проекцию/новый индекс после проверки схемы, а не выдавать client-side truncation за bounded read. Full detail читается отдельным точечным запросом по ID. Проверить на Supabase backend и FREE_MODE backend, включая legacy project filtering. Измерить пик RSS, количество/размер HTTP payload, latency на больших synthetic fixtures и реальном read-only профиле. Gate B без результатов измерений не принят.

**Порядок:** сначала Gate A offline (снижение амплификации), затем Gate B (снижение входящего объёма и RSS), и только потом canary. До изменения кода выяснить, какие summary/status/project_id поля реально доступны как отдельные столбцы в `director_results` и других таблицах; не добавлять миграцию вслепую. Ни одна production операция этим документом не разрешена.

## 9. Подтверждённая схема Supabase для bounded read (SELECT only, 2026-11-19)

`information_schema.columns` в проекте `oxbxnswywgpdlcfltmbq`: `public.director_results` содержит `id bigint,created_at timestamptz,action_id bigint,run_id bigint,result_type text,summary text NOT NULL,data_json jsonb`; **отдельного project_id и status нет**. `public.director_runs` содержит `id,created_at,language,region_code,data_json,project_id,status,started_at,finished_at,current_step,error_message,updated_at`. `public.director_actions` содержит `id,created_at,run_id,decision_id,action_type,description,status,completed_at,data_json`; **нет project_id**. Таблицы `director_decisions`, `director_recommendations`, `director_constraints` не появились в выборке `information_schema.columns` с заданными именами; не утверждать, что защищённые сущности отсутствуют вообще: проверить фактическую схему/адаптер отдельно.

Read-only aggregates: `director_results` **8 rows**, 2 `data_json` >1 MiB, max `pg_column_size(data_json)=2,336,825 B`, max `octet_length(summary)=114 B`; `director_runs` **159 rows**, 5 >1 MiB, max 2,419,593 B; `director_actions` 0 rows. `pg_column_size` — физический размер Postgres значения, не сетевой размер или RSS. Числа актуальны только на момент SELECT.

**Решение для Gate B:** результат-лист запрашивать через `SELECT id,created_at,action_id,run_id,result_type,summary` **без data_json**, с ограничением строк и детерминированным порядком. `project_id` результата нельзя считать доступным: исследовать принадлежность через `director_results.run_id → director_runs.id/project_id` (и обработку NULL/legacy), не вводить небезопасную cross-project выборку. Для runs выбирать `id,created_at,project_id,status,started_at,finished_at,current_step,error_message`, без data_json. Status у result = **unknown**, пока не установлен допустимый способ извлечения, не угадывать из payload. Полные детали — только явный точечный read с проверкой project scope. **Не утверждать, что PostgREST join уже реализован или работает**, до проверки backend контрактов. Схема миграции не требуется для первой версии компактного списка, но может потребоваться оптимизация индекса после профиля.

## 10. Проверка project scope для director_results (SELECT only)

2026-11-19, Supabase project `oxbxnswywgpdlcfltmbq`: `LEFT JOIN director_results r ON director_runs d.id=r.run_id` дал **8/8** результатов с непустым `run_id`, **0** orphan runs, **0** parent runs с NULL `project_id`, **8/8** scoped, **1** distinct project. `data_json ? 'project_id'` истинно для **8/8**, `data_json->>'project_id'=director_runs.project_id` также **8/8**. Это проверка **текущих 8 строк**, а не гарантия для будущих/legacy данных.

Live backend SHA `09ceb05f` `memory/supabase.py:_recent_for_project` 204–265 делает `.select('*')` и Python filter `_project_id_from_row` 192–202, который читает direct `project_id` или `data_json`; таким образом нынешний project filter **вынуждает загрузить большой JSON** до фильтрации. Предлагаемый альтернативный путь `director_results.run_id → director_runs.project_id` обоснован текущими строками, но **не эквивалентен автоматически legacy семантике**. Требуются offline tests для: NULL run_id, missing run, NULL parent project, mismatch embedded project vs parent, nested legacy project_id, run belonging to another project. При конфликте fail closed/partial и логировать только ID и категорию, не раскрывать данные другого проекта. Не переключать текущую логику без доказанной совместимости.

**Практический первый шаг Gate B:** тестовый read-model с выборкой `id,created_at,action_id,run_id,result_type,summary` и ограничением проектом через parent run; проверить PostgREST join или два ограниченных запроса только offline. Не читать `data_json` при построении списков. Никаких live API вызовов или миграций для этой проверки не требуется.
