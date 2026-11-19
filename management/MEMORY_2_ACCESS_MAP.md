# M02 — карта обращений к памяти: проверенная часть

**Дата:** 2026-11-19. **Статус:** в работе; не полная трассировка всех трёх репозиториев. Чтение GitHub, без изменений production.

## Проверенные исходники
- `peonyrhodo-bit/site-insight-engine/memory/supabase.py` (main, 1,903 строки): `SupabaseMemoryBackend`, основные операции чтения и записи.
- `peonyrhodo-bit/site-insight-engine/director/director.py` (main, 3,075 строк): `Director`, обращение к `memory_service.get_context` через `getattr` в строке 446.
- `peonyrhodo-bit/site-insight-engine/director/autonomy.py` (main, 910 строк): автономный цикл; прямых вызовов backend в исследованных текстовых совпадениях нет, но косвенные вызовы через Director и callbacks требуют трассировки.
- Поиск имен методов через простые regex **не доказывает отсутствие** вызовов: код использует динамические обращения и посредников.

## Обнаруженные операции backend
| Метод и строки в memory/supabase.py | Данные / назначение | Риск / направление M2 |
|---|---|---|
| `_recent_for_project` 204–270 | Упорядоченное чтение истории с пагинацией, включая legacy project_id | Размер страницы уже 50 после PR #66; не считать все выборки bounded по общему объёму |
| `_iter_paginated_rows` 271–304 | Пакетное чтение таблиц | Проверить materialization и условия выхода |
| `load_youtube_data` 305–461 | Видео и снимки | Тяжёлый read path; ограничить одновременно удерживаемые данные |
| `load_youtube_analysis_data` 503–624 | Подготовка данных аналитики | Сравнить full-history KPI и streaming parity |
| `iter_video_evidence` 625–676 | `videos`, `video_snapshots`; select/eq/order/range | Проверить индекс/временные окна и границы курсора |
| `save_youtube_data` 677–808 | `videos`, `video_snapshots`; upsert/insert | Идемпотентность, timestamps, повторные замеры |
| `load_research_data` 856–879 | Исследования | Проектная изоляция, объём, свежесть |
| `save_research_data` 975–996 | Исследования, запросы, связи | Сохранение lineage и исключение семантических дублей |
| `load_opportunity_data` 997–1053 | Каналы, ниши, снимки | Ограничение объёма в RAM без утраты аналитики |
| `save_opportunity_data` 1054–1131 | Upsert каналов/ниш и снимков | Историческая полнота и консистентность |
| `get_context` 1132–1207 | Общий контекст памяти Director | Проверить какие категории и объёмы агрегируются |
| `save_run` 1208–1233 | `director_runs` insert | Надёжность checkpoint и idempotency |
| `update_run` 1234–1246 | `director_runs`: SELECT data_json → merge → PATCH row → SELECT id | На 2026-11-19 18:26 PATCH id=222 завершился 500/57014; JSON строки 472 байта, значит гипотеза огромного payload для этого случая не подтверждена |
| `get_recent_runs` 1247–1264 | История циклов | Надёжность, проектная изоляция, сохранение причин |
| Прочие методы backend | decisions, chat_messages, director_actions, director_results, system_events, recommendations, feedback, constraints | Защищённые сущности: **без автоматического TTL** |

## Технические выводы и ограничения
1. Один backend обслуживает и тяжёлые исследовательские выборки, и критически важные решения/статусы. **Не заменять весь backend одним релизом.** Сохранить API совместимости и разделить внутренние read/write/retention контуры.
2. Наличие `_iter_paginated_rows` и страницы 50 **не доказывает ограниченный пик RAM**: вызывающий код может собрать все страницы в один dict/list. Нужен call graph и профили.
3. `update_run` делает read–merge–write, но первопричина 57014 **не установлена**. Не менять семантику или DB schema без карты вызовов, конкурентных обновлений и тестов.
4. У автономного Director доступ к памяти через `memory_service.get_context`; надо проследить создание сервиса, адаптеры, callback, API entrypoints, scheduler и вызовы в других репозиториях.
5. ТЗ §17 требует разделения ответственности: memory хранит и отдаёт, аналитика считает, quota/youtube_quota.py учитывает, Director выбирает. Не дублировать эти роли при M2.

