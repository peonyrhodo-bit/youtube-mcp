# План устранения OOM — Director 3.0

**Создан:** 2026-11-19. **Статус:** активен. **Прогресс:** 2/8. **Текущий шаг:** OOM-03. **Основной план:** 6/60; №006 заблокирован, №008 ожидает возобновления.

## Цель и ограничения

Вернуть стабильную доступность `site-insight-engine` без расхода YouTube-квоты и без скрытых изменений production. Все действия по умолчанию read-only. **Код, конфигурацию, деплой, тариф, автономный режим и БД не менять без отдельного согласования владельца.** Не вызывать `/director/run`.

## Подтверждённая отправная точка

- Render `server_failed` с `oomKilled.memoryLimit=512Mi` неоднократно 2026-11-19 (например, 17:22:21, 17:24:09, 17:27:37, 17:29:52 UTC).
- Render memory metric в 16:18 UTC: 536715260 байт при лимите 536870900 байт.
- Автономный worker запускается после старта; `WakeupReason.SCHEDULED` и `WakeupReason.RETRY` ошибки предшествовали как минимум одному OOM. **Корреляция, не доказательство причинности.**
- Пользователь наблюдал HTTP 503 главной страницы. См. `management/SERVICE_NETWORK_MAP.md`.

## Контрольные этапы

- ✅ **OOM-01** — Собрать точные стеки ошибок, временную шкалу OOM и показания памяти; отделить симптомы от причин.
- ✅ **OOM-02** — Прочитать путь автономного запуска, retry и загрузки памяти в фактически развёрнутой версии; построить гипотезы.
- 🔄 **OOM-03** — Проверить гипотезы безопасно (логи, статический анализ, существующие тесты); указать, что не подтверждено.
- ⬜ **OOM-04** — Подготовить минимальное исправление, оценку рисков, критерии отката и конкретную задачу на изменение.
- ⬜ **OOM-05** — Получить отдельное разрешение владельца на выбранные изменения production/кода/настроек.
- ⬜ **OOM-06** — Реализовать согласованное изменение в ограниченном объёме, с тестами и ссылками на коммиты/PR.
- ⬜ **OOM-07** — Проверить поведение после разрешённого деплоя: доступность, память, перезапуски, ошибки, автономный цикл; без платных API.
- ⬜ **OOM-08** — Зафиксировать результат, остаточные риски и возврат к №006, затем №008 основного плана.

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
