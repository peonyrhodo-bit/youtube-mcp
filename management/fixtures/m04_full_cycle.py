import asyncio
from contextlib import asynccontextmanager
import functools
import hashlib
import json
import logging
from pathlib import Path
import resource
import sys
import tempfile
from types import SimpleNamespace as NS

blocked = []

def offline(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname",
                 "socket.sendto", "subprocess.Popen", "os.system"}:
        blocked.append(event)
        raise RuntimeError("External operation blocked by offline fixture")

sys.addaudithook(offline)
resource.setrlimit(resource.RLIMIT_AS, (448 * 2**20, 448 * 2**20))
logging.disable(logging.CRITICAL)
import mcp
import mcp.client.streamable_http as transport
import server
from memory.memory import Memory
from memory.supabase import SupabaseMemoryBackend

mode, scenario = sys.argv[1:]
assert mode in {"full", "refs"}
assert scenario in {"normal", "mcp_error", "write_error"}
marks = []
research_outcomes = []
cycle_no = 0

def mark(name):
    marks.append({"cycle": cycle_no, "phase": name, **server._process_memory_mb()})

def instrument(obj, attr, name):
    original = getattr(obj, attr)

    @functools.wraps(original)
    async def measured(*args, **kwargs):
        mark(name + ":start")
        try:
            value = await original(*args, **kwargs)
            if name == "mcp_executor":
                research_outcomes.append({k: value.get(k) for k in (
                    "status", "persisted", "queries_collected", "queries_failed", "errors",
                )})
            return value
        finally:
            mark(name + ":end")

    setattr(obj, attr, measured)

class Database:
    def __init__(self, root):
        self.root = Path(root)
        self.keys = {}
        self.fail_result = False

    def table(self, name):
        return Query(self, name)

    def write(self, table, row, row_id=None):
        keys = self.keys.setdefault(table, [])
        if row_id is None:
            row_id = len(keys) + 1
            keys.append(row_id)
        row = {"created_at": "2026-11-19T12:00:00+00:00", **row, "id": row_id}
        with (self.root / f"{table}-{row_id}").open("w") as stream:
            json.dump(row, stream, ensure_ascii=False)
        return row

    def read(self, table, row_id):
        with (self.root / f"{table}-{row_id}").open() as stream:
            return json.load(stream)

class Query:
    def __init__(self, db, table):
        self.db, self.table = db, table
        self.fields = "*"
        self.orders, self.filters = [], []
        self.start, self.stop = 0, None
        self.operation = "read"
        self.payload = None
        self.conflict = None

    def select(self, fields):
        self.fields = fields
        return self

    def order(self, field, desc=False):
        self.orders.append((field, desc))
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def range(self, start, stop):
        self.start, self.stop = start, stop + 1
        return self

    def limit(self, count):
        self.stop = count
        return self

    def insert(self, payload):
        self.operation, self.payload = "insert", payload
        return self

    def upsert(self, payload, on_conflict):
        self.operation, self.payload = "upsert", payload
        self.conflict = on_conflict.split(",")
        return self

    def update(self, payload):
        self.operation, self.payload = "update", payload
        return self

    def execute(self):
        if (self.table == "director_results" and self.operation == "insert"
                and self.db.fail_result):
            raise RuntimeError("fixture 57014: result INSERT cancelled before commit")
        keys = self.db.keys.get(self.table, [])
        if self.operation in {"read", "update"}:
            ids = [v for v in keys if not any(k == "id" and x != v for k, x in self.filters)]
            rows = [self.db.read(self.table, row_id) for row_id in ids]
            rows = [r for r in rows if all(r.get(k) == v for k, v in self.filters)]
            for col, desc in reversed(self.orders):
                rows.sort(key=lambda r: (r.get(col) is None, r.get(col)), reverse=desc)
            if self.operation == "update":
                rows = [self.db.write(self.table, {**r, **self.payload}, r["id"]) for r in rows]
            rows = rows[self.start:self.stop]
        else:
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            rows = []
            for payload in payloads:
                row_id = None
                if self.conflict:
                    for key in keys:
                        current = self.db.read(self.table, key)
                        if all(current.get(c) == payload.get(c) for c in self.conflict):
                            row_id = key
                            break
                rows.append(self.db.write(self.table, payload, row_id))
        if self.fields != "*":
            rows = [{k: r.get(k) for k in self.fields.split(",")} for r in rows]
        return NS(data=rows)

@asynccontextmanager
async def fake_transport(url):
    assert url == "https://fixture.invalid/mcp"
    yield None, None, None

calls = {"search": 0, "stats": 0, "ai": 0}

class FakeMCP:
    def __init__(self, *streams):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass

    async def initialize(self):
        pass

    async def list_tools(self):
        return NS(tools=[NS(name="search_videos"), NS(name="get_video_stats")])

    async def call_tool(self, name, arguments):
        assert name in {"search_videos", "get_video_stats"}
        kind = "search" if name == "search_videos" else "stats"
        calls[kind] += 1
        if scenario == "mcp_error":
            raise RuntimeError("fixture MCP unavailable")
        ids = arguments.get("video_ids") or [f"v{calls['search']}-{i}" for i in range(3)]
        items = [
            {"id": vid, "snippet": {"title": "История природы", "channelId": "channel"},
             "statistics": {"viewCount": "1000", "likeCount": "20"}}
            for vid in ids
        ]
        return NS(structuredContent={"items": items, "videos": items, "_quota": {
            "search_calls": 1 if kind == "search" else 0, "search_list_calls": 1 if kind == "search" else 0,
            "videos_list_calls": 1 if kind == "stats" else 0, "other_units": 1,
        }})

