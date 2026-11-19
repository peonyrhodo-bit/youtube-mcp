# Memory & Intelligence 2.0 — architecture and retention proposal

**Status:** design only, pending review/approval. **No automatic deletion, migrations, API research, or production deployment authorized by this document.** Date: 2026-11-19. Owner context: Director OOM recovery OOM-07 remains open; this is a separate forward-looking design track.

## Objectives and non-negotiable invariants
1. Design for Render free 512 MiB RAM, without pretending 512 MiB is available to Python alone. Target routine process RSS <=300 MiB, investigate >350 MiB, protect service at >400 MiB; these are *initial proposed* thresholds, validate through profiling.
2. Preserve analytical fidelity and improve explainability, reproducibility, historical comparison, provenance, confidence, and freshness. Never silently drop records or substitute truncated history for complete history.
3. Preserve all current Supabase data; existing schema and adapters remain compatible until measured equivalence and migration/rollback plans are approved.
4. Distinguish RAM reduction, database storage, API quotas, and analytical quality: separate metrics and safeguards.
5. Failed research must not trigger unbounded autonomous retries or consume quota indefinitely. A bounded circuit breaker/backoff should preserve manual override and record explicit failed/partial status.

## Read-only baseline (2026-11-19)
Supabase public tables (pg_total_relation_size, includes indexes/TOAST; pg_stat_user_tables row counts approximate):
- video_snapshots 33,914,880 bytes (~32 MiB), ~12,483 rows
- director_runs 14,524,416 bytes (~14 MiB), ~159 rows
- data_relations 14,213,120 bytes (~14 MiB), ~30,522 rows
- videos 4,046,848 bytes (~3.9 MiB), ~1,203 rows
- director_results 3,817,472 bytes (~3.6 MiB), ~2 rows
- research_sets 3,121,152 bytes (~3 MiB), ~17 rows
- youtube_queries 638,976 bytes, ~378 rows.
This is not the total Supabase project storage quota or actual billed usage. Confirm plan/quota, Postgres size, indexes, TOAST, WAL/backups, Storage objects, and growth rate before setting thresholds.
Render after 50-row pagination patch: memory rose to 486,645,760 bytes (~464 MiB) at 18:29, followed by graceful shutdown; no confirmed OOM event for this shutdown. Earlier Supabase director_runs PATCH id=222 timed out 57014; row data_json only 472 bytes, zero user triggers, id primary key indexed. Root cause remains unproven.

## Proposed architecture
- Supabase remains authoritative system of record. Separate **immutable source observations**, **compact versioned analytical aggregates**, **decision/provenance records**, **ephemeral cache/job state**. Do not treat a summary as a replacement for source data unless the source is verified archived and restorable.
- Director uses a bounded query/working-set interface: server-side project_id and date predicates where compatible; deterministic cursor/keyset pagination on (created_at,id) instead of high OFFSET; bounded selected columns and explicit legacy compatibility path. Avoid loading all videos, 6k snapshots, 5k relations, research history, and duplicate intermediate structures in a single request.
- Batch/stream analytics with bounded windows; calculate incremental aggregates (daily/weekly, cohort, trend, confidence, anomaly) in DB or batch pipeline, with checksums and algorithm_version. For exact historical recomputation, stream source archive or pages without full RAM materialization.
- Write path: explicit state fields and versioned payloads; avoid unnecessary read-merge-write; protect concurrency/idempotency. Do not alter update_run semantics until callers, transactional races and data invariants are mapped.
- AI context retrieval: select relevant, recent, high-quality facts and provenance links; no giant raw JSON prompt. Distinguish known fact, inference, missing evidence, and stale data.
- Quota-aware autonomous scheduler: dedup queries by canonical form+locale+time window, TTL/cache, per-cycle caps, exponential backoff and circuit breaker on repeated youtube_mcp_api_error, no success mark on failed research, bounded retry counts. No live paid API tests without approval.

