# Codex task — Director research-set context memory (proposal only)

Status: **NOT APPROVED / NOT IMPLEMENTED**. Audit baseline: deployed site-insight-engine commit `f95bc0e4b68a083d8acf3bb09c1c8d4c3e9762dc`. Production budget 512 MiB. Do not modify production or run quota-consuming tests without separate approval.

## Verified problem mechanism

- Supabase read-only aggregates: 68 `research_sets` rows contain ~7,969,895 bytes of JSON text; `metadata.research_plan` 5,484,208 bytes and `metadata.operation_results` 1,768,295 bytes.
- `server.py:1478–1491`: `DataAdapter.get_project_state()` recursively serializes full `ResearchSetManager.all()`, including metadata, into new dict/list objects. `server.py:303–340` recursive serializer.
- `director/director.py:586–595,851–879`: `Director.inspect()` merges full state; unknown `research_sets` key persists as `DirectorContext.metadata['research_sets']`. The AI decision context is explicitly whitelisted (`director/director.py:330–386`) and does not directly include it.
- `data/research_sets.py:688–715,1213–1217`: `ResearchSet.summary()` and `ResearchSetManager.summaries()` already provide compact representations excluding heavy metadata.
- **Compatibility blocker:** `server.py:4006–4022` GET `/radar-debug` and `server.py:4032–4050` GET `/radar` both return `serialize(await runtime.data.get_project_state(...))`. Replacing full `research_sets` in the shared method would change these HTTP contracts. No external consumer inventory completed.

## Candidate design for implementation review

Introduce a Director-only compact state projection (or opt-in `include_full_research_sets` argument with backwards-compatible default) so `Director.inspect()` receives only `research_manager.summaries()` while existing `/radar` and `/radar-debug` contracts remain unchanged. Prefer a dedicated lightweight method/flag that avoids constructing full `research_sets` in the first place; do not generate full list and then trim. Keep full `ResearchSetManager`, `ResearchSet.to_dict()`, Supabase persistence, research deduplication and evidence drill-down unchanged. Consider memory impact of full debug endpoint separately.

## Acceptance tests (local synthetic fixtures, no external calls)

1. With 68 synthetic research sets whose `metadata` contains realistic ~100KB research plans/results, assert Director projection omits large nested metadata and contains required summary fields and correct `research_set_count`.
2. Assert original full `get_project_state()` result and `/radar`, `/radar-debug` JSON structures remain compatible, including full `research_sets[*].metadata` (unless explicit separate contract approval).
3. Assert Director AI bounded payload, research_history, decisions, recommendations, research deduplication and persistence of full research plans/results unchanged.
4. Measure process peak RSS and Python allocations before/after with repeatable isolated fixture; report baseline, peak and delta. Avoid claiming improvement from JSON sizes alone. Test under a 512MiB equivalent limit where feasible.
5. Cover empty/partial Supabase reads, exceptions and concurrent Director cycles; verify compact mode never silently reports complete when data is partial.
6. Search all repository modules/tests and external documented clients for `get_project_state`, `/radar`, `/radar-debug` and `research_sets` before code change. Inspect any generic `DirectorContext.to_dict()` persistence paths.

## Gate

No source-code changes, deploys, DB writes, or production calls as part of this management task. Implement only after user authorization and verified baseline. OOM root cause remains unproven; this is a measured data-volume and code-path optimization candidate, not a confirmed fix.

## Additional endpoint/call-path audit (deployed f95bc0e)

- `GET /director/snapshot` (`server.py:2267–2273`) explicitly awaits `director.inspect()`, which calls `DataAdapter.get_project_state()` and retains full serialized `research_sets` in Director metadata. Thus a read-only snapshot request can trigger this memory-heavy preparation even though its HTTP response is only `get_unified_state_snapshot()`. Include this path in optimization acceptance tests.
- `GET /director-debug` (`server.py:3963–4001`) builds a selected diagnostic payload from an existing Director context and **does not itself call inspect**. Do not conflate it with `GET /radar-debug`, which calls full `get_project_state()`.
- `GET /dashboard` (`server.py:3063+`) calls `director.status()` and memory `get_context()`, not `get_project_state()` in the inspected route start. The cycle handlers `server.py:2481+` and `2763+` call `run_once` and `run_autonomous_cycle`, which can inspect internally; verify actual mode-specific flow before test design.
- `GET /radar` and `GET /radar-debug` remain direct consumers of full `get_project_state()` and are a compatibility gate. Any Director-only compact projection should be selected **before** recursively serializing full research sets; trimming afterward does not eliminate transient allocation.

### Additional acceptance cases

- Verify `/director/snapshot` uses the compact projection and still returns the same unified snapshot shape and accurate counts.
- Verify `/director-debug` remains bounded and does not unexpectedly trigger data reload; distinguish from `/radar-debug` in tests and documentation.
- Verify the shared Runtime/Director instance does not retain stale full `metadata['research_sets']` after switching to compact projection; no silent stale-data regressions.