class FakeAI:
    async def generate_json(self, *, messages):
        calls["ai"] += 1
        assert messages
        return {"reason": "Локальная фикстура", "confidence": 0.8}

def refs_summary(original):
    def summarize():
        summary = original()
        if mode == "refs":
            for key in ("recent_results", "recent_runs"):
                if key in summary:
                    summary[key] = [{"id": row.get("id"), "details_omitted": True}
                                    for row in summary[key]]
        return summary

    return summarize

def checksum(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

async def main(db):
    rt = server.runtime
    backend = SupabaseMemoryBackend(client=db)
    rt.memory.backend, rt.memory.memory = backend, Memory(backend=backend)
    rt.data.storage = backend
    rt.research.storage = backend
    rt.ai.provider = FakeAI()
    transport.streamable_http_client = fake_transport
    mcp.ClientSession = FakeMCP
    for n in range(6):
        db.write("director_results", {"run_id": None, "result_type": "fixture", "summary": "seed",
                 "data_json": {"project_id": "fixture", "blob": str(n) * (220_000 if n >= 4 else 100)}})
    seed = [checksum(db.read("director_results", i)) for i in range(1, 7)]
    seed_digest = checksum(seed)
    director = rt.get_director(project_id="fixture")
    director.autonomy_config.max_research_steps = 1
    original_assess = director._autonomy_assess

    def schedule_fixture_research(state, payload):
        assessment = original_assess(state, payload)
        # Force one research phase per wake for a matched route through the fixture.
        assessment["evidence_sufficient"] = False
        return assessment

    director._autonomy_assess = schedule_fixture_research
    director._memory_state_summary = refs_summary(director._memory_state_summary)
    for name, phase in [
        ("inspect", "history"), ("analyze", "analysis"), ("decide", "decision"),
        ("_autonomy_research", "research"),
    ]:
        instrument(director, name, phase)
    instrument(rt.research, "execute", "mcp_executor")
    instrument(rt.memory, "get_context", "memory_read")
    instrument(rt.data, "get_project_state", "data_state")
    original_serialize = server.serialize

    def serialize(value):
        if type(value).__name__ != "DirectorCycle":
            return original_serialize(value)
        mark("serialize_cycle:start")
        try:
            return original_serialize(value)
        finally:
            mark("serialize_cycle:end")

    server.serialize = serialize
    for name in ("update_run", "save_result", "save_decision", "save_recommendation", "save_event"):
        instrument(rt.memory, name, name)

    summaries = []
    steps = 3 if scenario == "normal" else 1
    for index in range(1, steps + 1):
        global cycle_no
        cycle_no = index
        db.fail_result = scenario == "write_error"
        mark("wake:start")
        try:
            returned = await server._execute_autonomous_cycle(project_id="fixture")
            error = None
        except RuntimeError as exc:
            if scenario != "write_error":
                raise
            error = str(exc)
            returned = None
        mark("wake:end")
        run = db.read("director_runs", index)
        result_ids = db.keys["director_results"][6:]
        match = db.read("director_results", result_ids[-1]) if result_ids else None
        durable = run["data_json"].get("result")
        assert isinstance(durable, dict)
        if returned is not None:
            assert len(result_ids) == index and match["run_id"] == index
            assert match["data_json"]["result"] == durable == returned
        else:
            assert not match and run["status"] == "partial" and error
        assert [checksum(db.read("director_results", i)) for i in range(1, 7)] == seed
        summaries.append({"run_id": index, "storage_status": run["status"],
                          "cycle_status": durable["status"], "error": error,
                          "step": run.get("current_step"),
                          "returned_status_string": str(returned["status"]) if returned else None,
                          "failure": durable["state"]["metadata"].get("failure"),
                          "result_rows": len(result_ids), "research_sets": len(db.keys.get("research_sets", [])),
                          "run_file_bytes": (db.root / f"director_runs-{index}").stat().st_size,
                          "tables": {k: len(db.keys.get(k, [])) for k in (
                              "decisions", "system_events", "videos", "video_snapshots", "youtube_queries",
                          )},
                          "calls": dict(calls)})
        del run, match, durable, returned
    assert not blocked, blocked
    assert calls["search"] > 0, calls
    if scenario != "mcp_error":
        assert calls["ai"] > 0, calls
    if scenario == "mcp_error":
        assert research_outcomes and all(o["status"] == "failed" for o in research_outcomes)
    else:
        assert research_outcomes and all(o["queries_collected"] > 0 and o["persisted"]
                                         for o in research_outcomes), research_outcomes
    assert all(any(m["phase"] == p + ":end" for m in marks)
               for p in ("history", "analysis", "decision", "research", "save_result"))
    print(json.dumps({"mode": mode, "scenario": scenario, "phases": marks,
                      "runs": summaries, "research": research_outcomes, "seed_digest": seed_digest}, ensure_ascii=False))

with tempfile.TemporaryDirectory() as root:
    asyncio.run(main(Database(root)))
