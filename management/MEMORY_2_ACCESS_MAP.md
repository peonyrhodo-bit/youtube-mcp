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

## M02 — верификация источника memory_state: выявлен разрыв между историческими данными и текущим кодом

Дополнительный read-only просмотр `site-insight-engine`:
- `director/director.py:__init__` (243–270) создаёт Director и подключает сервисы; явного построения `memory_state` здесь нет.
- `inspect` (445–476) получает `external_context` от `memory_service.get_context` и передаёт его ключи через `_merge_context` без переименования в `memory_state`; `_merge_context` (851–886) неизвестные ключи помещает напрямую в `context.metadata[key]`.
- `memory/director_adapter.py:get_context` (600–662) делегирует `memory.get_context`, нормализует ID рекомендаций и read-status; **не создаёт `memory_state`**.
- `memory/supabase.py:get_context` (1132–1202) возвращает ключи `runs,decisions,recommendations,constraints,events,chat,actions,results,_memory_read`, **не `memory_state`**. `get_recent_results` (1419–1431) использует `_recent_for_project` без проекции.
- В изученном текущем `director/director.py` `_memory_state_summary` (888–903) читает `context.metadata['memory_state']`, но прямого присваивания нет. **Следовательно, нельзя утверждать, что текущий `get_context` автоматически наполняет именно этот summary.** Крупные `memory_state` внутри исторических run IDs 43/45/77/79 — доказательство формата сохранённых запусков 14–16 ноября, не обязательно текущего runtime после деплоя 19 ноября.
- Текущий `server.py:serialize` (303–343) и `DirectorCycle.to_dict` (autonomy.py 118–119) по-прежнему дают подтверждённый путь глубокой сериализации. `_autonomy_assess` (director.py 2570–2641) по-прежнему дублирует basis в state и логирует JSON целиком, **если** `memory_state` присутствует.

**Контрольный следующий шаг:** установить точный SHA исторических деплоев и сравнить версию конструктора `memory_state`; read-only проверить текущие логи `DIRECTOR WORK PLAN` (только длины/ключи) и текущий объект `memory_state`, не выполнять новых циклов. До этого не считать «вложение истории через memory_state» доказанным для текущего production и не внедрять патч на предположении.

## M04 — текущий Render: подтверждённое oversized logging (19 ноября, read-only)

`Render.list_deploys` для `srv-dae6fi61egvs73b4pa90`: действующий deploy `dep-dbvjoo8jo6nc73a4ljt0`, commit `09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae`, live с 18:14:49 UTC; предыдущий `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc` деактивирован. Последний commit менял page size Supabase, не logging.

`Render.list_logs`, filter `DIRECTOR WORK PLAN`, 18:14–18:33 UTC: первое найденное сообщение 18:16:53 имеет 15 108 символов, последующие сообщения 18:17:52, 18:19:03, 18:19:56 и далее **ровно 100 000 символов** каждый в выдаче. Попытка JSON.parse полного текста неуспешна: сообщения обрезаны/содержат продолжение, поэтому **нельзя заключать, что реальный work_plan ровно 100 KB** или что вложенный memory_state текущего цикла имеет конкретный размер. Но **чрезмерно длинное логирование в текущем production подтверждено**.

Текущий `director/director.py` (2640–2641) вызывает `json.dumps(work_plan['basis'])` и `json.dumps(work_plan)` прямо в `logger.info`; два больших строковых представления на каждый assessment. Сокращение этих логов до счётчиков/IDs/байтов с сохранением важных error/status сообщений — отдельная низкорисковая кандидатная оптимизация после offline tests. Причина роста RSS и конструктор текущего `memory_state` **ещё не доказаны**. Не менять production без разрешения.

## M02/M04 — текущий production действительно содержит вложенные старые результаты (19 ноября)

**Новая read-only улика, уточняющая предыдущую неопределённость:** в `Render.list_logs` действующего deploy `09ceb05f`, сообщение `DIRECTOR WORK PLAN` 18:16:53 UTC, и повторные сообщения 18:17:52/18:19:03 UTC, видны **не только** ключи `memory_state`, но и конкретное значение `recent_results_count: 8` и `recent_results[0]`: `id:9`, `run_id:79`, `created_at:2026-11-16T16:17:32.821997+00:00`, `result_type:autonomous_cycle`, `data_json.result.state.metadata.work_plan`. Это доказывает, что **текущий процесс 19 ноября переносит полный результат исторического автономного цикла в новый work_plan**. Значит, риск вложенной истории актуален в production; прежняя оговорка «не доказано для текущего production» теперь **снята**.

