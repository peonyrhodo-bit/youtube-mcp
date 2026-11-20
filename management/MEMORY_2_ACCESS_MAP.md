# M02 — карта обращений к памяти

**Статус:** в работе. Последняя [сводная карта исходников](#m02--сводная-карта-исходников-2026-11-20) датирована 2026-11-20. Ниже также сохранены исторические наблюдения от 2026-11-19.

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

## M02 — сводная карта исходников, 2026-11-20

Эта секция уточняет предыдущие частичные инвентаризации. **Подтверждено**
означает, что операция и условный путь вызова прослежены в зафиксированном
исходнике. **Риск** означает воспроизводимое свойство реализации или
ограничение доказательств. **Не проверено** означает, что вызов, привязка
среды или фактический объём не установлены. Указанные размеры выборок — по
коду, исторические замеры отдельно. Запросы к Supabase, Render и YouTube
во время этой сверки не выполнялись.

| Сервис | Версия и граница инспекции | Статус |
|---|---|---|
| Director / site-insight-engine | `09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae` (main). Сверили все места `.table`, фабрику клиента, прямой PostgreSQL, динамические вызовы адаптеров, HTTP и фоновые маршруты. Относительно исторического `f95bc0e` в runtime менялся только размер страницы `_recent_for_project`: 1000 → 50. | Подтверждено по Git. Текущая запущенная конфигурация не проверена. |
| YouTube MCP / youtube-mcp | `5772895a8b79ab8c575ea366f70e837303e46b00` (main и ранее зафиксированный live SHA). В дереве runtime один Python-модуль и Dockerfile. Не найден прямой драйвер Supabase/PG, REST/RPC или DB-вызов. | Подтверждён косвенный путь квоты через Director. |
| Orchestrator / ai-youtube-system | `bf119e2f834efcd63bb8ee0c95dab4a405958348` (исторический live), `9ee2cd31d03fc46064fb35b56fc1f2f9475a3ef6` (main). Сверены `server.py`, `scheduler.py`, `service_watchdog.py`, `backup.py`, зависимости, Docker/Compose и workflow. Прямого SQL/REST клиента Supabase в этих деревьях не обнаружено. | Подтверждены прокси и диагностические маршруты. Реальные настройки окружения не проверены. |

### Входные маршруты и адаптеры

Далее D — Director в указанной версии. Точные ссылки на код привязаны к SHA.
Одна строка в таблице хранения может иметь несколько входных маршрутов.

| ID | Вызов и доказательство | Статус |
|---|---|---|
| A1 | D GET/POST `/director/run` → обычный цикл, при ключе идемпотентности полный просмотр истории, резервирование, результат/ошибка. D POST `/director/autonomous/run`, startup worker и обрабатываемые им wakeup/cron → блокировка на проект в процессе → регистрация цикла → heartbeat → этапы и финальная запись. Само получение wakeup/cron не доказывает успешный цикл. [D server.py:2304–2439](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2304-L2439) [D server.py:2490–2675](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2490-L2675) [D server.py:2693–3056](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2693-L3056) [D server.py:3803–3877](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3803-L3877) [D server.py:4082–4109](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L4082-L4109) | Подтверждено |
| A2 | D `Runtime.get_director` передаёт `ServerMemory` и `DataAdapter`. `inspect` вызывает контекст памяти и состояние DATA. Входы: обычный и автономный циклы, snapshot, продолжение цикла из чата и повторная инспекция после исполнения исследования. `/director/status` и команда чата о статусе используют уже имеющееся состояние. [D server.py:1978–2005](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1978-L2005) [D server.py:2267–2301](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2267-L2301) [D director/director.py:432–617](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/director.py#L432-L617) [D server.py:3419–3639](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3419-L3639) [D server.py:3689–3717](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3689-L3717) | Подтверждено |
| A3 | D dashboard, рекомендации (список, карточка, действие), events и history → `ServerMemory.get_context` → `Memory.get_context` → Supabase; каждый просит все восемь коллекций. Действие по рекомендации просит до 100 каждой, `/director/history` передаёт пользовательский `limit` всем коллекциям. [D server.py:3064–3242](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3064-L3242) [D server.py:3880–3957](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3880-L3957) [D memory/director_adapter.py:600–670](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L600-L670) [D memory/memory.py:267–325](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/memory.py#L267-L325) | Подтверждено; риск нагрузки и 404 для записи вне окна |
| A4 | D `/radar`, `/radar-debug` и A2 → `DataAdapter.get_project_state`. D `Runtime` передаёт тот же backend в `DataAdapter` и в реальный research executor. `/director-debug` сериализует уже собранные снимок, assessment и план. [D server.py:1679–1734](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1679-L1734) [D server.py:1074–1238](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1074-L1238) [D server.py:3964–4052](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3964-L4052) | Подтверждено |
| A5 | D `/director/recommendations/{id}/action` → lookup A3 → явный accept/reject/discuss → feedback. `/director/feedback` → `Director.apply_feedback` → feedback и при наличии ограничения отдельный `save_constraint`. Чат пишет сообщения; чат-обработчик accept/reject сам возвращает подсказку, отдельной записи согласия не производит. `/director/decision`, `/director/result` пишут соответствующие объекты. [D server.py:3188–3415](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3188-L3415) [D director/director.py:2036–2150](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/director.py#L2036-L2150) [D server.py:3548–3582](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3548-L3582) [D server.py:3610–3641](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3610-L3641) [D server.py:3721–3801](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3721-L3801) | Подтверждено по этим маршрутам |
| A6 | Orchestrator POST run → GET D run с параметрами; history → D history; POST chat → POST D chat; events/radar/radar-debug → соответствующие D маршруты A3/A4. Status проверяет D health, director-debug читает локальные диагностические структуры D. `scheduler.py` шлёт POST во вход Orchestrator по конфигурации, watchdog делает health probes, backup архивирует локальные файлы. [O server.py:34–76](https://github.com/peonyrhodo-bit/ai-youtube-system/blob/bf119e2f834efcd63bb8ee0c95dab4a405958348/server.py#L34-L76) [O server.py:103–231](https://github.com/peonyrhodo-bit/ai-youtube-system/blob/bf119e2f834efcd63bb8ee0c95dab4a405958348/server.py#L103-L231) [N server.py:58–101](https://github.com/peonyrhodo-bit/ai-youtube-system/blob/9ee2cd31d03fc46064fb35b56fc1f2f9475a3ef6/server.py#L58-L101) [N server.py:128–255](https://github.com/peonyrhodo-bit/ai-youtube-system/blob/9ee2cd31d03fc46064fb35b56fc1f2f9475a3ef6/server.py#L128-L255) [O scheduler.py:8–66](https://github.com/peonyrhodo-bit/ai-youtube-system/blob/bf119e2f834efcd63bb8ee0c95dab4a405958348/scheduler.py#L8-L66) [O service_watchdog.py:28–88](https://github.com/peonyrhodo-bit/ai-youtube-system/blob/bf119e2f834efcd63bb8ee0c95dab4a405958348/service_watchdog.py#L28-L88) [O backup.py:1–37](https://github.com/peonyrhodo-bit/ai-youtube-system/blob/bf119e2f834efcd63bb8ee0c95dab4a405958348/backup.py#L1-L37) [O Dockerfile:1–17](https://github.com/peonyrhodo-bit/ai-youtube-system/blob/bf119e2f834efcd63bb8ee0c95dab4a405958348/Dockerfile#L1-L17) | Подтверждено по коду; запуск дополнительных процессов в целевой среде не проверен |
| A7 | MCP tools get_video_stats/get_channel_stats/search_channels/search_videos/search_trending_videos/search_radar_videos → `youtube_get` → POST `authorize` и после ответа POST `finish` в D. MCP блокирует запрос YouTube при неуспешном допуске. Сбой finish может сорвать возврат результата после уже сделанного вызова. В D internal endpoints проверяют секрет и вызывают менеджер квоты. [Y server.py:41–100](https://github.com/peonyrhodo-bit/youtube-mcp/blob/5772895a8b79ab8c575ea366f70e837303e46b00/server.py#L41-L100) [Y server.py:147–210](https://github.com/peonyrhodo-bit/youtube-mcp/blob/5772895a8b79ab8c575ea366f70e837303e46b00/server.py#L147-L210) [Y server.py:214–289](https://github.com/peonyrhodo-bit/youtube-mcp/blob/5772895a8b79ab8c575ea366f70e837303e46b00/server.py#L214-L289) [Y server.py:414–453](https://github.com/peonyrhodo-bit/youtube-mcp/blob/5772895a8b79ab8c575ea366f70e837303e46b00/server.py#L414-L453) [Y server.py:678–716](https://github.com/peonyrhodo-bit/youtube-mcp/blob/5772895a8b79ab8c575ea366f70e837303e46b00/server.py#L678-L716) [D server.py:2069–2130](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2069-L2130) | Подтверждено по коду; совпадение DB target не проверено |
| A8 | Фабрика сначала выбирает Supabase при настроенных credentials, иначе in-process storage для FREE_MODE или явного memory backend; не каждый маршрут ведёт в PostgREST. Менеджер квоты отдельно выбирает direct PG, локальный SQLite или unavailable. [D memory/director_adapter.py:476–560](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L476-L560) [D memory/supabase.py:75–100](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L75-L100) [D server.py:1679–1715](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1679-L1715) | Подтверждено ветвление; активная конфигурация не проверена |

### PostgREST: память цикла и защищённые записи

**H:** `_recent_for_project` делает SELECT всех полей, страницы 50 со
смещением, сортирует DESC с ID как tie-breaker. Фильтрация Python: прямой
`project_id` имеет приоритет, иначе первый рекурсивно найденный
`data_json.project_id`. Без project ID запрос не изолирует проект.
Набранные строки материализуются; короткая страница трактуется как конец.
Нет ограничения по числу просматриваемых страниц или байтам. Исключение
execute → `MemoryTableReadError` с префиксом. `_safe_list` возвращает
пустой список для неверной формы и отбрасывает не-dict элементы, поэтому
некорректный ответ может имитировать конец истории. Разные offset-запросы
не образуют согласованный снимок. [D memory/supabase.py:112–132](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L112-L132) [D memory/supabase.py:154–265](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L154-L265)

**C:** `get_context` собирает исходы по коллекциям; один сбой даёт
partial/error, а адаптер поднимает `MemoryReadError`. Семантическая сборка
добавляет `memory_state`, включая исходные recent results. Атомарный
in-process backend может вернуть контекст без статусов таблиц. Лимиты
по умолчанию backend: 10 runs, 30 events, по 20 для остальных. Защищённые
коллекции ограничены окном истории, которое не доказывает полноту
открытых/действующих записей. [D memory/supabase.py:1132–1202](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1132-L1202) [D memory/memory.py:267–410](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/memory.py#L267-L410) [D memory/director_adapter.py:637–670](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L637-L670)

Для insert ниже типовой объём — одна строка и вложенный JSON без byte cap.
Клиентские повторы не предусмотрены в самих методах. У insert без
уникального ключа повтор после неоднозначного ответа может создать дубль.
Проект при записи берётся из аргумента/метаданных вызова, если явно не
указано иначе. Фактическая RLS не проверена.

| Метод и маршрут | Таблица, поля, фильтр и объём | Ошибка, повтор и статус |
|---|---|---|
| `get_recent_runs` (A2/A3), `create_run` guard и idempotency lookup (A1) | `director_runs`: H, SELECT *, created_at/id; guard и Supabase lookup используют `limit=None`, держат всю совпавшую историю. Guard повторно проверяет статус и heartbeat, lookup читает ключ, состояние и результат из JSON. [D memory/supabase.py:1247–1260](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1247-L1260) [D memory/director_adapter.py:710–803](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L710-L803) [D server.py:2376–2448](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2376-L2448) | Подтверждено; риск OOM и короткого/несогласованного окна. Исключение lookup ведёт к отказу, если оно не было превращено в пустой успех ниже. |
| `save_run` (A1) | `director_runs`: language, region_code, data_json, при наличии project_id/status/started_at/finished_at/current_step/error_message/updated_at. Возврат ID; guard распознаёт unique violation как конфликт. [D memory/supabase.py:1208–1232](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1208-L1232) [D memory/director_adapter.py:803–827](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L803-L827) | Подтверждено. Наличие и применимость частичного уникального индекса в текущей среде не проверены. |
| `update_run` (A1 и stale recovery) | `director_runs`: SELECT одного `data_json` → whole-row JSON PATCH + lifecycle колонки, WHERE только id, возвращает id. [D memory/supabase.py:1234–1245](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1234-L1245) | Подтверждено; риск потерянного обновления. Детали ниже. |
| `get_recent_decisions/save_decision` (A1/A2/A3/A5) | `decisions`: H created_at/id, insert decision, run_id, data_json. [D memory/supabase.py:1265–1300](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1265-L1300) [D server.py:2548–2565](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2548-L2565) [D server.py:2808–2819](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2808-L2819) [D server.py:3477–3505](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3477-L3505) [D server.py:3721–3764](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3721-L3764) | Подтверждено; ошибку чтения C поднимает, старые решения за пределами окна не покрыты. |
| `get_recent_chat_messages/save_chat_message` (A2/A3/A5) | `chat_messages`: H created_at/id, insert role/message/run_id/data_json. [D memory/supabase.py:1305–1342](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1305-L1342) [D server.py:3610–3641](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3610-L3641) | Подтверждено; запись пары сообщений отдельными вызовами. |
| `get_recent_actions/save_action` (A2/A3) | `director_actions`: H created_at/id, insert action_type, description, run_id, decision_id, status, data_json. [D memory/supabase.py:1347–1388](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1347-L1388) [D memory/memory.py:541–588](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/memory.py#L541-L588) | Чтение подтверждено; writer определён, производственный call site вне обёртки не найден. Полного отбора unfinished и отдельного task reader не найдено. |
| `get_recent_results/save_result` (A1/A2/A3/A5) | `director_results`: H created_at/id, insert result_type, summary, action_id, run_id, data_json. [D memory/supabase.py:1393–1432](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1393-L1432) [D server.py:2583–2600](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2583-L2600) [D server.py:2832–2847](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2832-L2847) [D server.py:3766–3801](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3766-L3801) | Подтверждено; риск OOM и атрибуции legacy. |
| `get_recent_events/save_event` (A1/A2/A3) | `system_events`: H created_at/id, insert event_type/data_json. [D memory/supabase.py:1437–1470](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1437-L1470) [D server.py:2603–2622](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2603-L2622) [D server.py:2848–2863](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2848-L2863) | Подтверждено; чтение события не доказывает фиксацию всех этапов. |
| `get_recent_recommendations/save_recommendation` (A1–A3/A5) | `recommendations`: H id DESC; insert run_id, decision_id, title, description, recommendation_type, topic, region, language, rationale, suggested_action, confidence, priority, status, data_json(source_data, metadata, feedback/result/lesson и lifecycle timestamps). [D memory/supabase.py:1475–1624](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1475-L1624) | Риск: внешний catch возвращает [] при исключении и скрывает partial. 404 lookup и пустой «complete» возможны. |
| `get_recent_constraints/save_constraint` (A2/A3/A5) | `constraints`: H id DESC; insert title/description/type, scope/status, topic/region/language, execution_condition/reason, confidence/priority, три source ID, data_json(active/review/expiry и metadata). [D memory/supabase.py:1777–1902](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1777-L1902) [D memory/director_adapter.py:1093–1130](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L1093-L1130) | Риск: внешний catch возвращает []; newest N не доказывает полноту действующих ограничений. |
| `save_recommendation_feedback/apply_recommendation_feedback` (A5) | INSERT `recommendation_feedback`: recommendation_id, feedback_type, comment, scope, topic, region, language, data_json. Затем PATCH `recommendations.status` по id для accept/reject/defer, без project/version predicate. Записи раздельны. [D memory/supabase.py:1630–1770](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1630-L1770) [D memory/director_adapter.py:934–963](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L934-L963) [D memory/memory.py:704–725](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/memory.py#L704-L725) | Риск: ошибка PATCH проглатывается, повтор может ещё раз записать feedback, non-None ответ не доказывает изменение строки. Отдельного читателя feedback в C нет. |

### PostgREST: данные исследований и аналитики

**I:** `_iter_paginated_rows` читает offset-страницы 500 по умолчанию,
максимум 1000, с заданным ключом сортировки. Проекция * по умолчанию.
Нет общего лимита страниц или байт. Сканеры наследуют short-page и
`_safe_list`, ошибка execute прерывает чтение. `_summarize_project_table`
фильтрует как H, читает *, ограничивает счётчики меток, однако проходит
все страницы. `DataAdapter.get_project_state` переносит данные в общие
реестры, отслеживает один `_loaded_project_id`, ловит ошибки загрузки и
сборки объектов. Переключение проектов может повторить полные сканы;
попадание в кэш не доказывает свежесть. [D memory/supabase.py:271–303](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L271-L303) [D memory/supabase.py:809–854](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L809-L854) [D server.py:1108–1258](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1108-L1258)

**E:** реальный `ResearchExecutor` вызывает storage через `asyncio.to_thread`;
для обновления известных видео, завершения сбора, query status и ledger
есть несколько отдельных точек записи. При completed/partial и отсутствии признака persisted Director вызывает
`DataAdapter.ingest_research_execution`. Он записывает те же категории из
сырого результата, в частности сериализует все связи реестра. Во всех
батчах предыдущие HTTP/SQL операции могут сохраниться при падении следующей;
перезапрос чтения и повтор бизнес-операции имеют разные последствия.
[D director/research_executor.py:495–523](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L495-L523) [D director/research_executor.py:625–661](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L625-L661) [D director/research_executor.py:905–950](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L905-L950) [D director/research_executor.py:1025–1053](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L1025-L1053) [D director/research_executor.py:1230–1258](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L1230-L1258) [D director/research_executor.py:1304–1459](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L1304-L1459) [D director/research_executor.py:1555–1577](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L1555-L1577) [D director/research_executor.py:1674–1698](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L1674-L1698) [D director/director.py:2427–2456](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/director.py#L2427-L2456) [D server.py:945–1026](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L945-L1026)

| Метод и маршрут | Таблица, поля, фильтр и объём | Ошибка, повтор и статус |
|---|---|---|
| `load_youtube_analysis_data` (A2/A4, основной DATA reader) | `videos` → video_id/data_json/first_seen/last_seen, asc video_id; `video_snapshots` → id/video_id/created_at/data_json, desc id. I сканирует все страницы; Python scope, снимки без owner исключаются с partial. Рабочая выборка 3000 videos/6000 snapshots (макс. 10000/20000) и 100 top evidence по умолчанию. [D memory/supabase.py:462–622](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L462-L622) [D server.py:1108–1165](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1108-L1165) [D analytics/streaming.py:1–136](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/analytics/streaming.py#L1-L136) | Подтверждено; ограничение удерживаемых строк не гарантирует объём HTTP или RSS, агрегаты растут с сущностями. |
| `load_youtube_data` (A4 fallback, E обновление известных видео) | Те же две таблицы по I с SELECT *, все подходящие videos и 2 снимка/видео по умолчанию, 1–20 настраивается. Отсутствующий project снимка может наследоваться через известный video_id. Старые payload остаются в metadata видео. [D memory/supabase.py:305–459](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L305-L459) [D director/research_executor.py:495–523](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L495-L523) | Подтверждён прямой вызов E; риск полной материализации и расхождения атрибуции с compact loader. |
| `iter_video_evidence` | `videos` by video_id limit 1, data_json/first_seen/last_seen; `video_snapshots` by video_id, id/video_id/created_at/data_json, desc id, offset 500; параметра проекта и фильтра owner нет. [D memory/supabase.py:625–675](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L625-L675) [D server.py:1062–1072](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1062-L1072) | Метод и обёртка подтверждены. В текущем D нет production call site обёртки по статическому поиску. Риск при будущем подключении: scope определяется после получения JSON. |
| `save_youtube_data` (E) | `videos` upsert по video_id, пишет video_id/data_json/first_seen/last_seen, возвращает video_id; owner в JSON переписывается проектом вызова. `video_snapshots` insert video_id/JSON с project_id/snapshot_id/research_id/query_ids/statistics, возвращает id/video_id/data_json. Батчи 100 по умолчанию (1–500); все payload, ответы снимков и ID накапливаются. [D memory/supabase.py:677–806](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L677-L806) | Подтверждено; ключ видео глобальный, второй проект может заменить JSON первого. Снимки insert без on_conflict, повтор может дублировать. |
| `load_research_data` (A2/A4) | `youtube_queries` / `research_sets` / `data_relations`: H id DESC до 2000/1000/5000 строк, затем полный I-скан тех же таблиц для распределений status/lang/region или типов связей. SELECT *, Python scope. [D memory/supabase.py:856–878](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L856-L878) [D server.py:1187–1244](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1187-L1244) | Подтверждено; риск двойного чтения и накопления исторических связей. |
| `save_research_data`, `save_youtube_query`, `save_research_set` (E) | `youtube_queries` по project_id/query_id: text/language/region/metadata/source/status. `research_sets` по project_id/research_id: name/objective, языки/регионы, ID запросов/видео/снимков, gathered/missing/expected и reusable/reused, source/status, timestamps/metadata. По одному upsert/строке, возврат id. [D memory/supabase.py:880–912](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L880-L912) [D memory/supabase.py:975–992](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L975-L992) | Подтверждено; повтор по тому же ключу заменяет поля, накопительные массивы без byte cap. |
| `save_data_relations`, `save_data_relation` (E) | `data_relations`: project_id, source_type/source_id, relation, target_type/target_id — составной ключ; metadata, возврат id. Bulk дедуплицирует вход перед единственным upsert массива. Single-row вариант определён отдельно. [D memory/supabase.py:915–992](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L915-L992) | Bulk подтверждён; production call site одиночного метода не найден. Нет ограничения массива числом строк или байт. |
| `load_opportunity_data` (A2/A4) | `channels`, `channel_snapshots`, `niches`, `niche_snapshots`: I полный *, затем H * по id или captured_at/id, Python scope. Working set 500/500/250/500 по умолчанию, максимумы 2000/5000/1000/5000. [D memory/supabase.py:994–1052](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L994-L1052) [D server.py:1167–1185](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1167-L1185) | Подтверждено; число сканов и входящий JSON не ограничены объёмом working set. |
| `save_opportunity_data` (E) | Те же 4 таблицы: whitelist идентификаторов, описаний, метрик и timestamps, плюс project_id/data_json. Составные ключи project_id + channel_id/niche_id, для снимков ещё captured_at. Returns id; батчи по 100 (1–500). Списки набираются перед отправкой. [D memory/supabase.py:1054–1126](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1054-L1126) | Подтверждено; повтор по стабильному ключу upsert, не единая транзакция, размер JSON не ограничен. |

### Прямой PostgreSQL: квота

Это отдельный путь к хранилищу, а не REST backend памяти. Scope
глобальный для connection, дня и bucket; теги проекта могут жить в JSON.
Контур подключается через `YOUTUBE_QUOTA_DATABASE_URL`; тождество этой
БД с Supabase project памяти не следует из кода. В таблице ниже нет
offset-пагинации: операции точечные, агрегатные или bounded LIMIT.

| Метод и маршрут | SQL-поля и объём | Ошибка, повтор и статус |
|---|---|---|
| `_connect/_check_schema` (A8) | `SELECT 1 LIMIT 0` по `private.youtube_quota_usage/events`; соединение с 10-секундным connect timeout. [D quota/postgres_youtube_quota.py:25–59](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/quota/postgres_youtube_quota.py#L25-L59) | Подтверждено; фабрика обрабатывает backend startup failure. |
| `_usage_in_connection/get_usage/get_remaining/get_status/get_available_budget` (inspect health, planning, E preflight/finalize, authorize) | SUM(search_calls, other_units) в usage после начала квотного дня. Одна агрегатная строка, число просканированных записей зависит от дня и индексов. [D quota/postgres_youtube_quota.py:62–107](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/quota/postgres_youtube_quota.py#L62-L107) [D quota/postgres_youtube_quota.py:328–360](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/quota/postgres_youtube_quota.py#L328-L360) [D server.py:1890–1915](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L1890-L1915) [D director/research_executor.py:1701–1715](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L1701-L1715) | Подтверждено; ошибка может остановить допуск или пометить состояние недоступным на вызывающем уровне. Для обёртки get_available_budget внешний call site не найден. |
| `preflight_call/record_planned_call/finish_planned_call` (E) | Проверка usage, INSERT events operation/method/bucket/units/planned/remaining_json/metadata_json return id, повторный агрегат usage. Если недостаточно — UPDATE status/reason/finished_at по id AND planned, затем исключение. [D quota/postgres_youtube_quota.py:129–193](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/quota/postgres_youtube_quota.py#L129-L193) [D director/research_executor.py:166–184](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/research_executor.py#L166-L184) | Подтверждено. Planned event не равен фактическому вызову или списанию; повтор создаёт новый event. |
| `authorize_call` (A7) | Транзакция с advisory lock и SUM. INSERT usage created_at/operation/search_calls/other_units/metadata_json при допуске, INSERT events created_at/operation/method/bucket/units/status/remaining_json/metadata_json, return id; при блокировке также reason. При отказе только blocked event. [D quota/postgres_youtube_quota.py:194–280](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/quota/postgres_youtube_quota.py#L194-L280) | Подтверждено; транзакция защищает расход от параллельной проверки в этом пути. Ключа идемпотентности допуска нет, повтор после потери ответа требует сверки. |
| `finish_call` (A7) | SELECT events.metadata_json по id → merge → UPDATE status/reason/finished_at/metadata_json по id. Нет guard на предыдущий статус и нет row lock в SELECT. [D quota/postgres_youtube_quota.py:282–313](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/quota/postgres_youtube_quota.py#L282-L313) | Подтверждено; конкурирующие завершения могут перезаписать metadata/status. |
| `record_usage`, `get_events` | INSERT usage operation/search_calls/other_units/metadata_json; SELECT events id/created_at/operation/method/bucket/units/status/reason/remaining_json/metadata_json/finished_at id DESC LIMIT 1–1000. [D quota/postgres_youtube_quota.py:108–128](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/quota/postgres_youtube_quota.py#L108-L128) [D quota/postgres_youtube_quota.py:315–326](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/quota/postgres_youtube_quota.py#L315-L326) | Методы существуют; вызывающий production route в проверенных деревьях не найден. |

### update_run: конкуренция и два эпизода 57014

1. HTTP run c idempotency key сохраняет terminal status/result или ошибку.
   Автономный worker/manual endpoint создаёт run и запускает heartbeat.
   Во время одного цикла отдельные вызовы записывают initializing,
   director_cycle, partial/result, final/result или failure. При
   регистрации старого запуска другая попытка может вызвать stale recovery.
   [D server.py:2641–2675](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2641-L2675) [D server.py:2693–2729](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2693-L2729) [D server.py:2732–2790](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2732-L2790) [D server.py:2870–2921](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2870-L2921) [D memory/director_adapter.py:747–794](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L747-L794)
2. `ServerMemory.update_run` добавляет project_id/updated_at, делегирует
   в рабочий поток через `Memory.update_run`. Backend делает SELECT
   `data_json` по id, поверхностно объединяет два словаря и отдельным
   PATCH заменяет весь JSON, включая дублируемые lifecycle поля из
   входного patch. Нет транзакции, сравнения версии/статуса, блокировки
   строки или фильтра project_id в обоих HTTP запросах. Пустой результат
   вызывает ошибку на уровне адаптера. [D memory/director_adapter.py:565–570](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L565-L570) [D memory/director_adapter.py:829–844](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L829-L844) [D memory/memory.py:429–434](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/memory.py#L429-L434) [D memory/supabase.py:1234–1245](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1234-L1245)
3. Конкретная гонка: heartbeat и запись результата читают прежний JSON
   A; результат пишет A + result, затем heartbeat пишет A + updated_at.
   В колонках status может сохраниться новое значение, а в JSON
   исчезнуть результат или остаться устаревший статус. При обратном
   порядке теряется обновление heartbeat. Процессная блокировка охватывает
   цикл, heartbeat создан внутри этого цикла и пишет без собственной
   синхронизации. Отмена ожидающего `to_thread` не откатывает уже начатую
   блокирующую операцию. Частичный уникальный индекс защищает регистрацию
   активных строк, но не этот merge. Это доказуемая возможность по коду,
   регистрация такого исхода в целевой среде не установлена.
   [D server.py:2693–2729](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2693-L2729) [D server.py:2752–2790](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2752-L2790) [D server.py:2885–2921](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2885-L2921) [D supabase/migrations/20261011000000_director_run_lifecycle.sql:1–23](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/supabase/migrations/20261011000000_director_run_lifecycle.sql#L1-L23)
4. [Исторический журнал OOM](OOM_RECOVERY_PLAN.md) фиксирует два
   разных обнаружения 57014: GET полной истории (17:20 UTC) и PATCH
   `id=222` (18:26 UTC, 2026-11-19). Сохранённый JSON строки 222
   около 472 байт; это не размер отправленного тела PATCH. Тайм-аут
   доказывает отмену statement, а не потерю обновления, блокировку или OOM.
   Не установлены SQL wait/locks, объём тела запроса и причина отмены.
   Первый безопасный шаг — офлайн смоделировать порядок SELECT/PATCH и
   ошибки, затем проектировать условный update или атомарный merge.
   Раздельные статусы этапов не считать подтверждённой записью после
   сбоя; повтор проверять на идемпотентность.

### Защищённое состояние и legacy

- **Риск ложного отсутствия.** Catch в recommendations/constraints
  убирает ошибку всей таблицы; H также может преобразовать неправильную
  форму ответа в пустую страницу. Даже нормальный C complete означает
  успешное чтение окна, а не наличие полного индекса pending/active.
  `Director.inspect` различает partial/error, но на D переход к
  реальному executor не проверяет подтверждённую полноту защищённых
  таблиц. [D memory/supabase.py:1569–1624](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1569-L1624) [D memory/supabase.py:1864–1902](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1864-L1902) [D director/director.py:442–579](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/director.py#L442-L579) [D director/director.py:2375–2414](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/director.py#L2375-L2414)
- **Согласия и отказы.** В текущем коде статус рекомендации и отдельный
  feedback могут разойтись при сбое; прямой `/director/feedback` требует
  самостоятельной проверки допустимых входов и полномочий. Восстановление
  полного журнала явных согласий через C не найдено. Не установлена
  отдельная долговечная задача по §13 для каждого подтверждённого
  согласия. По ТЗ сообщение чата согласия не даёт, а явное согласие
  разрешает только подготовку связанной задачи. Существующий status,
  поле feedback или строку action нельзя объявлять доказательством
  соответствия этому правилу. [D server.py:3252–3415](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3252-L3415) [D server.py:3548–3582](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3548-L3582) [D memory/supabase.py:1695–1769](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1695-L1769)
- **`director_results`.** Фактическая схема из сохранённой
  [проверки §9–10](MEMORY_2_IMPLEMENTATION_BLUEPRINT.md) содержит id,
  created_at, action_id, run_id, result_type, summary, data_json. Прямого
  project_id нет. H использует рекурсивный JSON, без join по run_id.
  Адаптер записи проставляет project_id в JSON через metadata/result,
  а вызывающий путь может положить дополнительный вложенный результат.
  Исторический снимок 8/8 совпадений с parent run отражает только
  просмотренные строки. NULL/отсутствующий run_id, orphan parent,
  конфликт parent/embedded или нескольких вложенных project_id способны
  изменить результат фильтра. Если не найдено ни одного поля, строка
  исключается из project-scoped чтения без отдельной диагностики.
  Подтверждённых утечек нет. До контрактных фикстур сохранить старую
  атрибуцию, при новом компактном чтении возвращать partial/unavailable
  для неоднозначных записей. [D memory/director_adapter.py:965–1029](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/director_adapter.py#L965-L1029) [D memory/supabase.py:168–204](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L168-L204) [D memory/supabase.py:1393–1432](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/supabase.py#L1393-L1432)

### PR #67 и #69

| Изменение | Достижимые вызовы | Статус |
|---|---|---|
| #67, `70608b71647e50480bba9c4d69f3d249587a1dcc` | После применения ветки A2/A3 читают рекомендации и ограничения через C без прежнего внешнего catch. Граница `Director._autonomy_research` проверяет текущее состояние чтения перед executor. Она достижима из POST `/director/autonomous/run` и фонового wakeup worker. Отдельный POST `/director/research` и одноимённая команда чата строят план и эту ветку не вызывают. Проверка не вводит полный индекс защищённых состояний и не исправляет malformed page в H. [P memory/supabase.py:1569–1620](https://github.com/peonyrhodo-bit/site-insight-engine/blob/70608b71647e50480bba9c4d69f3d249587a1dcc/memory/supabase.py#L1569-L1620) [P memory/supabase.py:1861–1897](https://github.com/peonyrhodo-bit/site-insight-engine/blob/70608b71647e50480bba9c4d69f3d249587a1dcc/memory/supabase.py#L1861-L1897) [P director/director.py:432–451](https://github.com/peonyrhodo-bit/site-insight-engine/blob/70608b71647e50480bba9c4d69f3d249587a1dcc/director/director.py#L432-L451) [P director/director.py:2400–2440](https://github.com/peonyrhodo-bit/site-insight-engine/blob/70608b71647e50480bba9c4d69f3d249587a1dcc/director/director.py#L2400-L2440) [D server.py:3441–3450](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3441-L3450) [D server.py:3689–3717](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3689-L3717) | Условный source call graph подтверждён; SHA не предок D, runtime-применение не проверено. |
| #69, `2e8e6f1a6ae5b68ed8b5370332d6a9331392d8bd` | `get_recent_run_refs` читает один projected window до 50 строк, ≤20 refs и экспериментальный выходной cap 64 КиБ после декодирования. По поиску имя встречается только в определении и тестах. Guard/idempotency/context продолжают H. [Q memory/supabase.py:1263–1383](https://github.com/peonyrhodo-bit/site-insight-engine/blob/2e8e6f1a6ae5b68ed8b5370332d6a9331392d8bd/memory/supabase.py#L1263-L1383) [Q tests/test_supabase_run_refs.py:73–259](https://github.com/peonyrhodo-bit/site-insight-engine/blob/2e8e6f1a6ae5b68ed8b5370332d6a9331392d8bd/tests/test_supabase_run_refs.py#L73-L259) | Эксперимент. Ни одного runtime call site в ветке не найдено; SHA не предок D. |

### Критические риски и минимальная безопасная работа

Номера сопоставлены с [матрицей M01](https://github.com/peonyrhodo-bit/youtube-mcp/blob/d4e3bf0f0647008f4f68ab62c193b80e8156139c/management/MEMORY_2_TZ_TRACEABILITY.md).

| Серьёзность | Риск и R-ID | Последствие | Минимальное действие после документальной сверки |
|---|---|---|---|
| Высокая | Ложная пустота protected state, неполнота newest N (R16, R17, R27, R35, R37, R40) | Исследование без учёта ограничений, неверный статус рекомендации | Офлайн тесты error/partial/malformed и blocked executor, отдельно доказать полноту active/pending с правилами атрибуции; никаких изменений legacy semantics до проверки. |
| Высокая | Read–merge–write с heartbeat и stale recovery (R15, R17, R18, R34) | Потерянный результат, разъезд статусов, преждевременный новый запуск | Фикстуры гонки и 57014; проверить компактный heartbeat и условное обновление по проверяемой версии, затем валидировать переходы. |
| Высокая | Полная история run/research и копирование результатов (R12, R15, R17, R18, R34) | Повторный OOM, потеря heartbeat; тяжёлые HTTP и лог-буферы | Измерить отдельно rows/bytes/RSS; ограничить обычные проекции по контракту, оставить full retrieval, исключить вложение прежнего payload в новый план и логи. |
| Высокая | Неоднозначный legacy scope, глобальный upsert videos (R08, R09, R12, R25, R31) | Смешение/утрата наблюдений между проектами | Офлайн фикстуры NULL/orphan/mismatch и video_id в двух проектах; явная неполнота вместо изменения правил владения. |
| Высокая | Раздельный feedback insert и recommendation PATCH, непроверенная задача (R27, R28, R37–R40) | Расхождение решения, статуса и задачи, повторная запись | Проверить explicit action → feedback/status/task на сбоях и повторах в фикстуре; потребовать подтверждённые ID и переходы. |
| Высокая | Quota ledger: исторический разрыв между events/usage и неподтверждённый DB target (R22–R24, R31) | Неверное представление расхода и повтор операции после сбоя | Сопоставить уже доступные обезличенные свидетельства версий/путей/интервалов; офлайн проверить authorize/finish и повторы без вызова квоты. |
| Средняя | Double-scan, unbounded bulk, повторы DATA и registry cache (R09, R12, R17, R34) | Рост RSS/latency, дубли снимков, устаревший или частичный контекст | Профиль типовой фикстуры, ограничить чтение и партии по байтам после проверки; ввести сверку результата до повтора insert. |

**Дополнительный путь усиления памяти:** C сохраняет raw results в
`memory_state` → `Director._memory_state_summary` выбирает последние
элементы целиком → `work_plan.basis` и assessment → JSON-лог → результат
цикла → `director_runs.data_json` и `director_results.data_json`. Snapshot
и диагностические маршруты сериализуют часть тех же структур. Срез по
числу строк ограничивает количество элементов, но может не уменьшать их
размер. Сохранённые ранее SQL-замеры (~2.34/2.42 MB) измеряли storage size,
а не HTTP/RSS. [D memory/memory.py:327–410](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/memory.py#L327-L410) [D memory/memory.py:879–912](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/memory/memory.py#L879-L912) [D director/director.py:888–905](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/director.py#L888-L905) [D director/director.py:2575–2648](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/director/director.py#L2575-L2648) [D server.py:2783–2898](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L2783-L2898) [D server.py:3964–4004](https://github.com/peonyrhodo-bit/site-insight-engine/blob/09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae/server.py#L3964-L4004)

### Условия закрытия

В статических деревьях три сервиса прослежены до sink, включая косвенные
маршруты, и точки без вызывающего пути отмечены. M02 **остаётся открытым**:
не подтверждены фактические маршруты и конфигурации целевой среды
(включая идентичность Supabase REST и quota PG endpoint), реальный объём
по всем путям, полнота защищённого состояния, атрибуция legacy и условия
57014. Для документальной приёмки нужна независимая сверка покрытия sink и
зависимостей. Для оперативных выводов достаточно начать с существующих
обезличенных свидетельств, замеров на фикстурах, конкурентных сценариев
и данных M03/M04, без запуска production-цикла. Причину OOM/57014 и
соответствие ТЗ §18–19 из этой карты принять нельзя.
