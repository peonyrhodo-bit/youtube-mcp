# Director 3.0 — offline test specification for bounded memory

**2026-11-19; status: executable test design, not yet executed.** No production code, migrations, network or YouTube calls authorized. Source inspected at live Director SHA `09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae`.

## Verified regression points
- `memory/memory.py:399–408` assigns raw `results` to `memory_state.recent_results` and raw events/chat/runs to same state; `context['results']` also remains raw.
- `memory/memory.py:879–912` `snapshot` includes `state=context['memory_state']`, despite compact docstring.
- `director/director.py:888+` `_memory_state_summary` uses `rows[-5:]` without field projection; therefore even row cap 5 does not cap bytes.
- The fixture must exercise **all** raw input channels, not only `memory_state.recent_results`, to prevent bypass.

## Synthetic fixtures (no production PII or data copied)

**F1 nested-large-result:** 2,340,000-character deterministic ASCII `payload` inside a synthetic `director_results.data_json`; embed `work_plan.basis.memory_state.recent_results` of a previous result and two levels of nesting. Use stable synthetic `id=9,run_id=79` only as illustrative IDs, never retrieve live row. Include 5 and 20 results; compare JSON bytes before/after.

**F2 protected overflow:** 150 pending recommendations, 150 active constraints, 150 unresolved decisions, 150 unfinished actions, each with unique IDs, project_id and status. Place a consent-required task near end of list; assert never silently omitted or treated as approved.

**F3 scope:** two projects A/B with overlapping result IDs, legacy null-project records, and matching legacy semantics fixture; ensure no cross-project source IDs in envelope or drill-down.

**F4 read states:** complete/partial/error/unavailable, empty success, missing source, malformed data_json, failed Supabase query. Preserve explicit errors and source counts.

**F5 scale:** baseline 20 results, ×2 and ×5 source history, 1,203 videos, 12,483 snapshots, 30,522 relations using synthetic lightweight rows. No network.

## Tests to implement first (pytest, offline, separate feature branch)

| Test ID | Entry point | Assertion / failure signal |
|---|---|---|
| BM-01 | `Memory.get_context` operational projection | serialized ContextEnvelope <= proposed 65,536 UTF-8 bytes; no 2.34MB marker; `details_omitted=true` |
| BM-02 | `Memory.snapshot` | same cap and no full `data_json` via `state`; counts remain correct |
| BM-03 | `Director._memory_state_summary` | no `rows[-5:]` raw copies; nesting depth does not affect output bytes |
| BM-04 | `Director.inspect` / work-plan basis | project assessment, work plan and final run payload do not embed historical `data_json`; refs point to original IDs |
| BM-05 | `_autonomy_assess` logging | captured log contains IDs/counts/completeness but not synthetic payload marker, secrets, or full basis JSON |
| BM-06 | protected overflow F2 | exact total counts, all IDs retrievable; `partial` when hidden; actions requiring hidden consent/constraints fail closed |
| BM-07 | F3 project scope | no B refs in A envelope, no cross-project drill-down, legacy project rules unchanged |
| BM-08 | F4 read errors | `error` != `complete empty`; original error surfaced; no fake success |
| BM-09 | immutable L0 | SHA256 hashes of synthetic durable rows before/after same; no UPDATE/DELETE SQL emitted |
| BM-10 | F5 scaling | bounded envelope bytes at ×1/×2/×5; measure RSS and wall time separately; no assertion of RAM gains without measurement |
| BM-11 | UTF-8 boundary | Russian/CJK/emoji summaries cap by encoded bytes; valid JSON and no broken Unicode |
| BM-12 | stable order | same input -> same ResultRef order and omitted counts; equal timestamps tie-break by ID |
| BM-13 | retrieval failure | source ref exists but full read fails -> explicit unavailable, never invented source content |
| BM-14 | legacy callers | full history API semantics unchanged; new projection opt-in or feature flag until approved |

## Harness and gates

- Pure fake memory backend implementing existing get_context contract; monkeypatch external clients and network to **raise on any request**. Never connect to live Supabase/Render/YouTube in pytest.
- Use `json.dumps(...,ensure_ascii=False,separators=(',',':'))` and `len(...encode('utf-8'))` for bytes; test both compact context and final serialized work-plan, not just one nested field.
- Use deterministic random seed; assert project isolation, idempotent output and immutability; capture logs with pytest caplog.
- Record per-test peak RSS (if available), runtime and JSON bytes; don't convert Python object bytes to DB storage sizes.
- Feature flag off: old behavior unchanged; flag on: bounded envelope; do not deploy or change production defaults without separate approval.
- Acceptance for **test design**: every known raw-copy entrypoint covered; acceptance for **implementation** only after tests actually run and evidence is recorded. This document does not claim passing tests.

## Immediate implementation order (approval required for code changes)

1. Introduce pure `ResultRef` projection and `ContextEnvelope` builder with deterministic UTF-8 byte budgeting; no database calls in projection.
2. Wire into `Memory.get_context` operational branch and `snapshot`, preserving full history method for drill-down.
3. Wire Director summary/work plan/logs; verify no alternate raw path.
4. Run BM-01…BM-14 on synthetic data, inspect failures, benchmark; only then consider canary/deploy approval.
