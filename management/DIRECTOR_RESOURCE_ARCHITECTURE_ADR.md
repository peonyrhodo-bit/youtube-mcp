# ADR — ресурсно-устойчивая архитектура Director 3.0 (проект решения)

**Дата:** 2026-11-20. **Статус:** ПРОЕКТ, НЕ утверждённая поправка к ТЗ. **Основание:** обсуждение с владельцем 2026-11-20; новые факты из Supabase Dashboard Usage. **Приоритет:** критический инцидент доступности и риск повторения. **Охват:** Director, Memory 2.0, Supabase, Render, YouTube API, ручные и автоматические запросы.

## 1. Неподвижные требования (не ломать)
- Исходное `/тз директор 3,0` неизменно без отдельного согласования владельца. Не менять назначение Director, не сводить его к анализу одного канала: поддерживать предусмотренные ТЗ рынки, сегменты, исследования и рекомендации.
- Сохранять полноту исторических фактов, доказательств, прогнозов, результатов, рекомендаций, задач, согласий и пользовательских ограничений. Не удалять данные, не вводить TTL/автоочистку без отдельного утверждения и проверенного восстановления.
- Качество аналитики, корректность исторических сравнений, свежесть и происхождение доказательств важнее искусственно частых запусков. Не маскировать неполный анализ под полноценный. Сохранять автономность и возможность анализа по запросу в любое время.
- Нулевой бюджет; никаких платных тарифов/API, изменения production, Render, Supabase, YouTube-квот, деплоев и слияний без отдельного согласования. Не запускать живой YouTube поиск ради тестов. Запрет на автоматическое создание пользовательских задач/производство/публикации без согласия сохраняется.
- Отсутствие OOM, 402 и превышения квот нельзя обещать без измерений; при риске — безопасное ограничение работы с явным статусом.

## 2. Подтверждённый инцидент Supabase (со слов владельца: текст страницы Usage)
Организация `peonyrhodo`, тариф Free, период **10 ноября — 10 декабря 2026**. Страница Usage: **Services restricted**, ответы **HTTP 402**, причина **Egress Exceeded**. Uncached egress **37,98 / 5 ГБ (760%)**, превышение **32,98 ГБ**; cached egress **0 / 5 ГБ**; Database Size **0,104 / 0,5 ГБ (21%)**, отображаемый максимальный размер проекта **98,79 MB**; Storage **0 / 1 ГБ**. Это **сетевой исходящий трафик**, НЕ исчерпание размера БД или Storage. По сообщению Dashboard, снятие ограничения после начала следующего расчётного периода может происходить с задержкой; платный тариф — не согласован.
**Не доказано:** доля egress именно Director, конкретные endpoint/потребитель, причина 37,98 ГБ и профиль по каждому запросу. Часовые циклы и неограниченные полные чтения — обоснованная гипотеза, не установленная причина. Не приписывать весь трафик одному компоненту без разборки. Проверять другие API/потребители, число запросов, размеры ответов, повторные загрузки и ретраи. Факты Dashboard отличаются по моменту и методике от SQL `pg_database_size=88 452 243 B` на 2026-11-20; не объявлять противоречием.