**Но:** прямой конструктор `context.metadata['memory_state']` по-прежнему не локализован в изученных модулях `director/director.py`, `memory/director_adapter.py`, `memory/supabase.py`. Вероятны другой слой инициализации/подготовки контекста или отдельная ветка вызова. Не приписывать источник конкретной функции до нахождения. Текущий лог обрезается на 100000 символов; размер полного JSON и RSS этого объекта не измерены.

Дополнительно `Render.list_deploys` подтверждает, что предыдущий commit `f95bc0e` (14 ноября) и текущий `09ceb05f` (19 ноября) содержат одинаковый вызов `_memory_state_summary()` в `work_plan.basis` (director.py:2584). `director_runs` за 19 ноября (IDs 212–223, read-only SELECT) в основном 320–472 B без сериализованного `work_plan`; **это не отсутствие work_plan в runtime**, а отсутствие успешного финального сохранения этих циклов. Не использовать отсутствие payload в run 222/223 как доказательство, что проблема исчезла.

**Приоритет исправления:** bounded projection `recent_results` до включения в `work_plan`/логирование, с immutable full results по ID; после — убрать full-json logging. Изменения и тесты ещё не выполнялись.

## M02 — подтверждена идентичность вложенного result с Supabase (read-only)

`SELECT id,run_id,result_type,pg_column_size(data_json),created_at FROM director_results ORDER BY pg_column_size(data_json) DESC LIMIT 10`: `director_results.id=9`, `run_id=79`, `result_type=autonomous_cycle`, **2 336 825 B**, `created_at=2026-11-16 16:17:32.821997+00`. Точно те же id/run_id/type/time присутствуют в текущем Render `DIRECTOR WORK PLAN` 2026-11-19 18:16:53 UTC, в `basis.memory_state.recent_results[0]` с полным `data_json.result.state.metadata.work_plan`. Это подтверждённая cross-source связка production→durable result, а не совпадение формы.

Проверены `director/director.py` и `director/autonomy.py` на предыдущем Render SHA `f95bc0e`: в director.py есть **только чтение** `context.metadata['memory_state']` и его включение в `work_plan`, как и в текущем SHA. В текущем `Director.__init__` (277–279) создаётся новый `DirectorContext(project_id=...)` без заполнения `memory_state`. `memory/director_adapter.py:get_context` и `memory/supabase.py:get_context` не создают ключ с таким названием. Точный runtime-писатель `memory_state` всё ещё **не локализован**, несмотря на наблюдаемый факт наличия в live logs. Не делать фиктивный вывод об отсутствии проблемы из-за этого пробела; возможны другой сервис/модуль, исторически созданный контекст или несовпадение загруженной версии и default branch — требует проверки.

**Следующее:** найти вызывающий слой через read-only repo tree/конструкторы сервиса и подтвердить реальную ветку выполнения; отдельно спроектировать bounded projection прямо в `_memory_state_summary` как защиту на выходе, независимо от происхождения `memory_state`. Принимать M02 только после закрытия трассировки и критериев полноты.

## M02 — дополнительная трассировка фабрики и контрактов памяти

Read-only: `server.py:Runtime.get_director` (1978–2003) создаёт Director через `create_director(project_id,mode,research_service,memory_service,analytics_service,ai_service,data_service)`; `director/director.py:create_director` (3061–3074) просто возвращает `Director(**services)`, а `Director.__init__` (273–279) создаёт пустой `DirectorContext`. Эти две фабрики **не создают `memory_state`**. `Director.inspect` (445–476) получает `memory_service.get_context` и `_merge_context` (851–886) сохраняет незнакомые ключи в metadata; Supabase get_context отдаёт `results`, не `memory_state`. Точное присваивание остаётся неизвестным, несмотря на достоверный live-log с `memory_state.recent_results`.

