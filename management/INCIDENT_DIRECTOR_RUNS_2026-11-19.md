# Инцидент: циклы Директора не достигают успешного завершения

Дата расследования: 2026-11-19. **Статус: подтверждён сбой; единая первопричина не установлена.** Связанные пункты плана: №012, №014, №015, №017, №018, №048, №050.

## Ожидаемое поведение

По ТЗ §6, §12 и §19 Директор регулярно выполняет циклы, сохраняет результат, восстанавливается после ошибок, а рекомендации доступны на сайте. Успех проверяется по конечному результату, не по наличию кода.

## Фактические доказательства

1. Read-only SQL к `public.director_runs` в Supabase `oxbxnswywgpdlcfltmbq` показал **151 запись**: `failed=124`, `partial=25`, `running=1`, `status IS NULL=1`. Статуса `completed` в выборке нет. Это исторический срез, не доказательство отсутствия иных таблиц/результатов.
2. Последние записи: id 214–209, 207–204 — `failed`, `current_step=stale_timeout`; сообщения о превышении 1800 секунд без heartbeat. id 208 — `failed`, `current_step=director_cycle`, `ReadError: [Errno 11] Resource temporarily unavailable`. id 215 — `running` с 2026-11-19 13:57 UTC; проверить, не устарел ли статус.
3. Render `site-insight-engine` 2026-11-19 13:57:05 UTC: GET `/rest/v1/director_runs?select=*&order=created_at.desc,id.desc&offset=0&limit=1000` вернул HTTP 500, PostgreSQL code `57014`, `canceling statement due to statement timeout`. Далее `memory.director_adapter.MemoryTableReadError` и `Autonomous wakeup failed`. Следующая попытка чтения в 13:57:20 UTC вернула HTTP 200. Следовательно, наблюдаемая ошибка чтения не была постоянной.
4. Render `youtube-mcp` 13:58:43, 13:58:49, 13:58:54, 13:59:01 UTC: `search.list attempted=1 succeeded=0 error=UnicodeEncodeError`; источник этих запросов не подтверждён. Отдельно 13:59:07 `anyio.ClosedResourceError` в SSE writer. Не считать эти ошибки единой причиной без трассировки.

## Подтверждено и неизвестно

- **Подтверждено:** SQL timeout способен прервать конкретное автономное пробуждение; ряд циклов завершается `stale_timeout`; поисковые запросы MCP терпят `UnicodeEncodeError`.
- **Не подтверждено:** что именно SQL timeout вызывает все 124 отказа; почему heartbeat прекращается; что MCP ошибки вызваны именно Директором; существуют ли рекомендации в иной таблице; какой триггер запуска является основным.
- **Безопасный следующий шаг:** исследовать `memory/director_adapter.py:create_run`, механизм heartbeat, объём и индексирование запросов; проверить имена таблиц рекомендаций и реальные строки; сопоставить временные метки логов и циклов. Не запускать YouTube API, не менять БД/продакшн.

## Запрос к Codex (после установления причины)

Создать узкий PR с воспроизводимым регрессионным тестом подтверждённого дефекта и минимальным исправлением. Не менять канонические ТЗ, не включать платные ресурсы, не запускать живой YouTube-поиск. Считать работу завершённой только после CI и проверки ожидаемого результата.

## Уточнение по исходному коду (следующий проход)

- `site-insight-engine/memory/director_adapter.py:create_run` (строки ~710–800): перед созданием нового цикла загружает **все** записи запусков через `_recent_for_project(... limit=None, project_id=..., order_key="created_at")` и только после загрузки ищет активные записи. Для устаревших активных записей выставляет `failed/stale_timeout` при возрасте более 1800 секунд. Это подтверждает механизм возникновения наблюдаемых статусов, **но не объясняет, почему heartbeat перестаёт обновляться**.
- `site-insight-engine/memory/supabase.py:_recent_for_project` (строки ~204–267): использует `select("*")`, сортировку `created_at DESC, id DESC`, страницы по 1000 записей и **фильтрует project_id в Python после загрузки**. Таким образом, каждый запуск читает больше данных, чем требуется для проверки активных циклов. Именно такой URL с `limit=1000` и `select=*` виден в логе SQL timeout. **Совпадение кода и запроса подтверждено**, но доказательства, что именно неоптимальная форма запроса является единственной причиной тайм-аута, пока нет (нужны EXPLAIN/индексы/нагрузка).
- `site-insight-engine/server.py:_director_run_heartbeat` (строки ~2692–2710): фоновая задача пытается обновлять запись примерно каждые 60 секунд и при ошибке пишет лог, продолжая попытки. Запускается в `_execute_autonomous_cycle_locked` после `create_run`. Следовательно, падение `create_run` происходит **до запуска heartbeat нового цикла**.
- **Потенциальный узкий кандидат на исправление для Codex:** отдельный индексируемый запрос только к активным запускам проекта с необходимыми полями и безопасной поддержкой legacy-строк, вместо полного сканирования. Не реализовывать без теста на сохранение защиты от параллельных циклов и без проверки схемы БД.

