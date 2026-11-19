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