Выявлена дополнительная граница контракта: `memory/director_adapter.py:get_context` (639–649) допускает backends без `_memory_read` и присваивает им статус complete (например, in-process backend). Проверить фактический класс `Runtime.memory` и все альтернативные реализации get_context до окончательного заключения о происхождении memory_state. Без этого M02 не закрывать.

Независимый от источника защитный seam для будущего offline patch: `Director._memory_state_summary` (888–903), где сейчас `rows[-5:]` без проекции и с полным `data_json`; добавить bounded fields/byte caps + IDs и source retrieval, не менять durable originals. Требуются тесты на 2.34MB historical fixture, project isolation, partial/error reads и неизменность источника. Никаких изменений runtime.

## M02 — КОНСТРУКТОР memory_state НАЙДЕН, upstream-трассировка закрыта (read-only)

В `site-insight-engine/memory/memory.py` обнаружен ранее пропущенный слой `Memory`:
- `memory/director_adapter.py:ServerMemory.__init__` (476–495) создаёт `self.backend = self._create_backend()` и `self.memory = Memory(backend=self.backend)`; `_create_backend` (520–559) выбирает Supabase при наличии URL+KEY, иначе допустим in-memory fallback.
- `server.py:Runtime.__init__` (1674–1683) создаёт `self.memory = ServerMemory()`; `Runtime.get_director` (1978–2003) передаёт этот объект как `memory_service`.
- `memory/director_adapter.py:ServerMemory.get_context` (600–662) вызывает `self.memory.get_context`.
- **`memory/memory.py:Memory.get_context` (267–325)** вызывает `self.backend.get_context` и затем `self._build_memory_context(context)`.
- **`memory/memory.py:_build_memory_context` (327–410)** формирует `context['memory_state']` (399–408), присваивая `recent_results: results` (404) без bounded projection. Это точный upstream конструктор. Исходные `results` читаются через `memory/supabase.py:get_context` (1132–1202), `get_recent_results` (1419–1431) без field projection.
- `Director.inspect` (445–476) через `_merge_context` (851–886) кладёт `memory_state` в `context.metadata`; `_memory_state_summary` (888–903) берёт последние 5 объектов **целиком**; `work_plan.basis` (2584) включает summary; `_autonomy_assess` (2634–2641) сохраняет дубли и логирует полные JSON; `DirectorCycle.to_dict` и `server.serialize` глубоко копируют.

**Вывод:** полный путь от durable source до live oversized plan и логов подтверждён кодом и cross-source наблюдением `director_results.id=9` / `run_id=79`. Прежние пометки «конструктор не локализован» **устарели**; исправлены этой записью. M02 upstream tracing технически завершён, но **формальная приёмка M02 не проведена** (тестовые критерии/проверка полноты и ограничений впереди).

**Контракт будущего исправления:** полная запись `results` и durable Supabase history не удаляются; bounded read-model для планирования в `_build_memory_context` и/или `_memory_state_summary` должен ограничивать размер, а не только count, сохранять id/run_id/type/time/status, provenance, явный флаг omitted + drill-down; не терять pending constraints/approvals и корректную обработку partial/error. Offline tests на вложенных 2.34 MB fixtures и memory profiling до production patch. Никаких production изменений.

## M02 — первый read-only проход по YouTube MCP и Orchestrator (19 ноября)

GitHub `list_repositories(owner=peonyrhodo-bit)` подтвердил 4 доступных репозитория: `youtube-mcp`, `site-insight-engine`, `ai-youtube-system`, `SEKRETAR`. Для M02 проверены **основные server.py** двух ещё не изученных сервисов:

| Репозиторий / файл | Проверенный сетевой путь | Прямые Supabase-операции в данном файле | Ограничение вывода |
|---|---|---|---|
| `peonyrhodo-bit/youtube-mcp/server.py` (995 строк) | `YouTubeQuotaGuard.authorize/finish` через `requests.post` к `YOUTUBE_QUOTA_AUTH_URL/internal/youtube-quota/{action}` (строки 41–100); `requests.get` к YouTube API после разрешения (161–205); fail-closed при ошибке квоты | По просмотренным импортам и поиску `supabase/postgres/database` в файле прямых SQL/REST обращений не обнаружено | Другие файлы, библиотеки и конфигурация ещё не инвентаризированы; центральный quota ledger расположен вне MCP |
| `peonyrhodo-bit/ai-youtube-system/server.py` (277 строк) | `httpx.AsyncClient` к `ENGINE_URL` (начиная с 21, 67); прокси-маршруты `/director/run` (162–183), `/director/history` (193–197), `/director/chat` (202–208) | По проверенному файлу прямых Supabase SQL/REST обращений не обнаружено | Прокси не доказывает отсутствия других Supabase-клиентов в репозитории |