## Дополнительная проверка heartbeat (2026-11-19)

1. В `server.py:_execute_autonomous_cycle_locked` после `create_run` создаётся `heartbeat_task`. Затем цикл ожидает `director.run_autonomous_cycle`. В `finally` задача heartbeat отменяется. При успешном возврате директорского цикла код сначала сохраняет результат, решение, рекомендацию (если есть), событие, затем присваивает финальный статус `succeeded/failed/partial/blocked/skipped`. Значит `running` не является подтверждением результата.
2. Read-only SQL: у run 215 `started_at=13:57:15Z`, `updated_at=13:58:26Z`, `status=running`, `current_step=director_cycle`, `finished_at=NULL`. Для run 214, 213, 212, 211 последние heartbeat были примерно через минуту после начала, затем записи переведены в `stale_timeout` спустя ~30 минут. Снимок сделан после событий; актуальное состояние нужно перепроверять при следующем аудите.
3. Render по точному фильтру `Director run heartbeat failed` за 09:00–14:20 UTC дал **одно** событие для `run_id=206` в 09:37:44 UTC. Это доказывает минимум одну ошибку фонового обновления, но не объясняет остальные прерывания: отсутствие такого лога не доказывает успешность heartbeat.
4. В том же окне Render показал 28 сообщений `Autonomous wakeup failed` (scheduled/retry). Это наблюдаемые отказы пробуждения, не 28 доказанных независимых первопричин.
5. Отдельно нужно проверить причину блокировки event loop/срок жизни процесса и получить полный traceback heartbeat run 206, затем сопоставить с прекращением `updated_at`. Не считать причиной только сон Render.

## Уточнение первопричины конкретного heartbeat-сбоя (run 206)

По полному фрагменту Render traceback около **2026-11-19 09:37:44 UTC**:

- `server.py:_director_run_heartbeat` строка 2700 вызывает `runtime.memory.update_run`.
- В цепочке синхронного HTTP/2-клиента `httpcore` возникает **`httpcore.ReadError: [Errno 11] Resource temporarily unavailable`** во время `network_stream.read`; запрос `GET /rest/v1/director_runs?select=data_json&id=eq.206&limit=1` непосредственно перед этим получил HTTP 200, поэтому нужно отдельно проверить следующий HTTP-запрос/операцию и не приписывать ошибку самому успешному GET.
- В том же коротком окне обнаружен `memory.read_status.MemoryReadError: Memory context read partial: runs` в `memory/director_adapter.py:get_context`, а также ошибка ASGI. Это подтверждает **транспортные ошибки чтения и частичные данные памяти** в момент сбоя, но не доказывает, что все случаи `stale_timeout` имеют тот же источник.
- Следующая задача: изолировать цепочку `update_run -> backend.update_run`, выяснить повторное чтение `data_json` перед PATCH, проверить поведение при временном `httpx.ReadError`, не ослабляя гарантий сохранения и защиты от дублирования. Не лечить проблему простым игнорированием исключения.

## Последующий снимок run 215/216 и временной порядок (2026-11-19)

Read-only Supabase SQL показал:

| Run | status | started_at UTC | updated_at UTC | finished_at UTC | step |
|---|---|---|---|---|---|
| 215 | failed | 13:57:15.596618 | 14:32:15.016398 | 14:32:15.016387 | stale_timeout |
| 216 | running | 14:32:07.085076 | 14:33:16.926171 | NULL | director_cycle |