## 3. Целевая модель поведения (предложение, не новое утверждённое ТЗ)
1. **Render boot / health check ≠ запуск Director.** Пробуждение сервиса не должно автоматически вызывать дорогой автономный анализ. Устранить/защитить стартовый `first_run_at=now`, проверить все триггеры, retries, дубли после restart и идемпотентность.
2. **Сбор данных ≠ глубокий анализ ≠ выдача рекомендаций.** Лёгкое плановое обновление и дешёвая проверка изменений; глубокий анализ по необходимости, по согласованному расписанию и по прямому запросу пользователя. Частота 24/сутки НЕ должна сохраняться только по инерции; изменение обязательных 24 слотов в ТЗ требует отдельного решения. До решения текущий контракт ТЗ остаётся действующим.
3. **Ручной запрос** (например, «Проанализируй британский сегмент YouTube») разрешён независимо от ежедневного расписания: оценить нужные рынки/язык/период, прочитать компактный контекст, выявить недостающие факты, запросить только обоснованные новые данные с предварительной оценкой YouTube-квоты, провести анализ, вернуть доказательства/ограничения, сохранить значимые выводы. Не скачивать всю историю по умолчанию.
4. **Утренний автоматический результат** желателен в первой половине дня по местному времени владельца. Ориентир **10:00**, пробуждение Render за **10–15 минут** — НЕ утверждённое расписание; уточнить часовой пояс, скорость cold start, реальные временные затраты и способ доставки результата. Будильник только будит/проверяет готовность, не запускает тяжёлый цикл.
5. **При 402/отказе памяти:** не делать вид, что память пуста; fail-closed для утверждений о полноте, явный `blocked/degraded`, сохранить намерение/очередь безопасным доступным способом либо честно сообщить о невозможности долговечного сохранения. Возможные offline-результаты только с явной маркировкой устаревших данных и без ложных обещаний сохранения в Supabase. Не обходить блокировку скрытым платным сервисом.

## 4. Технические границы
- Server-side фильтрация по project/market/date, выбор только нужных полей, bounded pagination с устойчивым порядком; legacy `project_id` внутри JSON и project isolation проверять тестами. **Не** заменять весь архив «последними N» без доказательства аналитического паритета; отдельный путь для долгосрочных трендов и защищённых сущностей.
- Компактная рабочая память (проверяемые сводки, индексы, агрегаты с provenance, датой обновления, версией и ссылками на исходники), исходные записи остаются источником истины. Инкрементальные обновления и дедуп идентичных запросов; ограниченное время жизни только у воспроизводимого кэша, НЕ у обязательной истории.
- Бюджет на запуск: максимальные bytes Supabase response, число/размер строк, RAM peak/RSS, длительность, API запросы, YouTube units и число retry; оценка бюджета ДО выполнения, лимиты и circuit breaker, предотвращение одновременных дублирующих запусков. Лимиты подбирать по измерениям, не выдумывать числа.
- Отдельный учёт egress Supabase и storage; при недостаточном бюджете — безопасная деградация с ясным объяснением, что не было проверено. Различать billing egress и объём БД/WAL. Ограничивать и объём ответов, и число запросов (малые страницы могут увеличить общий трафик).
- Запись run/status не должна многократно перечитывать/перезаписывать многомегабайтный JSON. Учитывать SQL 57014, ошибочную сериализацию `CycleStatus.WAITING/SLEEPING`, OOM и остановку Render как отдельные дефекты.
- Нельзя считать простое сокращение частоты запусков достаточным решением: ручные запросы, ретраи, рестарты и сторонние потребители также расходуют egress.

## 5. Порядок работы и доказательства приёмки
**A. Только чтение:** полная карта триггеров startup/schedule/manual/retry; call graph и объём Supabase/YouTube запросов, разбивка egress по дням/endpoint/потребителю если доступна; разбор 37,98 ГБ с неопределённостью; текущие лимиты и измерения Render. Без новых дорогостоящих live запросов.
**B. Контракты:** согласовать изменение расписания/24 слотов и ожидаемую свежесть; набор эталонных сценариев по разным сегментам (включая британский), качество рекомендаций и provenance; защищённые сущности, восстановление, очереди, idempotency.
**C. Изолированные изменения:** сначала выключаем связку boot→heavy cycle и устраняем неограниченное чтение, затем инкрементальные сводки и бюджетирование. В отдельных PR/feature flags; без изменения production до разрешения.
**D. Offline regression:** измерить для типовых и тяжёлых ручных запросов, ежедневного цикла, рестарта, 402, 57014, YouTube quota exhausted, пустого/частичного контекста, нескольких проектов и роста данных ×2/×5: качество, сохранение/ссылки, egress bytes, число HTTP запросов, RSS peak, latency, статусы, retry. Не расходовать YouTube-квоту.
**E. Canary после разрешения:** проверить фактические метрики и ограничения в течение согласованного окна, откат при росте egress, ухудшении качества, OOM/402. Успех кода/HTTP 200 ≠ завершение.