## Следующие действия до закрытия M02
- Найти композиционный root/entrypoints и вызовы всех методов backend в site-insight-engine, включая динамические обращения.
- Проследить MCP и Orchestrator: кто пишет в те же таблицы и какие API контракты используются.
- Построить граф по R01–R34 из `MEMORY_2_TZ_TRACEABILITY.md` и отметить неизученные пути.
- Сопоставить чтения с реальными размерами строк, индексами и временными диапазонами.
- **Не закрывать M02**, пока не проверены все три репозитория и важные вызовы.

## Дополнительная проверка — реальные ограничения загрузки

- `_iter_paginated_rows` (строки 271–303): `.select(columns).order(order_key).range(offset, offset+page_size-1)`, затем `yield from page`. Это **OFFSET pagination**, не cursor/keyset; `project_id` **не фильтруется на сервере** в данном helper. Сортировка только по одному полю `order_key` может быть неоднозначной при равных значениях, если нет уникального tie-breaker. Проверить уникальность каждого order_key и конкурирующие вставки, прежде чем менять.
- `load_youtube_analysis_data` (503–623): по умолчанию `DIRECTOR_ANALYSIS_PAGE_SIZE=500`, `DIRECTOR_ANALYSIS_WORKING_VIDEOS=3000`, `DIRECTOR_ANALYSIS_WORKING_SNAPSHOTS=6000`, `DIRECTOR_ANALYSIS_TOP_EVIDENCE=100`. Сканирует все страницы, подаёт записи в `StreamingYouTubeAnalytics`, **но одновременно сохраняет до 3000 видео и 6000 снимков в списках**. Поэтому утверждение «вся история целиком загружается в RAM» неверно; верно «в RAM удерживается ограниченный, но потенциально слишком крупный рабочий набор плюс аккумулятор и другие категории». Историческая аналитика считается потоково; менять выборку без теста паритета нельзя.
- В `load_youtube_analysis_data` фильтрация project_id для видео/снимков выполняется **после** получения строк, а не в запросе; для снимков без project_id явно выставляется `status=partial` и счётчик исключённых legacy записей. Улучшение серверной фильтрации требует учёта legacy и схемы, иначе возможна потеря наблюдений.
- `load_research_data` (856–878) по умолчанию удерживает до 2000 запросов, 1000 research_sets и 5000 relations, а также вычисляет summary; `load_opportunity_data` (997–1052) удерживает до 500 channels, 500 channel snapshots, 250 niches и 500 niche snapshots. Эти **несколько параллельных рабочих наборов** вероятно важнее размера страницы как гипотеза пиков RAM; подтвердить профилем.
- `get_context` (1132–1202) читает 8 коллекций отдельно (runs, decisions, recommendations, constraints, events, chat, actions, results), по умолчанию 10–30 строк; отмечает каждую `complete/partial/error` и не превращает ошибку в успешную пустую таблицу. Сохранить этот контракт при редизайне.
- `director/director.py` (436–482): `inspect` получает контекст через динамический `memory_service.get_context`, затем обрабатывает статус полноты. В `director/director.py` (587–610) также динамически вызывает `data_service.get_project_state`, поэтому следующий поиск должен учитывать *два* пути загрузки.

**Оценка:** код доказывает наличие ограниченных рабочих наборов и потокового агрегатора, но **не доказывает**, что текущие размеры подходят для 512 MiB Render. Первая безопасная цель — профилирование удерживаемых структур и server-side фильтрация/курсор при сохранении полных аналитических агрегатов. Production не изменён.

## Director context и аналитика — подтверждённая трассировка

**Исходник:** `site-insight-engine/director/director.py`, main, прочитан 2026-11-19.