Для 215 диагностическая строка указывает **последнее фактическое обновление 13:58:26.023374 UTC**, `age=2021s`. Важно: `started_at` 216 на 7.93 секунд раньше `finished_at` 215. Это **не является доказательством двух одновременно исполнявшихся циклов**: `create_run` вычисляет времена и выполняет очистку старой строки до вставки новой, а сохранённое `started_at` не обязательно равно моменту SQL INSERT. Код `memory/director_adapter.py:create_run` проверяет `updated_at`, переводит устаревший run в failed через `update_run`, затем делает `save_run` под защитой уникального частичного индекса. Нужны точные INSERT/PATCH-времена и трассировка процесса, прежде чем утверждать гонку.

**Наблюдение:** как минимум два последовательных цикла (215 и предшествующие) заканчиваются по тайм-ауту, а не штатным результатом; 216 на момент снимка оставался running. Повторять запрос позднее, не считать статус running успехом.

## Новый диагностический сигнал: запуск процесса Render (2026-11-19)

- В логах `site-insight-engine` за 14:33–14:35 UTC видны `DIRECTOR PROJECT ASSESSMENT` (14:33:57), `DIRECTOR WORK PLAN` (14:33:58), успешный GET `director_runs` (14:34:05), успешный POST к OpenRouter (14:34:06). Это доказывает, что цикл/связанные операции работали после последнего `updated_at` run 216 (14:33:16), но сами логи без correlation id **не связывают каждую операцию однозначно с run 216**.
- **14:35:24 UTC** Render зафиксировал `Started server process [40]`, `Starting site-insight-engine`, `Autonomous wakeup worker started: poll=5s interval=3600s`, `Application startup complete`. Это подтверждённый старт нового серверного процесса и фонового worker.
- В узком окне 14:34:45–14:35:50 UTC не найдено явного `Shutting down` или сообщения об остановке старого процесса. Поэтому **не установлено**, был ли это рестарт, масштабирование, замена инстанса или другая причина. Также пока не доказано, что процесс был завершён именно во время run 216.
- Гипотеза для следующей проверки: перезапуски/замены процессов могут отменять in-process heartbeat и циклы без терминальной записи в БД. Проверить Render events/deploy history и start/shutdown лог в другие интервалы, затем сопоставить с `stale_timeout` по run_id.

## ПОДТВЕРЖДЕНО: массовые OOM-kill на Render (2026-11-19)

**Источник:** Render `list_events`, service `srv-dae6fi61egvs73b4pa90`, интервал 09:00–14:40 UTC. Многочисленные события `server_failed` имеют `details.reason.oomKilled.memoryLimit='512Mi'`, `evicted=false`. События `server_available` подтверждают циклы восстановления.

Проверенные примеры (UTC):

| server_failed, oomKilled | server_available после сбоя |
|---|---|
| 13:22:35 | 13:23:02 |
| 13:55:05 | 13:57:03 |
| 14:31:05 | 14:32:08 |
| 14:34:09 | 14:35:28 |
| 14:38:15 | не проверено в выбранном окне |

**Вывод:** принудительное завершение процесса по памяти является доказанной причиной прерывания работы сервиса и может объяснять потерю in-process heartbeat, последующие `stale_timeout` и появление нового процесса в 14:35:24. Для конкретного run_id причинную связь следует устанавливать по интервалу жизни процесса и correlation ID. Предыдущая формулировка «рестарт/масштабирование/замена не установлены» уточняется: Render прямо сообщает OOM-kill для ряда инстансов.

**Приоритет P0 (без затрат):** исследовать пиковую память загрузки истории и контекста, многократные `select('*')`/пагинацию, число параллельных циклов и удерживаемые структуры. Подготовить профилирование на синтетических данных с лимитом 512 MiB, измерение RSS по фазам и bounded-loading/streaming. Не предлагать переход на платный тариф как обязательное решение. До разрешения — только read-only аудит и задания на тесты.

**Отдельные подтверждённые проблемы:** `httpcore.ReadError` в heartbeat run 206 и `57014 statement timeout` на запросе `director_runs`. Нельзя сводить их к OOM без дополнительных доказательств.

## Привязка к production-деплою (2026-11-19)

Render `list_deploys` для `site-insight-engine`: последний deploy со статусом `live` — `dep-dbsa40v4bgms73fng8ug`, commit `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc` ("Offload constraint persistence from event loop"), `finishedAt=2026-11-14T18:03:10.818637Z`. В первой странице из 15 деплоев более поздних деплоев нет. Render `list_events` за 19 ноября показывает `oomKilled.memoryLimit=512Mi` и в 14:42:35, 14:44:40 UTC.

