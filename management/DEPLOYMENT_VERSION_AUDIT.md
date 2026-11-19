# №007 — рабочие ветки, версии и автодеплой

**Дата проверки:** 2026-11-19. **Статус:** завершено в пределах инвентаризации конфигурации и активных деплоев. Источники: Render `list_services` и `list_deploys`, GitHub inventory №002.

| Render service | GitHub repository | Render branch | Auto-deploy | Current Render deployment | Live commit | Commit date |
|---|---|---|---|---|---|---|
| `ai-youtube-system` | `peonyrhodo-bit/ai-youtube-system` | `main` | `yes`, trigger `commit` | `dep-daharu9t0dsc73dslegg` | `bf119e2f834efcd63bb8ee0c95dab4a405958348` | 2026-09-10 |
| `site-insight-engine` | `peonyrhodo-bit/site-insight-engine` | `main` | `yes`, trigger `commit` | `dep-dbsa40v4bgms73fng8ug` | `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc` | 2026-11-14 |
| `youtube-mcp` | `peonyrhodo-bit/youtube-mcp` | `main` | `yes`, trigger `commit` | `dep-dbvfvmbu2v8c73foid1g` | `5772895a8b79ab8c575ea366f70e837303e46b00` | 2026-11-19 |

Each of these deployments has Render status `live`, and trigger `new_commit`. This confirms the Render deploy association, not that every application feature works. Older deployments in the history have status `deactivated`.

**Important distinctions:**
- The management audit branch `project-management/director-audit-2026-11-19` is separate from production `main` and is **not** configured as the Render deploy branch.
- The orchestrator is running a substantially older commit (September) than the Director and MCP (November); no conclusion of incompatibility is warranted without API compatibility tests.
- `autoDeploy=yes` confirms configured behavior, not guaranteed deployment for every future commit; the observed `new_commit` deploys support historical operation.
- No GitHub `main` head-versus-deployed-SHA equality check was performed; do not infer that deployed commit is identical to latest repo head.

**Evidence/closure:** repository binding, branch, deploy policy, live deployment SHA and historical trigger all checked for all three services. №007 completed. Follow-up functional checks belong to №010, №011 and №058.