1. `DirectorContext` (строки 156–174) одновременно содержит `observations`, `analytics`, `topics`, `opportunities`, `research_history`, `decisions`, `recommendations`, `feedback`, `constraints` и `metadata`. Это **долгоживущий контекст**, где могут сосуществовать разные рабочие наборы; оценить суммарный RSS и жизненный цикл каждого поля.
2. `Director.inspect` (436–633) сначала вызывает `memory_service.get_context` (449–459), затем `data_service.get_project_state` (587–595), объединяя оба результата в контекст. Это **два независимых пути загрузки**. Ветви `complete/partial/error` (473–579) различают полноценное и неполное чтение; контракт критичен для ТЗ §6.2 и должен сохраниться.
3. `_merge_context` (851–886) для list **заменяет** список, для dict создаёт `merged = dict(current)` и обновляет его; неизвестные ключи кладёт в `context.metadata`. Это shallow copy словаря, **не доказательство глубокого копирования всех объектов**. Но старые/новые ссылки и накопление metadata требуют heap profile.
4. `DirectorContext.to_analysis_dict` (179–208) специально **избегает `dataclasses.asdict`** и отдаёт read-only view со ссылками на исходные коллекции. В `Director.analyze` (1109–1138) этот view передаётся `analytics_service.analyze`. Следовательно, нельзя утверждать, что каждый аналитический вызов глубоко копирует данные; проверять реальные копии внутри конкретного сервиса.
5. `_memory_state_summary` (888–903) берёт по 5 последних записей из 8 семантических категорий; сам по себе компактный, но оригинальные коллекции остаются в контексте.
6. `DirectorContext.to_dict` (176–177) и `DirectorResult.to_dict` (232–233) используют `asdict(self)`, что может **глубоко копировать вложенные списки и словари** при вызове. Надо найти реальные call sites, размеры payload и частоту; наличие метода не означает, что он участвует в OOM.

**Гипотеза для проверки M04:** одновременное удержание рабочих наборов `data_service` + `memory_service` + `context.metadata` + сериализация `asdict` могут объяснять пик, но **причинная связь с OOM не доказана**. В M16–M22 проектировать compact view для конкретной фазы и отложенную выборку доказательств, сохраняя потоковые агрегаты и полный доступ к истории.

## M02 — дополнительные реальные call sites и риск повторной загрузки

Проверены `director/director.py` и `director/autonomy.py` в `site-insight-engine` (main).

- `Director._autonomy_research` около строк 2426–2456: при `completed/partial` research, если executor ещё не сохранил данные, вызывается `data_service.ingest_research_execution`; комментарий прямо запрещает повторное сохранение всего in-memory opportunity registry из-за риска исчерпания **512 MiB**. **После сохранения всегда вызывается `await self.inspect()`**, то есть в одном автономном цикле данные могут повторно загружаться и объединяться. Не доказано, что старые объекты при этом остаются живыми; проверить GC, ссылки, heap и peak RSS.
- `Director.inspect` вызывает оба источника `memory_service.get_context` и `data_service.get_project_state`; повторный `inspect` после research — конкретная точка измерения для M04.
- `DirectorContext.to_dict` (176–177) и `DirectorResult.to_dict` (232–233), `DirectorState/CycleEvent/DirectorCycle.to_dict` (`director/autonomy.py`, 77/92/119) используют `asdict`. В `Director` подтверждены вызовы `last_cycle.to_dict()` (625, 642), `plan.to_dict()` (2374, 2501), `decision.to_dict()` (1596, 2703–2704), `recommendation.to_dict()` (1788, 2747). **Вызова именно `DirectorContext.to_dict()` в этих двух файлах не обнаружено**; не приписывать ему OOM без других call sites.
- `Director._autonomy_research` (2461–2466) кладёт в `context.metadata` весь `research_execution` и `data_ingestion`. Эти поля могут увеличивать живой контекст, особенно если результаты содержат вложенные payload. Нужна оценка размеров/срока жизни, а не слепое удаление (важны статусы и доказательства).
- `Director.analyze` использует `context.to_analysis_dict()` (1131), то есть shallow view без глубокой копии. Сохранить это при оптимизации.
- `Director.apply_feedback` (около 2069–2140) сохраняет обратную связь через `memory_service.apply_recommendation_feedback` и ограничения через `save_constraint`. Эти данные — **защищённые** (R27/R30), не кандидаты на TTL.