**Классификация:** эти OOM-события произошли спустя ~5 суток после последнего показанного успешного деплоя, поэтому их нельзя считать дефектами более раннего релиза, уже устранёнными последующим деплоем. При этом не доказано, что на момент любого будущего аудита проблема сохраняется; требуется свежий снимок events и сравнение с текущим deploy. Операционные события не тождественны code regression.

## Первичный аудит памяти на ТОЧНОМ deployed commit f95bc0e (2026-11-19)

Прочитан `peonyrhodo-bit/site-insight-engine` именно с ref `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc`, а не произвольный HEAD.

- `memory/supabase.py:204–264`: `_recent_for_project` делает `select('*')` страницами до 1000 строк, фильтрует legacy `project_id` в Python, накапливает выбранные строки в `rows`. При `limit=None` удерживает **всю историю** таблицы, при `limit=N` удерживает N строк (но может прочесть больше из-за фильтрации). Временная память страницы и декодированного ответа дополнительно увеличивает RSS.
- `memory/director_adapter.py:710–738`: `create_run` вызывает `_recent_for_project(TABLE_RUNS,limit=None,...)` или `get_recent_runs(limit=100000,...)` для active-run guard.
- `server.py:2386–2402`: `_find_completed_idempotent_run` также вызывает `_recent_for_project(TABLE_RUNS,limit=None,...)` для idempotency lookup. Это **второй независимый путь** безграничного чтения истории.
- `memory/supabase.py:1005–1052`: загрузка opportunity history ограничена конфигурацией (channels 500, snapshots 500, niches 250, niche snapshots 500, с максимальными лимитами 2000/5000/1000/5000). Это существенно отличается от безграничного чтения runs; нельзя утверждать, что именно этот участок вызвал OOM без измерений.
- `memory/supabase.py:1132+`: `get_context` использует ограниченные значения по умолчанию (runs 10, decisions 20, events 30 и др.).

**Доказано по коду:** два пути unbounded run-history scan, большие page payloads и дополнительные bounded history buffers. **НЕ доказано:** что они являются непосредственной причиной OOM; всего в runs на снимке было ~152 записи, что само по себе недостаточно для вывода о 512MiB RSS. Следующее действие — анализ размеров `data_json` и агрегатов, логов `peak_rss_raw`, а также жизненного цикла больших результатов/LLM контекста. Никаких code patches до проверки.

## Фактические размеры director_runs JSON (read-only SQL, 2026-11-19)

`SELECT count(*), sum(pg_column_size(data_json)), max(...), avg(...), percentile_cont(0.95) ... FROM public.director_runs`:
- 152 строки; сумма `pg_column_size(data_json)` ~10 MB; максимум 2,419,593 байт; среднее 70,399 байт; p95 = 2,630 байт.
- Наибольшие строки, `pg_column_size` / `octet_length(data_json::text)`: id43 (2,419,593 / 7,471,972), id77 (2,373,980 / 7,327,691), id45 (2,337,021 / 7,214,609), id79 (2,336,837 / 7,213,866), id33 (1,068,232 / 3,304,350). Все они исторические `partial` или NULL status.

Интерпретация: `pg_column_size` характеризует серверное хранение (возможно с компрессией), `octet_length(data_json::text)` — объём текстового представления, ближе к JSON-трафику, но не к реальному RSS Python. Полная история содержит несколько многомегабайтных документов; `select('*')` может приводить к крупному HTTP payload и нескольким копиям в памяти. **Причинность OOM не установлена.** Следующий шаг: измерить размер ответа и peak RSS для конкретных фаз на deployed commit, проверить не загружаются ли крупные документы многократно.

## Измеренная память процесса на Render — важное подтверждение (2026-11-19)

Render app logs `srv-dae6fi61egvs73b4pa90`, интервал 14:30–14:38 UTC, поиск `peak_rss_raw`:

| UTC | Этап | peak_rss_raw | Linux MiB | elapsed |
|---|---|---:|---:|---:|
| 14:33:22.426 | `SUPABASE FULL HISTORY ANALYTICS COMPLETE` (1203 videos, 12483 snapshots, 6000 working snapshots) | 418056 | 408.26 | 45.507s |
| 14:33:25.547 | `SUPABASE OPPORTUNITY DATA LOADED` (500 channels, 16 niches, 262 niche snapshots) | 418056 | 408.26 | 2.827s |
| 14:33:55.606 | `SUPABASE RESEARCH HISTORY SCANNED` (330 queries, 68 research_sets, 30478 relations) | 458028 | 447.29 | 30.057s |