## 6. Решения, которые ещё нужно получить от владельца
- Допустимо ли официально изменить требование 24 часовых слотов на режим лёгких проверок + утренний глубокий анализ + внеплановые пользовательские запросы?
- Часовой пояс, желаемое время утреннего результата, допустимая свежесть данных и необходимость промежуточных оповещений.
- Что делать при отсутствии доступной памяти/квоты: запретить глубокий анализ или разрешить явно помеченный ограниченный offline-ответ?
- Только после доказательной оценки — разрешения на конкретные PR, изменение расписания, Render/Supabase/деплой.

**Связанные документы:** `management/MEMORY_INTELLIGENCE_2_PLAN.md` (M02/M03/M04/M08/M15/M16–M22/M31–M39), `management/MEMORY_2_ACCESS_MAP.md`, `management/SUPABASE_STORAGE_MAP.md`, `management/OOM_RECOVERY_PLAN.md`, `management/MASTER_PLAN.md`. **M03 🔄, M04 🔄, OOM-07 открыт; Memory 0/40 формально принято.** Документ не заменяет ТЗ и не является разрешением на реализацию.


## 7. Read-only аудит реальных API-журналов (2026-11-20)

**Источник:** Supabase unified logs, `edge_logs`, UTC окна 2026-11-18 00:00–19 00:00 и 2026-11-19 00:00–20 00:00; read-only агрегаты ClickHouse. Это **двое суток**, не весь биллинговый период. Источник не возвращал размер тела ответа, поэтому нельзя вычислить egress в ГБ или атрибутировать все 37,98 ГБ.

| Показатель | 18 ноября | 19 ноября |
| --- | ---: | ---: |
| Всего `edge_logs` | 7 505 | 8 202 |
| `GET /rest/v1/director_runs` HTTP 200 | 775 | 880 |
| `GET /rest/v1/director_runs` HTTP 500 | 428 | 347 |
| `GET /rest/v1/constraints` HTTP 200 | 752 | 764 |
| `GET /rest/v1/system_events` HTTP 200 | 743 | 756 |
| `GET /rest/v1/director_results` HTTP 200 | 708 | 750 |
| `GET /rest/v1/data_relations` HTTP 200 | 535 | 671 |
| `GET /rest/v1/video_snapshots` HTTP 200 | 324 | 380 |

В обе даты все перечисленные топовые маршруты в агрегате имели `request.cf.asOrganization=Render`; за 19 ноября **все 8 202 edge_logs** имеют `org=Render` и `user_agent=python-httpx/0.28.1`. Это **не идентифицирует конкретный процесс/компонент** внутри Render и не исключает иных путей egress, например прямого SQL, Auth, Storage, других дат/проектов. Проверить идентификатор сервиса, вызывающие цепочки, scheduler/retry и прочих потребителей.

**Особенно показательно:** из `GET /director_runs` 19 ноября **1 098 запросов** имели `?select=%2A&order=created_at.desc%2Cid.desc&offset=0&limit=1000`, только **15** — аналогичный `limit=50`; есть также `select=data_json&id=eq...&limit=1`. Это прямо подтверждает массовые полные чтения и риск многократной передачи больших JSON. Ранее замеренный max `director_runs.data_json` = 2 419 593 байта; **не умножать** его на все запросы как факт egress. HTTP 500 не обязательно передавали полные данные. Результаты за 18–19 ноября не подтверждают объём трафика за 10–20 ноября.

**Промежуточное заключение:** Render-hosted Python клиент — **доказанный основной источник наблюдаемых Data API обращений** в эти дни. Повторные полные чтения `director_runs` — **подтверждённый приоритетный дефект эффективности**. Точная доля в 37,98 ГБ, распределение по сервисам и причина повторов остаются открытыми. Дальше: read-only карта call sites и источников запуска; сопоставление времён и объёмов ответа при наличии метрик; сравнение других дней без дорогостоящего полного сканирования. Не изменять production до отдельного разрешения.