**Приоритет следующей трассировки:** определить реализацию `data_service.get_project_state`, сборку приложения/создание сервисов, размер `research_execution` и `context.metadata` перед/после повторного `inspect`, затем MCP/Orchestrator. Сохранять различие между проверенным call site и гипотезой об OOM.

## Проверка DataAdapter.get_project_state — уточнение гипотезы о повторной загрузке

**Подтверждённый источник:** `peonyrhodo-bit/site-insight-engine/server.py`, main, строки 1074–1415. Это конкретная реализация `data_service.get_project_state` из `Director.inspect`.

- `DataAdapter.get_project_state` начинает с компактной структуры result (1074–1107). При наличии registry и смене `_loaded_project_id` выбирает `storage.load_youtube_analysis_data` (1114–1129), иначе legacy `load_youtube_data`. Полученный набор переносится в `youtube_registry`, предварительно очищенный (1132–1164); это попытка избежать одновременного удержания двух полных копий.
- `load_opportunity_data` и `load_research_data` также вызываются **только когда `_loaded_project_id != project_id`** (1166–1245). После успешного прохода `_loaded_project_id = project_id`. Поэтому предыдущая гипотеза «каждый повторный inspect снова загружает всю Supabase историю» **не подтверждается кодом и для обычного того же проекта неверна**. Исключения: смена проекта, сброс маркера/новый adapter, ошибки до установки маркера и другие не исследованные пути.
- После загрузки `get_project_state` **каждый вызов** (если registry существует) выполняет `videos = youtube_registry.videos()` и создаёт `observations`, `previous_observations`, `trend_current_observations` (1256–1415). Каждый video преобразуется через `video.to_dict()` (1268–1276); для видео с предыдущим снимком создаётся `dict(observation)` (1373), а текущая запись переиспользуется в `trend_current_observations` (1367–1371). Это конкретный путь **повторного построения производных списков/словарей в RAM**, не обязательно повторного DB read.
- При каждом `Director.inspect` (director/director.py 587–595) `get_project_state` возвращает новый result, а `_merge_context` заменяет списки. Старые списки могут стать доступны для GC, но пик при временном сосуществовании до освобождения памяти и объём сериализованных видео требуют измерений. **Нельзя утверждать OOM без heap/RSS profile**.
- Возможная оптимизация для M18–M22: компактные observation projections, reuse по версии registry, bounded matched trend cohorts, ленивый evidence drill-down, но только при сохранении полного аналитического результата и семантики обновления после исследования. Нельзя без тестов кэшировать устаревшие наблюдения.

**Обновлённая гипотеза M04:** проверить peak RSS на границах `load_* → registry → observations_built → Director.inspect → analyze → _autonomy_research → inspect`, различая DB fetch и пересборку рабочих структур. Приоритет — доказательство, не преждевременное изменение кода.

## M04 — план измерения и ограничение доступа (2026-11-19)

Кодовые точки измерения из `site-insight-engine/server.py`:
- `get_project_state` 1126–1245: холодная загрузка из Supabase только при смене `_loaded_project_id`; отметка `DIRECTOR MEMORY phase=project_data_loaded` в 1246–1254.
- `get_project_state` 1256–1415: построение `observations`, `previous_observations`, `trend_current_observations` из registry; отметка `DIRECTOR MEMORY phase=observations_built` в 1410–1415.
- `Director.inspect` и `Director.analyze`: сравнить RSS после merge и во время анализа; повторный inspect после research отделять от холодной DB загрузки.