В точном deployed commit `f95bc0e`, `memory/supabase.py:30–39` функция `_peak_rss_raw` возвращает `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`. На Linux `ru_maxrss` — peak resident set size в KiB. Последний пик 447.29 MiB = ~87.4% от Render 512 MiB; между замерами рост исторического пика 39.04 MiB. Показатель **накопительный**, не показывает текущий RSS или точную аллокацию этапа; при параллельных задачах нельзя приписывать рост только сканированию research.

Независимое Render event `server_failed` с `oomKilled.memoryLimit=512Mi` в 14:34:09 UTC (после этих замеров) усиливает причинную связь общего превышения памяти с завершением процесса. Но какой именно объект/фаза довели память до лимита между 14:33:55 и 14:34:09 — пока неизвестно. Предпочтительное следующее действие: собрать последующие логи в 14:33:55–14:34:09 и изучить память/структуры research и LLM context, без продакшен-тестов и расходов.

## Точная последовательность за 15 секунд до OOM (Render app logs, 14:33:54–14:34:10 UTC)

- 14:33:55.940 `DIRECTOR MEMORY phase=project_data_loaded`: `vmhwm_mb=449.8, vmrss_mb=449.8`, youtube=1203, relations=5000, research_sets=68.
- 14:33:56.119 `observations_built`: `vmhwm_mb=450.8, vmrss_mb=450.8`, observations=1203.
- 14:33:57.132 `inspect` завершён, `understand` стартовал; 14:33:57.221 `assess` стартовал.
- 14:33:58.719 `analytics_start`: `vmhwm_mb=491.7, vmrss_mb=441.3` — к этому моменту был временный пик 491.7 MB.
- 14:34:00.227 `analytics_basic_complete`: `vmhwm_mb=491.7, vmrss_mb=444.0`.
- 14:34:01.626 `analytics_complete`: `vmhwm_mb=491.7, vmrss_mb=448.9`.
- 14:34:01.719 `_autonomy_analyze` завершён; `_autonomy_decide` стартовал.
- 14:34:03.329 GET `/director-debug` 200.
- 14:34:05.560 GET Supabase `director_runs?select=*&order=created_at.desc,id.desc&offset=0&limit=1000` 200 (unbounded history scan).
- 14:34:06.715 POST OpenRouter `/chat/completions` 200.
- 14:34:09.0 Render `server_failed` `oomKilled.memoryLimit=512Mi`.

**Вывод:** перед OOM накопленный пик процесса ~491.7 MB, а последняя подтверждённая стадия — `decide`, с одновременной загрузкой истории запусков и вызовом LLM. Точная аллокация, превысившая лимит, неизвестна; нельзя утверждать, что OpenRouter или history scan по отдельности являются доказанной первопричиной. Показания `vmhwm_mb` и `vmrss_mb` — разные метрики (исторический пик и текущая резидентная память). Проверить код `_process_memory_mb` для точной единицы MB перед арифметическим сравнением с MiB.

## Разбор decide на deployed commit f95bc0e

- `server.py:49–62`: `_process_memory_mb()` читает `VmRSS`/`VmHWM` из `/proc/self/status`, делит KiB на 1024. Значения в логах — **MiB**, несмотря на суффикс `_mb`. Следовательно, `491.7` означает **491.7 MiB**, запас до лимита 512 MiB ~20.3 MiB.
- `director/director.py:2650+`: `_autonomy_decide` вызывает `self.decide(analysis)`.
- `director/director.py:1432–1527`: `decide` делает `opportunities=list(analysis.get(...))`, затем `all_opportunities=list(opportunities)`, затем новый список после фильтрации; при наличии AI вызывает `_enrich_decision_with_ai(decision,analysis)`. Это **несколько списков ссылок**, но не копии всех вложенных JSON; сами по себе не доказывают большой расход.
- `director/director.py:1585–1635`: `_enrich_decision_with_ai` формирует `ai_context=self.to_ai_decision_dict()` и отправляет ограниченное представление анализа (topics, analytics, opportunities, signal interpretation, hypothesis) в `generate_decision`, при этом полный `analysis` остаётся в памяти. Требуется проверить реальный размер `to_ai_decision_dict` и сериализацию/логирование в AI client.
- GET `director_runs?select=*` в 14:34:05 произошёл **во время decide**, но код `_find_completed_idempotent_run` относится к отдельному пути обработки idempotent request и не доказано, что этот конкретный GET вызван им. Не связывать без call stack.