## Data lifecycle policy — proposed, not enacted
Class A **permanent/protected**: decisions, hypotheses, feedback, recommendation lineage, source references, versioned analytics results, run summaries, provenance, audit records. No automatic deletion.
Class B **historical source**: videos, video_snapshots, channel/niche snapshots, research evidence, relations. Retain full-fidelity source until archive format, manifests, checksum, access control, restore tests, and exact analytical equivalence are proven. Consider tiered access: recent hot records in Supabase; older full-fidelity records in low-cost archival store; keep indexed summaries/metadata in Supabase. No archive provider or cost chosen yet.
Class C **ephemeral**: transient API response caches, redundant transport logs, temporary staging, failed retry artifacts. Define per-table TTL and dependencies only after inventory; delete only after audit and explicit approval.
Deduplicate only on semantically identical keys with preserved lineage; different observation timestamps must never be collapsed. Rollups preserve min/max/first/last/count, sample interval and anomaly indicators, but cannot replace raw data for exact historical analysis.
**Safe retention workflow:** dry-run inventory -> classify records/dependencies -> export/archive -> manifest/checksum -> restore test -> compare analytical outputs -> approve -> limited deletion batch -> monitor storage and quality -> expand. Hard stop on missing provenance, orphaned references, or mismatch. Use soft-delete/quarantine window where feasible. PostgreSQL DELETE does not necessarily immediately shrink allocated database files; plan VACUUM/autovacuum and measure actual storage effects.

## Analytical improvements and measurable gates
- Historical trend comparison across time horizons and cohorts, source coverage, freshness and confidence scores, anomaly flags.
- Version every computed result with source dataset hash/manifest, time range, algorithm version, configuration and completeness; enable deterministic replay.
- Gold-set regression tests: fixed project history, old vs new parity for existing KPI definitions; explain intentional algorithm changes separately. Check trend direction, cohort metrics, dedup correctness, legacy project isolation, time-zone boundaries, missing data and partial reads.
- Performance gates on realistic fixture of >=1,203 videos, >=12,483 snapshots, >=30,522 relations and representative large JSON rows: measure peak RSS, query count/latency, result accuracy, and full-cycle completion. Stress with growth multipliers and failure injection (57014, API 5xx, malformed AI JSON).
- Operational SLOs (initial proposals): no OOM across sustained representative runs; routine RSS <=300 MiB and measured peak comfortably below 512 MiB; bounded retries and no unplanned paid API calls; all historical queries remain reproducible.

## Implementation phases (separate branch, incremental, rollbackable)
0. **Inventory/measurement:** exact Supabase quota/usage, per-table/TOAST/index and time-series growth, retention dependencies, current analytics inputs/outputs, update_run call sites, worker lifecycle and RSS profiler. Read-only only.
1. **Compatibility contracts/tests:** snapshot golden data, schemas, provenance IDs, legacy project matching, output parity, rollback plan. No production behavior change.
2. **Memory-efficient read path:** bounded server-side filtering, keyset pagination, streaming projections, controlled caches; benchmark and deploy behind flag only after tests.
3. **Analytics 2.0:** incremental/versioned summaries, provenance and quality indicators; compare side by side, do not overwrite old results.
4. **Lifecycle/archive:** define archive storage and restore procedure, dry-run cleanup, test restore and parity, seek explicit deletion approval before any destructive action.
5. **Autonomy resilience:** bounded research retries/circuit breaker and quota budget, idempotent run writes; ensure full cycle completes or fails clearly.
6. **Canary/monitor/rollback:** release in small stages, confirm memory, DB growth, quality, cycle success and error budgets; retain old adapter until acceptance.

## Decisions required
- Actual Supabase plan/storage quota and permissible archive provider/budget.
- Whether exact raw historical snapshots must be queryable immediately or can be restored on demand.
- Minimum retention of operational logs/cache; data governance and backup requirements.
- Explicit approval for any future deletion, schema migration, new paid infrastructure, or external API calls.

**Recommendation:** memory efficiency, retention and analytics improvements belong in one architecture program but should be delivered as independent, reversible workstreams. Do not wait for this redesign to mitigate urgent OOM/retry issues safely.