**Попытка прочитать Render memory metrics и `DIRECTOR MEMORY` logs за 2026-11-19 18:10–20:00 UTC не выполнена:** подключение Render ответило `no workspace selected` и потребовало выбрать workspace с явным подтверждением пользователя. Никаких чисел из этой попытки не получено; старые исторические замеры не выдавать за новые. Нужен подтверждённый workspace для продолжения read-only измерений. Не вызывать `select_workspace` без подтверждения.

## Render read-only evidence — 2026-11-19 18:15–18:29 UTC (подтверждённый workspace)

Пользователь явно подтвердил Render workspace `tea-dabd4dijnfac73afejug`. Получены **read-only** `memory_usage`/`memory_limit`, логи `DIRECTOR MEMORY`, события деплоя для Director `srv-dae6fi61egvs73b4pa90`.

- Render memory usage: 18:15 **104337410 B (~99.5 MiB)**, 18:21 **389423100 B (~371.4 MiB)**, 18:27 **422379520 B (~402.8 MiB)**, 18:29 **486645760 B (~464.1 MiB)**. Лимит **536870900 B (~512 MiB)**. Это 90.6% лимита; метрика не доказывает OOM.
- Логи `phase=project_data_loaded` / `phase=observations_built` повторяются ~каждую минуту, при **стабильных 1203 видео, 500 channels, 16 niches, 262 niche snapshots, 5000 relations**, но `research_sets` растёт **68→79** за 18:16–18:29. Это согласуется с последовательными циклами и пересборкой наблюдений; причина увеличения памяти требует анализа ссылок/объектов.
- 18:16:51: `project_data_loaded` RSS **284.3 MiB**, `observations_built` **285.0 MiB** (прирост ~0.7 MiB). 18:17:49: **320.4→321.4 MiB** (~1.0 MiB). 18:29:33: **398.8→398.8 MiB**. Таким образом, **непосредственное создание 1203 observations в этих измерениях не объясняет десятки/сотни MiB роста**. Важно: это только измерения на границах фаз, а не allocation profiler.
- 18:16:53 `analytics_start` RSS **273.6 MiB**, `analytics_basic_complete` 18:16:55 **277.3 MiB**. 18:26:30 `analytics_start` **411.6 MiB**, `analytics_complete` 18:26:34 **411.6 MiB**. Эти точки **не доказывают** крупного устойчивого роста внутри базового анализа, хотя временные пики возможны.
- 18:26:28 `vmhwm_mb=516.5` при текущем `vmrss_mb=421.7`. **VmHWM 516.5 MiB превышает номинальные 512 MiB**, но VmHWM процесса и Render container metric не эквивалентны, и это **не является доказательством OOM kill**. После этого процесс продолжал писать логи до 18:29:41.
- Запрос Render events за 18:10–19:00 показал успешный deploy 18:14:49; в возвращённом наборе не было `server_failed`. Не утверждать, что событие отсутствовало за все возможные интервалы без полного просмотра страниц.

**Обновлённый приоритет:** профилировать рост между циклами и удержание в `context.metadata`, `memory_state`, результатов research, логируемых/сохраняемых `DirectorResult`, а не объявлять `observations_built` доказанным виновником. Отдельно расследовать частоту автономных циклов (~1/мин в окне) относительно ТЗ о часовом расписании; это наблюдение, не окончательное заключение о scheduler. Никаких production изменений.

## Autonomy loop: уточнение минутных повторов и удержания результатов