**Новая гипотеза:** кратковременный пик может быть связан с одновременным удержанием аналитики и формированием AI-контекста/сериализацией. **Не доказано:** вклад LLM и источник GET history; нужна проверка размера bounded AI context, текущего RSS вокруг `generate_decision`, без дорогих вызовов API.

## Проверка ограничений AI payload на deployed commit f95bc0e

- `director/director.py:280–329`: `_bound_ai_value` рекурсивно ограничивает вложенность `max_depth=5`, количество элементов на каждом уровне `max_items=30`, строки `max_string_chars=4000`.
- `director/director.py:330–386`: `to_ai_decision_dict` ограничивает top-level списки (observations 8, opportunities 20, research_history 10 и т.д.) и применяет рекурсивную границу также к analytics/topics/metadata. Это не безграничная сериализация всей истории.
- `director/director.py:1585–1620`: `_enrich_decision_with_ai` создаёт bounded `ai_context` и сохраняет full `analysis` в локальном контексте.
- `server.py:1614–1655`: `generate_decision` вызывает `build_decision_prompt` и `provider.generate_json`.
- `ai/prompts.py:448–479`: `_serialize_context` делает `json.dumps` и `serialized.encode('utf-8')`, лимит по умолчанию 1,500,000 байт, переменная `DIRECTOR_AI_CONTEXT_MAX_BYTES`, clamp 64,000–4,000,000; превышение вызывает `ValueError` до provider call. Дополнительные кратковременные копии строк/bytes возможны, но размер именно контекста ограничен.

**Классификация:** гипотеза «в AI уходит неограниченная история» опровергнута кодом. Причинность AI-подготовки для OOM не установлена. Следующий приоритет — фактическая память полных analytics/results и удержание структур между фазами, а также идентификация источника `director_runs?select=*` при `decide`.

## Удержание данных в реестрах при загрузке (deployed f95bc0e)

`server.py:1090–1248` (`DataAdapter`): при первой загрузке project ID YouTube loader возвращает dict; код извлекает history_analytics, очищает live registry, поочерёдно переносит queries/videos/snapshots через `pop` и `add_*`, затем `del persisted`. Это **существующая защита** от одновременного удержания двух полных наборов; не считать её отсутствующей.

В отличие от YouTube loader, `load_opportunity_data` возвращает `persisted_opportunity`, из которого извлекается history_analytics, затем `OpportunityDataRegistry.from_dict(persisted_opportunity)` создаёт registry; явного `del persisted_opportunity` сразу после вызова нет. Research loader получает `persisted_research`, затем переносит 330 queries, 68 research sets, 30478 relations в live registries через `from_dict`/`add_relation`; временные dicts и registry могут сосуществовать до выхода из области видимости функции. Из логов на 14:33:55: 30478 relations scanned, но `project_data_loaded` показывает 5000 live relations — требуется изучить limit и структуру промежуточного агрегата до вывода о дублировании.

**Доказано:** отличающиеся стратегии переноса и жизненного цикла временных контейнеров; полноценное исследование пика требует проследить ссылки/освобождение объектов, размеры relation records и рабочие лимиты. **Не доказано:** что отсутствие `del` создаёт долговременную утечку или OOM; локальные переменные освобождаются после возврата, а registry может разделять вложенные объекты.

## Research relations: 30478 scanned vs 5000 working — code verified

Deployed `site-insight-engine` commit `f95bc0e`, `memory/supabase.py:856–878`: `load_research_data` requests working windows `queries=2000`, `research_sets=1000`, `relations=5000` via `_recent_for_project`; separately `_summarize_project_table` scans entire history to produce counters for all three tables. Thus log `SUPABASE RESEARCH HISTORY SCANNED ... relations=30478` reports `matched_rows` for historical summary, whereas `project_data_loaded relations=5000` reports bounded working registry. **Not evidence of data loss.**