## 2026-11-19 — explicit Director 3.0 specification alignment (authoritative source read)
Source: repository root `тз директор 3,0`, verified Git blob `784efdfeefc394110982aa7e81139f7c3580758c`; the broader `тз` is context, not a replacement for current-stage requirements. **This architecture is subordinate to the specification; it is not a substitute for requirement matrix #009.**

| Director 3.0 requirement (source sections) | Memory 2.0 contract | Retention/cleanup invariant | Verification |
|---|---|---|---|
| §1, §4: autonomous YouTube research; track videos, growth, countries/languages/formats | Immutable observations with source ID, collected_at, locale, format and snapshot chronology; bounded paged retrieval | Preserve repeat measurements and timestamps; archival restores full-fidelity history | Historical growth and cross-market replay on fixed fixtures |
| §3: continuously growing evidence-backed recommendation and task archive | Recommendations linked to versioned evidence, confidence, uncertainties, budget mode and user consent | **Never auto-delete** recommendations, approval decisions, evidence references or resulting tasks | Open old recommendation and reconstruct supporting data |
| §4, §5.2–5.4, §7: project plan, cycle plan, user requests, task progress, priorities and reasons for change survive cycles | Durable queue and append-only transitions; checkpoint/resume, idempotency keys and provenance | No TTL for open/blocked user tasks, approvals, plans or material decision history | Restart mid-task and verify no lost work or duplicates |
| §6: 24 hourly scheduled runs, status of each attempt, no parallel duplicates, distinguish partial/failed/success | Small indexed run state plus bounded append-only event log and durable last-success checkpoint | Preserve auditable outcomes, errors and actual quota use; compress technical traces only with retained summaries and evidence | Simulate restart/timeout and verify exact statuses, no false success |
| §6, §7: failed API calls must not loop forever; quota manager authoritative | Rate-limit/circuit-breaker with per-cycle and per-day budgets, cooldown, dedup and retry history | Do not erase failure history needed to prevent repeated useless research | 4/4 failed search case does not launch endless further searches |
| §2: Director itself costs zero, free tooling only; user-selected production budget | Cost-aware resource governor; budget mode versioned in recommendations | No mandatory paid archive, API or hosting dependencies | Full system runs without any paid service |
| §4: compare predictions with actuals; reuse prior findings; weekly report | Versioned predictive signals, outcomes, historical aggregations, report inputs and source links | Preserve prediction-to-outcome lineage and reporting periods | Prediction-vs-actual comparison and weekly report reproducible |
| §3, §4: user discussion in Russian, evidence-backed explanations | Query compact evidence packets with Russian summaries, source citations and freshness/confidence | Do not purge conversation state, feedback or accepted/rejected recommendation reasons | Russian answer references same stored research and decisions |
| §4, §5: explicit consent before creating downstream video-preparation task; no video creation/publishing at this stage | Durable consent and task linkage, immutable audit trail | Never auto-delete consent or task creation evidence | Verify no task without approval and no out-of-scope action |

### Important corrections to initial design
- **Self-cleaning must not erase the ever-growing recommendation/task archive required by §3.** Growth is managed through compact metadata, dedup, partitioning/archival of source payloads, and indexed retrieval, not erasure of decisions.
- **Zero-budget operation is mandatory in §2.1.** External archival storage is an *option only if free and restorable under verified limits*. Otherwise prioritize bounded storage, lossless compression, and cleanup of strictly ephemeral records; do not promise infinite storage on finite free tiers. Escalate when remaining capacity is insufficient rather than silently deleting valuable data.
- **No automatic deletion until the actual quota, free archive feasibility, retention classification, reference graph and tested recovery are established.** Dry-run + explicit approval required before first destructive production cleanup; thereafter a narrowly approved retention policy may operate automatically within fixed guards, audit log and pause thresholds.
- **Do not conflate memory with intelligence.** Better analytics requires independently measured improvement (coverage, predictive calibration, confidence, evidence completeness, recommendation usefulness) without weakening existing calculations or inventing success.
- The full 55k-character specification requires a clause-by-clause matrix in master plan #009 before implementation; the mapping above is a first, verified subset, not certification of complete coverage.