**Промежуточный вывод:** в проверенных server entrypoints MCP и Orchestrator взаимодействуют с Director по HTTP, а не напрямую с его памятью. Это сужает M02 карту вызовов, но **не является полной инвентаризацией двух репозиториев**. GitHub code search `supabase`, `director_runs`, `rest/v1` вернул пустые результаты в обоих репозиториях; отрицательный результат индекса поиска не считать доказательством отсутствия кода.

**Далее:** получить дерево файлов / точные модули обоих репозиториев и исследовать все storage/DB call sites, а также quota-authority endpoint в `site-insight-engine`. Дополнить таблицу методами, полями, объёмами и границами ответственности. M02 остаётся 🔄, 0/40 принято.

## M02 — MCP→Director→Postgres quota ledger: подтверждённая сквозная цепочка (19 ноября)

**Проверены source entrypoints и зависимости:**
- `youtube-mcp/server.py:YouTubeQuotaGuard` (41–100) вызывает `POST {YOUTUBE_QUOTA_AUTH_URL}/internal/youtube-quota/authorize|finish` через `requests`, перед фактическим `requests.get` к YouTube (161–205). При недоступности/отказе центральной квоты блокирует API вызов.
- `site-insight-engine/server.py` (2069–2127): закрытые `/internal/youtube-quota/authorize` и `/finish`, header secret, вызовы `runtime.quota_manager.authorize_call` (2092) и `finish_call` (2116).
- `site-insight-engine/quota/postgres_youtube_quota.py:YouTubeQuotaManager` (194–313): `psycopg` direct PostgreSQL; при authorize `pg_advisory_xact_lock` (212), читает агрегат usage, пишет `private.youtube_quota_usage` (249–257) и `private.youtube_quota_events` (265–275); при исчерпании пишет blocked event (229–239) без расходной строки; `finish_call` читает metadata (295–300), затем UPDATE `private.youtube_quota_events` (308–312). Это **отдельный direct-Postgres writer**, а не `memory/supabase.py` REST writer; он принадлежит Director, вызывается MCP по HTTP. Поля перечислены в SQL; рост: до одной usage + одной event записи на разрешённый вызов и одной event на заблокированный; фактическая скорость роста требует измерения.
- `ai-youtube-system/server.py` (277 строк) использует `httpx` к `ENGINE_URL` и проксирует Director endpoints. Прямого DB-клиента в этом файле нет.
- В проверенных `requirements.txt`: MCP содержит `requests`, Orchestrator `httpx`, прямых `psycopg`/`supabase` зависимостей не обнаружено. **Не считать это полным доказательством отсутствия иных способов DB доступа** без просмотра дерева и дополнительных модулей.

**M02 ограничение:** полная таблица reader/writer call sites по всем репозиториям и оценка фактических объёмов ещё не закрыта. Новые SQL/YouTube вызовы не выполнялись; это source-only инспекция. Статус 🔄, 0/40 accepted.

## M02/M15 — новая аномалия quota ledger: events 765, usage 0 (read-only, 19 ноября)

Read-only `information_schema.tables` подтвердил существование `private.youtube_quota_usage` и `private.youtube_quota_events` в проекте `oxbxnswywgpdlcfltmbq`. `SELECT COUNT(*),MIN(created_at),MAX(created_at)`: **usage=0**, **events=765** (2026-11-05 10:52:14 UTC — 2026-11-19 18:29:20 UTC). Events по status/bucket: succeeded/search=388, succeeded/other=296, error/search=55, planned/other=21, planned/search=5; всего succeeded=684. За 19 ноября events succeeded=18 и error=52. `quota/postgres_youtube_quota.py:_usage_in_connection` (70–84) суммирует **только** `private.youtube_quota_usage`, а `authorize_call` (194–280) в актуальном коде при разрешённом вызове должен INSERT и usage, и event в одной транзакции. Противоречие **подтверждено между текущим кодом и фактическим состоянием БД**, но причина **не установлена**: старые версии, альтернативный writer, отличающаяся prod DB connection, ручные/миграционные события или другие факторы. Нельзя заявлять, что quota фактически обходится или что события отражают реальные API вызовы без дополнительной проверки.