## 8. Статическая проверка вызывающих механизмов (2026-11-20)

**Источник:** `peonyrhodo-bit/site-insight-engine`, `main` на момент проверки (не утверждается, что идентичен каждому историческому deploy); только GitHub read-only.

1. `server.py:_autonomous_worker_loop` около строк 2950–3045: если в памяти scheduler нет активного расписания, создаёт `schedule_interval(... first_run_at=datetime.now(timezone.utc))`; далее `collect_due` → `next` → `_execute_autonomous_cycle`. На startup автономный worker может сразу запустить тяжёлый цикл. Scheduler in-memory, значит рестарт может создавать новое стартовое расписание; нужны тесты и сверка runtime флагов.
2. Тот же цикл при ошибке ставит `retry` с `max_attempts=3`, задержка до 60 секунд. При устойчивой ошибке Supabase это может повторять дорогие чтения; не доказано, сколько конкретно запросов в логах породили retries.
3. `memory/supabase.py:_recent_for_project` около строк 204–265: `select("*")`, страницы `page_size=50` в текущем `main`, проект фильтруется **после** получения полной страницы из-за legacy JSON. Сокращение страницы с 1000 до 50 не устраняет полную проекцию и может увеличить число запросов. 19 ноября в логах преобладает `limit=1000`; текущий `main` и исторические запросы относятся к разным версиям/моментам.
4. `memory/supabase.py:get_context` около строк 1135–1200 вызывает **восемь** reader-методов: runs, decisions, recommendations, constraints, events, chat, actions, results. Каждый reader использует общую схему `_recent_for_project`, что объясняет близкие числа GET по таблицам; точный caller каждого GET пока не установлен.
5. `server.py:/dashboard` около строк 3065–3090 вызывает `runtime.memory.get_context` со всеми восемью коллекциями и отдаёт `memory_context`. Поэтому обращения к Dashboard могут быть самостоятельным источником повторных чтений; **нет доказательств**, что именно dashboard вызывался сотни раз.
6. `memory/supabase.py:update_run` около строк 1236–1248 делает `SELECT data_json` перед merge и PATCH: потенциальное многомегабайтное read–modify–write для каждого обновления статуса. Нужна отдельная оценка, без слепой смены контракта.

**Причинная цепочка:** старт/плановый wake или dashboard → повторная сборка контекста → полные страницы JSON → трафик/RAM/SQL timeout → ограниченные retries. Это подтверждённый путь в коде, **но не доказательство, что все реальные 37,98 ГБ прошли через него**.

**Приоритет без потери функций:** (1) изолировать старт сервиса от тяжёлого цикла, не теряя on-demand; (2) сделать проекции/фильтры/пагинацию безопасными для legacy и истории; (3) заменить многократные полные dashboard context и run RMW на целевые обращения; (4) проверить retry/idempotency; (5) замерить bytes/request, calls/cycle и качество до/после. Любой patch — отдельный PR, тесты и разрешение. Никаких изменений в runtime на этом этапе.


## 9. P0 implementation plan — API read amplification (read-only code audit 2026-11-20)

Additional confirmed call sites in `site-insight-engine/main/server.py`:
- `GET /director/recommendations` around 3113 calls `get_context` for **all eight** tables although response uses only `recommendations`.
- `GET /director/recommendations/{id}` around 3145 and `POST /director/recommendations/{id}/action` around 3190 also read eight tables, **100 requested items per collection**, and then filter recommendations in Python.
- `GET /events` around 3880 and `GET /director/history` around 3910 also load all eight tables to return one collection.
- `_find_completed_idempotent_run` around 2387 invokes `backend._recent_for_project(TABLE_RUNS, limit=None, project_id=...)`, which scans all pages, loads all columns including large `data_json`, and then searches for the idempotency key in Python. This is a separate high-risk full-history read path; retain fail-closed behavior on incomplete read.
- `/director/dashboard` delegates to `/dashboard`, already confirmed full eight-table context.

