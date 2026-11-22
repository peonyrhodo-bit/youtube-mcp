# ЕДИНЫЙ РАБОЧИЙ ПЛАН — ИИ-директор YouTube 3.0

> **Единственный действующий перечень задач.** Версия консолидации: 22.11.2026. Основа: исходный MASTER_PLAN №001–060; дополнительно перенесены OOM-01–08, M01–M40, BACKLOG, задания Codex, функциональное восстановление, новая декомпозиция проверок, аудит Р01–Р26 и acceptance-тесты. **Другие файлы не удалены** до отдельного разрешения владельца. Они являются источниками истории и доказательств, а не параллельными планами.

## Панель состояния

- **Общий прогресс:** **6/60 исторических контрольных пунктов доказательно закрыто** (№001–005 и №007). Дополнительные подпункты OOM-01–05 закрыты **только как этапы диагностики и разрешения**, не как устранение OOM. M01–M40: **0/40 полностью принято**. Итоговый процент объединённого плана **пока не установлен**: вложенные задачи имеют разные уровни, и суммирование породило бы ложную точность.
- **Текущий активный пункт:** **№009 — завершить трассировку ТЗ и привязку проверок к единому плану**, используя существующие матрицы, без нового аудита. Далее №010 → №035/038 → функциональное восстановление до рекомендации.
- **Блокировки:** №006 (runtime orchestrator → Director не подтверждён); №008 (конфигурация после стабилизации); OOM-06/07 (проверка исправления и стабильности 512 MiB Render); protected-memory semantics (Issue #68, PR #67/#69); возможный Supabase HTTP 402 (актуальность проверить); конфликт PR #73 с согласованной автономностью. Не считать гипотезы доказанными.
- **Следующее конкретное действие:** закрыть только недостающие строки трассировки §18–19 ТЗ в №009, затем согласовать проверяемые критерии №010 и выполнить offline-тесты защищённого чтения №035. Ни один сквозной цикл не объявлять успешным заранее.
- **Главный результат:** исследование YouTube → достоверные данные → аналитика → обоснованная рекомендация → Supabase → русский интерфейс → обсуждение/feedback → следующий цикл. **НЕ ЛОМАТЬ СУЩЕСТВУЮЩУЮ АРХИТЕКТУРУ.**

## Правила отметок, зависимостей и доказательств

- `[x]` — результат **выполнен и проверен** применимыми доказательствами; `[ ]` — не завершён. Рядом: **ЧАСТИЧНО**, **БЛОКИРОВАНО**, **ОТЛОЖЕНО**, **ОТМЕНЕНО**. Закрытая историческая диагностика не означает закрытую техническую проблему.
- Каждая задача фиксирует **источник/исторический ID**, зависимости, действие, критерий приёмки и ссылку на тест/коммит/лог/среду. Без фактического результата статус остаётся `[ ]`.
- **Препятствия — вложенные `[ ]` под исходным пунктом** с причиной, разрешённым действием и возвратом к родителю. Не создавать параллельный BACKLOG.
- Код/CI/HTTP 200 не заменяют проверку результата. Live-вызовы, квоты, production, SQL-миграции и удаление данных — только при разрешении и безопасном плане.
- Render free (512 MiB исторически), Supabase free, нулевая обязательная стоимость, сохранность защищённой истории; не включать RLS вслепую. Quota manager — единственный источник учёта YouTube. Автономность не выключать скрытой сменой семантики флага. ТЗ, карта, дерево, технические доказательства неприкосновенны.
- **Порядок:** проверка частей до общего сквозного теста; при блокировке допускается независимый offline-пункт, затем возврат к родителю. Не производить/не публиковать видео на этапе Director 3.0.

## A. Базовые 60 контрольных пунктов — скелет выполнения

Исторические ID сохранены для ссылок из Issues/PR/тестов. Дополнительные рабочие подпункты ниже являются частью **этого же файла**. Для каждого базового пункта действует проверка по соответствующим разделам B–H и по исходному ТЗ.


### 01. Управление и требования

- [x] **№001** — Зафиксировать источники требований и запреты изменений
- [x] **№002** — Составить реестр трёх GitHub-репозиториев
- [x] **№003** — Составить реестр основных Render-сервисов
- [x] **№004** — Проверить удаление лишнего тестового сервиса
- [x] **№005** — Составить карту Supabase и хранилищ
- [ ] **№006** — Проверить связи сервисов и сетевые адреса **[БЛОКИРОВАНО]**
- [x] **№007** — Проверить рабочие ветки, версии и автодеплой
- [ ] **№008** — Проверить переменные конфигурации без раскрытия секретов (временно отложен до стабилизации Director) **[БЛОКИРОВАНО]**
- [ ] **№009** — Построить матрицу требований Директора 3.0
- [ ] **№010** — Утвердить критерии сквозной приёмки

### 02. Жизненный цикл

- [ ] **№011** — Выявить действующий механизм запуска циклов
- [ ] **№012** — Сопоставить ожидаемые и фактические циклы за период
- [ ] **№013** — Проверить защиту от параллельных запусков
- [ ] **№014** — Проверить фиксацию начала и окончания цикла
- [ ] **№015** — Проверить обработку прерванных циклов
- [ ] **№016** — Проверить поведение после перезапуска
- [ ] **№017** — Проверить таймауты длительных операций
- [ ] **№018** — Проверить повторы и экспоненциальные задержки
- [ ] **№019** — Проверить отсутствие бесконечных повторов
- [ ] **№020** — Подтвердить полный жизненный цикл на тестах

### 03. Исследование YouTube

- [ ] **№021** — Проверить построение исследовательского плана
- [ ] **№022** — Проверить выбор и ограничение поисковых запросов
- [ ] **№023** — Расследовать UnicodeEncodeError в YouTube MCP
- [ ] **№024** — Проверить обработку ошибок MCP без ложного успеха
- [ ] **№025** — Проверить лимиты YouTube-квоты и отказ при сбое учёта
- [ ] **№026** — Проверить сбор и сохранение поисковых результатов
- [ ] **№027** — Проверить обновление статистики известных видео
- [ ] **№028** — Проверить нулевые и частичные результаты
- [ ] **№029** — Проверить отсутствие повторного бесполезного исследования
- [ ] **№030** — Подтвердить сквозное исследование без лишнего расхода квоты

### 04. Данные и память

- [ ] **№031** — Проверить схему таблиц и миграции Supabase
- [ ] **№032** — Проверить сохранение исследовательских наборов
- [ ] **№033** — Проверить сохранение видео и снимков статистики
- [ ] **№034** — Проверить связи между результатами и источниками
- [ ] **№035** — Проверить чтение исторических данных и пагинацию
- [ ] **№036** — Проверить идемпотентность записи и защиту от дублей
- [ ] **№037** — Проверить транзакционность и частичные ошибки
- [ ] **№038** — Проверить ограничения памяти и размеры выборок
- [ ] **№039** — Проверить безопасность доступа и RLS без опасных изменений
- [ ] **№040** — Подтвердить восстановление данных после сбоя

### 05. Аналитика и рекомендации

- [ ] **№041** — Проверить входные данные аналитики
- [ ] **№042** — Проверить оценку тем и трендов
- [ ] **№043** — Проверить оценку возможностей и ниш
- [ ] **№044** — Проверить качество и полноту доказательств
- [ ] **№045** — Проверить различение фактов и гипотез
- [ ] **№046** — Проверить работу при недостатке данных
- [ ] **№047** — Проверить принятие решений Директором
- [ ] **№048** — Установить причину отсутствия итоговых рекомендаций
- [ ] **№049** — Проверить сохранение и отображение рекомендаций
- [ ] **№050** — Подтвердить сквозной результат: данные → рекомендация

### 06. UI, устойчивость и приёмка

- [ ] **№051** — Проверить API и доступность пользовательского интерфейса
- [ ] **№052** — Проверить русский язык и понятность результатов
- [ ] **№053** — Проверить действия пользователя и обратную связь
- [ ] **№054** — Проверить права и ограничения автономных действий
- [ ] **№055** — Проверить ошибки сети и деградированный режим
- [ ] **№056** — Проверить использование памяти на типовых нагрузках
- [ ] **№057** — Проверить CI и регрессионные тесты всех репозиториев
- [ ] **№058** — Провести безопасную сквозную приёмку в разрешённой среде
- [ ] **№059** — Сверить все требования ТЗ с доказательствами
- [ ] **№060** — Подготовить итоговый акт аудита и следующий план развития

### Вложенные препятствия и приоритетные действия (внутри исходных пунктов)

- [ ] **№009.1 [ЧАСТИЧНО, M01]** Дозакрыть требования §18–19 и ссылки на тесты по существующим матрицам `REQUIREMENTS_MATRIX.md`, `MEMORY_2_TZ_TRACEABILITY.md`; приёмка: каждое требование → функция/данные → проверка → доказательство/«не проверено».
- [ ] **№010.1** Установить критерии приёмки из существующих функционального и проверочного документов; приёмка: ожидаемое, фактическое, регрессия, среда и статус для каждого сценария.
- [ ] **№035.1 [ЧАСТИЧНО, M02/M09/M16/M17, Issue #68]** Проверить полное и безопасное чтение защищённой памяти, legacy project_id, курсоры, поля, ошибку/пустой ответ; PR #66/#70 merged — лишь частичные улучшения; PR #67/#69 открыты. Приёмка: ни один пользовательский consent/decision/task не теряется молча, bounded operational context и явные partial/error.
  - [ ] **№035.1.1 [БЛОКИРОВАНО, при наличии HTTP 402]** Проверить актуальность лимита Supabase, локальный безопасный путь тестирования, вернуться к №035.1.
- [ ] **№036.1 [ЧАСТИЧНО, PR #71/#72]** Сопоставить durable indexed idempotency и изолированную PostgreSQL-фикстуру с реальными контрактами; без миграций без согласования. Приёмка: параллельные старты не дублируются, ошибки чтения fail-closed.
- [ ] **№038.1 [ЧАСТИЧНО, OOM-06/M04/M19/M20]** Измерить RSS/объёмы, исключить ненужные копии ResearchSet и полные JSON на горячем пути, не ломая `/radar` и `/radar-debug`; приёмка: повторяемые тесты 512 MiB и паритет API/аналитики.
- [ ] **№038.2 [БЛОКИРОВАНО, OOM-07]** После разрешённого деплоя наблюдать отсутствие повторных OOM и сохранность автономной функции, затем вернуться к №006/008. HTTP 200 недостаточно.
- [ ] **№011.1 [КОНФЛИКТ, PR #73]** Сверить фактическую семантику `AUTONOMOUS_ENABLED` с требованием автономности; не объединять конфликтующий PR автоматически.
- [ ] **№023.1 [ДЕФЕКТ/НЕ ПРОВЕРЕНО]** Воспроизвести `UnicodeEncodeError` в MCP offline, исправить причину, проверить Unicode/Windows и регрессию.
- [ ] **№048.1 [БЛОКИРУЮЩИЙ РЕЗУЛЬТАТ]** Проследить точку потери цепочки Research → Analytics → Recommendation → DB → UI; приёмка: хотя бы одна реальная доказательная рекомендация доступна на сайте и принимает feedback.
- [ ] **№055.1 [УСЛОВНО]** Supabase HTTP 402: проверить текущий статус и влияние на чтение/запись, не обещать платного обхода.
- [ ] **№056.1 [OOM]** Сверить memory/RSS/latency на ×1/×2/×5 данных, нет бесконтрольных копий и потери исторических наблюдений.
- [ ] **№058.1 [ОТЛОЖЕНО ДО КОМПОНЕНТОВ]** Полный безопасный сквозной цикл только после проверок отдельных частей, без ложного успеха.

## B. OOM: все исходные OOM-01–08 (вложенная программа №038/056)

Источник: https://github.com/peonyrhodo-bit/youtube-mcp/blob/project-management/director-audit-2026-11-19/management/OOM_RECOVERY_PLAN.md. Результаты OOM-01–05 — исторически проверенные этапы диагностики, а не доказательство устранения OOM. Ниже исходные действия и полный журнал сохранены вместе с задачами.


## B.1. Исторический журнал и критерии OOM

**Перенесено из:** https://github.com/peonyrhodo-bit/youtube-mcp/blob/project-management/director-audit-2026-11-19/management/OOM_RECOVERY_PLAN.md. Отметки [x] относятся только к завершённым диагностическим этапам.

<details>
<summary>Полный текст исходных задач, критериев и технических результатов (раскрыть)</summary>

# План устранения OOM — Director 3.0

**Создан:** 2026-11-19. **Статус:** активен. **Прогресс:** 6/8. **Текущий шаг:** OOM-06 (код в draft PR, тесты не запущены). **Основной план:** 6/60; №006 заблокирован, №008 ожидает возобновления.

## Цель и ограничения

Вернуть стабильную доступность `site-insight-engine` без расхода YouTube-квоты и без скрытых изменений production. Все действия по умолчанию read-only. **Код, конфигурацию, деплой, тариф, автономный режим и БД не менять без отдельного согласования владельца.** Не вызывать `/director/run`.

## Подтверждённая отправная точка

- Render `server_failed` с `oomKilled.memoryLimit=512Mi` неоднократно 2026-11-19 (например, 17:22:21, 17:24:09, 17:27:37, 17:29:52 UTC).
- Render memory metric в 16:18 UTC: 536715260 байт при лимите 536870900 байт.
- Автономный worker запускается после старта; `WakeupReason.SCHEDULED` и `WakeupReason.RETRY` ошибки предшествовали как минимум одному OOM. **Корреляция, не доказательство причинности.**
- Пользователь наблюдал HTTP 503 главной страницы. См. `management/SERVICE_NETWORK_MAP.md`.

## Контрольные этапы

- [x] **OOM-01** — Собрать точные стеки ошибок, временную шкалу OOM и показания памяти; отделить симптомы от причин.
- [x] **OOM-02** — Прочитать путь автономного запуска, retry и загрузки памяти в фактически развёрнутой версии; построить гипотезы.
- [x] **OOM-03** — Проверить гипотезы безопасно (логи, статический анализ, существующие тесты); указать, что не подтверждено.
- [x] **OOM-04** — Подготовить минимальное исправление, оценку рисков, критерии отката и конкретную задачу на изменение.
- [x] **OOM-05** — Получить отдельное разрешение владельца на выбранные изменения production/кода/настроек.
- [ ] **OOM-06** — Реализовать согласованное изменение в ограниченном объёме, с тестами и ссылками на коммиты/PR. **[ЧАСТИЧНО]**
- [ ] **OOM-07** — Проверить поведение после разрешённого деплоя: доступность, память, перезапуски, ошибки, автономный цикл; без платных API.
- [ ] **OOM-08** — Зафиксировать результат, остаточные риски и возврат к №006, затем №008 основного плана.

## Правила продвижения

1. Только один активный этап; выполненное отмечать ✅ **после** записи наблюдений и доказательств.
2. Не закрывать OOM-07 лишь по HTTP 200: нужна проверка отсутствия повторяющихся OOM в согласованном окне наблюдения и корректности предусмотренных функций.
3. Если этап заблокирован, фиксировать причину и следующий разрешённый шаг; не выдавать предположение за доказательство.
4. После каждого шага обновлять **этот файл**: текущий этап, прогресс, ссылки на коммиты и результат.
5. Приоритет OOM временно выше №008; основной план **не перенумеровывать**, №006 не закрывать без сетевого доказательства.

## Журнал

- **2026-11-19:** план создан; OOM-01 открыт. Изменений в production нет.

- **2026-11-19 — OOM-01 завершён (read-only):** Render 17:20:33 UTC `GET /rest/v1/director_runs?select=*&order=created_at.desc,id.desc&offset=0&limit=1000` returned HTTP 200; 17:20:40 same query returned HTTP 500; 17:20:41 `postgrest.exceptions.APIError` code `57014`, `canceling statement due to statement timeout`, from `memory/supabase.py:_recent_for_project`; propagated as `MemoryTableReadError` for `director_runs` and autonomous scheduled wakeup failure. Render OOM at 17:22:21. The query requests up to 1000 full rows (`select=*`), a plausible source of heavy data transfer, but row sizes, indexes and causal link to OOM are **unverified**. Next OOM-02: examine deployed SHA `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc` at `memory/supabase.py`, `memory/director_adapter.py`, `server.py` autonomous worker and tests. No production changes.

- **2026-11-19 — OOM-02 завершён (read-only, deployed SHA `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc`):** `memory/supabase.py:_recent_for_project` defaults to `page_size=1000`, `select("*")`, stable offset pagination, and **client-side** project filtering; even `get_recent_runs(limit=10)` may fetch 1000 or more full records, including records for other projects. Project ID may be nested in legacy `data_json`, so blindly adding a DB-side filter risks compatibility. `get_context` invokes multiple such readers. `server.py:_autonomous_worker_loop` creates an initial schedule with `first_run_at=now` and uses up to three retries with exponential delay (bounded by 60s); startup log shows worker enabled at runtime. Hypotheses: oversized Supabase scans, expensive autonomous wake cycles/retries, and interaction with statement timeouts. Causality not yet proven. Next OOM-03: check data sizes, query plans/indexes and available regression tests without production writes or expensive calls. No production changes.

- **2026-11-19 — OOM-03 промежуточный результат (read-only SQL):** `pg_stat_user_tables` оценивает `director_runs` в 157 живых строк, `pg_total_relation_size` = 14,524,416 байт (включая индексы/TOAST); `director_results` 2 строки и 3,817,472 байта. `director_runs` уже имеет индекс `idx_director_runs_created_at` on `created_at DESC`, primary key on `id`, partial unique active project and status/updated index. Эти данные не доказывают, что индекс отсутствует или что именно `select=*` вызывает OOM. Подтверждены отдельные Supabase statement timeout и OOM. Требуется исследовать TOAST/payload sizes, query plan и тесты; пока OOM-03 остаётся активным. Никаких записей или миграций в Supabase не выполнялось.

- **2026-11-19 — OOM-03 дополнительная проверка (read-only):** `SELECT count(*), max/avg(pg_column_size(data_json))` for `director_runs`: actual 157 rows; max data_json 2,419,593 bytes; average 68,171 bytes; max row 2,419,704 bytes. PostgreSQL `EXPLAIN` (without ANALYZE, no query execution) for `SELECT * FROM director_runs ORDER BY created_at DESC,id DESC LIMIT 1000 OFFSET 0` estimates `Seq Scan -> Sort -> Limit` over ~163 rows. Existing `created_at DESC` index is not chosen for this small table and two-key order. These results support a heavy-payload/read-path hypothesis but **do not establish memory amplification or OOM causation**. Existing regression-test coverage not yet verified. Next: assess tests and formulate bounded, compatible query optimization. OOM-03 remains open.

- **2026-11-19 — OOM-03 test reconnaissance (read-only):** GitHub code search for `test_supabase` and `recent_for_project` returned no matches; attempted conventional paths `tests/test_memory_supabase.py`, `tests/test_supabase_memory.py`, `tests/test_memory_context.py`, `tests/test_autonomous_worker.py`, `tests/test_server.py`, `tests/conftest.py`, `pytest.ini`, `pyproject.toml` were not found at deployed SHA. This **does not establish that the repository lacks tests**; full tree/test inventory remains unverified. `requirements.txt` includes FastAPI, Uvicorn, Supabase, psycopg, but no pytest entry. Required regression scenarios: oversized JSON, legacy nested project_id, project isolation, Supabase statement timeout, retry bounds and post-restart behavior. OOM-03 remains active until coverage can be established or explicitly recorded as a test gap; no code/production changes.

- **2026-11-19 — OOM-03 завершён (evidence review, read-only):** `memory/supabase.py:get_context` marks table errors as partial/error; `memory/director_adapter.py:get_context` raises `MemoryReadError` for any non-complete memory context. Therefore the observed `director_runs` statement timeout is sufficient to fail the autonomous cycle and activate bounded retry logic. SQL evidence: 157 rows in `director_runs`, max `data_json` 2,419,593 bytes, avg 68,171 bytes, query plan Seq Scan + Sort for 1000 full rows, existing created_at index. OOM was observed later with memory near 512 MiB, but no allocation profile proves causal linkage. Tests not established from available code search/conventional paths; mark as verification gap. **OOM-04 now active:** design minimal, legacy-compatible fix with safeguards, regression tests, rollback and acceptance criteria. No source/production changes or approvals implied.

## OOM-04 — предлагаемый минимальный patch (НЕ одобрен к внедрению)

**Изменение A — приоритетное:** В `memory/supabase.py:_recent_for_project` для таблицы `director_runs` при заданном `project_id` и `limit` использовать серверный фильтр по выделенной колонке `project_id`, `ORDER BY created_at DESC,id DESC`, ограничение числа возвращаемых записей и без `select=*` для ненужных колонок **только если потребители допускают это**. Не менять формат возвращаемых строк без проверки вызовов. Для legacy строк с `project_id IS NULL` и вложенным `data_json.project_id` предусмотреть отдельную ограниченную совместимую ветку с объединением результатов по дате/id и дедупликацией; не скрывать неполное чтение. Выбор конкретного алгоритма и лимитов — после тестов на фикстурах.

**Изменение B — отдельный, необязательный follow-up:** после подтверждения эффективности A рассмотреть защиту автономного старта/повторных попыток при повторяющемся `MemoryReadError` (cooldown / fail-closed с явным состоянием), без бесконечных retry и без потери запланированных сигналов. Не включать автоматически в минимальный patch без необходимости и отдельного согласования.

**Тесты до деплоя:** 10 требуемых записей из большого набора; 5 документов >1 МБ; изоляция двух проектов; legacy JSON-only project id; правильное глобальное newest-first объединение современных/legacy записей; нулевой/малый лимит; ошибочный ответ Supabase 57014 (не маскировать как пустую историю); ограниченные retry; отсутствие лишних запросов/дублирования; регрессия формы `get_context`. Запустить тесты в изолированной среде; не вызывать production autonomous run.

**Риски:** неправильная фильтрация legacy, изменение порядка, пропуск истории при ограничении страниц, рост запросов при fallback, изменение контрактов адаптера, отсутствие прямого профиля памяти. Поэтому отдельная совместимая ветка и тесты обязательны.

**Rollback:** сохранить исходный SHA Director `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc`, внести изменения через отдельную ветку/PR, проверить тесты, после отдельного разрешения деплоить с возможностью отката к исходному SHA; никаких DB миграций/переключений env в первом патче. Если после деплоя вновь появляются OOM/503, ухудшается чтение истории или нарушается автономный цикл — откатить согласованным способом и зафиксировать инцидент.

**Критерии принятия:** проверенное сохранение истории и изоляции проектов; отсутствуют таймауты `director_runs` и повторяющиеся OOM в согласованном окне наблюдения; RSS остаётся с запасом ниже 512 MiB; автономный цикл и сеть работают штатно; отсутствие платных API/YouTube-запросов при проверке. Один HTTP 200 недостаточен.

**Дополнительное доказательство OOM-04 (read-only SQL):** из 157 `director_runs` у всех `project_id IS NOT NULL`, 5 `data_json` больше 1,000,000 байт; это обосновывает приоритет серверной фильтрации при сохранении legacy-совместимости. Измерение памяти Python и точная причинность OOM остаются непроверенными.

**Approval gate OOM-05:** запросить у владельца явное разрешение отдельно на (1) создание ветки/PR с изменением кода и тестами, (2) деплой в Render. До разрешения не менять код, runtime, env, БД или тариф. OOM-04 завершён как проектирование, не как внедрение.

- **2026-11-19 — OOM-05 approved, OOM-06 in progress:** Owner explicitly approved code/test preparation in a separate branch and deployment **only after successful verification**, with rollback. Director branch `fix/oom-bounded-memory-reads-20261119` from deployed baseline `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc`; draft PR https://github.com/peonyrhodo-bit/site-insight-engine/pull/66. Commit `0eac8b51d5c6029b6437f3201cc39023bf808ae9` reduces `_recent_for_project` default page size 1000→50 without changing row projection or result filtering; commit `c20ba94ccd7b771374299f3ebd9d04e6eebacae3` adds isolated fake-client tests for first-page bound, legacy nested project across pages, timeout propagation. **Tests not yet executed**; draft PR mergeable=false (may be draft/unchecked); no merge/deploy. This is a conservative mitigation rather than the full server-side filtering proposal; it preserves analytical data semantics but may increase request count and does not prove OOM eliminated. Before deploy: run tests and review query/request-count regression, verify analytics unchanged, review PR checks, then use authorized deploy with rollback and monitor. No production modifications.

- **2026-11-19 — OOM-06 CI verification:** GitHub Actions at Director PR #66 head `c20ba94ccd7b771374299f3ebd9d04e6eebacae3`: four PR workflow runs all completed **success** (Reliability audit tests, Director run lifecycle tests, Supabase history pagination tests, Supabase backend regression tests). History-pagination job 135768239092 (run 44582960387) log: `PYTHONPATH=. pytest -q tests/test_supabase_history_pagination.py` → **4 passed**; `PYTHONPATH=. pytest -q` → **163 passed, 4 warnings, 11 subtests passed**. The new `tests/test_memory_pagination.py` is in the full suite; no separate named test result was extracted. **Not a production-memory validation.** The 1000→50 page change can increase number of HTTP requests for sparse project matches; check request volume and SQL timeout risk before merging/deploying. Draft PR remains unmerged; no production change. OOM-06 remains active pending code/behavior review and deploy readiness.

- **2026-11-19 — OOM-06 request amplification review (read-only SQL + test commit):** Supabase aggregate shows exactly **1 project and 157 rows** in `director_runs` (all rows same project). For the known dataset, latest 10 rows need one 50-row page (same number of HTTP calls as prior 1000-row page); full history requires four pages (50+50+50+7) versus one with 1000-row pages. Lower peak response size but more round trips; performance and OOM improvement not proven. Added test `test_full_history_same_as_legacy_page_size` in PR #66 at commit `c41dbdd260087de53687dcddfef25177effa2a83`: compare all 157 records/order to old page_size=1000, assert 4 vs 1 requests. **New commit CI results pending** (no workflow runs yet returned at check). Do not merge or deploy until fresh CI passes and remaining review is complete.

- **2026-11-19 — OOM-06 latest CI + deployment readiness:** Director PR #66 head `c41dbdd260087de53687dcddfef25177effa2a83`: all four GitHub Actions workflows success. History-pagination workflow run 44584426355/job 135773398441 log: focused tests **4 passed**; complete suite **164 passed, 4 warnings, 11 subtests passed**. Read-only Render service inspection: Director `site-insight-engine` tracks `main`, `autoDeploy=yes`, `autoDeployTrigger=commit`; **merging PR into main would automatically trigger production deploy**. Therefore do not merge as an incidental review action. PR is draft; merge readiness and rollback need explicit final review, and successful CI is not evidence of runtime RSS or absence of OOM. User authorized conditional deployment, but safeguard: confirm PR review, tests and rollback plan before any merge; never call `trigger_deploy` after merge because auto-deploy is enabled. No production changes at this stage.

- **2026-11-19 — OOM-06 merged, OOM-07 deployment underway:** PR #66 merged via squash at `09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae` after all four CI workflows passed (164 full-suite tests). Render Director auto-deploy detected `dep-dbvjoo8jo6nc73a4ljt0`, `trigger=new_commit`, status **build_in_progress** at 18:13:53 UTC; prior deployed baseline `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc` still reported live in deploy list. Rollback baseline recorded; no claims yet of production success or OOM resolution. Next: verify deploy live and monitor OOM/RSS, read timeouts and autonomous loop before OOM-08 closure.

- **2026-11-19 — OOM-07 initial production observation:** Render deploy `dep-dbvjoo8jo6nc73a4ljt0` at `09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae` confirmed **live** since 18:14:49 UTC; prior `f95bc0e4` deactivated. Metrics samples for new instance at 18:15 and 18:16 UTC: **104,337,410 bytes** (~99.5 MiB) memory against **536,870,900 bytes** (512 MiB) limit; only two samples, not enough for sustained stability. Post-deploy logs show Director memory initialized, autonomous worker started, autonomous cycle started 18:15:00, initial Supabase history reads now `offset=0&limit=50` and HTTP 200 for director_runs, decisions, recommendations, constraints, system_events, chat_messages, director_actions, director_results. Subsequent videos/video_snapshots reads also HTTP 200 through 18:15:17. Log window returned 49 entries, no OOM/error in that limited set. **Autonomous cycle completion not observed**, no sustained RSS or timeout absence established; keep OOM-07 open. No rollback needed on initial evidence; recheck later window and full autonomous cycle before closing.

- **2026-11-19 — OOM-07 ongoing monitoring, caution:** Render deployment still live at `09ceb05`. RSS trend on new instance (UTC 18:15–18:21): **104,337,410 → 260,767,740 → 311,488,500 → 309,235,700 → 339,828,740 → 345,956,350 → 389,423,100 bytes** (~99.5→371.4 MiB) vs limit 536,870,900 bytes (512 MiB). This is **not** a flat memory trend and may be hazardous if it continues; no proof of long-term OOM elimination. Post-deploy logs show autonomy reached assess/analyze/decide and research repeatedly; research executions at 18:19:50 and 18:20:42 UTC **failed** (4 planned, 0 collected, 4 failed per reported research attempt). Those were autonomous application actions, not triggered by the audit. No complete autonomous cycle observed. Last read-only log check to 18:24 UTC returned no explicit OOM but only limited observations. **Do not close incident**; next check fresh RSS and Render events, classify research errors and determine whether safe rollback is needed. No additional code or production action in this observation.

- **2026-11-19 — OOM-07 follow-up metrics/error triage:** Memory of post-deploy instance `x67hb` peaked at **389,423,100 bytes (~371.4 MiB) 18:21 UTC**, then **384,131,070 at 18:22**, **369,127,420 (~352 MiB) at 18:23**, below 536,870,900-byte limit; short observation only. Render still reports `09ceb05` live. Autonomous cycle 1 continued through research/assess/analyze/decide; `AIProviderResponseError: AI response does not contain valid JSON` at 18:21:30; research at 18:21:57 failed with `youtube_mcp_api_error: search.list request failed`, 4 planned/0 collected/4 failed. Other research attempts likewise failed; **no evidence of completed autonomous cycle**. Log coverage to 18:40 UTC returned no explicit OOM, but latest log activity around 18:22 and latest memory sample 18:23, so cannot assert health to 18:40. These research calls were initiated by deployed autonomy, not this audit; quota counters appear in logs, investigate before triggering any manual paid/API activity. Keep OOM-07 open; classify YouTube MCP and AI JSON as separate incident tracks, not proven caused by memory patch. No rollback based on current RSS alone.

- **2026-11-19 — OOM-07 extended logs reveal write-side timeout:** Pagination through Render logs confirms at **18:26:03.827 UTC** `PATCH /rest/v1/director_runs?id=eq.222&select=id` returned **HTTP 500**; **18:26:04.722** autonomous wakeup failed, PostgREST `57014 canceling statement due to statement timeout`. Unlike pre-fix failure on history SELECT, this failure is on **director_runs PATCH**, outside the bounded read patch. Cycle 2 started afterwards, but no full-cycle success confirmed. RSS (new instance) 18:24–18:29 UTC: 391,852,030; 395,055,100; 394,788,860; **422,379,520 (~402.8 MiB)**; 396,136,450; 389,890,050 bytes. All sampled below 536,870,900-byte limit, but headroom only ~109 MiB at peak. Read-only Supabase SQL: `director_runs` now **159 rows**, max `data_json` 2,419,593 bytes, avg 67,320 bytes, five >1MB. Research `youtube_mcp_api_error: search.list request failed` repeats and autonomous cycle is retrying, potentially consuming quota; do not manually invoke research. **OOM-07 not closed; prioritize investigation of large row PATCH / JSON update and autonomous failure/retry loop, before claiming mitigation success or considering any further deploy.** No code or DB changes made in this step.

- **2026-11-19 — OOM-07 critical follow-up:** Render metric at 18:29 UTC **486,645,760 bytes (~464.1 MiB / 512 MiB)**, after 396,136,450 at 18:28. Logs at **18:29:49 UTC** show `Waiting for application shutdown` and `Application shutdown complete`; no further log entries in 18:29:49–18:50 window. Render deploy still reports `09ceb05` as `live` (deploy status is not proof instance healthy). **No explicit OOM kill in retrieved logs; cause of shutdown unknown**, investigate Render instance lifecycle, service events, and restart. This follows prior 18:26:03 `director_runs PATCH` HTTP 500 / PostgREST 57014 and repeated research failures. Prior baseline `f95bc0e4` had OOM too, so rollback is not a known safe remedy without evidence of regression. Keep OOM-07 open, do not assert fix successful. No production changes performed.

- **2026-11-19 — OOM-07 root-cause narrowing (read-only):** Render `list_events` 18:10–19:00 UTC contains only successful deploy/build events; **no `server_failed`/OOM reason** surfaced. Service metadata remains `plan=free`, one instance, no suspension, deploy `09ceb05` live. Source review of `memory/supabase.py:update_run` on main: `SELECT data_json WHERE id=run_id`, merge whole existing JSON with incoming `data`, then `UPDATE director_runs SET data_json=<whole merged document>, ... WHERE id=run_id RETURNING id`. This is a concrete write-amplification candidate for 18:26:03 PATCH 57014, but **not proven causal**; need inspect row id 222 size, triggers/indexes/locks and call-site contract read-only before proposing changes. The 18:29:49 graceful shutdown logs do not prove OOM; Render event history does not identify cause. No code, schema, deployment or API calls changed by this audit. OOM-07 remains open.

- **2026-11-19 — OOM-07 row-level verification overturns large-PATCH assumption:** Read-only SQL on `director_runs.id=222` (the 18:26:03 timed-out PATCH target): `status=partial`, `project_id=default`, **`pg_column_size(data_json)=472 bytes`**, entire row **696 bytes**, `updated_at=18:26:03.832199+00` (near failed PATCH timestamp). Thus this **specific** timeout cannot be attributed simply to rewriting a multi-MB JSON payload; update may even have persisted despite HTTP timeout, but that is **not established** by timestamp alone. `director_runs` has primary-key btree on `id`, created_at index, status/updated index, active-project partial unique index; **zero non-internal triggers**. No evidence to justify index/migration changes. Focus next on DB contention/transaction latency, API timeout semantics, repeated autonomous updates and application lifecycle; inspect update_run callers before altering persistence contract. GitHub code search for `update_run` yielded no matches (search limitations), so caller map still unverified. No writes or deployments performed.


</details>

## C. Memory & Intelligence 2.0: M01–M40

**Перенесено из:** https://github.com/peonyrhodo-bit/youtube-mcp/blob/project-management/director-audit-2026-11-19/management/MEMORY_INTELLIGENCE_2_PLAN.md. M01/M02 частично, все 40 остаются [ ] до доказательной приёмки.

<details>
<summary>Полный текст исходных задач, критериев и технических результатов (раскрыть)</summary>

# Memory & Intelligence 2.0 — рабочий план Director 3.0

**Версия:** 1.0 · **Дата:** 2026-11-19 · **Статус:** проектирование · **Прогресс:** 0/40 пунктов принято.

**Подчинение:** согласованное `/тз директор 3,0` (Git blob `784efdfeefc394110982aa7e81139f7c3580758c`), генеральное `/тз` как контекст; основной маршрут `management/MASTER_PLAN.md` (особенно №009–010, №011–020, №021–030, №031–050, №056–059). Проект архитектуры: `management/MEMORY_INTELLIGENCE_2_DESIGN.md`. Инцидент OOM: `management/OOM_RECOVERY_PLAN.md`, OOM-07 открыт.

**Правила:** исходные ТЗ не изменять. Без отдельного разрешения не менять production, схемы и данные Supabase, Render, API-квоты, тарифы, не удалять ничего. **Нулевой бюджет** — обязательное условие ТЗ. Полная история, доказательства, рекомендации, согласия и задачи сохраняются. Автоматическая очистка разрешается только после отдельного утверждения конкретной политики и успешной проверки восстановления. Статусы: ⬜ не начато · 🔄 в работе · ⛔ заблокировано · ⚠️ дефект · ✅ доказательно принято. Наличие кода или успешного HTTP не равно выполненному требованию.

## A. Требования и инвентаризация (M01–M08)
- [ ] **M01.** Построить полную матрицу пунктов `тз директор 3,0` → данные → жизненный цикл → интерфейс → тест → основной пункт аудита. **Приёмка:** ни одного обязательного требования без ссылки и проверки; спорные положения в DECISIONS.
- [ ] **M02.** Составить карту всех читателей/писателей Supabase в Director, MCP и Orchestrator. **Приёмка:** таблица методов, вызывающих путей, полей и объёмов, включая `update_run`.
- [ ] **M03.** Измерить реальные лимиты бесплатного Supabase: база, Storage, WAL/резервирование, ограничения, текущая доля и скорость роста. **Приёмка:** подтверждённые квоты и дата замера, без догадок.
- [ ] **M04.** Измерить RAM Render на этапах автономного цикла, пики, копии структур, OOM/остановки. **Приёмка:** воспроизводимый профиль и отделение доказанного OOM от штатного shutdown.
- [ ] **M05.** Инвентаризировать таблицы, JSON/TOAST, индексы, дубликаты, связи, возраст и размер записей. **Приёмка:** карта роста по таблицам и классификация каждой категории.
- [ ] **M06.** Выделить обязательные долговечные сущности: пользовательские задачи, планы, статусы, решения, рекомендации, согласия, доказательства, прогнозы, исходы, квоты. **Приёмка:** явные запреты удаления.
- [ ] **M07.** Проверить доступные *бесплатные* варианты архива и восстановления, ограничения, безопасность и стоимость 0. **Приёмка:** подтверждённая схема или честное ограничение без обязательного архива.
- [ ] **M08.** Согласовать бюджет RAM/хранилища, пороги предупреждений и пределы роста. **Приёмка:** документированные пороги на основании M03–M04.

## B. Контракты, качество аналитики и тесты (M09–M15)
- [ ] **M09.** Зафиксировать схемы, версии, project isolation, legacy ID, сортировку и семантику полной истории. **Приёмка:** контрактные тесты.
- [ ] **M10.** Собрать обезличенный эталонный набор текущих данных и ожидаемых результатов аналитики. **Приёмка:** повторяемые KPI/оценки/тренды, без публикации секретов.
- [ ] **M11.** Проверить требования ТЗ к трендам, повторным измерениям, конкуренции, монетизации, бесплатной реализуемости и бюджету производства. **Приёмка:** матрица входов, доказательств, неизвестных и тестов.
- [ ] **M12.** Спроектировать provenance: источники, время, язык/рынок, версии алгоритмов, полнота, уверенность, ссылки от рекомендаций к данным. **Приёмка:** восстановимый путь «рекомендация → доказательство».
- [ ] **M13.** Спроектировать сравнение прогнозов с фактами, когорты, временные окна и еженедельный отчёт. **Приёмка:** тесты воспроизводимости и сравнения.
- [ ] **M14.** Проверить работу при пропусках, устаревших и противоречивых данных. **Приёмка:** честные статусы «неизвестно/предварительно», без ложных выводов.
- [ ] **M15.** Утвердить тестовые пороги: точность/паритет старых KPI, доказательность, пиковая RAM, длительность цикла, запросы и квота. **Приёмка:** измеримые критерии до кодирования.

## C. RAM и доступ к данным (M16–M22)
- [ ] **M16.** Спроектировать bounded API памяти: server-side project_id/date filtering, legacy fallback, выбранные поля. **Приёмка:** полный и корректный результат без неограниченного SELECT *.
- [ ] **M17.** Спроектировать курсорную пагинацию с устойчивой сортировкой и обработкой параллельных записей. **Приёмка:** нет пропусков/дубликатов.
- [ ] **M18.** Ввести потоковую/пакетную обработку видео, снимков, связей и исследований. **Приёмка:** RAM ограничена при росте истории.
- [ ] **M19.** Исключить ненужные копии больших структур и бесконтрольные кэши. **Приёмка:** профили памяти до/после.
- [ ] **M20.** Разделить компактное состояние цикла и тяжёлые результаты; проверить `update_run`, блокировки, идемпотентность. **Приёмка:** запись/восстановление без 57014 на репрезентативных тестах.
- [ ] **M21.** Ввести безопасные лимиты на размер рабочего набора и graceful degradation без потери задач. **Приёмка:** OOM не приводит к ложному успеху или потере работы.
- [ ] **M22.** Проверить полноту аналитики при потоковой обработке на исходных данных. **Приёмка:** паритет M10/M15, все временные интервалы доступны.

## D. Самоочищающаяся Supabase (M23–M30)
- [ ] **M23.** Утвердить классы хранения: защищённые, исторические исходники, временные; явный список таблиц/полей. **Приёмка:** ни одна важная сущность не подпадает под TTL.
- [ ] **M24.** Определить retention по типу записи, зависимостям и полезности; защитить оригинальные временные снимки, необходимые для трендов. **Приёмка:** согласованная политика и доказуемая полнота.
- [ ] **M25.** Спроектировать компактные агрегаты и индексы для быстрого анализа, без подмены исходников. **Приёмка:** версии и проверяемая точность.
- [ ] **M26.** Спроектировать дедупликацию *только* семантически идентичных записей, с сохранением ссылок. **Приёмка:** никаких потерянных временных наблюдений.
- [ ] **M27.** Спроектировать бесплатный архив, манифесты, контрольные суммы и тест восстановления либо зафиксировать невозможность архива. **Приёмка:** восстановление проверено.
- [ ] **M28.** Реализовать **только dry-run** очистки: кандидаты, объём, связи, причины исключения, ожидаемая экономия. **Приёмка:** отчёт без удаления.
- [ ] **M29.** Получить отдельное разрешение на точную политику автоочистки, ограничения и аварийную остановку. **Приёмка:** явное согласование владельца.
- [ ] **M30.** После M27–M29: ограниченная очистка с журналом, карантином/восстановлением и проверкой реального освобождения объёма. **Приёмка:** ни одной нарушенной ссылки/аналитики; без разрешения ⛔.

## E. Автономность, качество решений и устойчивость (M31–M35)
- [ ] **M31.** Долговечная очередь пользовательских задач, планы циклов, причины переноса и resume после перезапуска. **Приёмка:** 24 часовых слота, без параллельных дублей.
- [ ] **M32.** Единый учёт квот, дедуп исследований, TTL полезных ответов, bounded retry/backoff/circuit breaker. **Приёмка:** ошибки MCP не порождают бесконечные вызовы.
- [ ] **M33.** Проверить статусы попытка/старт/частично/успех/ошибка/пропуск/блокировка/неизвестно. **Приёмка:** подтверждение результата, а не просто HTTP 200.
- [ ] **M34.** Проверить сохранение согласий пользователя и перехода «рекомендация → задача», без сценариев/публикаций. **Приёмка:** нет задач без согласия.
- [ ] **M35.** Проверить объяснения на русском, источники, неизвестные, режим бюджета и полезность рекомендаций. **Приёмка:** сквозные примеры по ТЗ.

## F. Внедрение, эксплуатация и приёмка (M36–M40)
- [ ] **M36.** Реализовать изменения в отдельных ветках и флагах, с независимыми миграциями и откатом. **Приёмка:** код-ревью, CI, документированные риски.
- [ ] **M37.** Провести offline/fixture нагрузочные тесты на текущих объёмах и росте ×2/×5, без платных API. **Приёмка:** измеренные RAM, latency, качество, квоты.
- [ ] **M38.** Провести ограниченный canary после разрешения, сравнить старую/новую аналитику и расход ресурсов. **Приёмка:** никаких регрессий, OOM и ложных завершений.
- [ ] **M39.** Настроить наблюдаемость: RSS, Supabase storage, рост, cleanup dry-run, пропуски, циклы, квоты, качество рекомендаций. **Приёмка:** тревоги и журнал действий.
- [ ] **M40.** Провести сквозную приёмку по полному ТЗ и обновить MASTER_PLAN, оставив архив и откат доступными. **Приёмка:** доказательства по каждому требованию; статус завершён только при фактическом результате.

## Первые действия и блокировки

**Следующий шаг:** M01 + M02 (только чтение) и M03 (подтверждение квот), затем M04. Проектирование и измерение разрешены; production-изменения, удаление и платные вызовы — только по отдельному согласованию. **OOM-07 не закрывать** до стабилизации сервиса. Не считать M01 выполненным только потому, что прочитаны отдельные разделы ТЗ: нужен полный перечень требований и трассировка.

**Важная граница:** ТЗ требует постоянно пополняемый архив рекомендаций, исторические сравнения и нулевую стоимость. При конечном бесплатном хранилище нельзя гарантировать бесконечный рост без внешнего бесплатного проверенного архива или остановки при нехватке места. Приоритет — сохранность данных и честное предупреждение, а не скрытое удаление.

## Журнал исполнения — 2026-11-19

- **M01 в работе, 0/40 принято.** Прочитано согласованное `тз директор 3,0` по разделам 1–20; составлена матрица из **34 контрактов памяти/аналитики R01–R34**: `management/MEMORY_2_TZ_TRACEABILITY.md`, коммит `399663c`. Для каждого: раздел ТЗ, контракт, класс хранения и способ проверки. Отдельно зафиксированы обязательный нулевой остаток полезной дневной квоты (§11) и запрет бессмысленных повторов (§6.3, §11.3): при недоступности источника фиксировать дефект, а не ложно объявлять норму. **Не закрыто:** атомарная трассировка всех подпунктов приёмки §18–19 в общем №009, проверка реализации и реального runtime. Следующий M02: карта чтений/записей по R-ID; затем M03 и M04. Production и Supabase не изменены.

- **M02 в работе (2026-11-19):** просмотрены `memory/supabase.py` (1903 строки), `director/director.py` (3075) и `director/autonomy.py` (910) в `site-insight-engine`; описаны read/write методы, риски материализации всех страниц, `get_context` и read–merge–write `update_run`. Карта `management/MEMORY_2_ACCESS_MAP.md`, коммит `86f630f`. До закрытия нужны реальные call sites, адаптеры и аудит MCP/Orchestrator. **0/40 закрыто**. Данные/production не изменены.


</details>

## D. Приоритеты и отложенные задачи BACKLOG

**Перенесено из:** https://github.com/peonyrhodo-bit/youtube-mcp/blob/project-management/director-audit-2026-11-19/management/BACKLOG.md. Каждая задача сопоставляется с №009–059; это не отдельная очередь.

<details>
<summary>Полный текст исходных задач, критериев и технических результатов (раскрыть)</summary>

# Очередь работ (приоритеты технического руководителя)

## P0 — управление и безопасность изменений
- [ ] Зафиксировать полную карту требований Директора 3.0 с критериями приёмки и ссылками на код/проверки.
- [ ] Проверить действующие версии и конфигурации трёх production-сервисов, не раскрывая секретов.
- [ ] Зафиксировать порядок безопасного тестирования без расходования YouTube-квоты и без платных сервисов.
- [ ] Отдельно оценить риск Supabase RLS и безопасный путь устранения без нарушения работы.

## P1 — сквозная функциональность Директора
- [ ] Проследить фактический путь: триггер → цикл → план → исследование → сохранение → аналитика → рекомендация → интерфейс.
- [ ] Сопоставить ошибки Render с записями `director_runs`, временем запросов и участками кода.
- [ ] Выяснить причину `UnicodeEncodeError` в MCP и воспроизвести без живых YouTube-запросов.
- [ ] Разобрать `stale_timeout`, `ReadError`, повторные попытки, идемпотентность и поведение после перезапуска.
- [ ] Проверить почему исследования сохраняются, а рекомендации не появляются; не делать вывод до трассировки.
- [ ] Проверить лимиты памяти, объёмы выборок, очистку временных объектов и работу при ограниченной RAM.

## P2 — приёмка требований
- [ ] Провести безопасные локальные/CI тесты; живые проверки — только с разрешёнными ограничениями квоты и среды.
- [ ] Проверить язык интерфейса, пользовательские задачи, обсуждение, подтверждение рекомендаций, бюджеты, отчёты и границы автоматизации.
- [ ] Составить итоговую матрицу: проверено / частично / дефект / не проверено / заблокировано.

## Отложено по решению владельца
- Исправление пропусков пробуждения бесплатных Render-сервисов; считать внешнее пробуждение нестабильным входным условием.
- Реализация следующих стадий автоматического производства/публикации видео до завершения текущего этапа.

## Правила заданий Codex
Одна проблема — одна ветка — один PR; точные затрагиваемые файлы, тесты, ожидаемый результат, запрет менять ТЗ и посторонний код. Ни один PR не принимать без анализа диффа и проверки регрессий.


</details>

## E. Идемпотентный поиск активного запуска (№013/035/036)

**Перенесено из:** https://github.com/peonyrhodo-bit/youtube-mcp/blob/project-management/director-audit-2026-11-19/management/CODEX_TASK_ACTIVE_RUN_LOOKUP.md. Предложение, не внедрённое исправление; технические детали и проверки сохранены.

<details>
<summary>Полный текст исходных задач, критериев и технических результатов (раскрыть)</summary>

# Задание Codex — оптимизация проверки активного цикла (черновик, без запуска)

Дата: 2026-11-19. **Статус: подготовлено для отдельного согласования; код не изменён.** Репозиторий: `peonyrhodo-bit/site-insight-engine`.

## Доказанный дефект

`memory/director_adapter.py:create_run` перед созданием цикла загружает всю историю `director_runs` посредством `_recent_for_project(limit=None)`. `memory/supabase.py:_recent_for_project` делает `select('*')`, `order(created_at DESC, id DESC)`, пагинацию по 1000 и фильтрацию проекта на стороне Python. Render зафиксировал SQL timeout (HTTP 500, PostgreSQL 57014) именно на таком запросе, после чего `Autonomous wakeup failed`. **Не доказано**, что оптимизация устранит все сбои или причины потери heartbeat.

## Данные схемы, проверенные только на чтение

- `director_runs_one_active_per_project_idx`: уникальный частичный индекс по `project_id` для `status IN ('requested','running')`.
- `director_runs_status_updated_at_idx`, `idx_director_runs_created_at`, PK по `id`.
- `EXPLAIN` узкого запроса `WHERE project_id='default' AND status IN ('requested','running')` показывает `Index Scan using director_runs_one_active_per_project_idx`.
- В текущих 151 строках `project_id IS NULL` — 0. Но поддержка legacy `data_json.project_id` в коде есть, её нельзя бездумно удалить.

## Предлагаемый объём PR (только после разрешения)

1. Выделить отдельный read-only метод поиска активных запусков, использующий `project_id`, `status`, индекс и минимальные столбцы; не изменять общий `_recent_for_project` для исторических выборок.
2. Сохранить корректную обработку legacy-полей и защиту от параллельных запусков; если legacy невозможно безопасно проверить без полной выборки, явно документировать компромисс и предложить отдельный безопасный путь.
3. Сохранить атомарную уникальность на уровне БД; обработать гонку двух воркеров и конфликт уникального индекса.
4. Добавить регрессионные тесты: большое количество завершённых запусков; один активный; устаревший активный; ошибка БД; legacy-строка; два конкурирующих старта; отсутствие полного `select('*')` на горячем пути.
5. Запустить локальные тесты/CI без живого YouTube API. Никаких изменений схемы/деплоя без отдельного разрешения. После PR сверить с Render и Supabase, не выдавать CI за доказательство production.

## Критерии приёмки

- Новый запуск не считывает всю историю только ради поиска активной записи.
- Одновременно допускается максимум один активный цикл проекта, включая гонку воркеров.
- Устаревшие записи обрабатываются корректно; живой цикл не перехватывается.
- Ошибки чтения не замалчиваются и не приводят к дублирующим запускам.
- Тесты зелёные, а последующая реальная проверка показывает завершённые циклы и сохранённые результаты.

**Ограничение:** этот кандидат не объясняет `UnicodeEncodeError` в youtube-mcp и прекращение heartbeat; их расследовать отдельно.


</details>

## F. ResearchSet и RAM (№038/056)

**Перенесено из:** https://github.com/peonyrhodo-bit/youtube-mcp/blob/project-management/director-audit-2026-11-19/management/CODEX_TASK_RESEARCH_SET_CONTEXT_MEMORY.md. Проверки API, stale cache, project isolation, RSS сохранены.

<details>
<summary>Полный текст исходных задач, критериев и технических результатов (раскрыть)</summary>

# Codex task — Director research-set context memory (proposal only)

Status: **NOT APPROVED / NOT IMPLEMENTED**. Audit baseline: deployed site-insight-engine commit `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc`. Production budget 512 MiB. Do not modify production or run quota-consuming tests without separate approval.

## Verified problem mechanism

- Supabase read-only aggregates: 68 `research_sets` rows contain ~7,969,895 bytes of JSON text; `metadata.research_plan` 5,484,208 bytes and `metadata.operation_results` 1,768,295 bytes.
- `server.py:1478–1491`: `DataAdapter.get_project_state()` recursively serializes full `ResearchSetManager.all()`, including metadata, into new dict/list objects. `server.py:303–340` recursive serializer.
- `director/director.py:586–595,851–879`: `Director.inspect()` merges full state; unknown `research_sets` key persists as `DirectorContext.metadata['research_sets']`. The AI decision context is explicitly whitelisted (`director/director.py:330–386`) and does not directly include it.
- `data/research_sets.py:688–715,1213–1217`: `ResearchSet.summary()` and `ResearchSetManager.summaries()` already provide compact representations excluding heavy metadata.
- **Compatibility blocker:** `server.py:4006–4022` GET `/radar-debug` and `server.py:4032–4050` GET `/radar` both return `serialize(await runtime.data.get_project_state(...))`. Replacing full `research_sets` in the shared method would change these HTTP contracts. No external consumer inventory completed.

## Candidate design for implementation review

Introduce a Director-only compact state projection (or opt-in `include_full_research_sets` argument with backwards-compatible default) so `Director.inspect()` receives only `research_manager.summaries()` while existing `/radar` and `/radar-debug` contracts remain unchanged. Prefer a dedicated lightweight method/flag that avoids constructing full `research_sets` in the first place; do not generate full list and then trim. Keep full `ResearchSetManager`, `ResearchSet.to_dict()`, Supabase persistence, research deduplication and evidence drill-down unchanged. Consider memory impact of full debug endpoint separately.

## Acceptance tests (local synthetic fixtures, no external calls)

1. With 68 synthetic research sets whose `metadata` contains realistic ~100KB research plans/results, assert Director projection omits large nested metadata and contains required summary fields and correct `research_set_count`.
2. Assert original full `get_project_state()` result and `/radar`, `/radar-debug` JSON structures remain compatible, including full `research_sets[*].metadata` (unless explicit separate contract approval).
3. Assert Director AI bounded payload, research_history, decisions, recommendations, research deduplication and persistence of full research plans/results unchanged.
4. Measure process peak RSS and Python allocations before/after with repeatable isolated fixture; report baseline, peak and delta. Avoid claiming improvement from JSON sizes alone. Test under a 512MiB equivalent limit where feasible.
5. Cover empty/partial Supabase reads, exceptions and concurrent Director cycles; verify compact mode never silently reports complete when data is partial.
6. Search all repository modules/tests and external documented clients for `get_project_state`, `/radar`, `/radar-debug` and `research_sets` before code change. Inspect any generic `DirectorContext.to_dict()` persistence paths.

## Gate

No source-code changes, deploys, DB writes, or production calls as part of this management task. Implement only after user authorization and verified baseline. OOM root cause remains unproven; this is a measured data-volume and code-path optimization candidate, not a confirmed fix.

## Additional endpoint/call-path audit (deployed f95bc0e)

- `GET /director/snapshot` (`server.py:2267–2273`) explicitly awaits `director.inspect()`, which calls `DataAdapter.get_project_state()` and retains full serialized `research_sets` in Director metadata. Thus a read-only snapshot request can trigger this memory-heavy preparation even though its HTTP response is only `get_unified_state_snapshot()`. Include this path in optimization acceptance tests.
- `GET /director-debug` (`server.py:3963–4001`) builds a selected diagnostic payload from an existing Director context and **does not itself call inspect**. Do not conflate it with `GET /radar-debug`, which calls full `get_project_state()`.
- `GET /dashboard` (`server.py:3063+`) calls `director.status()` and memory `get_context()`, not `get_project_state()` in the inspected route start. The cycle handlers `server.py:2481+` and `2763+` call `run_once` and `run_autonomous_cycle`, which can inspect internally; verify actual mode-specific flow before test design.
- `GET /radar` and `GET /radar-debug` remain direct consumers of full `get_project_state()` and are a compatibility gate. Any Director-only compact projection should be selected **before** recursively serializing full research sets; trimming afterward does not eliminate transient allocation.

### Additional acceptance cases

- Verify `/director/snapshot` uses the compact projection and still returns the same unified snapshot shape and accurate counts.
- Verify `/director-debug` remains bounded and does not unexpectedly trigger data reload; distinguish from `/radar-debug` in tests and documentation.
- Verify the shared Runtime/Director instance does not retain stale full `metadata['research_sets']` after switching to compact projection; no silent stale-data regressions.

## Cached Director lifetime and stale metadata (deployed f95bc0e)

- `server.py:1751` `Runtime.__init__` creates `self.directors: dict[str, Director] = {}`.
- `server.py:1978–2002` `Runtime.get_director(project_id, mode)` returns an existing Director object for that project, otherwise constructs and caches one. Note: requested `mode` is ignored if the cached object already exists; mode behavior warrants a separate review, not a proven incident.
- `director/director.py:435+` `Director.inspect` updates the existing `self.context` rather than constructing a new context per request.
- `director/director.py:851–879` `_merge_context` assigns unknown nonempty fields into `self.context.metadata`, and does **not delete absent keys**. Therefore if an earlier inspection stored `metadata['research_sets']`, merely omitting that key in later compact responses will leave the prior full serialized list reachable for as long as the cached Director remains alive.

**Implementation requirement:** explicitly clear/replace the obsolete full `metadata['research_sets']` in the Director-specific compact projection path, with careful behavior on partial/unavailable reads (do not erase evidence or report false completeness). A migration/cleanup test must populate the cached Director with full research metadata, invoke compact inspection again, then assert old full payload is not reachable via Director context; verify snapshot, state and status remain correct. Do not indiscriminately clear all context metadata or lose legitimate state. Verify cache behavior across multiple project IDs and mode choices. No code change or live experiment performed.

## Mode-aware cache review (separate concern; no fix in this task)

At deployed `f95bc0e`, `server.py:1978–2002` `Runtime.get_director(project_id, mode)` caches only by `project_id`, returns the existing instance before considering `mode`, and defaults new instances to `DirectorMode.AUTONOMOUS`. `director/director.py:242–271` constructor sets `self.mode=mode` and default `AutonomyConfig(enabled=mode == DirectorMode.AUTONOMOUS)`. `director/director.py:3039–3050` status reports stored mode. Thus a later mode argument cannot change an existing Director's mode or default autonomy configuration. This is verified behavior, **not a demonstrated incident**: inspected `server.py` call sites normally use the autonomous default; explicit autonomous worker passes the same mode. No evidence of a currently requested MANUAL instance in those paths. Keep any mode/cache redesign separate from the research-set projection task; add a regression check that compact projection does not mutate `mode`, `autonomy_config`, or cached instance identity.

## Partial-read and stale-state semantics (verified deployed f95bc0e)

- `server.py:1074–1110` `DataAdapter.get_project_state` initializes `research_sets=[]` and zero-valued `data_inventory`, then attempts loaders. `server.py:1186–1243` research restore is conditional on loader availability, first project load and a dict result. If research loader returns a non-dict, it is not restored, but the method can still return its result dict with the initial empty `research_sets` (the existing manager may nevertheless be nonempty). This is not an atomic verified-complete project read.
- `server.py:1478–1491` later populates `result['research_sets']` from the *current in-memory registry*, which may reflect a previous successful load rather than the latest Supabase read. `_loaded_project_id` (`server.py:1243`) gates reloading; repeated calls for the same project do not automatically re-fetch research.
- `director/director.py:586–617` `inspect` marks `runtime_health['project_data']['status']='healthy'` whenever the data service returns a dict; it marks degraded for non-dict, unavailable on raised exception. The returned dict is not independently checked for table-by-table freshness/completeness here. Do **not** interpret this healthy flag as proof that research tables were freshly read.
- `director/director.py:851–879` `_merge_context` stores unknown keys such as `research_sets` in metadata even when the value is an empty list; for known context collections, empty values are skipped unless `replace_empty=True`. Therefore proposed cleanup must distinguish: stale *duplicate projection* safe to drop vs authoritative live registry/evidence that must survive transient failed reads.

**Required test matrix:** (a) complete initial research load; (b) loader exception; (c) non-dict research result; (d) same-project cached registry/no reload; (e) fresh empty project; (f) partial table results; (g) switch between project IDs on one Runtime (check registry scoping). Assert status is not falsely upgraded by the *new* compact projection, no evidence is silently deleted, and stale serialized `metadata['research_sets']` is removed when appropriate without clearing authoritative `ResearchSetManager`. Any improvement to existing health classification is a separate behavioral change requiring approval.

## Shared mutable DATA adapter / cross-project isolation (deployed f95bc0e)

- `server.py:1675–1687` Runtime creates **one** `self.data=DataAdapter(storage=self.memory.backend)`; `server.py:1978–2002` passes this same adapter into every per-project cached Director.
- `server.py:698–752` DataAdapter owns one set of mutable `youtube_registry`, `research_manager`, `relations`, `opportunity_registry` and one `_loaded_project_id` flag, not a per-project registry map.
- `server.py:1126–1245` a project switch can clear/repopulate YouTube and research registries, replace opportunity registry and set `_loaded_project_id` at the end. There is no visible lock around the whole `get_project_state` load; awaits on storage allow overlapping calls. The exact exploitability and cross-project data exposure are **not established** and require controlled tests.
- `server.py:1437–1458` inventory counts can fall back to the current shared registries; if loading fails/returns partial data after a project switch, these may not reflect the requested project. This is a test hypothesis, not a demonstrated leak.

**Separate safety gate before memory implementation:** create isolated local tests with project A and B fixtures, disjoint research IDs/video IDs and mocked storage. Test A→B→A sequential requests, overlapping `asyncio.gather` A/B reads with controlled await interleaving, loader exception/non-dict for B after A, and cached Director A snapshot after B. Assert project IDs, observations, counts, research summaries, relations and persisted full metadata never mix. Verify any new compact method uses the same project-isolation safeguards and does not increase cross-project exposure. If isolation fails, treat as a separate safety defect requiring approval and priority review; do not opportunistically refactor storage during this memory-only task. No production execution or code modifications made.

## Concrete cross-project stale-research branch (code-confirmed, not live-reproduced)

Pinned deployed `site-insight-engine@f95bc0e`:

1. `server.py:1193–1200`: when `project_id != self._loaded_project_id`, research storage is awaited; research registry restoration occurs **only if** `persisted_research` is a dict.
2. `server.py:1217–1230`: `self.research_manager.clear()` is inside that dict branch. A non-dict research load leaves prior-project research entries intact.
3. `server.py:1245`: `self._loaded_project_id=project_id` runs regardless of whether the research loader returned a dict.
4. `server.py:1478–1491`: the returned `research_sets` is serialized from the current `self.research_manager.all()` without a project filter.

**Code-path consequence:** after successful project A load, a project B request with a non-dict research load can return A's research sets under B's project ID; subsequent B calls skip reload because `_loaded_project_id=B`. Whether such a non-dict result occurs in production is unverified. Other loaders can produce similar stale-state hazards; do not assert them without tracing each branch.

**Severity:** potential cross-project data isolation defect; elevate for explicit safety triage. Add a deterministic no-network unit test using mocked storage returning A data then non-dict for B, assert B never receives A IDs or metadata, that the load is flagged incomplete, and that a later B request can retry. Also test exceptions and interleaving. Candidate remediation (not approved): stage each project's complete data in isolated temporary registries and atomically publish only on verified successful load, or keep strictly project-scoped registries and explicit partial-read status; do not simply clear authoritative data on every transient error. Keep this safety fix distinct from research-set memory projection.


</details>

## G. Функциональное восстановление: этапы 0–11

**Перенесено из:** https://github.com/peonyrhodo-bit/youtube-mcp/blob/docs/plan-director-functional-recovery/%D0%BF%D0%BB%D0%B0%D0%BD%20%D0%B2%D0%BE%D1%81%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D1%8F%20%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D0%BE%D1%81%D0%BF%D0%BE%D1%81%D0%BE%D0%B1%D0%BD%D0%BE%D1%81%D1%82%D0%B8%20%D0%B4%D0%B8%D1%80%D0%B5%D0%BA%D1%82%D0%BE%D1%80%D0%B0%203%2C0. В исходном тексте этап 1 требует полный цикл рано; **фактический порядок выполнения:** сначала изолированные компоненты, общий сквозной цикл в №058.

<details>
<summary>Полный текст исходных задач, критериев и технических результатов (раскрыть)</summary>

# План восстановления работоспособности директора 3.0

**Назначение:** довести директора от текущего состояния до фактического выполнения своей основной задачи по ТЗ 3.0. Этот документ дополняет, но не заменяет «План проверки ТЗ директора 3.0». Подробный план аудита сохраняется без изменений и используется позже для полной формальной приёмки.

**Главный принцип:** технически запущенный цикл не считается работающим директором. Успех подтверждается только тогда, когда директор правильно оценивает состояние проекта, выбирает обоснованные исследования, получает реальные данные, делает проверяемые выводы, сохраняет их и предпринимает следующий необходимый шаг.

## Как выполнять этот план

Работать строго по этапам и не переходить к следующему, пока текущий не прошёл критерии приёмки либо не зафиксирована конкретная блокировка.

Для каждого этапа обязателен один и тот же рабочий цикл:

1. Изучить применимые пункты ТЗ и эталонной карты требований.
2. Проследить всю цепочку реализации во всех затронутых репозиториях.
3. Зафиксировать исходное поведение до изменений: входные данные, действия директора, ответы сервисов, логи, записи в хранилище и видимый результат.
4. Составить список подтверждённых дефектов и показать его пользователю до исправления.
5. После согласования исправить дефекты минимальными изменениями.
6. Запустить автоматические проверки в изолированной виртуальной среде, включая негативные сценарии и регрессии.
7. Проверить сквозной сценарий на работающем тестовом окружении с реальными интеграциями, где это безопасно.
8. Проверить работу в целевой реальной среде. Не выполнять опасные действия, не публиковать контент и не создавать расходы без отдельного разрешения.
9. Сопоставить логи, ответы API, сохранённые данные и фактическое поведение сайта.
10. Сохранить доказательства и указать статус: «Проверено успешно», «Проверено частично», «Обнаружен дефект», «Не проверено», «Заблокировано» или «Ожидает проверки в реальной среде».

Если реальную проверку выполнить нельзя, это не успех и не повод остановить работу с формулировкой «всё работает». Нужно точно указать недостающий доступ, настройку или среду. Если обнаружен большой или отдельный дефект, оформить самостоятельную задачу и продолжить только после решения о приоритете.

## [ ] Этап 0. Подготовить возможность доказательной проверки

**Зачем:** до исправлений установить, можем ли мы воспроизводимо запускать цикл и видеть, что с ним реально произошло.

**Что сделать:**
- Установить, как запускаются четыре компонента: `site-insight-engine`, `ai-youtube-system`, `youtube-mcp`, `youtube-office-watchdog`.
- Определить фактические адреса, конфигурацию, зависимости, способ запуска, доступные тесты, логи, хранилища и состояние тестового/рабочего окружения.
- Проверить, можем ли запускать директор в виртуальной среде без реальных побочных эффектов и неконтролируемого расхода YouTube API quota.
- Определить, как получить подтверждение из базы/памяти и сайта, что результат действительно сохранён и доступен.
- Установить идентификатор цикла или другой способ связать один запуск с запросами к API, исследованиями, сохранением и итогом.
- Зафиксировать исходное состояние и существующие ошибки, ничего не исправляя до получения базовой картины.

**Приёмка:** есть воспроизводимая инструкция запуска, понятен путь получения доказательств, известны ограничения тестовой и реальной среды. Если чего-то нет, создать конкретные блокирующие задачи. Сам по себе доступный health endpoint не является достаточным доказательством.

**Основа:** ТЗ §§6, 17–19; карта C03, D07, E01–E07, G01–G07, J01–J07, I07.

## [ ] Этап 1. Добиться фактического выполнения одного полного цикла

**Зачем:** выяснить, просыпается ли директор и выполняет ли работу до проверяемого результата, а не только начинает процесс.

**Проверить:**
- Что запускает цикл: планировщик, сигнал пробуждения или ручной вызов; какой механизм является главным.
- Доходит ли запуск до кода директора, не только до промежуточного API.
- Получает ли директор доступ к нужным зависимостям и данным.
- Доходит ли цикл до выбора задачи, реального исследовательского запроса, получения результата и сохранения результата.
- Какой статус записывается при полном успехе, частичном результате, ошибке и остановке.
- Не выдаётся ли «успех» при пустом результате, ошибке нижестоящего сервиса или несохранённой записи.
- Не завершается ли цикл сразу после общей фразы «данных недостаточно», не сохранив конкретные причины и следующий шаг.

**Виртуальные сценарии:** успешный цикл; нет доступного источника данных; ИИ недоступен; хранилище недоступно; пустой ответ; ошибка API; тайм-аут; частичный результат. В тестах внешние вызовы заменяются контролируемыми заглушками, где это необходимо.

**Приёмка:** один запуск имеет проверяемую последовательность шагов, фактический результат, корректный статус и сохранённую причину любого неполного завершения. Запуск функции или HTTP 200 сами по себе не проходят этот этап.

**Основа:** ТЗ §§5–7, 17–19; карта C01–C03, D05–D07, E01, G01–G05, J03–J04.

## [ ] Этап 2. Проверить, что директор действительно понял состояние проекта

**Это один из ключевых этапов.** Нельзя считать его пройденным на основании одной записи «состояние проекта проверено».

Перед выбором исследования директор должен сформировать проверяемый снимок состояния, основанный на ТЗ §6.2. Для каждого обязательного параметра фиксируются: полученное значение или факт, источник/запись, время актуальности, статус проверки, неизвестное или противоречие и влияние на следующий шаг.

Обязательные группы состояния:

1. **Работоспособность системы:** доступность ИИ, YouTube API и других разрешённых источников, памяти/хранилища, сайта и сохранения рекомендаций, планировщика; время последнего успешного цикла; ошибки и незавершённые операции; наличие другого активного цикла.
2. **Исследования:** завершённые и незавершённые задачи; пригодные для повторного использования результаты; недостаточно исследованные направления; гипотезы на проверку; наступившие повторные измерения; новые данные с прошлого цикла.
3. **Рекомендации и задачи:** рекомендации, ожидающие решения или обсуждения; принятые и отклонённые рекомендации; созданные задачи и их фактические статусы; новые данные, способные изменить старые выводы.
4. **Ресурсы и ограничения:** квота из единого менеджера; доступные бесплатные инструменты; ошибки/ограничения источников; выбранный режим бюджета; очередь пользовательских задач и их приоритет; выполнимость плана в оставшееся время.

**Специальные проверки против поверхностного «понимания»:**
- Сравнить снимок с фактическими данными в хранилище, журнале запусков, очереди задач и результатах исследований.
- Проверить не только наличие полей, но и корректность значений, актуальность и влияние на план.
- Для недоступных данных проверить, что они помечены как неизвестные, а не как «всё в порядке».
- Подготовить тестовый проект с заранее известными фактами, незавершёнными задачами, просроченным замером, ошибкой сервиса и ограниченной квотой. Сравнить, что директор обнаружил, что пропустил и как объяснил последствия.
- Сверить каждый пункт снимка с применимыми требованиями ТЗ; не ограничиваться произвольным коротким списком полей.
- Проверить, что пропуск важного параметра приводит к обнаруживаемому провалу теста, даже если цикл формально завершился.

**Приёмка:** все применимые параметры состояния из ТЗ §6.2 проверяются по отдельности; каждый результат подтверждён источником либо честно помечен неизвестным; найденные проблемы влияют на план цикла; журнал позволяет восстановить, что директор знал на момент решения.

**Основа:** ТЗ §§5.2, 6.2, 7.1–7.2; карта D05–D07, E01–E07, K15–K20, K39–K40, K50.

## [ ] Этап 3. Проверить общий план проекта и план конкретного цикла

**Зачем:** директор должен знать не только, что происходит, но и что проекту нужно делать дальше и почему.

**Проверить:**
- Существует ли сохраняемый общий план проекта, включающий цели ТЗ, направления исследований, ограничения, пользовательские задачи, незавершённые/заблокированные задачи, гипотезы, повторные проверки, приоритеты, бюджетный режим и критерии завершения.
- Формируется ли до работы план текущего цикла с конкретными задачами, ожидаемым результатом, причиной выбора, инструментами/источниками, квотой, ограничениями и критерием завершения.
- Соответствует ли порядок задач приоритетам ТЗ §7.3: (1) сохранность и восстановление; (2) полезные квотные исследования; (3) повторные измерения и проверка выводов; (4) новые исследования; (5) монетизация и реализуемость; (6) рекомендации и задачи; (7) оценка эффективности; (8) отчётность.
- Не вытесняются ли пользовательские задачи без объяснения; сохраняются ли они между циклами.
- Может ли директор изменить план при препятствии, сохранив причину и следующий шаг.
- Не является ли план формальным текстом вроде «исследовать YouTube», который невозможно принять или отклонить по результату.

**Тестовые сценарии:** есть просроченный замер и новые темы; недоступен один источник; есть пользовательская задача; квота ограничена; предыдущая задача не завершена; несколько задач конкурируют за приоритет.

**Приёмка:** до выполнения существует проверяемый план; после цикла видны фактическое выполнение, отклонения и причины. Для каждой незавершённой задачи назначен обоснованный следующий шаг.

**Основа:** ТЗ §§5.3–5.4, 7; карта B01–B10, D05–D07, K17–K20, K28, K57.

## [ ] Этап 4. Доказать, что директор выполняет полезные исследования на реальных данных

**Зачем:** не просто вызвать поиск, а получить данные, пригодные для ответа на конкретный исследовательский вопрос.

**Проверить:**
- Исследовательская задача соответствует плану и отвечает на конкретный вопрос.
- Директор выбирает подходящие инструменты YouTube MCP и действительно использует полученные данные в анализе.
- Запросы, ответы, источники, временные отметки и контекст можно связать с результатом.
- Покрываются разные направления, темы, форматы, рынки и языки, а не только несколько очевидных популярных результатов.
- Учитываются уже собранные данные: актуальные и достаточные повторно используются; устаревшие или недостаточные обновляются целевым запросом.
- Есть контролируемая стратегия расходования квоты: полезная очередь исследований, единый учёт, корректная обработка остатка и причины остановки. Не отправляются бессмысленные запросы ради формального нулевого остатка и не превышаются лимиты.
- Пустой, повторяющийся или нерелевантный ответ не считается выполненным исследованием.

**Виртуальные тесты:** валидный ответ; пустой ответ; повторяющиеся результаты; некорректные данные; тайм-аут; ограничение квоты; временная ошибка; сохранённые данные уже достаточны; сохранённые данные устарели. Затем — контролируемая интеграционная проверка с настоящим MCP/API и ограниченным числом запросов.

**Приёмка:** можно показать, какой вопрос исследовался, какие реальные данные получены, что из них использовано, какие ограничения остались и какой следующий вопрос возник. Учёт квоты соответствует фактическим вызовам в пределах доступных доказательств.

**Основа:** ТЗ §§8, 11; карта B01, C01–C09, K21–K30, K61.

## [ ] Этап 5. Проверить качество анализа, а не наличие текста

**Зачем:** директор должен делать обоснованные выводы, а не просто пересказывать найденные данные.

**Проверить для каждой существенной гипотезы/вывода:**
- Отделены ли наблюдаемые факты от выводов и предположений.
- Указаны ли источник, доказательства, ограничения и степень уверенности.
- Анализируются ли признаки роста, конкуренция, воспроизводимость и возможные причины успеха.
- Проверяются ли доступные факторы успеха формата: тема/угол подачи, формат, заголовок/обложка, начало, длительность/структура, потребность аудитории, визуальная подача, язык/страна/культура, актуальность публикации и повторяемость у разных авторов.
- Не объявляется ли единичный успех доказательством воспроизводимой возможности.
- Сопоставляются ли новые измерения с историей, прогнозами и предыдущими выводами; объясняется ли изменение оценки.
- Оцениваются ли реализуемость при нулевом бюджете, доступность бесплатных инструментов, сложность производства, путь к монетизации, сроки/зависимости/риски и неопределённость без обещания дохода.
- Если данных недостаточно, указывается конкретно, каких данных не хватает, почему они важны и каким исследованием их получить.

**Тестовые сценарии:** противоречивые данные; единичный вирусный пример; мало наблюдений; гипотеза не подтверждается; новый замер меняет прежний вывод; фактор недоступен; денежные показатели нельзя обосновать.

**Приёмка:** вывод можно проследить от исходных данных и методики; ограничения названы; неподтверждённые утверждения не представлены как факты; недостаток данных порождает конкретный план следующей проверки, а не беспричинное завершение работы.

**Основа:** ТЗ §§8–10; карта B02–B10, K21–K26, K31–K34, K54, K61–K62.

## [ ] Этап 6. Проверить память и устойчивость результатов

**Зачем:** директор должен накапливать знания между пробуждениями, а не каждый раз начинать как новый.

**Проверить:**
- Сохраняются ли исходные результаты, источники, контекст, время и методика.
- Сохраняются ли гипотезы, замеры, прогнозы, изменения выводов, причины изменений, планы и прогресс задач.
- Переживают ли записи перезапуск сервиса; читаются ли повторно тем же и зависимыми компонентами.
- Не объявляется ли запись успешной, если база фактически отклонила её.
- Не стираются ли предыдущие результаты без предусмотренной политики; нет ли дублей при повторном запуске.
- Согласованы ли статусы между директором, промежуточным API, базой и сайтом.

**Тестовые сценарии:** перезапуск после сохранения; недоступность базы; ошибка при записи; повтор операции; частично сохранённый цикл; восстановление после сбоя.

**Приёмка:** можно восстановить состояние проекта и ход рассуждения по сохранённым данным; успешность сохранения подтверждается чтением записи; сбои не маскируются и не приводят к ложному статусу.

**Основа:** ТЗ §§6.3, 8.5, 10, 14; карта E01–E07, G03–G05, K39–K40, K50.

## [ ] Этап 7. Проверить переход от исследования к полезной рекомендации

**Зачем:** результат работы директора — не просто найденные видео, а обоснованная возможность, понятная пользователю.

**Проверить:**
- Рекомендация создаётся из фактически сохранённого исследования, а не из шаблона или выдуманных данных.
- Она содержит обязательные поля ТЗ §12: суть идеи, доказательства, перспективность, конкуренцию/рост/воспроизводимость, риски и неизвестные, уверенность, реализуемость при нулевом бюджете, возможную монетизацию с оговорками и следующий проверяемый шаг.
- Рекомендация доступна через API и отображается на сайте после сохранения и перезапуска.
- Пользователь видит реальный статус рекомендации; он соответствует сохранённым данным.
- Исследовательские ограничения и запрещённые тематики проверяются на всех нужных путях до публикации рекомендации пользователю.
- При недостатке доказательств директор не создаёт уверенную рекомендацию только ради заполнения сайта.

**Приёмка:** можно взять конкретную рекомендацию на сайте и проследить её до исследования, исходных данных и аргументации. Нет неподтверждённых ключевых утверждений и ложного статуса.

**Основа:** ТЗ §§3, 9–12, 16; карта A07, B02–B08, E03–E05, F03, K31–K34, K55.

## [ ] Этап 8. Проверить диалог, решения пользователя и создание задачи

**Зачем:** директор должен продолжать работу с учётом обсуждения, а не терять контекст или принимать молчание за согласие.

**Проверить:**
- Обсуждение и уточнения связаны с правильной рекомендацией и её доказательствами.
- Ответы на вопросы используют известные данные и прямо обозначают неизвестное.
- Действия «Согласиться», «Отклонить», «Обсудить» имеют разные корректные результаты.
- Задача для дальнейшей подготовки видео создаётся только после явного положительного согласия.
- Отказ, отсутствие ответа, повторное нажатие и сетевой повтор не создают лишние задачи.
- Созданная задача связана с исходной рекомендацией и содержит необходимые сведения, статус и дальнейший этап.
- Создание задачи не запускает производство или публикацию видео, которые не входят в текущий этап ТЗ.

**Приёмка:** сквозные сценарии подтверждены сохранёнными данными и пользовательским интерфейсом; нет потери контекста, ложного согласия и дублирующих задач.

**Основа:** ТЗ §§12–14; карта A03–A04, E05–E07, F04–F08, K35–K38, K52–K60.

## [ ] Этап 9. Добиться устойчивой автономной работы

**Зачем:** один успешный запуск не доказывает, что директор сможет работать самостоятельно регулярно.

**Проверить:**
- Настроены ли 24 плановых запуска в сутки с явным часовым поясом.
- Существует ли согласованный механизм планирования; нет ли дублирующих или неконтролируемых запусков.
- Сохраняются ли пропущенные, неудачные и успешные запуски, причины и результаты.
- Не выполняются ли одновременно конфликтующие циклы; повторный запуск не дублирует завершённые операции и расход квоты.
- Восстанавливаются ли незавершённые задачи после временных ошибок и перезапуска.
- Watchdog проверяет доступность всех предусмотренных сервисов и честно сообщает о сбоях, но не подменяет полноценный исследовательский цикл.
- Каждый новый цикл использует обновлённое состояние проекта, прогресс и историю предыдущих циклов.

**Виртуальные тесты:** конкурентные запуски, пропущенный запуск, временная недоступность сервиса, перезапуск, повторная доставка сигнала, зависшая задача, ошибка watchdog.

**Реальная проверка:** сначала один контролируемый запуск, затем наблюдение за реальным расписанием в течение полного суточного периода. Проверяется не только число срабатываний, но и число фактически завершённых циклов, их результаты, сохранённые исследования, ошибки и пропуски.

**Приёмка:** доказано расписание и фактическое выполнение; каждый цикл имеет результат или честную причину неуспеха; нет незамеченных дублей, зависаний и ложных успехов.

**Основа:** ТЗ §§5–7, 15, 17; карта D01–D08, H01–H09, K15–K20, K39–K41, K50.

## [ ] Этап 10. Проверить сквозную работу директора целиком

Этот этап проводится только после прохождения предыдущих этапов. Используется известный тестовый проект с заранее подготовленным набором фактов и ожидаемых действий, а затем — безопасный сценарий на реальных данных.

**Сквозной сценарий:**
1. Наступает плановое пробуждение.
2. Директор проверяет доступность и полноту состояния проекта.
3. Сверяет общий план, обязательства, гипотезы, повторные измерения и приоритеты.
4. Выбирает конкретную исследовательскую задачу и записывает ожидаемый результат.
5. Получает реальные данные через разрешённые источники.
6. Сохраняет данные и контекст.
7. Анализирует факты, ограничения, причины успеха и гипотезы.
8. Решает, достаточно ли доказательств.
9. Если недостаточно — фиксирует точный пробел и ставит следующую полезную задачу; если достаточно — формирует обоснованную рекомендацию.
10. Сохраняет результат и показывает его на сайте с правильным статусом.
11. Следующий цикл читает предыдущий результат и продолжает работу, не теряя контекст и не повторяя без причины уже завершённые шаги.
12. Действия пользователя, если они нужны, требуют явного согласия и корректно сохраняются.
13. Журнал, база, API и сайт согласованно показывают, что произошло.

**Негативные варианты обязательны:** источник недоступен; данных мало; данные противоречат друг другу; база недоступна; ИИ возвращает пустой/ошибочный ответ; исследование частично завершено; цикл прерывается и возобновляется; появляется новая информация, меняющая старый вывод.

**Приёмка:** не просто завершён процесс, а доказан правильный результат каждого смыслового шага. Пропуск обязательного параметра состояния, бесполезное исследование, потеря данных, необоснованное решение «данных недостаточно» без следующего шага или ложный статус должны проваливать соответствующую проверку.

**Основа:** ТЗ §§18–20; карта J01–J07 и все применимые требования A–K.

## [ ] Этап 11. Отчётность и окончательное решение

Для каждого этапа сохранить:
- требование ТЗ и связанные ID эталонной карты;
- исходное поведение и обнаруженные дефекты;
- что изменено и в каких репозиториях;
- названия и результаты автоматических тестов;
- сценарии виртуальной и реальной проверки;
- безопасно сохранённые логи, ответы, записи и скриншоты, подтверждающие результат;
- что осталось неизвестным или заблокированным;
- результат регрессионной проверки.

Итоговые статусы:
- **Пройдено** — смысловое и техническое поведение подтверждено достаточными доказательствами в требуемых средах.
- **Частично пройдено** — часть результата доказана, часть нет.
- **Не пройдено** — обнаружен подтверждённый дефект.
- **Заблокировано** — не хватает доступа, конфигурации или среды.
- **Ожидает реальной проверки** — виртуальные тесты пройдены, но работа целевой системы ещё не подтверждена.

Нельзя объявлять директора готовым по результату только одного удачного цикла. Готовность текущего этапа определяется совокупностью требований ТЗ, сквозным сценарием и подтверждённой автономной работой.

## Связанные исходные документы

- [ТЗ «Директор 3.0»](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D1%82%D0%B7%20%D0%B4%D0%B8%D1%80%D0%B5%D0%BA%D1%82%D0%BE%D1%80%203,0)
- [Эталонная карта требований](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D1%8D%D1%82%D0%B0%D0%BB%D0%BE%D0%BD%D0%BD%D0%B0%D1%8F%20%D0%BA%D0%B0%D1%80%D1%82%D0%B0%20%D1%82%D1%80%D0%B5%D0%B1%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B9)
- [Правила аудита ТЗ 3.0](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%D0%BB%D0%B0%20%D0%B0%D1%83%D0%B4%D0%B8%D1%82%D0%B0%20%D1%82%D0%B7%203%2C0)
- [Существующий подробный план аудита — сохранён без изменений](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D0%BF%D0%BB%D0%B0%D0%BD%20%D0%BF%D1%80%D0%BE%D0%B2%D0%B5%D1%80%D0%BA%D0%B8%20%D1%82%D0%B7%20%D0%B4%D0%B8%D1%80%D0%B5%D0%BA%D1%82%D0%B5%D1%80%203%2C0)


</details>

## G.1. Детализация функционального восстановления: подпункты

**Перенесено из:** https://github.com/peonyrhodo-bit/youtube-mcp/blob/docs/decompose-new-verification-plan/%D0%9D%D0%9E%D0%92%D0%AB%D0%99%20%D0%A4%D0%90%D0%99%D0%9B%20%D0%9F%D0%A0%D0%9E%D0%92%D0%95%D0%A0%D0%9A%D0%98. Подпункты включены как самостоятельные задачи; ранний полный цикл — только итоговый gate.

<details>
<summary>Полный текст исходных задач, критериев и технических результатов (раскрыть)</summary>

# План восстановления работоспособности директора 3.0

Перед работой необходимо ознакомиться с файлами: «Техническое задание директора 3.0», «Эталонная карта требований», «Правила аудита ТЗ 3.0», «План проверки ТЗ директора 3.0».

**Назначение:** довести директора от текущего состояния до фактического выполнения основной задачи по ТЗ 3.0. Этот документ дополняет, но не заменяет существующий подробный план аудита. Подробный план аудита сохраняется без изменений и используется позже для полной формальной приёмки.

**Главный принцип:** технически запущенный цикл не считается работающим директором. Успех подтверждается только тогда, когда директор правильно оценивает состояние проекта, выбирает обоснованные исследования, получает реальные данные, делает проверяемые выводы, сохраняет их и предпринимает следующий необходимый шаг.

## Как выполнять этот план

Работать строго по этапам. Подзадачи внутри этапа выполнять последовательно с учётом указанных зависимостей. Не переходить к следующему этапу, пока текущий не прошёл критерии приёмки либо не зафиксирована конкретная блокировка.

Для каждой подзадачи обязательно фиксировать: ID; применимое требование ТЗ и ID эталонной карты; исходное поведение; действия и затронутые компоненты; ожидаемый результат; фактический результат; ссылки на логи/ответы/записи/скриншоты; найденные дефекты; результат автоматической и реальной проверки; статус.

Для каждого этапа обязателен рабочий цикл:
1. Изучить применимые пункты ТЗ и эталонной карты требований.
2. Проследить цепочку реализации во всех затронутых репозиториях.
3. Зафиксировать исходное поведение до изменений.
4. Составить список подтверждённых дефектов и показать его пользователю до исправления.
5. После согласования исправить дефекты минимальными изменениями.
6. Запустить автоматические проверки в изолированной виртуальной среде, включая негативные сценарии и регрессии.
7. Проверить сквозной сценарий на работающем тестовом окружении с реальными интеграциями, где это безопасно.
8. Проверить работу в целевой реальной среде. Не выполнять опасные действия, не публиковать контент и не создавать расходы без отдельного разрешения.
9. Сопоставить логи, ответы API, сохранённые данные и фактическое поведение сайта.
10. Сохранить доказательства и указать честный статус.

Если реальную проверку выполнить нельзя, это не успех. Нужно указать недостающий доступ, настройку или среду и создать конкретную блокирующую задачу. Health endpoint, HTTP 200, запуск отдельной функции или наличие записи о старте сами по себе не доказывают работу директора.

---

## Этап 0. Подготовить возможность доказательной проверки

**Цель:** подготовить безопасный и воспроизводимый способ запускать цикл и наблюдать фактические результаты.

### Подзадачи

- [ ] **0.1. Прочитать обязательные документы.** Изучить ТЗ 3.0, эталонную карту требований, правила аудита и существующий подробный план. Выписать применимые требования к циклу и приёмке. Результат: перечень требований со ссылками на разделы и ID карты.

- [ ] **0.2. Зафиксировать версии четырёх репозиториев.** Изучить site-insight-engine, ai-youtube-system, youtube-mcp и youtube-office-watchdog; определить ветви/коммиты и какие версии реально развернуты. Результат: таблица репозиторий — версия кода — среда развёртывания.

- [ ] **0.3. Восстановить схему архитектуры.** Установить роли компонентов, точки входа и маршруты данных от запуска до сохранённого результата. Результат: схема с реальными названиями компонентов и связей, подтверждённая кодом/конфигурацией.

- [ ] **0.4. Найти штатные точки запуска.** Определить, как запускается цикл вручную и автоматически, какие предварительные условия обязательны и какой механизм считается штатным. Результат: воспроизводимая инструкция запуска и список альтернативных входов, которые нельзя ошибочно принять за полный цикл.

- [ ] **0.5. Инвентаризировать настройки и зависимости.** Проверить переменные окружения, адреса сервисов, токены, внешние API, модели, тайм-ауты и разрешения. Секреты не копировать в отчёт. Результат: безопасный чек-лист необходимых настроек с отметками о подтверждённом наличии и пробелах.

- [ ] **0.6. Найти журналы и средства наблюдения.** Установить, где смотреть логи приложения, API, MCP, планировщика, watchdog и хранилища; как сопоставлять события одного запуска. Результат: инструкция сбора журналов и перечень недостающих средств наблюдения.

- [ ] **0.7. Подготовить безопасную тестовую среду.** Убедиться, что тест не вызовет реальную публикацию, необратимые изменения, лишние задачи или неконтролируемый расход квоты. Результат: подтверждённые границы безопасного тестирования и правила очистки тестовых данных.

- [ ] **0.8. Проверить доступ к хранилищу и сайту.** Установить, как читать сохранённые результаты и проверять их отображение пользователю. Результат: воспроизводимый способ проверить запись чтением и сопоставить её с отображением сайта.

- [ ] **0.9. Зафиксировать исходное состояние.** Сохранить известные ошибки, статусы сервисов, очередь задач, последние циклы, рекомендации и соответствующие записи до изменений. Результат: базовый снимок, с которым можно сравнить изменения.

- [ ] **0.10. Создать журнал проверки и правила статусов.** Подготовить единый формат записи подзадач и доказательств. Результат: ни один шаг не может быть отмечен как успешный без конкретного свидетельства.

**Критерии приёмки этапа 0:** существует воспроизводимый и безопасный способ запуска; известен путь данных; доступно наблюдение за выполнением и сохранением; исходное состояние зафиксировано. Если чего-то не хватает, этап получает статус «Заблокировано» с конкретными причинами.

Основа: ТЗ §§6, 17–19; карта C03, D07, E01–E07, G01–G07, J01–J07, I07.

## Этап 1. Добиться фактического выполнения одного полного цикла

**Цель:** доказать, что один запуск проходит весь обязательный путь, выполняет реальную работу и заканчивается проверяемым результатом, а не только успешным HTTP-ответом.

### Подзадачи

- [ ] **1.1. Составить карту полного цикла по ТЗ.** Перечислить обязательные шаги от пробуждения до сохранения результата и итогового статуса. Для каждого указать ожидаемый вход и выход. Результат: последовательность шагов со ссылками на ТЗ.

- [ ] **1.2. Найти фактическую точку входа.** Проследить штатный путь от расписания/сигнала/ручного запуска до кода директора. Результат: путь подтверждён кодом и журналами, а не предположением.

- [ ] **1.3. Проверить регистрацию запуска.** Установить, создаётся ли запись о цикле, присваивается ли ему идентификатор и связываются ли с ним последующие действия. Результат: запись запуска соответствует реальному событию.

- [ ] **1.4. Проверить начальные условия и блокировки.** Проверить флаги включения, доступность зависимостей, ограничения параллельных запусков и обработку отсутствующих настроек. Результат: цикл либо безопасно начинается, либо честно сообщает конкретную причину отказа.

- [ ] **1.5. Проследить выполнение кода директора.** Доказать, что запрос не заканчивается на промежуточном API и действительно вызывает необходимую логику директора. Результат: связанная цепочка событий с одним ID цикла.

- [ ] **1.6. Проверить получение состояния и входных данных.** Зафиксировать обращения к источникам состояния, полученные ответы и ошибки. Результат: видно, какие данные действительно поступили в цикл.

- [ ] **1.7. Проверить выбор следующего действия.** Установить, что директор выбирает конкретное действие/задачу, а не завершает цикл после формального сообщения. Результат: сохранённое решение с причиной и ожидаемым результатом; качество решения оценивается на этапе 2–3.

- [ ] **1.8. Проверить реальный исследовательский вызов.** Подтвердить отправку запроса к требуемому источнику, получение ответа и передачу данных дальше. Результат: запрос и ответ связаны с циклом. Полнота и полезность исследования дополнительно проверяются на этапе 4.

- [ ] **1.9. Проверить обработку ответа.** Проследить, что полученные данные распознаны, обработаны и переданы следующему компоненту; пустой ответ не считается полезным результатом. Результат: видны входные данные и фактический выход обработки.

- [ ] **1.10. Проверить сохранение результата.** Найти запись в хранилище, прочитать её обратно и сопоставить с ответом/результатом обработки. Результат: подтверждённая запись, а не только сообщение об успешном сохранении.

- [ ] **1.11. Проверить конечный статус.** Сопоставить статус цикла с реально выполненными шагами. Успех допустим только при выполнении всех обязательных операций. Результат: корректный статус успеха, частичного выполнения, ошибки или блокировки.

- [ ] **1.12. Проверить частичное завершение.** Смоделировать сбой после одного из промежуточных шагов. Результат: система фиксирует завершённые шаги, потерянные/незавершённые операции и причину остановки, не выдавая частичный результат за полный успех.

- [ ] **1.13. Проверить пустые и недоступные источники.** Отдельно проверить пустой ответ, недоступный MCP/API и отсутствие необходимых данных. Результат: причины различаются, ложного успешного исследования нет.

- [ ] **1.14. Проверить отказ ИИ и тайм-аут.** Смоделировать недоступность модели, ошибочный ответ и превышение времени ожидания. Результат: ошибка видна, цикл не зависает бесконечно и не объявляет несуществующий результат.

- [ ] **1.15. Проверить отказ хранилища.** Смоделировать недоступность или отказ записи. Результат: цикл не объявляет сохранение успешным без подтверждения; повторная попытка и восстановление ведут себя предсказуемо.

- [ ] **1.16. Проверить повторный запуск.** Повторить тот же тестовый запуск/сигнал и выяснить, создаются ли дубли результатов, задач или расходов. Результат: документировано и протестировано поведение повторов.

- [ ] **1.17. Проверить согласованность журналов.** Сверить события директора, промежуточного API, MCP и хранилища по времени и идентификатору. Результат: можно восстановить весь маршрут без необъяснимых пропусков.

- [ ] **1.18. Проверить регрессию.** После исправлений повторить исходный успешный и все выявленные негативные сценарии. Результат: подтверждено, что исправление не сломало соседние пути.

**Критерии приёмки этапа 1:** минимум один полный запуск доказан от штатной точки входа до сохранённого результата; все обязательные шаги имеют свидетельства; конечный статус соответствует фактам; негативные сценарии не создают ложного успеха. Этот этап доказывает техническую проходимость цикла, но сам по себе не доказывает смысловую правильность работы директора.

Основа: ТЗ §§5–7, 17–19; карта C01–C03, D05–D07, E01, G01–G05, J03–J04.

## Этап 2. Проверить, что директор действительно понял состояние проекта

**Цель:** доказать, что директор собирает полный, актуальный и достоверный снимок состояния и использует его в решениях. Наличие короткой записи «состояние проверено» не считается доказательством.

### Подзадачи

- [ ] **2.1. Извлечь полный перечень обязательных параметров из ТЗ §6.2.** Сопоставить каждый параметр с эталонной картой. Не заменять полный перечень выборочными примерами. Результат: исчерпывающий проверочный список.

- [ ] **2.2. Для каждого параметра определить источник истины.** Указать таблицу/запись/эндпоинт/журнал, откуда берётся значение, и как проверить его актуальность. Результат: матрица «параметр — источник — проверка».

- [ ] **2.3. Проверить полноту снимка состояния.** Сопоставить обязательные параметры с фактическим снимком директора. Результат: для каждого параметра есть значение, обоснованное отсутствие или зафиксированный пробел.

- [ ] **2.4. Проверить достоверность значений.** Сверить значения с первичными источниками, а не только проверить наличие полей. Результат: расхождения и ложные значения выявлены и описаны.

- [ ] **2.5. Проверить актуальность и время данных.** Найти устаревшие сведения и убедиться, что директор отличает свежие данные от старых. Результат: время получения/обновления и влияние устаревания видимы.

- [ ] **2.6. Проверить ошибки и неизвестное состояние.** Смоделировать недоступный источник или противоречивые записи. Результат: директор явно отмечает неизвестное/конфликт, не подменяет его утверждением «всё в порядке».

- [ ] **2.7. Проверить здоровье системы.** Сверить состояние ИИ, YouTube API/MCP, хранилища, сайта, сохранения рекомендаций, планировщика, последнего цикла, ошибок и незавершённых операций. Результат: известные проблемы попадают в снимок.

- [ ] **2.8. Проверить исследовательское состояние.** Сверить завершённые и незавершённые исследования, пригодные результаты, недостаточно изученные направления, гипотезы и наступившие повторные замеры. Результат: директор не забывает о незавершённой или просроченной работе.

- [ ] **2.9. Проверить рекомендации, задачи и решения пользователя.** Сверить ожидающие решения рекомендации, принятые/отклонённые решения, текущие задачи и новые сведения, способные изменить выводы. Результат: статусы соответствуют хранилищу и влияют на план.

- [ ] **2.10. Проверить ресурсы, квоты и ограничения.** Сверить доступную квоту, режим бюджета, доступные инструменты, ошибки источников, очередь задач и ограничения. Результат: директор не планирует заведомо невыполнимую работу.

- [ ] **2.11. Подготовить проект с заранее известными фактами.** Внести контролируемый набор известных состояний: незавершённую задачу, просроченный замер, ошибку сервиса, ограниченную квоту и противоречивые данные. Результат: есть эталон, с которым сравнивается понимание директора.

- [ ] **2.12. Сопоставить снимок и эталон по каждому параметру.** Зафиксировать, что директор нашёл, пропустил или неверно истолковал. Результат: таблица ошибок по отдельным требованиям.

- [ ] **2.13. Проверить влияние состояния на решение.** Изменить один значимый факт и проверить, изменился ли план там, где это необходимо. Результат: доказана причинная связь между состоянием проекта и выбранным действием.

- [ ] **2.14. Проверить, что пропуск обязательного параметра проваливает тест.** Удалить или сделать недоступным обязательное значение. Результат: проверка обнаруживает неполноту, даже если цикл формально завершён.

**Критерии приёмки этапа 2:** каждый применимый параметр из ТЗ §6.2 проверен отдельно; значения подтверждены источниками либо честно помечены неизвестными; ошибки и пробелы влияют на дальнейший план; тест обнаруживает пропуск обязательного параметра.

Основа: ТЗ §§5.2, 6.2, 7.1–7.2; карта D05–D07, E01–E07, K15–K20, K39–K40, K50.

## Этап 3. Проверить общий план проекта и план конкретного цикла

**Цель:** подтвердить, что директор выбирает нужную работу на основании состояния проекта, а не составляет формальный список действий.

### Подзадачи

- [ ] **3.1. Проверить наличие общего плана проекта.** Установить, где он хранится, как обновляется и как читается следующим циклом. Результат: сохранённый план доступен после перезапуска.

- [ ] **3.2. Сверить содержание общего плана с ТЗ.** Проверить цели, направления исследований, ограничения, пользовательские задачи, гипотезы, повторные измерения, приоритеты, бюджетный режим и критерии завершения. Результат: матрица полноты общего плана.

- [ ] **3.3. Проверить создание плана текущего цикла до выполнения действий.** Убедиться, что задачи и ожидаемые результаты записаны заранее, а не придуманы задним числом. Результат: временная последовательность плана и фактических действий.

- [ ] **3.4. Проверить конкретность задач.** Для каждой задачи должны быть вопрос/цель, обоснование, источник/инструмент, ожидаемый результат, ограничения и критерий завершения. Результат: задачи можно объективно принять или отклонить.

- [ ] **3.5. Проверить порядок приоритетов ТЗ §7.3.** Проверить последовательность: (1) целостность и восстановление; (2) полезные квотные исследования; (3) повторные измерения и проверка выводов; (4) новые исследования; (5) монетизация и реализуемость; (6) рекомендации и задачи; (7) эффективность; (8) отчётность. Результат: порядок соответствует ТЗ или каждое отклонение объяснено допустимой причиной.

- [ ] **3.6. Проверить конкурирующие задачи.** Создать ситуацию с просроченным замером, новой темой и пользовательской задачей. Результат: директор выбирает приоритет обоснованно и объясняет отложенные задачи.

- [ ] **3.7. Проверить ограничения квоты и бюджета.** Убедиться, что план выполним в пределах доступных ресурсов и не требует неразрешённых расходов. Результат: обоснованный план с лимитами.

- [ ] **3.8. Проверить адаптацию к препятствию.** Сделать источник недоступным или вернуть недостаточные данные. Результат: директор пересматривает план, фиксирует причину и следующий шаг, не стирая незавершённую задачу.

- [ ] **3.9. Проверить перенос задач между циклами.** Прервать выполнение и запустить следующий цикл. Результат: задачи не теряются и не создаются заново без причины.

**Критерии приёмки этапа 3:** общий и цикловой планы сохранены и конкретны; порядок соответствует ТЗ; каждое отклонение и незавершённая задача объяснены; последующие циклы учитывают предыдущий прогресс.

Основа: ТЗ §§5.3–5.4, 7; карта B01–B10, D05–D07, K17–K20, K28, K57.

## Этап 4. Доказать, что директор выполняет полезные исследования на реальных данных

**Цель:** подтвердить, что исследование отвечает на конкретный вопрос и даёт пригодные данные, а не просто вызывает поиск.

### Подзадачи

- [ ] **4.1. Проверить связь исследования с планом.** Сопоставить исследовательский запрос с задачей текущего цикла. Результат: объяснено, какой вопрос решает запрос.

- [ ] **4.2. Проверить выбор инструментов.** Сверить инструменты YouTube MCP/API с типом вопроса и ограничениями. Результат: инструмент выбран обоснованно.

- [ ] **4.3. Подтвердить реальные запросы и ответы.** Проверить журнал вызовов, параметры, время, ответы и ошибки. Результат: доказательство реального обращения, а не имитации результата.

- [ ] **4.4. Проверить релевантность данных.** Вручную оценить выборку: отвечает ли она на вопрос, относится ли к нужной теме и не состоит ли из случайных/повторяющихся результатов. Результат: протокол качества выборки.

- [ ] **4.5. Проверить широту исследовательского покрытия.** Сопоставить выборку с предусмотренными направлениями, темами, форматами, рынками и языками. Результат: обнаруженные пробелы покрытия и план их закрытия.

- [ ] **4.6. Проверить повторное использование сохранённых данных.** Дать директору доступ к достаточным актуальным результатам. Результат: он использует их вместо ненужного дублирования запросов.

- [ ] **4.7. Проверить обновление устаревших/недостаточных данных.** Подготовить данные, которые не отвечают на вопрос или устарели. Результат: директор выбирает целевой дополнительный запрос и объясняет зачем.

- [ ] **4.8. Проверить учёт квоты.** Сопоставить фактические вызовы и списание с единым учётом квоты, ограничениями и планом. Результат: объяснимый расход без превышений и двойного учёта.

- [ ] **4.9. Проверить пустые, повторные и ошибочные ответы.** Отдельно протестировать пустой ответ, дубли, нерелевантную выборку, тайм-аут и ошибку источника. Результат: такие ответы не засчитываются как успешное исследование.

- [ ] **4.10. Провести контролируемую интеграционную проверку.** Выполнить ограниченное реальное исследование на разрешённых источниках и проверить сохранённый результат. Результат: реальная выборка и доказательства обработки.

- [ ] **4.11. Проверить соблюдение тематических ограничений.** Проверить предусмотренные ТЗ фильтры на всех соответствующих путях поиска и обработки, включая обходные пути. Результат: негативные примеры блокируются там, где это требует ТЗ.

**Критерии приёмки этапа 4:** можно показать вопрос, запрос, реальный ответ, источники, качество выборки, учёт квоты, ограничения и вывод о достаточности. Формальный вызов поиска без полезного результата не проходит этап.

Основа: ТЗ §§8, 11; карта B01, C01–C09, K21–K30, K61.

## Этап 5. Проверить качество анализа, а не наличие текста

**Цель:** убедиться, что выводы обоснованы данными, неопределённость названа, а следующий шаг полезен.

### Подзадачи

- [ ] **5.1. Проверить разделение фактов и гипотез.** Выбрать утверждения в анализе и для каждого найти исходное подтверждение либо пометку о предположении. Результат: неподтверждённые факты выявлены.

- [ ] **5.2. Проверить источники и трассируемость выводов.** Для существенного вывода найти исходные данные, дату, метод и ограничения. Результат: можно воспроизвести основание вывода.

- [ ] **5.3. Проверить оценку роста и конкуренции.** Проверить, анализирует ли директор признаки роста, конкурентную среду, несколько примеров и воспроизводимость, а не только единичный популярный результат. Результат: вывод соответствует объёму доказательств.

- [ ] **5.4. Проверить факторы успеха формата.** Проверить применимые признаки: тема, формат, заголовок/обложка, начало, длительность/структура, потребность аудитории, визуальная подача, язык/страна/культура, актуальность и повторяемость. Результат: факторы либо обоснованно оценены, либо отмечены как неизвестные.

- [ ] **5.5. Проверить сопоставление с историей и повторными замерами.** Сравнить новый результат с предыдущими данными, прогнозом и выводом. Результат: изменения объяснены, а не скрыты.

- [ ] **5.6. Проверить экономическую реализуемость.** Проверить сценарий нулевого бюджета, бесплатные инструменты, сложность производства, зависимости, риски, путь монетизации и неопределённость. Результат: нет необоснованных обещаний дохода.

- [ ] **5.7. Проверить противоречивые и недостаточные данные.** Подать директору конфликтующие сведения и малую выборку. Результат: он не делает категоричный вывод и указывает, каких данных не хватает.

- [ ] **5.8. Проверить следующий шаг.** При недостатке данных директор должен указать конкретный пробел, полезное исследование, ожидаемый результат и критерий завершения. Результат: вместо беспричинного «данных недостаточно» появляется проверяемый план.

- [ ] **5.9. Провести независимую человеческую оценку.** Проверяющий, не участвовавший в подготовке конкретного вывода, оценивает его обоснованность по исходным данным и критериям ТЗ. Результат: зафиксированная оценка с примерами и объяснением разногласий.

**Критерии приёмки этапа 5:** существенные выводы прослеживаются до данных; гипотезы отделены от фактов; ограничения не скрыты; недостаточность данных ведёт к обоснованному следующему шагу.

Основа: ТЗ §§8–10; карта B02–B10, K21–K26, K31–K34, K54, K61–K62.

## Этап 6. Проверить память и устойчивость результатов

**Цель:** убедиться, что директор накапливает знания и восстанавливает работу между циклами и после сбоев.

### Подзадачи

- [ ] **6.1. Составить перечень обязательных сохраняемых данных.** Сверить ТЗ с фактическими таблицами/структурами: исходные результаты, источники, время, методика, гипотезы, замеры, прогнозы, выводы, планы и задачи. Результат: карта «требование — структура хранения».

- [ ] **6.2. Проверить полноту записей.** Сравнить результат цикла с тем, что фактически сохранено. Результат: нет тихо потерянных обязательных полей.

- [ ] **6.3. Проверить чтение после записи.** Прочитать сохранённые данные независимым запросом/компонентом и сопоставить с отправленными. Результат: подтверждение фактического сохранения.

- [ ] **6.4. Проверить чтение следующим циклом.** Перезапустить сервис и выполнить новый цикл. Результат: новый цикл получает предшествующие результаты и контекст.

- [ ] **6.5. Проверить ошибки записи и недоступность базы.** Смоделировать отказ и частичную запись. Результат: нет ложного подтверждения сохранения; ошибка и незавершённое состояние видимы.

- [ ] **6.6. Проверить повторные операции и дубли.** Повторить запись/событие в контролируемом тесте. Результат: предусмотренные повторы идемпотентны либо корректно обозначены.

- [ ] **6.7. Проверить восстановление незавершённого цикла.** Прервать цикл после сохранения части данных и запустить восстановление. Результат: директор понимает, что завершено, что нет и с какого места безопасно продолжить.

- [ ] **6.8. Проверить согласованность между компонентами.** Сравнить статусы и результаты в директоре, API, хранилище и сайте. Результат: расхождения обнаруживаются и не маскируются.

**Критерии приёмки этапа 6:** необходимые результаты переживают перезапуск, подтверждаются чтением и используются дальше; ошибки и частичное сохранение явно отражаются.

Основа: ТЗ §§6.3, 8.5, 10, 14; карта E01–E07, G03–G05, K39–K40, K50.

## Этап 7. Проверить переход от исследования к полезной рекомендации

**Цель:** доказать, что рекомендация следует из фактического исследования, соответствует требованиям и доступна пользователю с правильным статусом.

### Подзадачи

- [ ] **7.1. Проследить происхождение рекомендации.** Связать рекомендацию с задачей цикла, исследованием и первичными данными. Результат: происхождение подтверждено записями.

- [ ] **7.2. Проверить обязательные поля по ТЗ §12.** Проверить суть идеи, доказательства, перспективность, конкуренцию/рост/воспроизводимость, риски/неизвестные, уверенность, реализуемость без бюджета, возможную монетизацию с оговорками и следующий шаг. Результат: матрица полноты полей.

- [ ] **7.3. Проверить смысловую корректность полей.** Не только наличие, но и соответствие полей данным и выводам. Результат: нет заполнения шаблона выдуманными сведениями.

- [ ] **7.4. Проверить сохранение и API.** Убедиться, что рекомендация сохранена и возвращается через предусмотренный API. Результат: запись и ответ API совпадают.

- [ ] **7.5. Проверить отображение на сайте.** Проверить видимость, содержимое, дату и статус после сохранения и обновления страницы. Результат: пользователь видит актуальную рекомендацию.

- [ ] **7.6. Проверить статусы и фильтры.** Проверить соответствие статуса рекомендации источнику истины и выполнение тематических ограничений на всех путях до отображения. Результат: запрещённые/неподтверждённые материалы не проходят там, где требуется блокировка.

- [ ] **7.7. Проверить недостаточные доказательства.** Передать данные, на которых нельзя обоснованно создать уверенную рекомендацию. Результат: директор запрашивает данные или явно маркирует неопределённость.

- [ ] **7.8. Проверить обновление рекомендации новыми данными.** Изменить существенный исходный факт. Результат: система корректно обновляет оценку/статус или сохраняет объяснимую историю изменений.

**Критерии приёмки этапа 7:** конкретную рекомендацию на сайте можно проследить до источников и аргументации; данные и статусы согласованы; неизвестное не представлено как факт.

Основа: ТЗ §§3, 9–12, 16; карта A07, B02–B08, E03–E05, F03, K31–K34, K55.

## Этап 8. Проверить диалог, решения пользователя и создание задачи

**Цель:** подтвердить правильную обработку человеческих решений и сохранение контекста.

### Подзадачи

- [ ] **8.1. Проверить привязку диалога.** Убедиться, что обсуждение связано с правильной рекомендацией и её доказательствами. Результат: контекст не перепутан.

- [ ] **8.2. Проверить ответы на вопросы.** Задать вопрос, ответ на который известен, и вопрос с неизвестным ответом. Результат: директор использует данные и честно обозначает пробелы.

- [ ] **8.3. Проверить действие «Согласиться».** Проверить, что согласие выполняет только предусмотренное действие и сохраняется с контекстом. Результат: ожидаемый статус и дальнейший шаг.

- [ ] **8.4. Проверить действие «Отклонить».** Убедиться, что отказ сохраняется и не трактуется как согласие. Результат: корректный статус без создания согласованной задачи.

- [ ] **8.5. Проверить действие «Обсудить».** Убедиться, что оно открывает обсуждение, а не автоматически принимает рекомендацию. Результат: правильный переход состояния.

- [ ] **8.6. Проверить явное согласие перед созданием задачи.** Проверить отсутствие ответа, неоднозначный ответ и явное согласие. Результат: задача создаётся только при выполнении требования о согласии.

- [ ] **8.7. Проверить повторное действие и сетевой повтор.** Повторить запрос/нажатие. Результат: не появляются дубли задач и решений.

- [ ] **8.8. Проверить состав созданной задачи.** Сверить ссылку на рекомендацию, исходные сведения, статус и следующий этап. Результат: задача пригодна для дальнейшей работы и имеет правильный контекст.

- [ ] **8.9. Проверить границы разрешённых действий.** Убедиться, что создание задачи не запускает производство или публикацию видео без отдельного разрешения. Результат: побочные действия отсутствуют.

**Критерии приёмки этапа 8:** все три типа решения ведут к разным правильным результатам; согласие требуется явно; задачи и контекст сохранены; нет дублей и неразрешённых действий.

Основа: ТЗ §§12–14; карта A03–A04, E05–E07, F04–F08, K35–K38, K52–K60.

## Этап 9. Добиться устойчивой автономной работы

**Цель:** доказать, что система работает регулярно, восстанавливается после сбоев и сохраняет прогресс.

### Подзадачи

- [ ] **9.1. Проверить конфигурацию расписания.** Сверить требование 24 плановых запусков в сутки, часовой пояс, интервал и фактический механизм расписания. Результат: подтверждённая конфигурация.

- [ ] **9.2. Проверить реальное срабатывание расписания.** Сопоставить ожидаемое время с логом фактического запуска. Результат: расписание вызывает нужный путь запуска.

- [ ] **9.3. Проверить границы автономного запуска.** Проверить флаги включения, авторизацию, допустимые источники запуска и безопасное поведение при отключённой автономности. Результат: нет обхода установленных ограничений.

- [ ] **9.4. Проверить конкурентные и дублирующие запуски.** Инициировать несколько сигналов в контролируемой среде. Результат: нет конфликтующих циклов и двойных операций.

- [ ] **9.5. Проверить пропуск и неудачный запуск.** Создать контролируемую недоступность в запланированное время. Результат: пропуск/ошибка записаны, причина видна и дальнейшее поведение предсказуемо.

- [ ] **9.6. Проверить восстановление после перезапуска.** Перезапустить компонент во время и после цикла. Результат: незавершённые задачи обнаружены и безопасно обработаны.

- [ ] **9.7. Проверить работу watchdog.** Смоделировать недоступность каждого контролируемого сервиса. Результат: watchdog обнаруживает и сообщает о проблеме; его сигнал не считается выполнением исследовательского цикла.

- [ ] **9.8. Проверить перенос состояния между циклами.** Убедиться, что следующий цикл видит новые данные, историю, задачи и ошибки предыдущего. Результат: отсутствует беспричинный повтор или потеря прогресса.

- [ ] **9.9. Проверить квоту и ресурсы на серии циклов.** Сопоставить фактические обращения, остаток квоты, сохранённые результаты и план. Результат: серия запусков соблюдает ограничения.

- [ ] **9.10. Провести суточное наблюдение.** После виртуальных тестов и одного контролируемого запуска наблюдать целевое расписание в течение полного 24-часового периода. Результат: таблица ожидаемых и фактических запусков, результатов, пропусков, ошибок и расходов.

- [ ] **9.11. Проверить регрессию и устойчивость.** Повторно выполнить ключевые сценарии после исправлений. Результат: исправления не нарушили ручной запуск, расписание, сохранение или ограничения.

**Критерии приёмки этапа 9:** подтверждено фактическое расписание и поведение за полные сутки; каждый запуск имеет достоверный итог; пропуски и ошибки не скрываются; нет незамеченных дублей и потери прогресса.

Основа: ТЗ §§5–7, 15, 17; карта D01–D08, H01–H09, K15–K20, K39–K41, K50.

## Этап 10. Проверить сквозную работу директора целиком

**Цель:** проверить единый реальный процесс от пробуждения до сохранённого полезного результата и продолжения работы в следующем цикле.

### Подзадачи

- [ ] **10.1. Подготовить эталонный тестовый проект.** Заранее задать известные факты, состояние сервисов, очередь задач, гипотезы, просроченный замер и ограничения. Результат: эталон ожидаемых действий.

- [ ] **10.2. Зафиксировать ожидаемую последовательность.** Определить правильное состояние, приоритет, исследовательский вопрос, ограничения и критерии результата. Результат: сценарий можно оценить независимо от фактического ответа директора.

- [ ] **10.3. Запустить цикл штатным способом.** Не подменять его ручным вызовом внутренней функции, если проверяется штатная автономная работа. Результат: подтверждённая штатная точка входа.

- [ ] **10.4. Проверить полноту состояния и план.** Сверить снимок директора и выбор задачи с эталоном. Результат: оценка каждого обязательного параметра и причины выбора.

- [ ] **10.5. Проверить исследование и анализ.** Сверить реальный запрос, источники, данные, выводы и неопределённость. Результат: трассировка от вопроса до обоснованного вывода.

- [ ] **10.6. Проверить память, рекомендацию и сайт.** Прочитать сохранённые данные, открыть результат на сайте и сопоставить статусы. Результат: единая согласованная цепочка.

- [ ] **10.7. Проверить продолжение следующим циклом.** Запустить следующий цикл и убедиться, что он использует предыдущий результат и не повторяет завершённую работу без причины. Результат: доказанная преемственность.

- [ ] **10.8. Провести негативные сквозные сценарии.** Проверить недоступность источника, недостаток и противоречие данных, сбой базы, ошибку ИИ, частичное выполнение и восстановление. Результат: корректное поведение на всём маршруте.

- [ ] **10.9. Провести независимую оценку полезности.** Проверяющий, не выполнявший исправление, оценивает: правильно ли директор понял состояние, полезно ли исследование, обоснован ли вывод и понятен ли следующий шаг. Результат: письменная оценка с доказательствами и замечаниями.

**Критерии приёмки этапа 10:** все существенные шаги доказаны технически и содержательно; обязательный пропуск состояния, бесполезное исследование, потеря данных, ложный статус или необоснованное завершение проваливают соответствующую проверку.

Основа: ТЗ §§18–20; карта J01–J07 и все применимые требования A–K.

## Этап 11. Собрать доказательства и принять результат

**Цель:** обеспечить проверяемый итог, не подменяя отсутствующие тесты предположениями.

### Подзадачи

- [ ] **11.1. Сверить охват с ТЗ и эталонной картой.** Проверить, что все требования, относящиеся к этапам 0–10, связаны с проверками. Результат: матрица покрытия без необъяснимых пропусков.

- [ ] **11.2. Проверить комплект доказательств.** Для каждого статуса «Пройдено» должны быть результаты теста, логи/записи или иное проверяемое свидетельство. Результат: успешные статусы подтверждены материалами.

- [ ] **11.3. Составить перечень дефектов.** Для каждого дефекта указать влияние, шаги воспроизведения, ожидаемое и фактическое поведение, затронутые требования и ссылку на доказательства. Результат: дефекты пригодны для исправления и повторной проверки.

- [ ] **11.4. Проверить повторное выполнение после исправлений.** Повторить связанные позитивные, негативные и регрессионные сценарии. Результат: подтверждён не только факт изменения кода, но и исправление поведения.

- [ ] **11.5. Зафиксировать ограничения и неизвестное.** Отдельно перечислить то, что не проверено из-за доступа, среды, квот или невозможности безопасного запуска. Результат: ни одна блокировка не скрыта под статусом успеха.

- [ ] **11.6. Провести итоговую независимую проверку.** Проверяющий сопоставляет ТЗ, карту, план, доказательства и фактическое поведение. Результат: независимое заключение с обоснованием.

- [ ] **11.7. Присвоить итоговый статус.** Использовать только следующие значения:
- **Пройдено** — смысловое и техническое поведение подтверждено достаточными доказательствами в требуемых средах.
- **Частично пройдено** — часть результата доказана, часть нет.
- **Не пройдено** — обнаружен подтверждённый дефект.
- **Заблокировано** — не хватает доступа, конфигурации или среды.
- **Ожидает реальной проверки** — виртуальные тесты пройдены, но работа целевой системы не подтверждена.

**Критерии приёмки этапа 11:** каждое заключение обосновано; неподтверждённые проверки явно отмечены; дефекты имеют план устранения; подробный план аудита сохранён и будет применён для последующей полной формальной приёмки.

## Связанные исходные документы

- [ТЗ «Директор 3.0»](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D1%82%D0%B7%20%D0%B4%D0%B8%D1%80%D0%B5%D0%BA%D1%82%D0%B5%D1%80%203,0)
- [Эталонная карта требований](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D1%8D%D1%82%D0%B0%D0%BB%D0%BE%D0%BD%D0%BD%D0%B0%D1%8F%20%D0%BA%D0%B0%D1%80%D1%82%D0%B0%20%D1%82%D1%80%D0%B5%D0%B1%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B9)
- [Правила аудита ТЗ 3.0](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%D0%BB%D0%B0%20%D0%B0%D1%83%D0%B4%D0%B8%D1%82%D0%B0%20%D1%82%D0%B7%203%2C0)
- [Существующий подробный план аудита — сохраняется без изменений](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D0%BF%D0%BB%D0%B0%D0%BD%20%D0%BF%D1%80%D0%BE%D0%B2%D0%B5%D1%80%D0%BA%D0%B8%20%D0%82%D0%97%20%D0%B4%D0%B8%D1%80%D0%B5%D0%BA%D1%82%D0%B5%D1%80%203%2C0)


</details>

## H. Проверки ТЗ Р01–Р26, декомпозиция и матрица покрытия

**Перенесено из:** https://github.com/peonyrhodo-bit/youtube-mcp/blob/docs/plan-director-functional-recovery/%D0%BF%D0%BB%D0%B0%D0%BD%20%D0%BF%D1%80%D0%BE%D0%B2%D0%B5%D1%80%D0%BA%D0%B8%20%D1%82%D0%B7%20%D0%B4%D0%B8%D1%80%D0%B5%D0%BA%D1%82%D0%BE%D1%80%203%2C0. Историческое упоминание четвёртого watchdog — не действующая архитектура: реально три репозитория; watchdog не возвращать.

<details>
<summary>Полный текст исходных задач, критериев и технических результатов (раскрыть)</summary>

## Обязательный комплект каждого аудита

Каждое задание на аудит должно включать три документа:

1. [Правила аудита ТЗ 3.0](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%D0%BB%D0%B0%20%D0%B0%D1%83%D0%B4%D0%B8%D1%82%D0%B0%20%D1%82%D0%B7%203%2C0) — как проводить проверку.
2. [Эталонная карта требований](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D1%8D%D1%82%D0%B0%D0%BB%D0%BE%D0%BD%D0%BD%D0%B0%D1%8F%20%D0%BA%D0%B0%D1%80%D1%82%D0%B0%20%D1%82%D1%80%D0%B5%D0%B1%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B9) — что система должна делать.
3. [План проверки](https://github.com/peonyrhodo-bit/youtube-mcp/blob/main/%D0%BF%D0%BB%D0%B0%D0%BD%20%D0%BF%D1%80%D0%BE%D0%B2%D0%B5%D1%80%D0%BA%D0%B8%20%D1%82%D0%B7%20%D0%B4%D0%B8%D1%80%D0%B5%D0%BA%D1%82%D0%BE%D1%80%203%2C0) — какой именно пункт проверять, где искать реализацию и чем подтверждать результат.
## Обязательное прохождение всех уровней проверки

Для каждого пункта плана проверки исполнитель обязан:

1. **Проверить реализацию в коде:** найти соответствующую логику, сопоставить её с требованиями и выявить дефекты.
2. **Выполнить автоматические тесты:** запустить все применимые тесты, включая регрессионные. Непройденные тесты, ошибки окружения и пропущенные тесты должны быть явно зафиксированы.
3. **Провести проверку на работающей системе:** проверить фактическое поведение функциональности в живом окружении, используя реальные доступные интерфейсы, API и сервисы. Для каждого сценария зафиксировать действия, входные данные, ожидаемый и фактический результат.
4. **Предоставить воспроизводимую инструкцию:** описать пошагово, как другой человек может повторить живую проверку, где выполнять действия, что наблюдать и по каким критериям определять успех.
5. **Предоставить доказательства:** приложить результаты запусков, логи, ответы API, скриншоты или другие подходящие свидетельства. Для каждого результата должно быть понятно, какой именно критерий он подтверждает.
6. **Проверить регрессии:** убедиться, что проверяемое изменение не нарушило связанные ранее работающие функции.

### Критерий завершения

Пункт аудита получает статус **«Пройден»**, только если все применимые проверки завершены успешно и результаты подтверждены доказательствами.

Если живая проверка не проведена, среда недоступна, тест не запущен или результат не подтверждён, пункт нельзя считать пройденным. Следует указать статус «Не завершён» или «Заблокирован», причину, недостающие доказательства и конкретные шаги для завершения проверки.

Нельзя подменять фактическую проверку анализом кода, наличием тестов, успешной сборкой или предположением о поведении системы.

Если сценарий объективно невозможно безопасно выполнить в production, необходимо проверить его в подходящей работающей тестовой среде и отдельно описать ограничение production-проверки. Исключение не означает автоматического зачёта теста.


В задании можно писать, например: **«Ознакомься с файлом “План проверки ТЗ директора 3.0” и выполни пункт Р01»**. Исполнитель должен прочитать все три документа и выполнять только указанный пункт с его зависимостями; найденные соседние проблемы зафиксировать отдельно, не расширяя молча объём работы.
 
---

# План проверки соответствия директора YouTube ТЗ 3.0

## Назначение и комплект аудита

Этот файл — рабочий план проверки. Каждый запуск аудита выполняется **вместе с файлом «правила аудита тз 3,0»** и актуальными версиями:
- [ТЗ директора 3.0](тз%20директор%203,0);
- [Эталонная карта требований](эталонная%20карта%20требований);
- этим планом.

Правила аудита задают метод проведения проверки, требования к доказательствам, безопасной работе, исправлениям и статусам. План задаёт объём и порядок проверок. Эталонная карта задаёт целевое поведение и критерии приёмки. **Не копируй правила аудита в отчёт и не считай этот план подтверждением реализации.**

План охватывает четыре репозитория:
- `peonyrhodo-bit/site-insight-engine` — директор, исследования, аналитика, квота, память, рекомендации, UI;
- `peonyrhodo-bit/ai-youtube-system` — промежуточный API и оркестрация;
- `peonyrhodo-bit/youtube-mcp` — инструменты получения данных YouTube;
- `peonyrhodo-bit/youtube-office-watchdog` — периодические проверки сервисов.

## Как выполнять пункты

1. Выполняй пункты по порядку, но сначала изучи текущую архитектуру и изменения в рабочей ветке. Не начинай исправления до подтверждения дефекта.
2. Каждый пункт — самостоятельная небольшая проверка с отдельным результатом. Не объединяй несколько пунктов в один отчётный статус.
3. Внутри каждого пункта проверь код и применимые тесты; затем — реальные API, логи, состояние хранения и/или запуск в целевой среде, если есть безопасный доступ. Не делай реальные платные запросы, не публикуй контент и не меняй пользовательские данные ради теста.
4. Если для реальной проверки нет доступа или данных, укажи конкретно, что недоступно и кто/что требуется для продолжения. Не подменяй такую проверку анализом кода.
5. Требования, основанные на недоступных данных (например, закрытые метрики или причинность), проверяй на честное обозначение неизвестного, а не на наличие выдуманного значения.
6. Для каждого пункта зафиксируй ID эталонной карты, затронутый репозиторий/компонент, конкретные файлы и функции, сценарий, ожидание, фактический результат, ссылки/логи/тесты/записи как доказательства, статус и следующий шаг.
7. Если найден дефект, создай отдельную задачу или PR с минимальным исправлением. После изменения повтори этот пункт и связанные регрессионные проверки. Не закрывай пункт только потому, что исправление закоммичено.

Допустимые статусы: **Проверено успешно**, **Проверено частично**, **Обнаружен дефект**, **Не проверено**, **Заблокировано**, **Ожидает проверки в реальной среде**.

## План проверок

Р01–Р26 — верхнеуровневые группы проверок. Исполнитель назначает и закрывает отдельные подпункты из раздела «Декомпозиция проверок» (например, Р04.1), а не объединяет все подпункты в один недифференцированный результат. Верхнеуровневый пункт считается пройденным только после успешного завершения всех обязательных подпунктов и предусмотренной для него сквозной проверки. Р25–Р26 добавлены после сверки с исходным ТЗ для отдельной проверки фактического наполнения сайта и механизма пробуждений.

### [ ] Р01. Границы автономности и запрет опасных действий
**Карта:** A02–A07, I02, I04–I05, K44–K46, K51.  
**Область:** все четыре репозитория; инструменты, маршруты API, разрешения, конфигурация.  
**Проверить:** достижимые из автономного потока действия; отсутствие возможности публиковать, управлять каналом, покупать услуги или менять критические настройки; что ни один бюджетный режим не инициирует оплату; что исследовательская логика не запускает производство контента. Проверить фильтры 18+, новостей и политики не только на входе, но и перед итоговой рекомендацией.  
**Приёмка:** запрещённые действия недостижимы из автономного контура; безопасные тестовые примеры запрещённых тем не попадают в рекомендации; платные действия не выполняются.  
**Доказательства:** карта достижимых маршрутов/инструментов, тесты разрешений и фильтров, конфигурация без секретов, фактический результат безопасного теста.

### [ ] Р02. Режимы бюджета и нулевая стоимость
**Карта:** A05–A06, K11–K14, K51.  
**Область:** настройки, UI, директор, интеграции и конфигурация развёртывания.  
**Проверить:** допустимые значения режима, нулевой режим по умолчанию, сохранение выбора и его применение к рекомендациям; отсутствие обязательной платной зависимости; поведение при нулевом бюджете и недоступности нужных бесплатных данных.  
**Приёмка:** режим корректно сохраняется и читается после перезапуска; система не тратит деньги; при невозможности бесплатного исследования явно сообщает ограничение, а не обещает невыполнимый результат.  
**Доказательства:** значения до/после перезапуска, конфигурация зависимостей, тест нулевого режима, пример честно обозначенного ограничения.

### [ ] Р03. Стартовая готовность и состояние проекта
**Карта:** D05–D07, K15–K20, K39–K40, K58.  
**Область:** директор, планировщик, хранилище и API статуса.  
**Проверить:** стартовые health/readiness-проверки; различение неизвестного, работающего, завершённого и ошибочного состояния; сохранение плана проекта и цикла; запись причин решений, переносов и неудач; временные отметки запуска, последнего успеха и пропусков.  
**Приёмка:** статус отражает фактическое состояние, а не сам факт HTTP-вызова; после перезапуска доступна сохранённая история; неизвестное состояние не выдаётся за успех.  
**Доказательства:** ответы health/status, записи запусков и планы до/после перезапуска, логи одного успешного и одного неуспешного цикла.

### [ ] Р04. Расписание и единственный механизм запуска
**Карта:** D01–D04, K27, K57–K58, H01, H07.  
**Область:** site-insight-engine, ai-youtube-system, watchdog и GitHub Actions.  
**Проверить:** фактические расписания, соответствие требованию 24 плановых запусков в сутки, отсутствие неуправляемых дублирующих планировщиков, порядок приоритетов и поведение при совпадающих запусках. Сверить выбор задач с порядком ТЗ: (1) сохранность и восстановление; (2) обязательные квотные исследования; (3) повторные измерения и проверка выводов; (4) новые исследования; (5) монетизация и реализуемость; (6) рекомендации и задачи; (7) оценка эффективности; (8) отчётность. Если порядок изменён, проверить, что причина и последствия сохранены в журнале. Различать запланированный запуск, фактический запуск и успешное завершение полезной работы.  
**Приёмка:** расписание подтверждено конфигурацией и историей; конкурентный/повторный вызов не запускает опасную параллельную работу; перенос задач объясним.  
**Доказательства:** расписания, история workflow/циклов, результаты теста повторного и параллельного запуска, причины переноса задач.

### [ ] Р05. Идемпотентность, сбои и восстановление цикла
**Карта:** D03–D07, G03–G05, E04, K39–K40, K50, J04.  
**Область:** директор, API, память и все зависимости цикла.  
**Проверить:** повторный запрос, тайм-аут, временную недоступность зависимости, остановку посередине операции и повтор после восстановления. Проверить, не создаются ли дубли и не объявляется ли несохранённый результат успешным.  
**Приёмка:** повторы ограничены и безопасны; прогресс либо сохраняется, либо операция получает честный частичный/ошибочный статус; восстановление не дублирует результаты.  
**Доказательства:** тестовые сценарии отказа, журналы до/после восстановления, сравнение идентификаторов и записей.

### [ ] Р06. Контракты и доступность промежуточного API
**Карта:** C03, G01–G07, K46, I01, I07.  
**Область:** ai-youtube-system и API директора/MCP.  
**Проверить:** методы, адреса, заголовки, схемы запросов и ответов, авторизацию служебных маршрутов, обработку некорректного ответа, тайм-аутов и HTTP-ошибок. Проверить конфигурацию адресов и секретов.  
**Приёмка:** контракты совпадают между вызывающим и принимающим компонентами; ошибка нижестоящего сервиса не превращается в успех; секретные маршруты защищены, секреты не попадают в логи.  
**Доказательства:** контрактные/интеграционные тесты успеха и ошибок, безопасные примеры запросов/ответов, результаты проверки конфигурации.

### [ ] Р07. YouTube MCP: инструменты и фактическое получение данных
**Карта:** C01–C03, C08–C09, K21–K26, K61–K62.  
**Область:** youtube-mcp/server.py и вызывающий исследовательский исполнитель.  
**Проверить:** доступность требуемых инструментов, валидность входных параметров, формат и полноту ответа, обработку пустых результатов, ошибки API и происхождение возвращённых данных. Выполнить минимальный безопасный запрос, только если доступ и квота позволяют.  
**Приёмка:** данные реально получены и используются исследованием; ошибки/пустые ответы распознаются; источник и контекст результата сохраняются; отсутствующие метрики обозначаются неизвестными.  
**Доказательства:** тесты инструментов, обезличенный запрос/ответ или запись вызова, сохранённый результат с источником и временной отметкой.

### [ ] Р08. Единый учёт квоты и дневной лимит
**Карта:** C04–C08, K28–K30, K41, I04.  
**Область:** модуль квоты директора, MCP, журнал запросов и отчётность.  
**Проверить:** единственность источника истины по расходу квоты; соответствие списаний фактическим вызовам; расчёт остатка; поведение при лимите и ошибках; объяснение неиспользованного остатка. Проверить, что система не делает бесполезные вызовы ради формального нулевого остатка.  
**Приёмка:** квота учитывается согласованно, ограничения API не обходятся, исчерпание лимита не вызывает бесконечные повторы; причина остановки видима.  
**Доказательства:** сопоставление тестовых вызовов с учётом, журнал остатка и ошибок, тест лимита без ненужных реальных запросов.

### [ ] Р09. Покрытие рынка и разнообразие исследовательских направлений
**Карта:** B01–B03, K21–K22, K57, K62.  
**Область:** стратегия исследования, очередь и память исследованных направлений.  
**Проверить:** как выбираются рынки/темы, как обнаруживаются перекосы в сторону популярных тем, как фиксируется уже исследованное; есть ли проверка переносимости между рынками/языками и разные авторские примеры.  
**Приёмка:** выбор направления объясним и журналируется; система не выдаёт единичный успех за воспроизводимую возможность; недоступные рынки/факторы не считаются проверенными.  
**Доказательства:** план и журнал выборки, примеры нескольких направлений, обоснование покрытия и ограничений.

### [ ] Р10. Качество доказательств и причинные выводы
**Карта:** B02–B10, C09, E02, E05, K23–K26, K32, K53–K54, K61–K62.  
**Область:** аналитика, гипотезы, история измерений и рекомендации.  
**Проверить:** разделение фактов, выводов и гипотез; ссылки и даты; повторные сопоставимые измерения; сравнение периодов; объяснение причин успеха без выдачи корреляции за причинность; отсутствие выдуманных закрытых метрик.  
**Приёмка:** каждый существенный вывод можно проследить до источника и измерения; неопределённость видима; гипотезы имеют проверяемый сигнал и сохраняемую историю.  
**Доказательства:** одна рекомендация от источника до вывода, история повторного замера, пример неизвестной метрики и тестируемой гипотезы.

### [ ] Р11. Методика оценок, реализуемость и монетизация
**Карта:** B03–B05, K14, K23–K25, K31–K34, K54.  
**Область:** аналитика и формирование рекомендаций.  
**Проверить:** отдельные критерии роста, масштаба, воспроизводимости, конкуренции, скорости производства, потенциальной окупаемости и уверенности; прозрачность сводного балла; реалистичность пути к первым доходам и ограничения при нулевом бюджете.  
**Приёмка:** методика документирована и применяется последовательно; допущения и недостающие данные видимы; доход не гарантируется, а сводный балл не скрывает отдельные оценки.  
**Доказательства:** пример расчёта с исходными данными, правила формирования балла, тест отсутствующих входных данных.

### [ ] Р12. Структура и качество рекомендации
**Карта:** B08, B09, F03, K31–K34, K52–K55.  
**Область:** хранилище рекомендаций, API, UI и директор.  
**Проверить:** обязательные поля: уникальный ID, дата, статус, аудитория/рынок/язык, спрос/рост, источники, риски, неизвестные, уверенность, проведённые проверки и следующие шаги. Проверить краткую пользовательскую карточку отдельно от подробных доказательств.  
**Приёмка:** данные сохранены и возвращаются после перезапуска; карточка понятна по-русски и не подменяется набором баллов; предварительные выводы и неизвестные обозначены явно.  
**Доказательства:** сохранённая запись и API-ответ, карточка в UI, подробный отчёт и проверка после перезапуска.

### [ ] Р13. Гипотезы и накопление знаний
**Карта:** B06–B10, E01–E05, K25–K26, K32, K62.  
**Область:** аналитика, память и исследовательский исполнитель.  
**Проверить:** создание гипотезы, связь с доказательствами, тестовым сигналом, повторными измерениями и изменением уверенности; сохранение старых выводов и причин пересмотра.  
**Приёмка:** гипотезу можно проследить от основания до проверки; новые данные обновляют оценку, но не стирают историю; непроверяемые факторы отмечены как недоступные.  
**Доказательства:** запись гипотезы, несколько связанных измерений, история изменения статуса/прогноза.

### [ ] Р14. Память и устойчивость хранения
**Карта:** E01–E07, K17–K20, K50, K52, K56, K59, K61.  
**Область:** фактические хранилища, адаптеры, API и сервисы.  
**Проверить:** сохранение результатов, состояния проекта, рекомендаций, сообщений чата, задач и истории; чтение после перезапуска; недоступность БД; согласованность ссылок и статусов между сервисами; правила актуальности сохранённых данных.  
**Приёмка:** успешное сохранение подтверждается чтением; при сбое данные не объявляются сохранёнными; восстановление не создаёт дублей; повторно используются только достаточные и актуальные данные.  
**Доказательства:** чтение записей до/после перезапуска, тест сбоя хранения, сверка связей и статусов.

### [ ] Р15. Контекст диалога и дополнительные исследования
**Карта:** F04–F05, E06, K35–K37, K56.  
**Область:** чат, API, память и директор.  
**Проверить:** обсуждение конкретной рекомендации, уточняющие вопросы, сохранение существенного контекста и запуск дополнительного исследования только когда оно нужно. Проверить связь результата исследования с исходной рекомендацией и диалогом.  
**Приёмка:** после продолжения или перезапуска контекст не теряется; ответ использует сохранённые данные и отделяет известное от неизвестного; результаты дополнительного исследования доступны в истории.  
**Доказательства:** сценарий диалога с несколькими сообщениями, связанная запись исследования и повторное чтение контекста.

### [ ] Р16. Явное согласие и создание задачи
**Карта:** A03–A04, F06–F07, E03–E07, K35–K38, K59–K60.  
**Область:** UI, API, директор, память и подсистема задач.  
**Проверить:** состояния согласия, отказа и отсутствия ответа; идемпотентность повторного подтверждения; создание только задачи на будущее рассмотрение, без запуска производства, публикации или передачи следующему блоку. Проверить метаданные и историю задачи.  
**Приёмка:** без явного положительного согласия задача не создаётся; согласие создаёт ровно одну связанную задачу с ID, датой, статусом, текстом, режимом бюджета и историей; никакой производственный процесс не запускается.  
**Доказательства:** тесты согласия/отказа/тайм-аута/повтора, запись задачи и логи отсутствия downstream-вызовов.

### [ ] Р17. Русскоязычный интерфейс и действия пользователя
**Карта:** F01–F08, K35–K38, K42, K49, K55.  
**Область:** сайт, чат, API-ответы, уведомления и ошибки.  
**Проверить:** русский язык всех пользовательских сообщений; русские пояснения к иностранным названиям; ясность кнопок Agree/Reject/Discuss и объяснение последствий; соответствие UI фактическим статусам backend.  
**Приёмка:** пользователь понимает содержание рекомендации и действие, которое подтверждает; отображаемый статус подтверждён API/хранилищем; английские термины пояснены по-русски, если не являются оригинальным названием.  
**Доказательства:** проверенные основные UI-сценарии и снимки/ответы без секретов, сверка статуса интерфейса с backend.

### [ ] Р18. Промежуточная оркестрация и сквозная передача данных
**Карта:** C03, C09, G01–G07, E07, K39–K40, K46.  
**Область:** site-insight-engine ↔ ai-youtube-system ↔ youtube-mcp и хранилище.  
**Проверить:** один безопасный исследовательский запрос по всей цепочке: формирование запроса, передача, получение данных, возврат результата, обработка ошибок, сохранение и использование результата директором. Проверить сквозной идентификатор и тайм-ауты.  
**Приёмка:** формат и статус не искажаются на переходах; сбой любого звена виден; итоговый результат подтверждён сохранёнными данными, а не только HTTP 200.  
**Доказательства:** трасса одного успешного и одного ошибочного сценария, идентификаторы запросов, результат в хранилище и соответствующий статус.

### [ ] Р19. Watchdog и три Render-сервиса
**Карта:** H01–H09, K39–K40, K46.  
**Область:** youtube-office-watchdog, workflow и целевые Render-сервисы.  
**Проверить:** расписание workflow, корректность каждого из трёх адресов, HTTP-коды, тайм-ауты, сетевые ошибки, ограниченные повторы, отдельный результат по каждому сервису. Различать пробуждение, доступность и готовность выполнять работу.  
**Приёмка:** история подтверждает плановые запуски; сбой отдельного сервиса не скрывается общим зелёным статусом; проверка не запускает исследовательский цикл и не создаёт неконтролируемую нагрузку.  
**Доказательства:** история Actions, результаты по каждому адресу, контролируемый тест ошибки или тестовая имитация без воздействия на production.

### [ ] Р20. Еженедельный отчёт и честность сводных показателей
**Карта:** D08, K21, K26, K29, K39, K41, K63.  
**Область:** отчётность директора, хранилище запусков, аналитика и задачи.  
**Проверить:** отчёт формируется из фактических данных и включает направления исследований, гипотезы и их статусы, изменения прогнозов и причины, бюджетную реализуемость, возможную монетизацию и ограничения, распределение по странам/языкам/темам/форматам, задачи и прогресс, квоту, ошибки и приоритеты.  
**Приёмка:** каждое число и статус прослеживается до источника; отсутствующие данные обозначены; отчёт не заявляет о выполнении по одному лишь факту запуска.  
**Доказательства:** тестовый отчёт и ссылки на исходные записи/измерения, проверка обязательных разделов и неизвестных значений.

### [ ] Р21. Логи, аудит и доказательная отчётность
**Карта:** D07, G05, I07, J01, J06–J07, K39–K43, K47–K48.  
**Область:** все четыре репозитория и комплект аудита.  
**Проверить:** корреляцию событий по идентификатору, раздельные статусы запуска/завершения/сохранения, отсутствие секретов в логах, реестр проверок и полноту доказательств. Убедиться, что для каждого ID карты есть проверка либо объяснение невозможности проверки.  
**Приёмка:** отчёт содержит факты и ссылки на доказательства; статусы выбраны из согласованного набора; непроверенные обязательные требования блокируют заявление о полной готовности.  
**Доказательства:** реестр аудита, примеры логов с корреляционными ID, перечень покрытых и непроверенных ID, список ограничений.

### [ ] Р22. Тестовая стратегия и регрессии
**Карта:** J01–J07, K42–K48.  
**Область:** тесты всех четырёх репозиториев и сквозной стенд.  
**Проверить:** наличие и фактический запуск подходящих модульных, интеграционных, persistence-, error/recovery- и end-to-end-тестов; соответствие каждого теста конкретному требованию карты; повторные тесты после исправлений. Отдельно указывать тесты, которые не удалось запустить.  
**Приёмка:** каждый применимый пункт покрыт проверкой или явно обоснованным ограничением; зелёный тест не заменяет production-проверку там, где она обязательна; после исправления не появились регрессии.  
**Доказательства:** команды и результаты тестов, CI-ссылки, список непокрытых проверок и объяснение неприменимости.

### [ ] Р23. Секреты и безопасная эксплуатация
**Карта:** G06–G07, I01–I06, K45–K47.  
**Область:** код, история репозиториев, переменные окружения, GitHub Actions и Render.  
**Проверить:** отсутствие открытых секретов в текущем коде/логах, корректность доступа к служебным маршрутам, безопасные настройки окружения, отсутствие неразрешённых разрушительных операций и изменений вне объёма задания. Проверку истории на секреты проводить только разрешённым безопасным способом; не выводить секретные значения в отчёт.  
**Приёмка:** секреты передаются через безопасную конфигурацию; доступ ограничен; аудит не расходует бюджет/квоту и не изменяет данные без необходимости.  
**Доказательства:** результаты безопасного сканирования и тестов доступа, названия проверенных настроек без их значений, перечень использованных тестовых ограничений.

### [ ] Р24. Финальный сквозной сценарий и решение о готовности
**Карта:** A01–J07, K01–K63; особенно C01–C09, D01–D08, E01–E07, F03–F08, G01–G07, K43, K47–K50.  
**Область:** все четыре репозитория и целевая среда.  
**Проверить:** один полный безопасный цикл от планового запуска через выбор исследовательской задачи, получение YouTube-данных, учёт квоты и анализ до сохранённой рекомендации, отображения пользователю и формирования отчётности. Отдельно проверить путь явного согласия в Р16, не запуская производство. Выполнить построчную сверку исходного ТЗ с картой, чтобы обнаружить условия, не получившие ID.  
**Приёмка:** каждый переход подтверждён реальным результатом и сохранёнными данными; нет необъяснённых расхождений статусов; каждому требованию карты соответствует результат проверки; незакрытые обязательные проверки не позволяют объявить систему полностью готовой.  
**Доказательства:** сквозная трасса, записи хранения, рекомендация в UI, отчёт цикла, результаты построчной сверки ТЗ и перечень оставшихся блокеров.


### [ ] Р25. Наполнение сайта и полнота пользовательских разделов
**Карта:** A01–A03, B08–B09, E03–E07, F01–F08, K31–K38, K41, K49, K52–K55, K59–K60.  
**Область:** пользовательская часть site-insight-engine, API рекомендаций/задач, хранилище и чат.  
**Проверить:** что на сайте действительно доступны и связаны между собой: список и подробная карточка рекомендаций; блоки «Почему директор это рассматривает» и «Что ещё необходимо проверить»; переход к источникам/подробному отчёту; чат по конкретной рекомендации; действия «Согласиться», «Отказать», «Обсудить»; отдельный раздел задач; переключатель режима бюджета; реальные статусы работы и истории; недельный отчёт или доступный путь к нему. Проверить не только шаблоны UI, но и наполнение из реальных сохранённых данных: рекомендация после сохранения появляется в списке, детали и ссылки открываются, задача появляется после согласия, отказ не создаёт задачу, а тестовые/заглушечные данные не выдаются за реальные.  
**Приёмка:** все требуемые ТЗ пользовательские разделы доступны, содержат согласованные с backend данные и работают в сквозных сценариях. Нет ложных кнопок, пустых обещаний, демонстрационных записей под видом реальных результатов или расхождения статусов сайта и хранилища.  
**Доказательства:** скриншоты/видео пользовательских сценариев, ответы API, связанные записи хранилища и проверка после перезапуска. Не добавлять проверку маркетинговых страниц или иных страниц, которых ТЗ не требует.

### [ ] Р26. Пробуждения директора, расписание и «будильники»
**Карта:** §4 п.2, §6.1–§6.3, §7.2–§7.3, §19; A01, D01–D07, K15–K19, K27–K30, K39–K40.  
**Область:** планировщик в site-insight-engine и ai-youtube-system, GitHub Actions/cron, а также watchdog — только в пределах его отдельной роли.  
**Проверить:** что именно инициирует каждое пробуждение директора; какие расписания и часовой пояс действуют; действительно ли запланировано 24 запуска в сутки; что происходит при пропущенном запуске, задержке, перезапуске и одновременном событии; что при каждом пробуждении сначала проверяются сервисы, источники данных, память, планировщик, незавершённые циклы, задачи и режим бюджета; что сохраняется причина пробуждения, идентификатор цикла, фактическое начало/окончание и итог. Отдельно доказать, что watchdog лишь проверяет доступность Render и не подменяет исследовательский цикл.  
**Приёмка:** механизм пробуждения установлен по конфигурации и фактической истории, пропуски и дубли выявляются, каждое пробуждение оставляет диагностируемый результат. Не путать «сработал cron/будильник», «HTTP-сервис ответил» и «директор выполнил полезное исследование».  
**Доказательства:** конфигурация расписания, история Actions/планировщика и записей циклов, контролируемый тест пропуска/повтора и подтверждение стартовых проверок.

## Декомпозиция проверок на самостоятельные задания

### Правило уровней и статусов
- Р01–Р26 — группы проверок, сохраняющие связь с исходным ТЗ и эталонной картой. Подпункты Рxx.1, Рxx.2 и т. д. — рекомендуемые единицы назначения исполнителю.
- Каждый подпункт выполняется как отдельная проверка: отдельный сценарий, ожидаемый результат, фактический результат, доказательства и статус по общим правилам аудита. В отчёте указывать конкретные файлы/функции, команды или действия, среду и ссылки на результаты.
- Родительский пункт нельзя считать пройденным, пока все обязательные подпункты не пройдены и не выполнена указанная для родителя интеграционная проверка. Если подпункт неприменим, это нужно обосновать доказательствами; недоступность среды означает «Заблокировано»/«Ожидает проверки в реальной среде», а не «Пройдено».
- Подпункты не отменяют общих требований: анализ кода, запуск всех применимых автоматических и регрессионных тестов, живой тест на работающей системе, воспроизводимая инструкция ручной проверки и доказательства. Для опасных/платных действий использовать безопасную тестовую среду или имитацию; не совершать реальное запрещённое действие.
- Если во время подпункта обнаружена отдельная неисправность вне его объёма, зафиксировать её как отдельный дефект/задачу, не расширяя молча текущую проверку.

### [ ] Р01. Границы автономности и запрет опасных действий
- **Р01.1 — Карта достижимых действий.** Проследить от автономного цикла до инструментов/API все достижимые действия; доказать отсутствие незащищённого пути к публикации, управлению каналом, покупке и критическим настройкам.
- **Р01.2 — Граница между исследованием и производством.** Проверить, что исследовательский контур не запускает создание/производство контента и не передаёт задачу следующим производственным блокам.
- **Р01.3 — Фильтры и бюджетные запреты.** Проверить фильтры 18+, новостей и политики на входе и перед рекомендацией, а также блокировку платных действий при всех режимах бюджета.

### [ ] Р02. Режимы бюджета и нулевая стоимость
- **Р02.1 — Настройка режима.** Проверить допустимые значения, режим по умолчанию, сохранение выбора и чтение выбранного режима после перезапуска.
- **Р02.2 — Отсутствие обязательных платных зависимостей.** Проверить рабочие зависимости, конфигурацию и путь выполнения на предмет обязательных платных API/услуг.
- **Р02.3 — Нулевой бюджет и нехватка бесплатных данных.** На живом безопасном сценарии проверить, что система продолжает доступную бесплатную работу и честно объясняет невозможность недоступного исследования.

### [ ] Р03. Стартовая готовность и состояние проекта
- **Р03.1 — Health и readiness.** Проверить различие доступности HTTP-сервиса и готовности выполнять работу, включая частично недоступные зависимости.
- **Р03.2 — Состояния цикла.** Проверить корректное различение неизвестного, ожидающего, выполняющегося, завершённого и ошибочного состояния.
- **Р03.3 — Состояние проекта и диагностика.** Проверить сохранение плана, причин решений/переносов/ошибок и временных отметок, а также чтение истории после перезапуска.

### [ ] Р04. Расписание, приоритеты и конкурентные запуски
- **Р04.1 — Фактическое расписание.** Сверить конфигурации всех планировщиков и часовые пояса; доказать, сколько запусков запланировано за сутки и как это подтверждается историей.
- **Р04.2 — Единственность механизма запуска.** Найти дублирующие cron/workflow/планировщики и установить, есть ли неуправляемые повторные запуски.
- **Р04.3 — Порядок приоритетов.** На контролируемом наборе задач проверить все восемь приоритетов из ТЗ, включая объяснение переноса задач и сохранение причины.
- **Р04.4 — Повторные и конкурентные запуски.** Проверить одновременный запуск, повторный вызов и защиту от двойной обработки; отдельно различить плановый запуск, фактический запуск и завершение полезной работы.

### [ ] Р05. Идемпотентность, сбои и восстановление цикла
- **Р05.1 — Повтор запроса и тайм-аут.** Проверить, что повтор после тайм-аута не создаёт дубли и не скрывает неизвестный результат первой операции.
- **Р05.2 — Отказ зависимости и прерывание посередине.** Контролируемо вызвать отказ/остановку и проверить частичный статус, сохранённый прогресс и журнал ошибки.
- **Р05.3 — Восстановление и повторное выполнение.** После восстановления проверить продолжение цикла, согласованность записей и отсутствие повторного создания результата.

### [ ] Р06. Контракты и доступность промежуточного API
- **Р06.1 — Контракты успешных запросов.** Сверить методы, маршруты, заголовки, схемы и типы данных между вызывающими и принимающими компонентами.
- **Р06.2 — Ошибочные ответы и тайм-ауты.** Проверить некорректные данные, HTTP-ошибки, тайм-ауты и недоступность нижестоящего сервиса.
- **Р06.3 — Авторизация и конфигурация.** Проверить защиту служебных маршрутов, конфигурацию адресов и отсутствие секретов в логах/ответах.

### [ ] Р07. YouTube MCP: инструменты и получение данных
- **Р07.1 — Набор инструментов и валидация входа.** Проверить доступность обязательных инструментов и отклонение некорректных параметров.
- **Р07.2 — Реальное получение и структура данных.** Выполнить безопасный запрос при наличии доступа/квоты; проверить схему, полноту и происхождение ответа.
- **Р07.3 — Пустые результаты и ошибки источника.** Проверить пустой ответ, ограничение API и ошибку; убедиться, что директор не трактует их как успешное исследование.
- **Р07.4 — Сохранение происхождения данных.** Проследить источник, дату/время и результат от ответа MCP до используемой записи/вывода директора.

### [ ] Р08. Единый учёт квоты и дневной лимит
- **Р08.1 — Единый источник учёта.** Сопоставить фактические вызовы с записями списания и проверить отсутствие независимых противоречивых счётчиков.
- **Р08.2 — Расчёт остатка и достижение лимита.** Проверить граничные значения, остановку при лимите и отсутствие бесконечных повторов/обхода ограничений.
- **Р08.3 — Ошибки и объяснение неиспользованной квоты.** Проверить, что расход/остаток и причина остановки отражаются в состоянии и отчёте; не отправлять бесполезные запросы ради нулевого остатка.

### [ ] Р09. Покрытие рынка и разнообразие исследований
- **Р09.1 — Выбор следующего направления.** Проверить, как формируется и объясняется выбор рынка/темы с учётом приоритетов.
- **Р09.2 — Учёт ранее исследованного.** Проверить память выборки, предотвращение необоснованных повторов и обнаружение перекосов.
- **Р09.3 — Переносимость и ограничения покрытия.** Проверить примеры нескольких рынков/языков/авторов и честную фиксацию факторов, которые недоступны для проверки.

### [ ] Р10. Качество доказательств и причинные выводы
- **Р10.1 — Прослеживаемость утверждений.** Для выбранного вывода проследить каждое существенное утверждение до источника, даты и измерения.
- **Р10.2 — Сопоставимость повторных измерений.** Проверить сравнение периодов/измерений и обработку неполных либо несопоставимых данных.
- **Р10.3 — Корреляция, причинность и неизвестные.** Проверить, что гипотезы не выдаются за доказанные причины и закрытые/недоступные метрики не выдумываются.

### [ ] Р11. Методика оценок, реализуемость и монетизация
- **Р11.1 — Отдельные критерии оценки.** Проверить расчёт/отображение роста, масштаба, воспроизводимости, конкуренции, скорости производства, потенциальной окупаемости и уверенности.
- **Р11.2 — Сводный балл и допущения.** Пересчитать пример по исходным данным; проверить последовательность методики и видимость неизвестных.
- **Р11.3 — Реализуемость и монетизация при ограничениях.** Проверить обоснование возможного пути к доходу без гарантии дохода и без нарушения нулевого бюджета.

### [ ] Р12. Структура и качество рекомендации
- **Р12.1 — Полнота записи и обязательные поля.** Проверить ID, дату, статус, рынок/аудиторию/язык, спрос/рост, источники, риски, неизвестные, уверенность и следующие шаги.
- **Р12.2 — Сохранение и API.** Проверить созданную рекомендацию в API/хранилище, повторное чтение после перезапуска и целостность ссылок.
- **Р12.3 — Пользовательская карточка и доказательства.** Проверить краткую карточку в UI отдельно от подробного отчёта и доступность источников.

### [ ] Р13. Гипотезы и накопление знаний
- **Р13.1 — Создание проверяемой гипотезы.** Проверить связь гипотезы с основанием, сигналом проверки и планом измерений.
- **Р13.2 — Обновление уверенности по новым данным.** Добавить/использовать новое тестовое измерение и проверить, как изменяется оценка.
- **Р13.3 — История и пересмотр вывода.** Проверить, что старый вывод не стирается, а причина пересмотра и статус доступны после перезапуска.

### [ ] Р14. Память и устойчивость хранения
- **Р14.1 — Полнота сохраняемых сущностей.** Отдельно проверить сохранение состояния проекта/цикла, исследований, рекомендаций, чатов, задач и истории.
- **Р14.2 — Чтение после перезапуска.** Для тестовых записей проверить чтение из каждого применимого хранилища после перезапуска соответствующего сервиса.
- **Р14.3 — Ошибка записи и восстановление.** Проверить недоступность БД/ошибку записи, честный статус и последующее восстановление без потери/дублирования.
- **Р14.4 — Согласованность связей и актуальность.** Проверить ссылки между рекомендацией, чатом, задачей и источниками, а также решение о повторном использовании устаревших данных.

### [ ] Р15. Чат и дополнительное исследование по обсуждению
- **Р15.1 — Контекст конкретной рекомендации.** Проверить, что чат использует именно связанную рекомендацию и её актуальные данные.
- **Р15.2 — Инициирование дополнительного исследования.** На живом безопасном сценарии проверить постановку дополнительной задачи, когда вопрос требует новых данных.
- **Р15.3 — Сохранение диалога и результата.** Проверить историю сообщений, выводы и результат исследования после перезапуска.

### [ ] Р16. Явное согласие и создание задачи
- **Р16.1 — Согласие, отказ и отсутствие ответа.** Проверить каждое состояние и отсутствие задачи без явного положительного согласия.
- **Р16.2 — Идемпотентность подтверждения.** Повторить подтверждение и проверить, что создаётся ровно одна задача.
- **Р16.3 — Полнота задачи и связь с рекомендацией.** Проверить ID, дату, статус, текст, бюджетный режим, историю и ссылки на рекомендацию/чат.
- **Р16.4 — Отсутствие производственного запуска.** Доказать по логам/трассе, что согласие не запускает создание контента, публикацию или передачу в следующий блок.

### [ ] Р17. Русскоязычный интерфейс и действия пользователя
- **Р17.1 — Язык и понятность сообщений.** Проверить ключевые экраны, ошибки, уведомления и пояснения к иностранным терминам.
- **Р17.2 — Семантика действий пользователя.** Проверить согласие, отказ и обсуждение: правильные действия, подтверждения и отсутствие побочных эффектов.
- **Р17.3 — Согласованность UI и backend.** Сверить видимые статусы и данные с API/хранилищем после изменений и перезапуска.

### [ ] Р18. Промежуточная оркестрация и сквозная передача данных
- **Р18.1 — Успешный путь данных.** Проследить один безопасный запрос от директора через API и MCP до результата и сохранения.
- **Р18.2 — Идентификаторы, контракты и тайм-ауты.** Проверить сохранение корреляции запроса и поведения на границах сервисов.
- **Р18.3 — Отказ одного звена.** Вызвать контролируемую ошибку и проверить, что она видна на всём пути и не маскируется HTTP 200.
- **Р18.4 — Использование сохранённого результата.** Проверить, что директор действительно использует возвращённые данные, а не только получает ответ API.

### [ ] Р19. Watchdog и три Render-сервиса
- **Р19.1 — Расписание и запуск watchdog.** Проверить конфигурацию расписания и фактическую историю GitHub Actions.
- **Р19.2 — Проверка каждого Render-сервиса.** Проверить адрес, тайм-аут, HTTP-ответ и отдельный результат каждого из трёх сервисов.
- **Р19.3 — Ошибка и ограниченные повторы.** Проверить сетевую ошибку/недоступность без бесконечных повторов и без сокрытия отказа.
- **Р19.4 — Роль watchdog.** Доказать, что watchdog сообщает о доступности и не подменяет цикл исследования директора.

### [ ] Р20. Еженедельный отчёт и честность сводных показателей
- **Р20.1 — Полнота разделов отчёта.** Проверить наличие всех обязательных категорий из ТЗ, включая исследования, гипотезы, прогнозы, реализуемость, квоту, ошибки и задачи.
- **Р20.2 — Прослеживаемость цифр и статусов.** Выбрать значения отчёта и проследить до исходных записей/измерений.
- **Р20.3 — Отсутствующие данные и фактический статус.** Проверить, что неизвестные данные обозначены явно, а запуск не приравнивается к выполненной полезной работе.

### [ ] Р21. Логи, аудит и доказательная отчётность
- **Р21.1 — Трассировка событий.** Проверить корреляционные ID и различение начала, завершения, сохранения и ошибки.
- **Р21.2 — Реестр покрытия требований.** Сверить ID карты с проверкой, доказательством и статусом; отдельно вывести непроверенные ID.
- **Р21.3 — Достаточность доказательств и отсутствие секретов.** Проверить ссылки/логи и убедиться, что отчёт подтверждает именно заявленные критерии, не раскрывая секреты.

### [ ] Р22. Тестовая стратегия и регрессии
- **Р22.1 — Инвентаризация и запуск автоматических тестов.** Для каждого репозитория собрать применимые тестовые команды и реально выполнить их; зафиксировать пропуски и причины.
- **Р22.2 — Покрытие требований и негативных сценариев.** Сопоставить тесты с ID карты, включая ошибки, границы, восстановление и persistence.
- **Р22.3 — Живые проверки и регрессии.** Проверить работающую среду по правилам аудита и повторить связанные тесты после каждого исправления.

### [ ] Р23. Секреты и безопасная эксплуатация
- **Р23.1 — Секреты в коде, истории и логах.** Выполнить безопасное сканирование разрешёнными средствами; не выводить значения секретов в отчёт.
- **Р23.2 — Доступы и конфигурация окружения.** Проверить ограничения доступа и корректность названий/наличия необходимых настроек без раскрытия значений.
- **Р23.3 — Безопасность самого аудита.** Проверить, что тесты не вызывают реальные платные/запрещённые действия, не повреждают пользовательские данные и не выходят за объём задачи.

### [ ] Р24. Финальная сквозная проверка и решение о готовности
- **Р24.1 — Сквозной успешный цикл.** Провести безопасный сценарий от планового запуска через исследование и квоту до сохранённой рекомендации, UI и отчётности.
- **Р24.2 — Сквозные ошибки и согласие.** Проверить поведение при отказе ключевой зависимости и отдельно пройти согласие/отказ без запуска производства.
- **Р24.3 — Сверка исходного ТЗ с картой построчно.** Сопоставить каждое проверяемое условие исходного ТЗ с ID карты; добавить недостающие ID до итогового решения.
- **Р24.4 — Итоговое решение.** Сверить все подпункты, статусы, доказательства и блокеры; не объявлять готовность при незавершённых обязательных проверках.

### [ ] Р25. Наполнение сайта и полнота пользовательских разделов
- **Р25.1 — Рекомендации и подробности.** Проверить список, карточку, причины рассмотрения, оставшиеся проверки, источники и подробный отчёт.
- **Р25.2 — Чат и действия по рекомендации.** Проверить связанный чат, обсуждение, согласие и отказ на конкретной записи.
- **Р25.3 — Раздел задач и режим бюджета.** Проверить создание/отсутствие задачи в соответствующих сценариях и сохранение настройки бюджета.
- **Р25.4 — Реальные данные и статусы.** Проверить, что UI получает реальные записи backend, не показывает заглушки как факты и согласован с хранилищем после перезапуска.
- **Р25.5 — Доступ к недельному отчёту.** Проверить наличие отчёта или работающего пути к нему и совпадение с фактическими данными.

### [ ] Р26. Пробуждения директора, расписание и «будильники»
- **Р26.1 — Источники пробуждения и часовой пояс.** Установить по конфигурации все триггеры, расписания и часовой пояс.
- **Р26.2 — Частота и фактическая история.** Подтвердить 24 плановых запуска в сутки и сопоставить план с фактическими записями.
- **Р26.3 — Предстартовые проверки.** Проверить состояние сервисов, источников, памяти, плана, незавершённых циклов, задач и режима бюджета при пробуждении.
- **Р26.4 — Пропуски, задержки, повторы и параллельность.** Проверить контролируемые сценарии и корректность восстановления/диагностики.
- **Р26.5 — Результат каждого пробуждения и граница watchdog.** Проверить причину, ID цикла, время начала/окончания и итог; доказать, что watchdog не заменяет исследовательскую работу.


### Дополнение к матрице: явное покрытие сайта и пробуждений
| Проверяемая область | Пункты плана |
|---|---|
| Фактическое наполнение сайта и пользовательские разделы, включая рекомендации, чат, задачи, режим бюджета и отчётность | Р12, Р15–Р17, Р20, Р25 |
| Срабатывание расписания, пробуждение директора и проверки состояния при каждом пробуждении | Р03–Р05, Р26 |
| Отличие доступности сервиса от реального выполнения исследования | Р03–Р05, Р19, Р26 |

## Матрица покрытия эталонной карты

Матрица показывает, где проверяется каждый блок карты. Внутри указанных пунктов все перечисленные ID нужно отмечать индивидуально, даже если они проверяются одним сценарием.

| Диапазон карты | Пункты плана |
|---|---|
| A01–A07 | Р01, Р02, Р16, Р24 |
| B01–B10 | Р09–Р13, Р20 |
| C01–C09 | Р07–Р08, Р18, Р24 |
| D01–D08 | Р03–Р05, Р20–Р21, Р24 |
| E01–E07 | Р10, Р13–Р16, Р18, Р24 |
| F01–F08 | Р12, Р15–Р17, Р24 |
| G01–G07 | Р06, Р18, Р21, Р23 |
| H01–H09 | Р19 |
| I01–I07 | Р01–Р02, Р05–Р06, Р08, Р21, Р23 |
| J01–J07 | Р21–Р24 |
| K01–K10 | Р01–Р24: при первичном запуске сопоставить каждый ID с его полным названием и внести ID в реестр проверки; не закрывать только по диапазону |
| K11–K20 | Р02–Р03, Р14 |
| K21–K30 | Р04, Р07–Р10, Р20 |
| K31–K38 | Р11–Р17 |
| K39–K50 | Р03–Р06, Р18–Р24 |
| K51–K63 | Р01–Р02, Р07–Р17, Р20 |

**Обязательная оговорка по покрытию:** матрица — навигация, а не автоматическая отметка «пройдено». В итоговом реестре должен быть отдельный результат для каждого ID карты A01–J07 и K01–K63. При выявлении условия исходного ТЗ, которому не соответствует отдельный ID, сначала обновить карту и только затем считать покрытие полным.

## Шаблон записи результата по каждому пункту

Скопируй этот шаблон для каждого Pxx и заполни фактическими данными.

- **Пункт плана / ID карты:**
- **Статус:** Не проверено
- **Требование и ожидаемое поведение:**
- **Репозиторий, файлы и функции:**
- **Проведённые проверки:** код / тесты / API / логи / хранилище / реальный запуск
- **Фактический результат:**
- **Доказательства и ссылки:**
- **Обнаруженный дефект и причина:**
- **Исправление или отдельная задача (если нужны):**
- **Регрессионная проверка:**
- **Ограничения и что осталось проверить:**
- **Следующий шаг / ответственный:**

## Условие завершения аудита

Аудит завершён только тогда, когда каждый ID карты имеет собственный зафиксированный результат, обнаруженные дефекты имеют понятные следующие шаги, а ограничения целевой среды указаны явно. **Нельзя объявлять полную готовность**, если обязательный пункт имеет статус «Не проверено», «Заблокировано», «Проверено частично» или «Ожидает проверки в реальной среде». Такие статусы допустимы в промежуточном отчёте, но должны оставаться видимыми до фактической приёмки.


</details>

## I. Приёмка функциональности Director (все тест-кейсы)

**Перенесено из:** https://github.com/peonyrhodo-bit/site-insight-engine/blob/main/docs/director-acceptance-test-plan.md. Файл исходно расположен в site-insight-engine; критерии перенесены сюда.

<details>
<summary>Полный текст исходных задач, критериев и технических результатов (раскрыть)</summary>

# YouTube Director 3.0 — acceptance test plan

This plan is for validating the autonomous research cycle without touching production. Run automated tests in CI first; run live acceptance checks only against a disposable/staging environment with explicit quota limits.

## 1. Researcher behavior

- [ ] Start with existing cached data and an objective; confirm the Director analyzes available evidence even when new YouTube research is unavailable.
- [ ] Keep evidence sufficiency false when a research task or per-cycle budget is exhausted; record the remaining evidence gaps and a useful next step.
- [ ] Confirm a recommendation cites the observations that support it and distinguishes facts, hypotheses, and unknowns.
- [ ] Confirm contradictory evidence can lower confidence or change the hypothesis rather than being ignored.
- [ ] Confirm the next cycle chooses a distinct useful task instead of repeating completed task keys or the same failed query indefinitely.

## 2. Research execution and persistence

- [ ] Verify every planned operation is either executed or explicitly marked blocked/skipped/failed with a reason.
- [ ] Verify malformed MCP responses fail visibly and are not recorded as successful research.
- [ ] Verify zero-result searches are persisted as zero-result outcomes, not treated as evidence of absence.
- [ ] Verify successful search results, query records, research-set records, snapshots, and data relations are persisted and retrievable.
- [ ] Verify a partial write or dependency failure produces an honest partial/failed status and can be retried without duplicating completed work.
- [ ] Verify stale-video refresh uses each video's latest successful snapshot and does not perform unnecessary search calls.

## 3. Timeouts, quotas, and degraded mode

- [ ] A handler that never returns times out within the configured bound and records an actionable failure.
- [ ] When the quota ledger is unavailable, outbound YouTube calls fail closed before reaching the MCP; cached-data analysis remains possible.
- [ ] When the quota ledger is available, authorization, completion/failure accounting, and quota reconciliation work for success, error, timeout, and cancellation paths.
- [ ] Exhausted quota leads to a useful analysis/wait state, not an infinite retry loop or a false claim that evidence is sufficient.
- [ ] Retryable upstream failures use bounded retries/backoff; permanent errors do not loop.

## 4. Memory and long-running reliability

- [ ] Measure peak RSS for a representative cached dataset and for a full autonomous wake; record baseline and post-change values.
- [ ] Test a large dataset and confirm reads/analysis are bounded or chunked instead of materializing unbounded duplicate copies.
- [ ] Confirm the process handles cancellation/shutdown cleanly and does not leave a cycle permanently marked running.
- [ ] Run repeated cycles and verify memory does not grow monotonically and old cycle state does not leak into the next wake.

## 5. Release gate

Do not call the release validated until:
1. CI is green on the exact candidate commit.
2. The service starts in staging with valid configuration.
3. Cached-data-only mode passes with quota storage intentionally unavailable.
4. A quota-enabled, tightly capped live test completes at least one search and verifies persisted results.
5. One end-to-end objective reaches analysis/recommendation with traceable evidence and a recorded next action.
6. Logs show no repeated task loop, unhandled timeout, or out-of-memory termination during the test window.

Record candidate commit, environment, test timestamp, quota spend, result IDs, and failures. Never paste credentials or connection strings into logs, issues, or chat.


</details>

## J. Решения консолидации и сверка PR

**Перенесено из:** https://github.com/peonyrhodo-bit/youtube-mcp/blob/project-management/director-audit-2026-11-19/management/PROJECT_UNIFIED_PLAN_REVIEW_2026-11-22.md. Старые ограничения «не удалять после утверждения» заменены текущим решением: удаление только по отдельному согласованию.

<details>
<summary>Полный текст исходных задач, критериев и технических результатов (раскрыть)</summary>

Версия для согласования • 22.11.2026 • Только документ, без изменений GitHub, Render, Supabase и кода

# 1. Решение: единый рабочий документ

Выбрать существующий management/MASTER_PLAN.md (60 пунктов) в репозитории youtube-mcp, ветка project-management/director-audit-2026-11-19. Это не решение по названию: MASTER_PLAN покрывает весь путь от инфраструктуры и запуска до исследований, анализа, рекомендаций, обратной связи и сквозной приёмки. OOM_RECOVERY_PLAN ограничен инцидентом; MEMORY_INTELLIGENCE_2_PLAN ориентирован на углублённое развитие памяти; docs/director-acceptance-test-plan.md — перечень проверок, а не маршрут разработки. Сохраняем все 60 оригинальных номеров, не создаём третий независимый план. Другие файлы сохраняются как неизменяемая историческая основа; после утверждения обновляется только выбранный MASTER_PLAN.

Важное уточнение: эти management-файлы отсутствуют в main site-insight-engine и найдены в youtube-mcp на ветке project-management/director-audit-2026-11-19. Все нижеуказанные статусы относятся к проверенному GitHub и историческим снимкам 19 ноября; текущие показатели Render/Supabase не измерялись повторно. При утверждении отдельно подтвердить, в какую существующую ветку должен вноситься обновлённый MASTER_PLAN, не перемещая оригиналы самовольно.

# 2. Изменение принципа управления

MASTER_PLAN превращается из последовательного перечня проверок в исполняемый маршрут по зависимостям. Для каждого №001–060 добавить неизменяемое поле «Исторический пункт», цель, статус, зависимость, что сделать, метод доказательства, критерий приёмки, источники, следующую задачу и «Возврат к №». Подзадачи наследуют номер исходного пункта (например, №038.OOM-07 или №035.M02); ссылки вида \[OOM-07\], \[M02\], Issue \#68, PR \#69 сохраняются дословно. Никаких ложных “выполнено” на основании одного кода, CI или HTTP 200.

Статусы: ВЫПОЛНЕНО / ЧАСТИЧНО / НЕ ВЫПОЛНЕНО / НЕ ПРОВЕРЕНО / ЗАБЛОКИРОВАНО / ОТМЕНЕНО ИЛИ ЗАМЕНЕНО. В журнале хранить дату, commit SHA, тест/лог, среду, результат и ограничения вывода. При открытии блокировки фиксировать связанный родительский пункт, выполнять только допустимое исправление и возвращаться к нему. Общий дефект создаётся один раз, несколько пунктов ссылаются на него. Отдельно отмечать разрешение владельца для live/quota/production/SQL.

# 3. Выявленные изменения статусов

- №001–005, №007: ранее отмечены выполненными со ссылками на исторические свидетельства 19 ноября. Статус ВЫПОЛНЕНО для соответствующих исторических критериев, актуальность live-конфигурации перепроверяется только там, где зависит новая задача.

- №006: ЗАБЛОКИРОВАНО — не доказана runtime-связь orchestrator → Director; не мешает offline-исследованию остальных звеньев. №008: ЧАСТИЧНО/ЗАБЛОКИРОВАНО до допустимой проверки конфигурации.

- OOM-01–05: исторически завершены как диагностика/согласование, без доказательства устранения OOM. OOM-06: ЧАСТИЧНО (PR \#66 уже merged; PR \#70 merged 22 ноября; дополнительные PR не приняты). OOM-07: НЕ ПРОВЕРЕНО / ЗАБЛОКИРОВАНО на доказательство стабильности в целевой среде. OOM-08: НЕ ВЫПОЛНЕНО.

- №035/038 и M02/M16/M17/M20: ЧАСТИЧНО — PR \#66 и \#70 в main дают частичное ограничение страниц и целевые чтения; \#69 не объединён, вопрос полноты защищённых записей открыт.

- №036: ЧАСТИЧНО — PR \#71 (проект индексированного идемпотентного поиска), \#72 (изолированный тестовый стенд) открыты, оба не означают внедрения.

- №011–020/054: ЧАСТИЧНО/НЕ ПРОВЕРЕНО; PR \#73 открыт и не объединён. Обязательная проверка конфликта между требованием автономности и AUTONOMOUS_ENABLED без самовольного выбора семантики.

- №041–050/051–053: НЕ ПРОВЕРЕНО в production; отсутствие рекомендаций подтверждалось снимком 19 ноября, но новое состояние БД не запрашивалось.

- M01/M02: ЧАСТИЧНО, матрица 34 контрактов и карта чтений существуют; M03–M40 не отмечать завершёнными по одному наличию материала.

# 4. Единая очерёдность: конкретное предложение по 60 пунктам

## Этап 0. Вход в работу без повторного общего аудита

№009 (закончить недостающую трассировку ТЗ, M01), №010 (утвердить тестовые критерии), №031/035 (только минимальные контракты схем и защищённых чтений), №008 (проверка конфигурации без секретов). Приоритет — документировать лишь спорные данные, а не повторять уже доказанные 001–007.

## Этап 1. Восстановить безопасное состояние памяти и инфраструктуры

№035.M02/M09/M16/M17 + Issue \#68, PR \#67/#69/#70; №038.OOM-06/07, M03/M04/M20; №055 для Supabase HTTP 402. Проверить, блокирует ли 402 все чтения; прежде чем трогать Supabase, определить возможный безопасный read-only/локальный режим. №036 с PR \#71/#72 — не внедрять миграции до подтверждения контракта.

## Этап 2. Запуск и управление циклом на offline-фикстурах

№011→013→014→015→016→017→018→019; №012 сравнение с существующими логами, №020 — только после составных тестов. PR \#73: проверить совместимость и формальную семантику AUTONOMOUS_ENABLED; никакого автоматического merge.

## Этап 3. Исследование YouTube и данные

№021→022→023→024→025; №026→032→033→034; №027→028→029; затем №030. Quota manager решает доступность и расход, директор не пересчитывает сам. UnicodeEncodeError воспроизвести offline. Сначала кэш и mock-MCP, потом отдельно согласованный минимальный живой запрос.

## Этап 4. Аналитика, решение, сохранение

№041→042→043→044→045→046→047→048→049→050. PR \#65 по ограничению рабочего набора рассматривается только после регрессионной проверки исторических трендов, расчётов и RSS. Проверка рекомендаций разделена на создание записи, сохранение, API, UI.

## Этап 5. Пользовательский интерфейс и обратная связь

№051→052→053→054; проверить согласие отдельным действием, сохранение feedback, попадание его в память и создание следующей задачи без автоматической публикации видео.

## Этап 6. Контролируемая приёмка и требования

№006 (непроверенная связь сервисов), №008 (конфигурация), №037/040 (восстановление и частичные сбои), №055/056/057 → №058 → №059 → №060. №020/030/050 — компонентные сквозные тесты до общего №058. M37–M40 используются как приёмочные критерии, не отдельный маршрут.

## Отложенное развитие без потери требований

M07/M08/M10–15/M18–19/M21–30/M31–39 встроены по необходимости в №031–059. Сложное архивирование и очистка M23–M30 не предшествуют первой рекомендации, пока не показана фактическая нехватка места; ничего не удалять. M31/M32/M34 и обязательные квоты/согласия относятся к обязательной приёмке.

# 5. Матрица переноса работ и историческая прослеживаемость

| Исторический ID                       | Встроить в                          | Что переносится                                                                           |
|---------------------------------------|-------------------------------------|-------------------------------------------------------------------------------------------|
| OOM-01–05                             | №038/056                            | Сохранить как доказанную историческую диагностику; не выполнять заново.                   |
| OOM-06–08                             | №035/038/055/056 + возврат №006/008 | Промежуточные исправления, измерение стабильности, закрытие инцидента.                    |
| M01–M02                               | №009/031/035                        | Дозакрыть конкретные пробелы требований, call-site и protected semantics.                 |
| M03–M08                               | №031/038/056                        | Фактические ограничения бесплатных Supabase/Render; без затрат и преждевременной очистки. |
| M09–M15                               | №035/041–046/059                    | Контракты и доказательность решений, тестовые пороги.                                     |
| M16–M22                               | №035/038/041–046/056                | Bounded reads/analysis, update_run, проверка исторической аналитики.                      |
| M23–M30                               | №031/038/040/055                    | Сохранность/архив/retention как условные вложенные задачи; удаление только с разрешения.  |
| M31–M35                               | №011–020/025/029/047/053/054        | Надёжный цикл, quota manager, согласия, понятность рекомендаций.                          |
| M36–M40                               | №057–060                            | Безопасное внедрение и финальная приёмка; не отдельная программа.                         |
| docs/director-acceptance-test-plan.md | №020/030/040/050/056–059            | Критерии тестирования без новых автономных планов.                                        |

# 6. Минимальная карточка исполняемой задачи (предлагаемая запись в MASTER_PLAN)

№035.1 \[M02; Issue \#68; PR \#67/#69/#70\] — Проверить полноту и стоимость чтения director_runs, protected state и смежных коллекций. Статус: ЧАСТИЧНО. Зависимости: №031 (схемы), №009 (семантика ТЗ); для offline-проверки live Supabase не нужен. Действия: сопоставить main и диффы PR; провести mock-тест на длинных JSON, legacy project-id и частичные ошибки; выявить угрозу потери согласий; замерить byte/RSS в допустимой среде. Приёмка: нет неограниченного чтения на маршруте рабочего контекста; невозможна тихая потеря защищённого состояния; тесты и результаты привязаны к SHA. Если HTTP 402 препятствует live-проверке — зарегистрировать №035.1.1 \[№055.SB-402\], проверить доступность данных без платного обхода; после разрешения вернуться к №035.1. Никакой merge PR без отдельного решения.

# 7. Зависимости и блокировки: выбор следующего действия

Первый конкретный пункт после утверждения: №009.1 — закрыть строго недостающую трассировку обязательных критериев ТЗ (§18–19) на базе существующих матриц, не перезапуская инвентаризацию. Следом №010.1 — собрать проверяемые критерии приёмки по имеющемуся test plan, затем №035.1 (protected memory и bounded reads). Одновременно никаких независимых веток работ. Причина такого начала: недоказанная семантика защищённой памяти в PR \#67/#69 не позволяет безопасно принять предложенные исправления; источник ТЗ и матрица уже существуют, требуется адресное завершение, а не новый аудит.

Отдельный общий блокер SB-402: сначала актуальность ошибки и её влияние на чтение/запись, затем действия в пределах бесплатной квоты; не считать 402 доказанным актуальным прямо сейчас. OOM: ранее были реальные убийства по 512 MiB, но последующий shutdown не доказан OOM; не делать автоматический rollback. Автономность: PR \#73 меняет смысл флага; конфликт требований выносится в решение владельца, а не снимается скрытым включением/выключением.

# 8. Конкретные PR и правила их принятия

- PR \#66 — MERGED: сокращение страниц, но не доказано лечение OOM.

- PR \#70 — MERGED 22.11: целевые чтения двух API, сохраняются дополнительные полнотные и runtime-проверки.

- PR \#67 — OPEN DRAFT: fail-closed при ошибках protected memory; тесты в описании не подтверждены.

- PR \#69 — OPEN DRAFT: opt-in bounded run references; пределы гипотетические, нет production замера.

- PR \#71 — OPEN DRAFT: схема идемпотентного поиска, без разрешённой миграции.

- PR \#72 — OPEN DRAFT: тестовая PostgreSQL-фикстура; зависит от PR \#71, не направлен прямо в main.

- PR \#73 — OPEN: условный autonomous worker; конфликт с утверждённой автономностью требует явного решения.

- PR \#65 — OPEN: ограничение аналитического рабочего набора, возможная потеря полноты исторической оценки; обязательна проверка паритета.

# 9. Неизменные запреты и подтверждение перед внесением правок

До согласования: не менять ни один GitHub-файл, ветку, PR, код, настройки, данные, тариф; не делать реальные YouTube-вызовы и тяжёлые тесты. После согласования — редактировать только существующий MASTER_PLAN, не удалять другие исторические документы. Подзадачи не увеличивают 60 верхнеуровневых пунктов; их статус считается отдельно. Любая новая реализация — после проверки входящих зависимостей, отсутствия дубликата и прав владельца.

# 10. Источники для сверки

- https://github.com/peonyrhodo-bit/youtube-mcp/blob/project-management/director-audit-2026-11-19/management/MASTER_PLAN.md

- https://github.com/peonyrhodo-bit/youtube-mcp/blob/project-management/director-audit-2026-11-19/management/OOM_RECOVERY_PLAN.md

- https://github.com/peonyrhodo-bit/youtube-mcp/blob/project-management/director-audit-2026-11-19/management/MEMORY_INTELLIGENCE_2_PLAN.md

- https://github.com/peonyrhodo-bit/site-insight-engine/blob/main/docs/director-acceptance-test-plan.md

- https://github.com/peonyrhodo-bit/site-insight-engine/issues/68

- https://github.com/peonyrhodo-bit/site-insight-engine/pull/70

- https://github.com/peonyrhodo-bit/site-insight-engine/pull/67

- https://github.com/peonyrhodo-bit/site-insight-engine/pull/69

- https://github.com/peonyrhodo-bit/site-insight-engine/pull/71

- https://github.com/peonyrhodo-bit/site-insight-engine/pull/72

- https://github.com/peonyrhodo-bit/site-insight-engine/pull/73

Граница анализа: это конкретный проект обновления, а не утверждение, что каждая функция и каждый исторический пункт полностью проверены. При фактическом обновлении MASTER_PLAN нужно заполнить карточки по всем 60 пунктам, сохраняя непроверенные статусы честно; история 19 ноября не доказывает состояние Render/Supabase 22 ноября.

</details>

## K. Исторические свидетельства №001–008 (не повторять уже выполненную работу)

## Журнал текущего положения

- **№001 — завершён (2026-11-19):** четыре исходных документа и их Git blob SHA проверены в GitHub; приоритет и запреты зафиксированы в `management/REQUIREMENTS_SOURCES_AND_CHANGE_GATES.md`. Сами ТЗ не изменены.
- **№002 — завершён (2026-11-19):** GitHub подтвердил три проектных репозитория, default branch `main`, видимость и архивность; свидетельства в `management/GITHUB_REPOSITORY_INVENTORY.md`.
- **№005 — завершён (2026-11-19):** Supabase подтвердил проект `site-insight-memory`, 19 таблиц `public`, состав полей, RLS-флаги и отсутствие FK; подробности и границы в `management/SUPABASE_STORAGE_MAP.md`.
- **№006 — заблокирован (2026-11-19):** адреса трёх сервисов, Director → Supabase и Director → MCP подтверждены; связь orchestrator → Director остаётся без runtime-свидетельства. Для закрытия нужен безопасный диагностический GET `/status` или эквивалентный уже существующий лог; бесплатные сервисы специально не будить. Доказательства: `management/SERVICE_NETWORK_MAP.md`.
- **№007 — завершён (2026-11-19):** Render подтвердил три привязки к `main`, включённый автодеплой по коммиту и live SHA каждого сервиса. Доказательства: `management/DEPLOYMENT_VERSION_AUDIT.md`.
- **№008 — приостановлен:** приоритет отдан OOM-инциденту; отдельный восьмиэтапный план `management/OOM_RECOVERY_PLAN.md` с контролем разрешений и возвратом к №006/№008.
- **№003 — завершён:** 2026-11-19 Render API подтвердил три основных сервиса: `ai-youtube-system`, `site-insight-engine`, `youtube-mcp`. Все три привязаны к ветке `main`.
- **№004 — завершён:** 2026-11-19 повторная инвентаризация Render API показала только эти три сервиса; `site-insight-engine-pr21-isolated` отсутствует.
- Остальные пункты не считать завершёнными без отдельных доказательств.

## Как фиксировать препятствия

Для заблокированного пункта добавлять под ним: `Блокировка: причина; что проверено; что нужно; дата; ответственный`. Не переносить пункт в «готово», пока не проверен результат.

## Связанный подплан Memory & Intelligence 2.0 (2026-11-19)

Создан `management/MEMORY_INTELLIGENCE_2_PLAN.md` — **40 контрольных пунктов M01–M40, 0/40 доказательно закрыто**, архитектура `management/MEMORY_INTELLIGENCE_2_DESIGN.md`. Подплан подчинён согласованному `тз директор 3,0`, связан с основными №009–010, №011–050 и №056–059; **не заменяет** их и не увеличивает показатель 6/60. Приоритет M01: полная трассировка требований ТЗ; затем M02–M04: карта вызовов, квоты Supabase, профили RAM. Отдельные ворота: без явного разрешения нельзя удалять/мигрировать production-данные, менять сервисы, тратить квоты или внедрять платные зависимости. OOM-07 остаётся открытым параллельно.


## L. Контроль полноты переноса и кандидаты на последующее удаление

| Источник | Охват в этом файле | Состояние исходного файла |
|---|---|---|
| `management/OOM_RECOVERY_PLAN.md` (project-management/director-audit-2026-11-19) | Раздел B: полный текст, ID, критерии и результаты | Сохранён до отдельного разрешения |
| `management/MEMORY_INTELLIGENCE_2_PLAN.md` (project-management/director-audit-2026-11-19) | Раздел C: полный текст, ID, критерии и результаты | Сохранён до отдельного разрешения |
| `management/BACKLOG.md` (project-management/director-audit-2026-11-19) | Раздел D: полный текст, ID, критерии и результаты | Сохранён до отдельного разрешения |
| `management/PROJECT_UNIFIED_PLAN_REVIEW_2026-11-22.md` (project-management/director-audit-2026-11-19) | Раздел J: полный текст, ID, критерии и результаты | Сохранён до отдельного разрешения |
| `management/CODEX_TASK_ACTIVE_RUN_LOOKUP.md` (project-management/director-audit-2026-11-19) | Раздел E: полный текст, ID, критерии и результаты | Сохранён до отдельного разрешения |
| `management/CODEX_TASK_RESEARCH_SET_CONTEXT_MEMORY.md` (project-management/director-audit-2026-11-19) | Раздел F: полный текст, ID, критерии и результаты | Сохранён до отдельного разрешения |
| `план восстановления работоспособности директора 3,0` (docs/plan-director-functional-recovery) | Раздел G: полный текст, ID, критерии и результаты | Сохранён до отдельного разрешения |
| `НОВЫЙ ФАЙЛ ПРОВЕРКИ` (docs/decompose-new-verification-plan) | Раздел G.1: полный текст, ID, критерии и результаты | Сохранён до отдельного разрешения |
| `план проверки тз директор 3,0` (docs/plan-director-functional-recovery) | Раздел H: полный текст, ID, критерии и результаты | Сохранён до отдельного разрешения |
| `docs/director-acceptance-test-plan.md` (main) | Раздел I: полный текст, ID, критерии и результаты | Сохранён до отдельного разрешения |
| `management/MASTER_PLAN.md` (историческая ветка) | Раздел A и K: №001–060 и журнал | Сохранён в истории Git |

**Другие конкурирующие документы/ветки:** открытый PR #10 `docs/plan-director-functional-recovery`; PR #19 `project-management/director-audit-2026-11-19`; ветки `docs/director-3-audit-check-plan`, `docs/decompose-new-verification-plan`, `audit-plan-decomposition`, `docs/audit-plan-priority-order`, `docs/director-3-audit-plan-coverage-review`. Не объединять их как новые активные планы; при согласовании удаления отдельно решить судьбу старых файлов/PR/веток, не удаляя исходные ТЗ, эталонные карты, дерево и доказательства.

**Технические документы, которые сохраняются как доказательства, не планы:** `management/MEMORY_2_TZ_TRACEABILITY.md`, `MEMORY_2_ACCESS_MAP.md`, `MEMORY_2_BOUNDED_CONTEXT_CONTRACT.md`, `MEMORY_2_IMPLEMENTATION_BLUEPRINT.md`, `MEMORY_2_OFFLINE_TEST_SPEC.md`, `REQUIREMENTS_MATRIX.md`, `IMPLEMENTATION_TRACE.md`, `STATE.md`, `DECISIONS.md`, `SERVICE_NETWORK_MAP.md`, `SUPABASE_STORAGE_MAP.md`, инциденты и журналы Render. Не удалять доказательства.

**Доказательная граница:** перенос текстов и критериев проверен; статусы runtime после 19–22 ноября не перепроверялись. Дубли исходных формулировок внутри одного файла оставлены для исключения потерь; это **не** несколько независимых планов. При работе исполнитель отмечает базовый пункт и связанные вложенные задачи, не создавая новых рабочих файлов.
