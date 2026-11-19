# Трассировка реализации — первый проход

Дата: 2026-11-19. Статус: **проверено только наличие и маршрутизация кода**, не подтверждена сквозная работоспособность. Связь с `REQUIREMENTS_MATRIX.md`.

| Требование | Файлы и функции (проверены в main) | Что установлено | Чего не хватает для приёмки |
|---|---|---|---|
| R-01 / R-05 / R-07 | `site-insight-engine/director/director.py`: `inspect`, `plan_research`, `decide`, `run_autonomous_cycle` | Существуют методы планирования и автономного цикла | Доказательства вызовов, результатов и сохранения |
| R-06 | `site-insight-engine/server.py`: `_run_director`, `_run_director_once`, `_director_run_heartbeat`, `_execute_autonomous_cycle`, `_autonomous_worker_loop`; `ai-youtube-system/scheduler.py` | Есть несколько путей запуска; интервал в отдельном scheduler.py по умолчанию 21600 с | Установить фактически используемый триггер и расписание по конфигурации и логам |
| R-08 | `site-insight-engine/director/director.py`: `plan_research`, `_autonomy_research`; `director/research_executor.py` | Есть исполнитель исследования | Проверить реальные входы, MCP-вызовы, ошибки и сохранение |
| R-09 / R-12 | `site-insight-engine/director/director.py`: `analyze`, `decide`, `create_recommendation`; `server.py`: `director_recommendations`, `recommendation_action` | Есть путь формирования и API выдачи рекомендаций | Проверить входные данные, записи в БД, реальный UI |
| R-12 / R-14 | `site-insight-engine/server.py`: `director_chat`, `director_feedback`, `recommendation_action` | API обсуждения и обратной связи присутствуют | Проверить сценарии и влияние решений на будущие циклы |
| R-17 | `ai-youtube-system/server.py`: `director_run`, `engine_request`; `site-insight-engine/server.py`: `director_run_get`, `director_run_post` | **Проверен контракт:** внешний POST `ai-youtube-system /director/run` проксируется как GET `site-insight-engine /director/run`; GET поддерживается явно для обратной совместимости | Проверить рабочие адреса и реальные HTTP-ответы; это не доказательство успешного цикла |

## Риски, требующие доказательств

1. `ai-youtube-system/scheduler.py` отправляет POST на конфигурируемый `DIRECTOR_URL`. Само существование файла не доказывает, что scheduler запускается в Render.
2. Наличие методов `create_recommendation` и маршрута `/director/recommendations` не доказывает, что рекомендации сохраняются и видны пользователю.
3. Проверка пробуждений Render отделена от дефектов выполнения самого Директора; механизм пробуждения пока не изменять.

## Следующая проверка

Сопоставить фактические production-логи и записи `director_runs` с путями `_run_director` и `_execute_autonomous_cycle`, установить последнее подтверждённое звено и первую точку потери результата. Никаких живых YouTube-вызовов в рамках этого чтения.