**Minimal patches proposed (NOT approved, no code changed):**
1. **P0-A: narrow endpoint readers.** Recommendations list/detail/action read only recommendations; events only events; history only runs; preserve response shapes, authorization/project isolation, ordering, limits and errors. For detail/action prefer server-side identity predicate where schema supports it; legacy nested IDs require a verified compatibility fallback. Avoid treating incomplete read as not found.
2. **P0-B: bounded idempotency index.** Add durable indexed lookup by `(project_id, idempotency_key)` or compatible separate lookup, while preserving historical records and preventing duplicate execution after restarts. Backfill/legacy compatibility before removing full scan; no migration without owner approval. Do not replace with fixed recent N without proof: old keys must still be recognized.
3. **P0-C: memory projection and project filtering.** Per-table narrow columns; prefer DB-side project_id filter with fallback for legacy JSON; verify across multiple projects and data_json-only historical rows. No TTL/deletion, no loss of quality or historical retrieval.
4. **P1: startup/scheduler.** Prevent implicit heavy analysis at service boot, preserve current 24 scheduled slots until owner approves a change, preserve manual run and morning delivery. Test cold start/redeploy, retry, overlap, Supabase 402/500, SQL 57014.
5. **P1: update_run.** Replace read–merge–write of large `data_json` only after proving merge semantics and concurrency tests; avoid lost fields and partial status bugs.
6. **Instrumentation:** bytes per response (when observable), count by route/caller, page count, duration, RAM peak, retry attempts, quality baseline. Compare before/after using offline fixture and only later approved canary.

**Acceptance gates:** every endpoint response contract unchanged; multi-project/legacy history correct; idempotency durable; errors fail closed; no duplicate cycles; no new YouTube quota consumption; recommendations and historical evidence remain accessible; measurable reduction in transferred bytes and RAM. Existing draft PRs #67/#69 must be assessed for overlap, not blindly duplicated. Do not alter source, Supabase, Render, billing or schedule without explicit approval.


## 10. Обязательное правило модульности от владельца (2026-11-20)

**Решение владельца:** не перегружать `server.py`. Он является **тонким транспортным/API-слоем**: маршруты, проверка/разбор входа, вызов профильного сервиса, преобразование ответа и HTTP-ошибок. Бизнес-логика, хранение, выборки, циклы и алгоритмы должны находиться в соответствующих пакетах: память — `memory/`, исследования — `research/`, планирование/пробуждения — в их профильных модулях, аналогично для других подсистем. Существующие имена модулей и структура проверяются перед рефакторингом; новые каталоги не создавать без необходимости.

**Применение к P0/P1:** выборки рекомендаций, истории, контекста, идемпотентность и совместимость legacy — в `memory/` и профильных сервисах; исследовательские алгоритмы — в `research/`; orchestration/scheduler — вне `server.py`. В `server.py` допускаются только тонкие обработчики и wiring. Исправление проблемы egress не должно увеличивать бизнес-логику в `server.py`; предпочтителен её постепенный вынос при сохранении публичных маршрутов и контрактов.

**Критерий ревью:** для каждой новой/изменённой функции указать владельца-модуль; отклонять PR, добавляющие тяжёлые запросы, циклы или исследования в `server.py`. Подтвердить regression tests, multi-project, историческую совместимость и отсутствие изменения поведения API. Это правило утверждено владельцем; остальные предложения ADR остаются проектом до отдельного одобрения.


## 11. Карта размещения P0/P1 с учётом правила владельца (2026-11-20)

Проверено read-only по `site-insight-engine/main/server.py`: файл ~4133 строки, уже импортирует `memory/` через adapter, `scheduler/scheduler.py`, `scheduler/wakeup.py`, `scheduler/jobs.py`, `analytics/`, `data/`, `director/`; исследовательский executor сейчас импортируется из `director/research_executor.py`, а наборы исследований — из `data/research_sets.py`. Наличие отдельного пакета `research/` этим аудитом **не подтверждено**. Не выдавать предлагаемые пути за существующие.