Проверен `site-insight-engine/director/autonomy.py` (main, 2026-11-19):
- `AutonomyConfig` (96–104): `max_steps_per_cycle=32`, `max_research_steps=10`, `step_timeout_seconds=120`; это лимиты **внутри одного wake**, не частота scheduler. `DirectorAutonomy.run` (235–267) увеличивает `cycle_count` при запуске.
- `_run_cycle` (345–394) делает INSPECT и UNDERSTAND один раз в начале, затем входит в `while steps < max_steps_per_cycle` (394). При недостаточности данных `research_handler` (450–468) может выполняться до 10 раз за один wake; после research `continue` возвращает к оценке, а не к внешнему hourly scheduler.
- `DirectorState.last_result: Any` (64), `metadata: dict[str, Any]` (74) могут держать ссылки на полные результаты. В исследовательской ветке `cycle.state.last_result = research_result` (461), `understanding = research_result` (464). В `Director._autonomy_research` дополнительно сохраняется `context.metadata[research_execution/data_ingestion]`. Проверить размер/время жизни и `DirectorCycle.to_dict()=asdict(self)` (118–119) при записи результата; это конкретный путь потенциального глубокого копирования.
- Логи `project_data_loaded` раз в ~минуту при `research_sets 68→79` **совместимы с несколькими research steps одного wake**, не доказывают запуск нового внешнего цикла каждую минуту. Прежняя формулировка о возможном нарушении часового расписания — **гипотеза**, требующая проверки `cycle_id`, `run_id`, scheduler и timestamp.
- Ограничение `max_research_steps=10` и рост research_sets на 11 не противоречат друг другу автоматически: логи могут охватывать больше одного wake или разный смысл counters. Не выводить количество wake из количества research_sets.

**Следующая проверка:** trace `DirectorCycle.to_dict()` в `server.py` и persistence, `DirectorState.last_result` и `context.metadata`; по логам определить cycle/run IDs и фактические границы wake. M02 остаётся открытым.

## M02 — подтверждённая сериализация и многократное сохранение autonomous cycle

**Источник:** `site-insight-engine/server.py` (main, прочитан 2026-11-19), `director/autonomy.py`.

- `server.serialize` (303–343) **рекурсивно создаёт новые dict/list** для словарей и списков; для объектов с `to_dict` вызывает `serialize(value.to_dict())`, а для dataclass fallback `serialize(asdict(value))`. `DirectorCycle.to_dict` (autonomy.py 118–119) использует `asdict(self)`: это **подтверждённый путь глубокого копирования полного состояния цикла с `state.last_result` и `state.metadata`**, затем рекурсивного копирования сериализатором. Количество и объём копий в пике требуют измерения.
- `run_director_autonomous_cycle` (server.py 2735–2920): создаёт durable run (2739), вызывает `director.run_autonomous_cycle` (2775), затем `serialized = serialize(result)` (2780). `update_run` (2786–2789) пишет `result: serialized` со статусом partial, `save_result` (2832–2842) пишет тот же результат в отдельную таблицу, финальный `update_run` (2885–2899) снова пишет `result: serialized`. Таким образом **полный payload записывается минимум в два контура и дважды обновляется в runs** при успешном пути. Не утверждать три одновременно живых Python-копии: переменная `serialized` переиспользуется, но JSON/HTTP сериализация может выделять буферы.
- `server.py` manual run (2495–2597) тоже сериализует `DirectorResult`, добавляет `state_snapshot`, сохраняет в run и result. Не смешивать с автономным путём.
- При сбое `update_run` до `save_result` durable run остаётся частичным, а сохранение decision/recommendation/result может не выполниться; статус/восстановление — защищённый контракт. В прошлом зафиксирован SQL timeout 57014 на `update_run`, но **не доказано**, что причина — большой JSON конкретной строки.

**Предложение M19–M22 (пока без внедрения):** измерить `len(json.dumps(serialized))`, RSS до/после `serialize(result)`, распределение размеров `DirectorCycle.state.last_result` и `state.metadata`; разработать компактный durable run summary + полную версионированную evidence record/manifest, исключить повторную запись неизменного большого JSON, обеспечить восстановление и идемпотентность. Сначала parity tests по статусам, history/provenance и отказам, затем отдельное разрешение на production. **Не удалять существующие данные.**

## M03/M04 — read-only размер сохранённых запусков в Supabase (2026-11-19)

Выполнены **только SELECT** к проекту `oxbxnswywgpdlcfltmbq`, таблица `director_runs`, измерение `pg_column_size(data_json)` (размер хранимого значения PostgreSQL, **не точная длина JSON в HTTP и не RSS**).

