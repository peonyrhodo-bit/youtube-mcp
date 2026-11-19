# №006 — сетевые адреса и связи Render-сервисов

**Статус:** проверено частично · 2026-11-19. Источники: Render `list_services` (workspace `tea-dabd4dijnfac73afejug`) и GitHub source. Production не изменялся, внешние запросы не запускались.

## Проверенные адреса и конфигурация Render

| Сервис | Render ID | Публичный URL | Репозиторий | Ветка | Регион | План |
|---|---|---|---|---|---|---|
| Director engine | `srv-dae6fi61egvs73b4pa90` | https://site-insight-engine.onrender.com | `peonyrhodo-bit/site-insight-engine` | `main` | `oregon` | `free` |
| YouTube MCP | `srv-dadh2su1egvs73ddi04g` | https://youtube-mcp-u39z.onrender.com | `peonyrhodo-bit/youtube-mcp` | `main` | `oregon` | `free` |
| Orchestrator | `srv-dag8tl2d0e5s73af02q0` | https://ai-youtube-system.onrender.com | `peonyrhodo-bit/ai-youtube-system` | `main` | `oregon` | `free` |

Render metadata confirms `autoDeploy=yes` and `autoDeployTrigger=commit` for each service. No health-check path is configured in Render service metadata; this does not imply absence of application health endpoints.

## Logical network edges (code evidence)

1. **Orchestrator → Director:** `ai-youtube-system/server.py:21–24,60–69` uses `ENGINE_URL` with default `http://site-insight-engine:8000`, and `httpx` to request `ENGINE_URL + path`. The default hostname is **not** proof of working Render service discovery. Actual `ENGINE_URL` environment value has not been inspected.
2. **Scheduler → Director:** `ai-youtube-system/scheduler.py:8–15,25–38` posts to `DIRECTOR_URL`, default `http://localhost:8000/director/run`, interval `21600` seconds. This script's execution in the deployed web service is **not established**.
3. **Director → YouTube MCP health:** deployed `site-insight-engine@f95bc0e`, `server.py:1803–1830` probes `YOUTUBE_MCP_URL` or `MCP_URL` + `/health`, timeout 3s, only if configured. The live value is unknown; the health probe is not proof of the full research call path.
4. **Director → Supabase:** backend storage was previously verified in code and through read-only Supabase inventory; actual Render secret values and runtime connection success are outside this inventory and must not be disclosed.

## Remaining acceptance gates

- [x] All three public service URLs, Render IDs, repository bindings, branches and regions confirmed by Render.
- [x] Major logical HTTP edges identified from source.
- [ ] Confirm **without exposing secret values** whether `ENGINE_URL`, `DIRECTOR_URL` (if scheduler active), `YOUTUBE_MCP_URL/MCP_URL` are configured to valid targets in production. Prefer safe status indicators/allowlisted hostname-only checks; do not paste full env dumps.
- [ ] Verify application-level health/status for all three endpoints with read-only calls, accounting for free-tier wakeup; avoid launching Director cycles or YouTube API searches.
- [ ] Trace the actual Director research MCP transport and the active scheduler process before declaring the whole topology operational.

**Reason for not closing №006:** Render URLs and source wiring are proven, but effective runtime target configuration and successful inter-service requests are not. No guessed success claim.