**План разделения ответственности для будущего отдельного PR:**
- `server.py`: только FastAPI маршруты, проверка параметров, делегирование в сервис, HTTP mapping. Убрать из него прямые сканы памяти, циклы и сложные операции над рекомендациями.
- `memory/`: профильные методы `get_recommendations`, `get_recommendation_by_id`, `get_events`, `get_history`, индексированный поиск idempotency, SQL projection/pagination/legacy compatibility, сохранение и полнота памяти. Конкретные имена API — предложения, проверить существующий adapter.
- `scheduler/`: startup bootstrap, защита от дубликатов, wakeup/retry и управление частотой; не менять 24 слота без одобрения.
- `research/` как **целевая доменная граница по правилу владельца**: исследовательская логика и executor должны относиться к research, а не server. Текущая реализация частично в `director/research_executor.py` и `data/research_sets.py`; сначала карта зависимостей, затем поэтапный перенос с совместимыми импортами и тестами, без механического массового перемещения.
- `director/`: стратегическая оркестрация, рекомендации и правила принятия решений, без дублирования DB adapter; `analytics/` — аналитические расчёты; `data/` — модели и регистры; `quota/` — лимиты YouTube.

**Минимальные отдельные PR (порядок):** PR-A профильные read methods в `memory/` + тонкие endpoint wrappers; PR-B idempotency lookup в `memory/` + совместимость старых записей; PR-C startup worker в `scheduler/` + сохранение текущего расписания; PR-D оптимизация update_run без потери полей; PR-E поэтапное выделение `research/` после отдельной карты зависимостей. Каждый PR малый, тестируемый и не увеличивает бизнес-логику `server.py`. Проверить конфликт/пересечение с draft PR #67/#69.

**Статус:** архитектурная карта и порядок — предложение; правило тонкого `server.py` и доменной организации — решение владельца. Никаких изменений в исходниках или production не сделано.


## 12. PR-A — готовый scope для Codex (2026-11-20; проект, без реализации)

**Цель:** исключить ненужные чтения семи таблиц при запросе одного типа данных, без изменения API/истории/модульных границ.

**Подтверждённая точка расширения:** `memory/director_adapter.py:get_context` (около 600) оборачивает backend и проверяет `_memory_read.status`, бросает `MemoryReadError` при incomplete. `memory/supabase.py` уже содержит отдельные `get_recent_recommendations` (около 1567), `get_recent_runs` (1249), `get_recent_events` и другие; следует переиспользовать, а не дублировать. В `server.py` route `recommendation_action` (около 3188) читает восемь коллекций с лимитом 100 и ищет `recommendation_id` в Python. Все операции должны сохранять fail-closed semantics: ошибка чтения ≠ отсутствие рекомендации.

**Шаги PR-A:**
1. Добавить в `memory/director_adapter.py` узкие async methods для получения конкретной коллекции, использующие существующие backend methods и `_call_off_thread`, с единым `MemoryReadError`; не обращаться к `runtime.memory.backend` из HTTP layer.
2. Перевести `GET /director/recommendations`, `GET /events`, `GET /director/history` на профильные методы. Сохранить JSON response shape, сериализацию, ограничения и порядок, default project, ошибки и fallback backend.
3. Перевести `GET /director/recommendations/{id}` и action на поиск через память, не загружая семь посторонних коллекций. **Не вводить слепое ограничение «последние 100» для ID:** проверить историческую доступность, legacy recommendation_id и проектную изоляцию; отдельный targeted lookup/index только после проверки схемы.
4. Оставить `/dashboard` пока с полным контекстом, потому что его контракт реально содержит все коллекции; оптимизировать его отдельно через bounded projection/cache при измеренном сценарии.
5. Тесты: вызов каждого route → только необходимая коллекция; старый и новый JSON побайтово/семантически эквивалентны (кроме непреднамеренных ошибок); project A/B; old recommendation ID; 402/500/timeouts; недоступная память не превращается в 404/пустой список; alternative backend; не добавлена бизнес-логика в `server.py`.
6. Метрики offline: число вызовов backend по таблицам (ожидаемо 8→1 для list/history/events), байты сериализованного payload и RAM; это **оценка сокращения запросов**, не обещание 8× меньшего общего egress.