- Всего **159** строк; среднее **67 320 байт**, максимум **2 419 593 байт**, **5 строк >1 MiB**.
- По статусам: `failed` 131, среднее 456 байт, максимум 510; `partial` 26, среднее 368 290, максимум 2 419 593; `running` 1, 320; NULL status 1, 1 068 232.
- Крупнейшие: run IDs **43** (2 419 593 B), **77** (2 373 980 B), **45** (2 337 021 B), **79** (2 336 837 B), **33** (1 068 232 B). Четыре крупнейшие имеют `partial`, одна NULL; у них пустой `error_message`. **Не интерпретировать partial как доказанную ошибку сериализации**: статус может остаться промежуточным из-за других причин.
- Это доказывает наличие **крупных durable payload**, но не измеряет transient allocations `serialize`, HTTP JSON buffer или точную причину 57014/OOM. Тот ранее исследованный run **222** имел только ~472 B, поэтому его SQL timeout нельзя приписывать большому payload.

**Безопасный следующий эксперимент:** read-only агрегировать JSON keys/структуру крупнейших строк (без извлечения чувствительного полного содержимого), затем offline fixture для сравнения `asdict + serialize` и компактной projection с профилем peak RSS. Никакого удаления или UPDATE, сохранить историю/восстановимость.

## M03/M04 — локализован источник больших payload в циклах (read-only SQL)

Для `director_runs` IDs 43,45,77,79 выполнены только `SELECT` с `jsonb_each/jsonb_object_keys/pg_column_size`, без извлечения полного JSON. **Важно:** `pg_column_size` для извлечённых JSONB поддеревьев может отражать развёрнутую структуру; сумма вложенных размеров не равна размеру TOAST-сжатой строки.

- IDs 43/45/77/79: `result.state.metadata` ~6.97–6.98 MB в представлении JSONB поддерева, при общей строке ~2.34–2.42 MB. `result.events` всего ~2–6 KB.
- `state.metadata.work_plan` ~3.48 MB и `state.metadata.project_assessment` ~3.48 MB **каждое**. Для ID 43: `work_plan.basis` **3 483 649 B**, `project_assessment.memory_state` **3 478 618 B**, `work_plan.basis.memory_state` **3 478 618 B**.
- Главный вклад: `project_assessment.memory_state.recent_results` **3 472 138 B** (ID 43). Этот же `memory_state` вложен в `work_plan.basis`, поэтому **два пути включают крупную историю результатов**. `recent_runs` лишь 4774 B, `recent_events` 1191 B. Это подтверждённая структурная повторяемость больших данных, а не просто гипотеза о JSON.
- **Потенциальный механизм рекурсивного разрастания:** `recent_results` содержит ранее сохранённые `director_results`, которые могут включать полный сериализованный цикл с предыдущим `memory_state`. Новые `work_plan` и `project_assessment` включают их снова. Требуется отдельная проверка глубины вложения и фактического состава, без полного чтения payload. Не объявлять бесконечную рекурсию доказанной.
- ID 33 — **другой** manual-run формат: `result` содержит `state_snapshot`, не `result.state.metadata`. Не объединять разные контуры.

**Приоритетная безопасная проектная мера (ещё не реализована):** в `memory_state.recent_results` и других «контекстных» summary использовать ограниченные ссылки/ID, статусы, краткие summaries и хэши, а полные исторические результаты хранить **отдельно, неизменяемо и доступно по ссылке**. Не удалять `director_results` и не нарушать возможность анализа прошлого; ввести версионированную schema/provenance и offline parity tests. Проверить источник `_memory_state_summary` и места включения `project_assessment` в `work_plan.basis`.

## M02 — точная цепочка повторного включения полной истории (code-grounded)

`site-insight-engine/director/director.py`:

