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

## Follow-up: passive Render log verification (2026-11-19)

Read-only `Render.list_logs` for orchestrator `srv-dag8tl2d0e5s73af02q0`, window 2026-11-18T00:00Z–2026-11-19T16:00Z, confirmed application startup at **2026-11-19 00:26:43 UTC**, Uvicorn listening on `0.0.0.0:10000`, and logged GET `/` HTTP 200 on 2026-11-18. This proves that the orchestrator web app was serving requests at that earlier time, **not** that its proxy to Director succeeded or that it is healthy now. No `DIRECTOR_RUN` or inter-service success was established from this sample.

A narrow `type=request` log query for all three services for 2026-11-19 12:00–16:30Z returned no entries; this is **insufficient evidence** to conclude no requests occurred (request/app log types and retention/filtering differ). Do not interpret an empty filtered query as an outage.

Render integration currently exposes service metadata and logs but no read-only environment-variable getter in the available tool catalog; do not use mutation APIs to infer environment settings. Therefore the configured `ENGINE_URL` and `YOUTUBE_MCP_URL` remain unverified. Safe follow-up: examine sanitized application health output or owner-provided hostname-only settings; do not dump secrets.

## Follow-up: observed Director → Supabase and public MCP HTTP (2026-11-19)

Read-only Render application logs, window 2026-11-18T00:00Z–2026-11-19T17:00Z:

- **Director → Supabase confirmed for reads:** `site-insight-engine` logs at **16:28:32–16:28:40 UTC** show HTTP/2 **200 OK** from `https://oxbxnswywgpdlcfltmbq.supabase.co/rest/v1/` for `director_runs`, `decisions`, `recommendations`, `constraints`, `system_events`, `chat_messages`, `director_actions`, `director_results`. This is actual outbound service connectivity, but not proof of correct project isolation or write permissions.
- **Public MCP web root responded:** `youtube-mcp` logs at **14:00:48**, **15:00:51**, **16:00:47 UTC** show `GET /` **200 OK**. This does **not** prove the MCP tool transport or YouTube API search works.
- **Still open:** orchestrator → Director HTTP request success, Director → MCP research call success, effective production hostname settings. Do not equate a successful root GET with the application integration.

These observations strengthen №006 evidence but do not satisfy all remaining acceptance gates. Status remains **проверено частично**, progress unchanged.
