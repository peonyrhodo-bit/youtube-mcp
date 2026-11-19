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

## Cached Director lifetime and stale metadata (deployed f95bc0e)

- `server.py:1751` `Runtime.__init__` creates `self.directors: dict[str, Director] = {}`.
- `server.py:1978–2002` `Runtime.get_director(project_id, mode)` returns an existing Director object for that project, otherwise constructs and caches one. Note: requested `mode` is ignored if the cached object already exists; mode behavior warrants a separate review, not a proven incident.
- `director/director.py:435+` `Director.inspect` updates the existing `self.context` rather than constructing a new context per request.
- `director/director.py:851–879` `_merge_context` assigns unknown nonempty fields into `self.context.metadata`, and does **not delete absent keys**. Therefore if an earlier inspection stored `metadata['research_sets']`, merely omitting that key in later compact responses will leave the prior full serialized list reachable for as long as the cached Director remains alive.

**Implementation requirement:** explicitly clear/replace the obsolete full `metadata['research_sets']` in the Director-specific compact projection path, with careful behavior on partial/unavailable reads (do not erase evidence or report false completeness). A migration/cleanup test must populate the cached Director with full research metadata, invoke compact inspection again, then assert old full payload is not reachable via Director context; verify snapshot, state and status remain correct. Do not indiscriminately clear all context metadata or lose legitimate state. Verify cache behavior across multiple project IDs and mode choices. No code change or live experiment performed.

## Mode-aware cache review (separate concern; no fix in this task)

At deployed `f95bc0e`, `server.py:1978–2002` `Runtime.get_director(project_id, mode)` caches only by `project_id`, returns the existing instance before considering `mode`, and defaults new instances to `DirectorMode.AUTONOMOUS`. `director/director.py:242–271` constructor sets `self.mode=mode` and default `AutonomyConfig(enabled=mode == DirectorMode.AUTONOMOUS)`. `director/director.py:3039–3050` status reports stored mode. Thus a later mode argument cannot change an existing Director's mode or default autonomy configuration. This is verified behavior, **not a demonstrated incident**: inspected `server.py` call sites normally use the autonomous default; explicit autonomous worker passes the same mode. No evidence of a currently requested MANUAL instance in those paths. Keep any mode/cache redesign separate from the research-set projection task; add a regression check that compact projection does not mutate `mode`, `autonomy_config`, or cached instance identity.

## Partial-read and stale-state semantics (verified deployed f95bc0e)

- `server.py:1074–1110` `DataAdapter.get_project_state` initializes `research_sets=[]` and zero-valued `data_inventory`, then attempts loaders. `server.py:1186–1243` research restore is conditional on loader availability, first project load and a dict result. If research loader returns a non-dict, it is not restored, but the method can still return its result dict with the initial empty `research_sets` (the existing manager may nevertheless be nonempty). This is not an atomic verified-complete project read.
- `server.py:1478–1491` later populates `result['research_sets']` from the *current in-memory registry*, which may reflect a previous successful load rather than the latest Supabase read. `_loaded_project_id` (`server.py:1243`) gates reloading; repeated calls for the same project do not automatically re-fetch research.
- `director/director.py:586–617` `inspect` marks `runtime_health['project_data']['status']='healthy'` whenever the data service returns a dict; it marks degraded for non-dict, unavailable on raised exception. The returned dict is not independently checked for table-by-table freshness/completeness here. Do **not** interpret this healthy flag as proof that research tables were freshly read.
- `director/director.py:851–879` `_merge_context` stores unknown keys such as `research_sets` in metadata even when the value is an empty list; for known context collections, empty values are skipped unless `replace_empty=True`. Therefore proposed cleanup must distinguish: stale *duplicate projection* safe to drop vs authoritative live registry/evidence that must survive transient failed reads.

**Required test matrix:** (a) complete initial research load; (b) loader exception; (c) non-dict research result; (d) same-project cached registry/no reload; (e) fresh empty project; (f) partial table results; (g) switch between project IDs on one Runtime (check registry scoping). Assert status is not falsely upgraded by the *new* compact projection, no evidence is silently deleted, and stale serialized `metadata['research_sets']` is removed when appropriate without clearing authoritative `ResearchSetManager`. Any improvement to existing health classification is a separate behavioral change requiring approval.

## Shared mutable DATA adapter / cross-project isolation (deployed f95bc0e)

- `server.py:1675–1687` Runtime creates **one** `self.data=DataAdapter(storage=self.memory.backend)`; `server.py:1978–2002` passes this same adapter into every per-project cached Director.
- `server.py:698–752` DataAdapter owns one set of mutable `youtube_registry`, `research_manager`, `relations`, `opportunity_registry` and one `_loaded_project_id` flag, not a per-project registry map.
- `server.py:1126–1245` a project switch can clear/repopulate YouTube and research registries, replace opportunity registry and set `_loaded_project_id` at the end. There is no visible lock around the whole `get_project_state` load; awaits on storage allow overlapping calls. The exact exploitability and cross-project data exposure are **not established** and require controlled tests.
- `server.py:1437–1458` inventory counts can fall back to the current shared registries; if loading fails/returns partial data after a project switch, these may not reflect the requested project. This is a test hypothesis, not a demonstrated leak.

**Separate safety gate before memory implementation:** create isolated local tests with project A and B fixtures, disjoint research IDs/video IDs and mocked storage. Test A→B→A sequential requests, overlapping `asyncio.gather` A/B reads with controlled await interleaving, loader exception/non-dict for B after A, and cached Director A snapshot after B. Assert project IDs, observations, counts, research summaries, relations and persisted full metadata never mix. Verify any new compact method uses the same project-isolation safeguards and does not increase cross-project exposure. If isolation fails, treat as a separate safety defect requiring approval and priority review; do not opportunistically refactor storage during this memory-only task. No production execution or code modifications made.
