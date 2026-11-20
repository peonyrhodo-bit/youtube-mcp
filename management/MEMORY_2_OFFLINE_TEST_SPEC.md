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

## M04 — локальная фикстура RAM

Проверено на Linux x86_64, Python 3.12.14, Director
`09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae`. Скрипт ниже берёт точные
определения сериализации, сводки памяти и dataclass через AST, а также
локальный аккумулятор аналитики. Он не импортирует приложение и не
создаёт Runtime. Все данные синтетические, сеть блокируется через Python
audit hook, дочерние процессы из пустого окружения ограничены по
виртуальной памяти (448 МиБ) и времени (30 секунд). Не запускать приложение
или pytest для этой фикстуры. Код проверен для зафиксированного SHA,
перед переносом на другой SHA проверять извлекаемые определения.

Сценарии full и refs загружают одинаковые synthetic results и research_sets.
Первые имитируют декодирование JSON без затрат HTTP. Анализ использует
реальный потоковый аккумулятор, стадия research создаёт фиксированный
локальный результат, стадия сохранения кодирует имитацию PATCH в памяти.
Refs заменяет исходные данные в **выходной** сводке ссылками, сохраняя
те же ID. Это контрольный вариант, он не использует PR #69 и не определяет
правила хранения или формат production. Масштаб 1/2/5 меняет историю и
число аналитических входов. Окно последних пяти refs по коду остаётся
одного размера, поэтому оно изолирует амплификацию от роста всей истории.

Сохранить следующий блок как `probe.py` во временном каталоге:

```python
import ast
import json
import resource
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import Any

def deny_network(event, args):
    if event.startswith("socket."):
        raise RuntimeError("Offline fixture: socket operation blocked")

sys.addaudithook(deny_network)
resource.setrlimit(resource.RLIMIT_AS, (448 * 2**20, 448 * 2**20))
source = Path(sys.argv[1])
scale = int(sys.argv[2])
assert scale in (1, 2, 5)
variant = sys.argv[3]
assert variant in ("full", "refs")

def extract(path, names, class_name=None):
    tree = ast.parse((source / path).read_text())
    body = tree.body
    if class_name:
        body = next(n.body for n in body if isinstance(n, ast.ClassDef)
                    and n.name == class_name)
    selected = [n for n in body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
                and n.name in names]
    assert {n.name for n in selected} == set(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), path, "exec"), globals())

extract("server.py", {"_process_memory_mb", "serialize"})
extract("director/director.py", {"_memory_state_summary"}, "Director")
extract("director/autonomy.py", {
    "DirectorPhase", "CycleStatus", "DirectorState", "CycleEvent", "DirectorCycle",
})
# This module only defines counters, statistics and the local accumulator.
exec(compile((source / "analytics/streaming.py").read_text(),
             "analytics/streaming.py", "exec"), globals())

def measure(phase, **extra):
    print(json.dumps({"phase": phase, **_process_memory_mb(), **extra}), flush=True)

measure("baseline")
results = []
for i in range(20 * scale):
    size = 2_336_825 if i % 20 in (18, 19) else 512
    results.append(json.loads(json.dumps({
        "id": i, "data_json": {"evidence": "x" * size},
    })))
research_sets = [
    json.loads(json.dumps({"id": i, "metadata": {"research_plan": "r" * 120_000}}))
    for i in range(68 * scale)
]
measure("history", results=len(results), research_sets=len(research_sets))

acc = StreamingYouTubeAnalytics()
for i in range(1203 * scale):
    acc.add_video({"video_id": str(i), "title": f"Synthetic {i}"})
for i in range(12483 * scale):
    acc.add_snapshot({"video_id": str(i % (1203 * scale)), "data_json": {
        "statistics": {"viewCount": i + 100}, "_radar": {"age_hours": 72},
    }})
analytics = acc.to_dict()
measure("analysis")

# Synthetic completed research return, no MCP client or scheduler.
research_result = {"research_sets": research_sets[-5:], "analysis": analytics}
measure("research_fixture")

raw_rows = results[-20:]
rows = (
    [{"id": row["id"], "details_omitted": True} for row in raw_rows]
    if variant == "refs" else raw_rows
)
ctx = SimpleNamespace(context=SimpleNamespace(metadata={
    "memory_state": {"recent_results": rows},
}))
basis = {"memory_state": _memory_state_summary(ctx)}
work_plan = {"basis": basis}
state = DirectorState(last_result=research_result,
                      metadata={"project_assessment": basis, "work_plan": work_plan})
cycle = DirectorCycle(cycle_id="fixture", status=CycleStatus.COMPLETED, state=state)
assert len(basis["memory_state"]["recent_results"]) == 5
measure("before_logs")
basis_bytes = len(json.dumps(basis, ensure_ascii=False).encode("utf-8"))
plan_bytes = len(json.dumps(work_plan, ensure_ascii=False).encode("utf-8"))
measure("logs", basis_bytes=basis_bytes, plan_bytes=plan_bytes)

result = serialize(cycle)
measure("asdict_and_serialize")
patch = {"data_json": {**{"status": "running"}, "result": result}}
patch_bytes = len(json.dumps(patch, ensure_ascii=False).encode("utf-8"))
assert result["state"]["metadata"]["work_plan"]["basis"]["memory_state"]["recent_results"][0]["id"] == rows[-5]["id"]
measure("patch_encoding", patch_bytes=patch_bytes)
```