**Риск:** нулевой usage ledger может делать `get_status` нулевым при исторических событиях; отдельно проверить deployment/version и конфигурацию БД (без чтения секретов), временные интервалы event creation, и точный код writer на тот момент. Не инициировать authorize/finish, YouTube API, запись в quota tables или paid actions. Это open M02/M15 discrepancy, не основание принимать M02.

## M02/M15 — quota discrepancy уточнён: события относятся к другому operation path (read-only)

Дополнительная проверка `private.youtube_quota_events` по `operation,method,status`: `search_videos/search.list` succeeded=388,error=55,planned=5; `collect_video_snapshots/videos.list` succeeded=172,planned=2; `refresh_existing_video_stats/videos.list` succeeded=124,planned=19. Итого 765 событий. **Ни одного** `operation='youtube_get'`, `status='attempted'` или `status='blocked'` в этой таблице. Текущий `youtube-mcp/server.py:YouTubeQuotaGuard.authorize` (77–86) отправляет `operation='youtube_get'`, а `quota/postgres_youtube_quota.py:authorize_call` (265–276) создаёт `status='attempted'` при разрешении; при блокировке `status='blocked'` (229–239). Поэтому исторические 765 событий **не подтверждают вызов именно этого нового authorize-path**. Их operations соответствуют именам исследовательских задач, но точный writer/версия не доказаны.

В `quota/postgres_youtube_quota.py` есть **отдельная ветка** `record_planned_call` (129–154), `preflight_call` (156–179) и `finish_planned_call` (181–192), которая пишет/обновляет события без INSERT в `private.youtube_quota_usage`. Она **может объяснять** нулевой usage при событиях, но `succeeded` требует проверки call sites; утверждать происхождение каждой строки нельзя. `get_usage` (70–105) читает только usage. На 19 ноября events=70 (18 succeeded, 52 error); 0 usage. **Открытый вопрос:** что реально разрешает и учитывает live YouTube API запросы, и одинаковые ли production DB target у текущего Director и доступного Supabase проекта? Проверять только read-only и по версиям/логам, без секретов и пробных списаний.

## M02/M15 — сопоставление LIVE Render SHA с quota ledger (read-only)

`Render.list_deploys` подтвердил **live**: Director `09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae` (19 Nov 18:14:49 UTC), MCP `5772895a8b79ab8c575ea366f70e837303e46b00` (19 Nov 13:58:05 UTC), Orchestrator `bf119e2f834efcd63bb8ee0c95dab4a405958348` (10 Sep 13:18 UTC). `GitHub.fetch_file` **именно по live SHA** подтвердил MCP `server.py` 995 строк и `YouTubeQuotaGuard.authorize` с `operation='youtube_get'` (82), вызов `quota_guard.authorize` перед `requests.get` (162), `finish` на успехе/ошибках (166–205). Orchestrator live SHA `server.py` 252 строки, `ENGINE_URL` и HTTP прокси `/director/run`; отличается по длине от default branch (277), поэтому использовать live SHA при дальнейшем аудите.

Read-only SQL: в `private.youtube_quota_events` 765 строк, `operation='youtube_get'`=0, `status='attempted'`=0, `status='blocked'`=0, usage=0; event operations старые `search_videos` 448, `collect_video_snapshots` 174, `refresh_existing_video_stats` 143. 19 Nov 70 events (52 error, 18 succeeded). Render logs Director 19 Nov 00:00–19:00 UTC по точным строкам `Quota authorization failed closed` и `Quota event finalization failed` вернули 0 результатов; это **не доказывает отсутствие запросов или ошибок по другим путям**.

