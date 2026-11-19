# M02/M04/M16/M19 — контракт компактного контекста памяти (проект, не патч)

Дата: 2026-11-19. Статус: **проект тестов; не принято, production не изменён**.

## Проверенные входы и опасные места

1. `memory/supabase.py:get_context` читает полные `results` через `get_recent_results` (лимит строк, а не байтов).
2. `memory/memory.py:Memory.get_context` (267–325) строит семантический контекст через `_build_memory_context` (327–410); `memory_state.recent_results = results` (404) без проекции.
3. `director/director.py:_memory_state_summary` (888–903) копирует последние 5 записей каждого списка целиком; `work_plan.basis` (2584) включает summary; `project_assessment` и `work_plan` содержат повторные представления basis; `logger.info` (2640–2641) сериализует оба JSON целиком.
4. **Дополнительный читатель:** `memory/memory.py:Memory.snapshot` (879–912) называет ответ compact, но возвращает `state = context['memory_state']` с полными result payload. Его также нужно охватить тестами, иначе защита только Director не закрывает риск.
5. Supabase `director_results.id=9` (`run_id=79`) имеет `pg_column_size(data_json)=2 336 825 B`; он виден в `DIRECTOR WORK PLAN` текущего Render. `pg_column_size` — **не** размер HTTP-ответа или RAM.

## Разделение контрактов (без потери информации)

- **Durable/full:** Supabase сохраняет исходные результаты, временные снимки, решения, рекомендации, задачи, согласия, provenance, статусы, ссылки, версии и точные значения. Запрещено очищать, усекать или заменять `data_json` в хранилище ради RAM.
- **Operational/read-model:** планирование, `memory_state` в контексте Director, `Memory.snapshot`, AI context и диагностические логи получают **компактные представления**, а не вложенный `data_json` предыдущего цикла.
- **Drill-down:** сохранять стабильные `id`, `run_id`, `result_type`, `created_at`, `project_id` (если имеется), `summary` (ограниченная строка), `status` (если имеется), явный `details_omitted`, `source_table=director_results`, `source_record_id`. Для фактов и рекомендаций — ссылки на исходные evidence IDs. Не утверждать, что есть рабочий retrieval endpoint, пока он не проверен.
- **Protection:** pending recommendations/approvals, unresolved decisions, active constraints и unfinished actions нельзя скрывать молча; если они превышают рабочий лимит, сохранять полные счётчики, идентификаторы, явную неполноту и блокировать действия, требующие невидимых ограничений или согласий. Не принимать решения на неполных данных как на полных.
- **Read completeness:** `complete`, `partial`, `error`, unavailable сохраняют исходную семантику; отсутствие данных не равно пустому успешному чтению. Не терять ошибки таблиц.
- **Project isolation:** каждый компактный объект и его drill-down должен относиться только к запрошенному project_id, включая legacy записи с отсутствующим project_id; не изменять правила фильтрации без контрактных тестов.

## Offline тесты, обязательные до кода в production

| ID | Вход/действие | Ожидаемое доказательство |
|---|---|---|
| BC-01 | Вложенный synthetic result размером 2.34 MB и 5–20 результатов | Размер JSON operational-context ограничен **заранее согласованным byte cap**, независимо от числа строк; `data_json` не попадает в summary |
| BC-02 | Повторные результаты, содержащие старый `work_plan.basis.memory_state` | Размер нового summary не растёт с глубиной вложения; ни одной рекурсивной копии `data_json` |
| BC-03 | Полный набор source rows до/после вызова | Источники не мутируют, hashes исходного `data_json` равны, durable full results доступны |
| BC-04 | Pending approvals/constraints/decisions > cap | Счётчики и IDs сохранены; статус incomplete виден; запрещено автоматическое согласие/публикация/исполнение |
| BC-05 | `complete`, `partial`, `error`, empty, unavailable | Различимая диагностика и правильное поведение; ошибка не превращается в успешную пустую память |
| BC-06 | Два project_id и legacy записи | Нет cross-project утечек; legacy semantics не изменены |
| BC-07 | `Memory.snapshot` и `Director._memory_state_summary` | Оба не возвращают тяжёлые `data_json`; проверены все пути экспорта |
| BC-08 | Work-plan и assessment logging | Логи содержат только безопасные размеры, IDs, статусы, причины; нет вложенного full JSON; нет чувствительных полей |
| BC-09 | Два и пять раз больше исторических данных | Сравнимые peak RSS, latency и результаты, нет неконтролируемого роста; измерить, а не предполагать |
| BC-10 | Невозможность retrieve full source | Явный unavailable/partial, не подменять источник выдуманным summary |

## Решения, требующие отдельного согласования

1. Числовые byte caps на summary, snapshot и лог: выбирать после baseline profiling M04, не выдавать произвольный порог за проверенный.
2. На каком уровне ограничивать: ранняя проекция в `Memory._build_memory_context` (меньше дальнейших копий) **и** независимый защитный лимит на `Director._memory_state_summary` и `Memory.snapshot`; отдельная задача — избежать первоначальной полной загрузки больших результатов из Supabase, не потеряв full retrieval.
3. Семантика неполных protected collections и точные fail-closed действия; согласовать с ТЗ и тестами.
4. Порядок внедрения: offline tests → code review → отдельное разрешение на production patch/deploy → canary с RSS/latency/quality/quotas → формальная приёмка.

## Ограничение M02

Согласно `MEMORY_INTELLIGENCE_2_PLAN.md`, M02 принимается только после карты **всех читателей/писателей Supabase в Director, MCP и Orchestrator** с методами, путями, полями, объёмами и `update_run`. Закрытие трассы `memory_state` — лишь часть M02; до инвентаризации двух других репозиториев этап остаётся в работе.