**Отдельно:** `_find_completed_idempotent_run` с `limit=None` — PR-B, не смешивать с PR-A; startup/retry — PR-C. Проверить перекрытие с существующими draft PR #67/#69. Не менять 24 slots, Supabase schema, runtime или deployment в PR-A.

**Статус:** техническое задание для Codex подготовлено в документации. Никакой PR с кодом не создан; тесты не запускались.


## 13. PR-B — durable idempotency lookup, no full-history scan (2026-11-20; проект, без реализации)

**Подтверждённый код:** `site-insight-engine/main/server.py:_find_completed_idempotent_run` около 2385–2441 напрямую обращается к `runtime.memory.backend._recent_for_project(TABLE_RUNS, limit=None)`; fallback `get_context(limit_runs=100)`. Затем Python перебирает строки и проверяет `row.idempotency_key` либо `row.data_json.idempotency_key`; статус `row.idempotency_status` или `data_json.idempotency_status`; результат `row.result` или `data_json.result`. Для `failed` и `in_progress` возвращает HTTP 409, для `completed` с dict result возвращает сохранённый результат, при ошибке чтения HTTP 503 (fail closed). `memory/supabase.py:save_run` около 1210 пишет весь `data_json`, выделяя только некоторые поля в колонки, поэтому нельзя предполагать, что idempotency_key уже есть в отдельной колонке. `update_run` около 1236 делает полный SELECT data_json перед merge.

**Предлагаемая реализация в отдельном PR-B после PR-A:**
1. Провести read-only проверку схемы `director_runs`, индексов и распределения legacy ключей; проверить фактический формат `data_json`, **не выгружая массивы больших JSON**. Не менять схему без отдельного согласования.
2. Добавить узкий API `memory/` для поиска `(project_id, idempotency_key)` с устойчивой семантикой `completed`, `failed`, `in_progress`; server.py только вызывает его и маппит HTTP.
3. Предпочтение индексированному серверному поиску. Варианты после аудита: отдельная indexed колонка/таблица ключей с безопасным backfill, либо проверенный PostgreSQL expression index по JSONB; RLS, права и legacy project_id обязательно проверить. Индекс по JSONB нельзя считать бесплатным или автоматически доступным через PostgREST.
4. Никакой эвристики «последние N записей»: сохранённый старый ключ должен находиться всегда. Не менять статусную логику 409/503, не возвращать 404/None при неполном чтении.
5. Защита от гонки: атомарная reservation/unique constraint либо эквивалентный существующий механизм; два параллельных одинаковых запроса не должны запускать два цикла. Проверить restart/multi-worker и project A/B.
6. Тесты offline: legacy JSON-only ключи, top-level keys, completed result reuse, failed/in_progress 409, database unavailable 503, duplicate concurrency, old keys, разные проекты, status transitions, no full table scan, no loss of run data.
7. Сравнить число и размер запросов до/после; не обещать снижение суммарного egress в ГБ без измерений.

**Порядок:** PR-A narrow API readers → PR-B indexed idempotency → PR-C scheduler startup. Параллельно проверить, какие изменения уже покрывают draft PR #67/#69. Код/SQL/Render/production без отдельного одобрения не менять.


## 14. PR-C — scheduler startup, wakeups and bounded retry (2026-11-20; проект, без реализации)

**Подтверждено read-only в `site-insight-engine/main/server.py`:**
- `AUTONOMOUS_ENABLED` около строки 84 читается из env (default `false`), но `startup()` около 4079 **безусловно** делает `asyncio.create_task(_autonomous_worker_loop())`, пишет `Director continuous cycle: enabled`. Само по себе это не доказывает фактический production env или количество выполненных циклов; показывает несоответствие флага и startup.
- `_autonomous_worker_loop` около 2948 при отсутствии active schedule создаёт interval `AUTONOMOUS_WAKE_INTERVAL_SECONDS` (default 3600) с `first_run_at=now`, а затем обрабатывает due wakeups и вызывает `_execute_autonomous_cycle`.
- Ошибка выполнения ставит retry до `max_attempts=3` (до 60 секунд задержки), даже если причина — системная недоступность хранилища. Есть локальная блокировка параллельных циклов проекта, но этого недостаточно для устойчивой координации между процессами.
- `shutdown()` отменяет worker. Нет доказательства, что этот код был точной версией во время всех исторических GET или что все GET вызваны worker.