**Вывод:** код live MCP нового типа подтверждён, но записи в проверенном Supabase проекте не подтверждают выполнение `authorize_call` нового типа. Возможные причины (не доказаны): неиспользованный endpoint, runtime env направляет на иной quota authority/DB, события пишутся другим producer, ограничения доступа/логирования. Проверить read-only request logs `/internal/youtube-quota/*` и конфигурационные **имена и наличие** переменных без значений; не выполнять вызов authorize/finish или YouTube API. M02/M15 остаются open.

## M02/M15 — Render request-log coverage limitation (read-only)

Render `list_logs(type=['request'],path=['/internal/youtube-quota/authorize'|'.../finish'])` на Director и MCP, окно 19 Nov 00:00–19:00 UTC, дал **0 записей**, `hasMore=false`. Контрольный запрос **без path filter** `list_logs(type=['request'])` на Director за 18:00–18:35 UTC тоже вернул **0 записей**. Поэтому отрицательный результат **не может служить доказательством отсутствия HTTP запросов**: для данного сервиса/интервала request-log источник вообще не продемонстрировал покрытие. Приложение ранее выдавало app logs, это другой тип.

`Render.get_service` подтвердил production Director и MCP (оба web_service, free, Oregon, main), но возвращает метаданные сервиса **без списка env var keys**; доступный Render connector имеет метод изменения env, но не обнаружен безопасный read-only метод перечисления ключей. **Не делать update_env ради диагностики**, не извлекать секреты. На данном этапе невозможно подтвердить совпадение `YOUTUBE_QUOTA_AUTH_URL`, `YOUTUBE_QUOTA_SHARED_SECRET` и DB target только этими инструментами.

**Доказано:** live MCP code перед вызовом YouTube требует quota authorization; проверенный Supabase ledger не содержит `youtube_get`/`attempted`; запросов quota endpoint в доступных request logs не найдено, но нет и положительного контроля покрытия. **Не доказано:** отсутствовали ли сами запросы, правильность live env, identity Postgres, корректность фактических расходов. Следующее безопасное действие — искать существующие app logs MCP (quota unavailable/authorization failure), сопоставить временные метки без инициирования API вызовов.

## M02/M15 — фактические app logs MCP: 4× UnicodeEncodeError перед подтверждённым YouTube response

`Render.list_logs` MCP `srv-dadh2su1egvs73ddi04g`, 19 Nov 18:26:30–18:28:00 UTC, полный набор 36 строк, `hasMore=false`: 4 пары сообщений `YouTube API request started endpoint=search` → `YouTube API call accounting: endpoint=search.list attempted=1 succeeded=0 error=UnicodeEncodeError` в 18:27:01.226→01.441, 18:27:06.860→06.965, 18:27:12.001→12.154, 18:27:17.064→17.258 UTC. Это **4 фактические неуспешные попытки в MCP**, не доказанные 4 сетевых запроса YouTube или списания квоты. Остальные записи включают независимый `ClosedResourceError` SSE transport (18:27:18); не связывать его с Unicode без трассировки.

Live SHA MCP `5772895a...`, `server.py:youtube_get` 147–207: лог started на 158; `quota_guard.authorize` на 162 **до** `requests.get` к YouTube на 164; quota authorization `requests.post` (55–60) отправляет JSON и `X-Quota-Secret` header. UnicodeEncodeError мог возникнуть при формировании HTTP header/JSON/URL в quota authorization или позднее; **нет stack trace этой ошибки** в проверенном фрагменте, точный источник не установлен. Отсутствие `operation='youtube_get'` и `attempted` в проверенном Supabase согласуется с отказом до INSERT, но **не доказывает**, что backend DB один и тот же. Особо проверить offline, без секретов, что конфигурационные значения, передаваемые в HTTP headers, допустимы по кодировке (только булевы проверки), и исключения до network call; не печатать secret, не делать live authorize/YouTube calls.

**Приоритет:** M15 quota accounting discrepancy + blocked research. Нужно контрактное offline тестирование `UnicodeEncodeError` до/после quota authorization, классификация attempted vs actually sent vs charged и fail-closed, без production изменений. M02 остаётся open.

## M04 — сопоставление RAM, фаз и остановок, 2026-11-20