`memory/supabase.py:204–264` `_recent_for_project` requests `select('*')` in pages of 1000 rows, sorts descending by id for relations, and filters project IDs client-side for legacy `data_json` compatibility; can fetch more data than needed, particularly if project rows are sparse. `_summarize_project_table` (`memory/supabase.py:797–851`) iterates pages of 500 and retains bounded counters rather than entire history. Its full-table `select('*')` page still incurs network/JSON parsing cost for columns not needed by counters. This is a **verified efficiency opportunity**, not yet proven primary OOM trigger.

Potential follow-up task, no implementation permission: benchmark (locally with synthetic data) selecting only summary columns where compatible with legacy metadata, and preserving exact counts; inspect relation-row payload sizes, memory peaks during per-page scans. No changes to production/DB.

## Реальные размеры исследовательских таблиц — Supabase read-only SQL (2026-11-19)

Метод: `count(*)`, `sum(octet_length(row_to_json(t)::text))`, `max(...)` без выгрузки содержимого строк. Это текстовое представление JSON в PostgreSQL, **не** фактическая сеть PostgREST и **не** Python RSS.

| public table | rows | total JSON text bytes | max row JSON text bytes |
|---|---:|---:|---:|
| data_relations | 30478 | 7783443 | 269 |
| youtube_queries | 330 | 398744 | 1358 |
| research_sets | 68 | 7969895 | 132625 |

Для `research_sets`: avg 117204 B, median 120343 B, p95 129495 B, **65 из 68** строк >100000 B. Это систематически крупные записи, а не единичный выброс. Общий текстовый JSON объём трёх таблиц 16152082 B (~15.4 MiB). Учитывать, что `load_research_data` сохраняет только до 5000 из 30478 relations в working registry, но все 68 research_sets. Вопросы для следующей проверки: какие колонки/JSON-поля research_sets занимают большую часть и как `ResearchSet.from_dict` копирует их; можно ли сохранить полный evidence в БД, загружая компактное представление в рабочий реестр. Не делать вывод об OOM из одного размера строк.

## Research sets: breakdown of JSON size by column/key (Supabase read-only SQL)

All 68 `public.research_sets` rows, aggregate `octet_length(jsonb::text)`:

| Field | JSON text bytes |
|---|---:|
| metadata | 7255359 |
| metadata.research_plan | 5484208 |
| metadata.operation_results | 1768295 |
| snapshot_ids | 548094 |
| video_ids | 97547 |
| expected_data | 4692 |
| gathered_data | 4391 |
| query_ids | 7830 |
| missing_data | 431 |

The two metadata subkeys together are 7252503 bytes, ~91.0% of whole `research_sets` JSON representation (7969895 bytes), and nearly all metadata. `research_plan` max per row 91929 bytes; `operation_results` max 29756 bytes. Query returned aggregate sizes and key names, no research content.

Deployed `data/research_sets.py:751–802` `ResearchSet.from_dict` passes `metadata` through, and `__post_init__` line ~274 does `self.metadata=dict(self.metadata or {})` — **shallow copy** of outer dict, not a recursive deep copy of the two large nested payloads. The full metadata remains reachable in the live registry, so retained memory is plausible, but double deep copying is not proven. Assess whether the active Director cycle actually needs full plans and operation results in every live `ResearchSet` before proposing compact hydration. Preserve full evidence in Supabase and avoid semantic regression.

## Verified recursive materialization of research_sets in DataAdapter (deployed f95bc0e)

`server.py:1478–1491`: after restoring `ResearchSet` instances into `self.research_manager`, DataAdapter obtains `research_sets=self.research_manager.all()` and assigns `result['research_sets']=serialize(research_sets)`. `server.py:303–340`: generic `serialize` recursively builds **new dicts and lists** for nested objects, calling `ResearchSet.to_dict()` (`data/research_sets.py:719–747`) and then serializing its full `metadata` recursively. This creates a **distinct nested object graph** for the returned project data while original ResearchSet instances remain in the live registry. Contrast with shallow `metadata=dict(...)` in `ResearchSet.__post_init__`.

Since Supabase SQL found `research_sets.metadata.research_plan` 5,484,208 bytes and `operation_results` 1,768,295 bytes in textual JSON across 68 records, full recursive serialization has a meaningful *potential* transient memory cost. No direct allocation measurements; **not proof that this step caused OOM**, and Python object memory differs from JSON byte sizes. Need trace whether `result['research_sets']` is consumed or discarded by downstream Director, and whether full nested metadata is needed in the project data contract. Any fix must preserve evidence and downstream behavior; no code changes authorized.
