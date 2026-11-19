# Memory 2.0 — first reversible patch changeset (approval pending)

Status: **design only**, 2026-11-19. No production or source-code edits in this changeset. Based on `site-insight-engine@09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae`.

## P0: fix hidden read errors before optimizing size

### Verified code paths

- `memory/supabase.py` imports `MemoryTableReadError` from `memory.read_status` and `get_context` (1132–1202) **already supports** partial/error status and logs table-level failure.
- `get_recent_recommendations` (1569–1624) wraps the complete read/enrichment in `try/except Exception: return []`.
- `get_recent_constraints` (1864–1902) does the same.
- `_recent_for_project` (204–265) converts backend query failure into `MemoryTableReadError(table_name,partial_rows=rows,cause=exc)`; the two broad catches currently erase this status and partial rows.
- `_safe_list` (112+) returns [] on malformed response, another separately testable ambiguity; **do not silently change shared helper** in P0 without compatibility tests.

### Minimal proposed diff (not applied)

1. In `get_recent_recommendations` and `get_recent_constraints`, remove outer `try/except Exception: return []` while preserving existing enrichment behavior. For errors during enrichment, propagate a contextual error rather than declaring successful empty list. If partial rows were fetched, wrap as `MemoryTableReadError` with `partial_rows` so `get_context` can report partial. Ensure no raw payload is logged.
2. Keep `get_context` table-level error handler unchanged unless a failing offline test proves a gap. Confirm `_memory_read.status` becomes `partial` or `error`, never `complete`, on protected-table read failure.
3. Add an explicit autonomous-action guard that **does not treat missing/unavailable constraints or recommendations as permission**; guard design and downstream call sites must be checked before claiming safety. A status change alone is insufficient if callers ignore it.
4. Keep full history, schema, write paths, and FREE_MODE behavior unchanged in P0. Feature flag if any behavior affects existing read callers. No production deployment without approval.

### Exact offline tests (write after approval)

| Test | Setup | Expected |
|---|---|---|
| P0-01 | fake client `recommendations.execute()` raises RuntimeError | `_memory_read.tables.recommendations.status=error`, not complete/empty |
| P0-02 | fake client `constraints.execute()` raises RuntimeError | `_memory_read.tables.constraints.status=error`, not complete/empty |
| P0-03 | fake client returns one page, then raises on next page | `partial`, preserved one-page rows, error reported |
| P0-04 | fake client returns genuine empty list | `complete`, zero rows, no errors |
| P0-05 | enrichment encounters malformed/non-dict data_json | no invented status, no crash where old code accepted it |
| P0-06 | fake autonomous decision when constraints read fails | action requiring consent/constraints blocked, reason explicitly incomplete memory |
| P0-07 | synthetic cross-project nested project_id collision | cannot infer permission from first nested project_id; project isolation tested |
| P0-08 | FREE_MODE memory backend | no regression in supported no-Supabase path |

## P1: bounded results and runs read (separate patch)

Read `director_results` columns `id,created_at,action_id,run_id,result_type,summary` and `director_runs` metadata without `data_json`. Current 8/8 result and 7/7 decision rows match their parent run's project_id, but future/legacy records may not. Design a project-scoped, fail-closed parent-run filter with orphan/mismatch tests. Do not use `SELECT *` for L1 lists. Preserve explicit full-detail lookup.

## P2: context envelope and anti-amplification (separate patch)

Cap serialized L2 context at proposed 64 KiB, preserve protected item IDs and incompleteness, remove historical raw `data_json` from `memory_state`, `snapshot`, work-plan basis and logs. Validate end-to-end run payload size; no claim of lower RSS until P1 input/read profiling.

## Approval and evidence gates

- **Before any source edits:** explicit approval to modify source code in a non-production branch.
- **Before merge/deploy:** separate approval, CI and offline fixtures with reproducible outputs.
- **Before autonomous production canary:** separate approval and baseline RSS/read metrics.
- The management document itself does not constitute approval or a passing test.