Анализ опирается на уже сохранённые логи, метрики и git-версии.
Новых обращений к Render, базе, YouTube или AI не было. Ниже часы из
источников приведены в **UTC** за 2026-11-19 (Москва = UTC+3).
`VmRSS` — текущая резидентная память процесса, `VmHWM` — его максимум
с момента старта. Поля с суффиксом `_mb` в Director выражены в МиБ.
Render `memory_usage` — отдельная метрика инстанса, измеренная в байтах.
Выборки разной частоты и масштаба нельзя вычитать друг из друга для
расчёта аллокаций. HWM около границы фазы не локализует момент пика.

| Окно UTC и версия | Фаза / наблюдение | Память и граница вывода |
|---|---|---|
| 14:33:55–14:33:56, `f95bc0e` | DATA загружены, затем построены 1203 observations. В реестре 5000 связей и 68 наборов исследований | RSS 449,8 → 450,8 МиБ. Стоимость самой загрузки из этих двух точек не выделяется. [Логи](INCIDENT_DIRECTOR_RUNS_2026-11-19.md#точная-последовательность-за-15-секунд-до-oom-render-app-logs-143354143410-utc) |
| 14:33:58–14:34:01, `f95bc0e` | Начало анализа → basic complete → analytics complete → начало decide | RSS 441,3 → 444,0 → 448,9 МиБ. HWM 491,7 МиБ уже виден при `analytics_start`; момент пика предшествует этому замеру или совпадает с ним. [Логи](INCIDENT_DIRECTOR_RUNS_2026-11-19.md) |
| 14:34:05–14:34:09, `f95bc0e` | В окне decide успешный GET полной истории runs и ответ LLM; затем Render `server_failed` с `oomKilled.memoryLimit=512Mi` | **Подтверждённый OOM.** Конкретный источник GET и выделение памяти, пересёкшее лимит, неизвестны. [Логи и разбор decide](INCIDENT_DIRECTOR_RUNS_2026-11-19.md) |
| 17:20–17:29, `f95bc0e` | GET полной истории: HTTP 500 / `57014` в 17:20:40–41. Render отдельно зафиксировал `oomKilled` в 17:22:21, 17:24:09, 17:27:37 и 17:29:52 | **Подтверждены разные события.** Timeout отменяет SQL statement. Он предшествовал первому OOM в этом окне; причинная связь не доказана. [Журнал OOM-01](OOM_RECOVERY_PLAN.md) |
| 18:15–18:21, `09ceb05` | Новый deploy. Повторяются inspect, analyse/assess/decide и исследовательские шаги. В 18:19:50 и 18:20:42 research завершился с 4 planned / 0 collected / 4 failed | Метрика Render 104 337 410 → 389 423 100 B (99,5 → 371,4 МиБ). Нет замера до/после каждого MCP-вызова. Сбой research и рост памяти совпали по окну; вклад YouTube не измерен. [Журнал OOM-07](OOM_RECOVERY_PLAN.md) |
| 18:16–18:29, `09ceb05` | Повторные DATA/observations; стабильные 1203 видео и 5000 связей, research_sets 68 → 79. Шаги могут входить в один wake | RSS DATA→observations: 284,3→285,0; 320,4→321,4; 398,8→398,8 МиБ. Это небольшие разницы на границе; размер временных копий и число wake не установлены. [Сохранённые измерения](#render-read-only-evidence--2026-11-19-18151829-utc-подтверждённый-workspace) |
| 18:26:03–18:26:04, `09ceb05` | Сохранение run 222, PATCH HTTP 500 / `57014`, затем ошибка wake. В исторической проверке сохранённый JSON строки 472 B | **Подтверждённый write-side timeout.** 472 B — размер сохранённого значения. Размер запроса, результат конкретного PATCH, блокировки и причина отмены неизвестны. [Журнал OOM-07](OOM_RECOVERY_PLAN.md) |
| 18:26:28–18:27, `09ceb05` | HWM/RSS в app log 516,5/421,7 МиБ. Analyse 18:26:30–34: RSS 411,6 МиБ на обеих границах. В 18:27 MCP регистрировал неуспешные попытки с `UnicodeEncodeError` | Render 422 379 520 B (402,8 МиБ) в 18:27. HWM уже накоплен, логи продолжались. Ни SQL/MCP ошибка, ни HWM не подтверждают OOM в этом окне. [Измерения Render](#render-read-only-evidence--2026-11-19-18151829-utc-подтверждённый-workspace) · [Логи MCP](#m02m15--фактические-app-logs-mcp-4-unicodeencodeerror-перед-подтверждённым-youtube-response) |
| 18:29, `09ceb05` | Render 486 645 760 B (464,1 МиБ, 90,6% от 536 870 900 B), затем в 18:29:49 Uvicorn записал ожидание и завершение application shutdown | **Зафиксирована штатная последовательность завершения приложения.** Инициатор, причина остановки и статус выхода не установлены. В просмотренных событиях для этого окна `oomKilled` не найден. [Журнал](OOM_RECOVERY_PLAN.md) |

В хронологии до и после деплоя разные интервалы и разная нагрузка.
Переход со страниц 1000 на 50 уменьшает максимальное число строк на
HTTP-ответ. Материализация всех накопленных строк на полном пути
сохраняется. По этим наблюдениям нельзя доказать исчезновение OOM
или сделать сравнение одинаковых циклов.

### Где образуются крупные структуры

| Граница | Подтверждено по исходнику `09ceb05` | Ограничение доказательства |
|---|---|---|
| History → память | `_recent_for_project` загружает `select("*")`, после фильтрации добавляет совпавшие строки в список. Idempotency/active-run lookup используют `limit=None`. `get_context` передаёт полные recent results в `memory_state`. [Backend](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L204-L265) · [Guard](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L710-L740) · [Память](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/memory.py#L327-L410) | Размер строки и совокупный объём чтения не ограничены page size. Пик PostgREST не изолирован в сохранённых логах. |
| DATA → реестр → аналитика | `DataAdapter.get_project_state` гидратирует реестры, затем сериализует наборы и связи для context. В историческом замере 68 research_sets дали около 7,97 MB текстового JSON, из которых около 7,25 MB приходились на research_plan и operation_results. [Сборка](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1108-L1258) · [Экспорт](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1474-L1523) · [Размеры](INCIDENT_DIRECTOR_RUNS_2026-11-19.md#research-sets-breakdown-of-json-size-by-columnkey-supabase-read-only-sql) | Shallow-копии разделяют вложенные объекты, рекурсивная сериализация создаёт новые контейнеры. Текстовый объём не равен RSS. |
| Исследование → повторный inspect | После исследования Director повторно читает контекст и хранит результат исследования/ingestion. Автономный state удерживает `last_result`; шаги могут повторяться в одном цикле. [Research](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/director.py#L2424-L2478) · [Autonomy](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/autonomy.py#L394-L468) | Нет непрерывных замеров удержания/освобождения; повторный inspect не обязательно снова загружает весь DATA. |
| Assessment и логи | `_memory_state_summary` срезает список до пяти элементов, сохраняя полные вложенные записи. `json.dumps` вызывается для basis и work_plan до передачи в logger. Сохранённая выдача логов включает обрезанные сообщения по 100 000 символов. [Сводка](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/director.py#L888-L905) · [Логи](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/director.py#L2575-L2648) | Срез сам по себе копирует ссылки. Повторное JSON-кодирование создаёт строки, реальный размер сообщения больше либо равен видимой длине при обрезке. |
| Цикл → сохранение | `DirectorCycle.to_dict()` вызывает `asdict`; затем `server.serialize` повторно строит dict/list. Сериализованный результат передаётся в partial run, отдельный result, затем final run. `update_run` читает прежний JSON и отправляет объединённый документ. [Dataclass](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/autonomy.py#L108-L119) · [Serialize](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L303-L343) · [Writes](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2778-L2901) · [PATCH](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1234-L1245) | `asdict` копирует вложенные контейнеры; Python может переиспользовать неизменяемые строки. Объём повторных HTTP payload и пиковая память реального клиента не измерены. |

**Статус M04: в работе.** Воспроизведён ограниченный локальный профиль
сериализации и накопления на синтетических данных. Для приёмки остаются
профиль полного цикла с подменёнными внешними сервисами, достаточная
корреляция исторических фаз по instance/deploy/run ID и свидетельство
причины поздней остановки после 18:29 UTC. Доказательства и команда
воспроизведения в [офлайн-спецификации](MEMORY_2_OFFLINE_TEST_SPEC.md#m04--локальная-фикстура-ram).