1. `inspect` (445–459) вызывает `memory_service.get_context(... limit_results=20, limit_runs=10, ...)`. Источник может вернуть **полные** `director_results.data_json`; ограничение числа строк **не ограничивает их размер**.
2. `_memory_state_summary` (888–903) берёт `self.context.metadata['memory_state']`, для `recent_results` и прочих категорий делает `rows[-5:]` **без проекции вложенных полей**. Название «Compact» относится лишь к количеству записей. Это конкретная точка переноса полных прежних результатов в новое планирование.
3. `understand` (929–945) уже включает этот `memory_state` в возвращаемый словарь.
4. При формировании `work_plan` (2570–2589) `basis.memory_state = self._memory_state_summary()`; затем (2634–2639) **один и тот же объект** `work_plan['basis']` присваивается `state.metadata['project_assessment']`, `self.context.metadata['project_assessment']`, и содержится в `state.metadata['work_plan']`. В памяти это может быть общая ссылка; при `asdict`/JSON сериализации две ветви становятся дублирующими копиями.
5. `logger.info('DIRECTOR PROJECT ASSESSMENT: %s', json.dumps(work_plan['basis']))` и `logger.info('DIRECTOR WORK PLAN: %s', json.dumps(work_plan))` (2640–2641) **каждый раз сериализуют крупную историю в строку лога**. Это дополнительные временные буферы и объём логов, даже без `server.serialize`.
6. `server.py` (2780–2789, 2832–2842, 2885–2899) глубоко сериализует цикл и несколько раз сохраняет полный результат. Read-only Supabase SQL подтвердил: `recent_results` ~3.47 MB внутри `project_assessment.memory_state`, ещё раз через `work_plan.basis.memory_state` для run 43.

**Уточнение:** это подтверждённый кодом механизм **вложенной исторической самоссылочной структуры по значениям**, а не доказанная бесконечная рекурсия Python-ссылок. Рекомендованный порядок безопасного патча: (a) bounded lightweight projection для `recent_results` в summary, сохраняя IDs, статус, timestamps, short summary и provenance; (b) убрать дублирующую тяжёлую сериализацию при logging, логировать счётчики и ID; (c) исключить двойное хранение `basis` в сериализуемом state, сохранив доступ к оценке/плану; (d) offline tests с legacy huge fixtures, status/error/restore parity. Ни один пункт не внедрён.

## M02 — патч-контракт и критичная граница источника memory_state

Проверено дополнительно: `memory/supabase.py:get_context` (1132–1202) читает `results` через `get_recent_results` (1419–1431), который вызывает `_recent_for_project` с ограничением **числа строк**, но без lightweight projection. `memory/director_adapter.py:get_context` (600–660) делегирует backend и сохраняет статусы полноты. `director/director.py:inspect` (445–476) вызывает memory service с `limit_results=20` и применяет только complete-read semantics для удаления устаревших значений.

**Важная неразрешённая деталь:** в изученном `director/director.py` явного присваивания `context.metadata['memory_state']` не обнаружено; `_memory_state_summary` (888–903) **читает** это поле. Следовательно, хотя наличие больших `recent_results` в сохранённых `work_plan.basis.memory_state` доказано SQL, **точный конструктор memory_state в runtime ещё надо найти**. Не утверждать, что `get_context` напрямую формирует `memory_state` без трассировки дополнительного слоя. Проверить factory/adapter и другие модули, прежде чем править.

**Тестовый контракт будущего патча (без изменения production):**
1. Полный результат по ID сохраняется в авторитетной истории; рабочий summary не включает `result.data_json.result` и вложенные `state.metadata`.
2. `recent_results` ограничен одновременно по числу и по размеру (в байтах), содержит ID, project_id, run_id, тип, дату, статус/краткое описание и ссылку/provenance; не выдумывать отсутствующие поля.
3. Разделить API чтения полной записи для аудита и лёгкой проекции для планирования; сохранить `complete/partial/error` семантику, проектную изоляцию и корректность legacy unscoped.
4. Проверить сериализацию повторных циклов на искусственных данных 2–5 MB: размер **нового** результата должен оставаться ограниченным независимо от размера истории; полный архив восстанавливается по ID.
5. Проверить отказ Supabase на update: статус и результаты не теряются, идемпотентность и retry bounded; логирование без полного JSON.

M02/M03/M04 — **не приняты**, это read-only evidence и проектирование.