**Предлагаемый PR-C после PR-A/PR-B, с соблюдением модульности:**
1. Вынести lifecycle/wakeup/interval/retry orchestration из `server.py` в `scheduler/` и профильный сервис `director/`; в `server.py` оставить только wiring запуска/остановки.
2. Согласовать семантику `AUTONOMOUS_ENABLED`: `false` не запускает автономный worker; ручной on-demand остаётся доступен. Сначала проверить production env и существующие потребители; **не отключать действующую автономность случайно**.
3. Убрать немедленный тяжёлый запуск при каждом startup; сохранить текущие 24 плановых слота до отдельного решения владельца, а missed-run и cold-start семантику согласовать и проверить. Простое `first_run_at=now+3600` без восстановления пропущенных запусков недопустимо.
4. Добавить durable schedule/wakeup identity или проверенную идемпотентность на multi-worker/restart, ограничить ретраи и отличать transient errors от 402/исчерпания квоты. На 402 — явный degraded/fail-closed, без бесконечного повторного чтения и без ложного «полного анализа».
5. Логи/метрики: `startup_reason`, `schedule_id`, `wakeup_id`, `cycle_id`, `retry_attempt`, `source` (manual/scheduled/retry), `memory_read_count`, `bytes` если доступны; без секретов.
6. Offline tests: `AUTONOMOUS_ENABLED=false/true`, web health without analysis, manual on-demand, 24 scheduled slots, restart before/after due, 2 workers, duplicate wake, failed/partial memory, Supabase 402/500/57014, no new YouTube API consumption, no regressions in multi-project history or recommendations.
7. Не менять live Render env, расписание, deployment, Supabase или billing без явного согласования и canary. Перед PR проверить draft PR #67/#69 и действующий scheduler API.

**Статус:** точная карта дефекта и техническое задание PR-C записаны. Реализация, тесты и production изменения не выполнялись.


## 15. Проверка пересечения с существующими draft PR #67/#69 (2026-11-20)

Проверены GitHub описания:
- [site-insight-engine PR #67](https://github.com/peonyrhodo-bit/site-insight-engine/pull/67): fail-closed protected memory read, перед исследованием, 6 offline tests заявлены, тесты не выполнены на момент описания. Не является исправлением endpoint read amplification, idempotency или scheduler startup.
- [site-insight-engine PR #69](https://github.com/peonyrhodo-bit/site-insight-engine/pull/69): opt-in `get_recent_run_refs` без `data_json`, bounded projected references; runtime caller не изменён, autonomous cycles не меняются, нет доказанного production OOM fix. Заявлены 175 тестов и 11 subtests Codex, независимо здесь не запускались. Пределы 64 KiB/20 refs/5 pages — гипотезы, не утверждённые owner.
- Оба draft и не должны автоматически merge/deploy.

**Совместимость планов:** PR-A должен использовать единый fail-closed `MemoryReadError` и не ослаблять protected-memory gate #67. PR-B должен искать старые ключи надёжно, а не подменять их `get_recent_run_refs` из #69: bounded refs не доказывают полноту исторического поиска. PR-C должен учитывать защиту от неполной памяти и не создавать повторных циклов. При разработке смотреть фактические diff, тесты и ветки, не полагаться только на описание PR.

**Гейт:** перед реализацией source PR и review; далее изолированные PR, offline CI, review архитектуры (server thin; memory/scheduler/research), затем отдельное решение владельца о merge и production. В этом шаге исходники, база, deployment и настройки не изменялись.