В существующем локальном checkout Director указанный коммит должен быть
доступен. Команды читают Git без смены ветки, кладут исходники и результаты
во временный каталог. Каждый прогон — отдельный процесс.

```bash
set -euo pipefail
probe_dir=$(mktemp -d)
director_repo=/workspace/site-insight-engine
git -C "$director_repo" archive 09ceb05fbefcd8c6b9093ab03c76731fc5ca95ae \
  server.py director/director.py director/autonomy.py analytics/streaming.py \
  | tar -x -C "$probe_dir"
# Скопируйте блок Python выше в "$probe_dir/probe.py".
for scale in 1 2 5; do
  for variant in full refs; do
    for trial in 1 2 3; do
      timeout 30s env -i PATH="$PATH" python -I "$probe_dir/probe.py" \
        "$probe_dir" "$scale" "$variant" > "$probe_dir/$scale-$variant-$trial.jsonl"
    done
  done
done
```

### Измерения 2026-11-20

18 прогонов завершились с кодом 0. Таблица показывает медианы из трёх
отдельных процессов. RSS/HWM даны в МиБ; значения PATCH — длина
UTF-8 JSON в фикстуре. Сводку измерять в одинаковом окружении, сравнивая
также базовый RSS, а не только абсолютные пики.

| Масштаб / режим | RSS после history | RSS после analysis | RSS после research fixture | HWM после логов | HWM после asdict/serialize | HWM после кодирования PATCH | PATCH, байт |
|---|---:|---:|---:|---:|---:|---:|---:|
| ×1 full | 29,5 | 29,5 | 29,5 | 40,4 | 40,4 | 54,0 | 9 963 452 |
| ×1 refs | 29,4 | 29,5 | 29,5 | 29,5 | 29,5 | 30,5 | 613 020 |
| ×2 full | 41,7 | 41,7 | 41,7 | 52,6 | 52,6 | 66,2 | 9 963 459 |
| ×2 refs | 41,7 | 41,7 | 41,7 | 41,7 | 41,7 | 42,8 | 613 027 |
| ×5 full | 78,4 | 78,4 | 78,5 | 89,4 | 89,4 | 103,0 | 9 963 460 |
| ×5 refs | 78,4 | 78,5 | 78,5 | 78,5 | 78,5 | 79,5 | 613 028 |

Базовый RSS 17,9 МиБ, HWM 20,9 МиБ в медиане. Разброс финального
HWM каждой группы 0–0,1 МиБ. В ×5 синтетический исходный JSON
увеличивает HWM на 23,5 МиБ относительно refs, при одинаковой загрузке.
Отсутствие нового HWM на этапе `asdict_and_serialize` не означает нулевые
аллокации. Реальный цикл может повторно удерживать результаты и
включает больше форматов и вспомогательных буферов.
Этот сценарий проверяет локальный механизм, без воспроизведения
лимита контейнера, сетевых ответов, живых запросов, повторов цикла,
причин kill или graceful shutdown. Следующий офлайн профиль полного
цикла должен использовать только поддельные Supabase/MCP/AI клиенты и
подтверждать отдельно границы фаз, выходные статусы и отсутствие дублей.
