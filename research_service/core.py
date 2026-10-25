"""Durable jobs, invite authentication and evidence validation. Standard library only."""
from contextlib import contextmanager
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/news-case-studies-2026-10-25.json"
TERMINAL = {"completed", "insufficient_evidence", "failed", "cancelled", "interrupted"}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class Problem(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def validate_request(body):
    if not isinstance(body, dict) or set(body) - {"question", "domain", "mode", "start_date", "end_date"}:
        raise Problem("지원하지 않는 조사 설정입니다.")
    domain, mode = body.get("domain"), body.get("mode")
    if domain not in {"politics", "entertainment"} or mode not in {"demo", "live"}:
        raise Problem("조사 분야와 실행 방식을 선택하세요.")
    question = body.get("question", "")
    if not isinstance(question, str) or not 5 <= len(question.strip()) <= 2000:
        raise Problem("질문은 5~2,000자로 입력하세요.")
    period = {}
    for field in ("start_date", "end_date"):
        value = body.get(field)
        try:
            if not isinstance(value, str) or len(value) != 10 or date.fromisoformat(value).isoformat() != value:
                raise ValueError()
        except ValueError:
            raise Problem("조사 시작일과 종료일을 YYYY-MM-DD로 입력하세요.") from None
        period[field] = value
    if period["start_date"] > period["end_date"]:
        raise Problem("시작일은 종료일보다 늦을 수 없습니다.")
    return {"question": question.strip(), "domain": domain, "mode": mode, **period}


class Store:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, token_hash TEXT NOT NULL UNIQUE,
                    active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, request TEXT NOT NULL,
                    idem TEXT NOT NULL, state TEXT NOT NULL, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, result TEXT, error TEXT,
                    UNIQUE(user_id, idem));
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL,
                    at TEXT NOT NULL, stage TEXT NOT NULL, message TEXT NOT NULL);
            """)
        self.path.chmod(0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def add_user(self, name):
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise Problem("사용자 이름은 1~80자로 입력하세요.")
        token = secrets.token_urlsafe(32)
        try:
            with self.connect() as db:
                db.execute("INSERT INTO users(id,name,token_hash) VALUES(?,?,?)", (uuid.uuid4().hex, name.strip(), digest(token)))
        except sqlite3.IntegrityError:
            raise Problem("이미 존재하는 사용자 이름입니다.") from None
        return token

    def disable_user(self, name):
        with self.connect() as db:
            changed = db.execute("UPDATE users SET active=0 WHERE name=?", (name,)).rowcount
        if not changed:
            raise Problem("사용자를 찾을 수 없습니다.", 404)

    def user(self, token, session=False):
        if not isinstance(token, str) or not token or len(token) > 200:
            return None
        with self.connect() as db:
            if session:
                row = db.execute("SELECT u.id,u.name FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>? AND u.active=1", (digest(token), time.time())).fetchone()
            else:
                row = db.execute("SELECT id,name FROM users WHERE token_hash=? AND active=1", (digest(token),)).fetchone()
        return dict(row) if row else None

    def login(self, token):
        user = self.user(token)
        if not user:
            raise Problem("초대 토큰을 확인하세요.", 401)
        session = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute("DELETE FROM sessions WHERE expires<?", (time.time(),))
            db.execute("INSERT INTO sessions VALUES(?,?,?)", (digest(session), user["id"], time.time() + 43200))
        return session, user

    def logout(self, token):
        with self.connect() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (digest(token),))

    def create(self, user_id, body, idem):
        request = validate_request(body)
        if not isinstance(idem, str) or not 8 <= len(idem) <= 128:
            raise Problem("8~128자의 Idempotency-Key가 필요합니다.")
        encoded = json.dumps(request, sort_keys=True, ensure_ascii=False)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM jobs WHERE user_id=? AND idem=?", (user_id, idem)).fetchone()
            if existing:
                if existing["request"] != encoded:
                    raise Problem("같은 요청 키에 다른 조사 조건을 사용할 수 없습니다.", 409)
                return self.unpack(existing), False
            if db.execute("SELECT count(*) FROM jobs WHERE user_id=? AND state IN ('queued','running','cancelling')", (user_id,)).fetchone()[0] >= 5:
                raise Problem("사용자당 진행 중인 작업은 5개까지 가능합니다.", 429)
            if db.execute("SELECT count(*) FROM jobs WHERE state IN ('queued','running','cancelling')").fetchone()[0] >= 20:
                raise Problem("전체 작업 대기열이 가득 찼습니다. 잠시 후 시도하세요.", 429)
            job_id, stamp = uuid.uuid4().hex, now()
            db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?)", (job_id, user_id, encoded, idem, "queued", stamp, stamp, None, None))
            self.event(job_id, "queued", "조사를 대기열에 등록했습니다.", db)
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return self.unpack(row), True

    @staticmethod
    def unpack(row):
        data = dict(row)
        data.pop("idem", None)
        data.pop("user_id", None)
        data["request"] = json.loads(data["request"])
        data["result"] = json.loads(data["result"]) if data["result"] else None
        return data

    def get(self, user_id, job_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE user_id=? AND id=?", (user_id, job_id)).fetchone()
            if not row:
                raise Problem("조사를 찾을 수 없습니다.", 404)
            data = self.unpack(row)
            data["events"] = [dict(r) for r in db.execute("SELECT id,at,stage,message FROM events WHERE job_id=? ORDER BY id", (job_id,))]
        return data

    def listing(self, user_id):
        with self.connect() as db:
            return [self.unpack(r) for r in db.execute("SELECT * FROM jobs WHERE user_id=? ORDER BY created_at DESC LIMIT 100", (user_id,))]

    def event(self, job_id, stage, message, db=None):
        if db is None:
            with self.connect() as connection:
                self.event(job_id, stage, message, connection)
        else:
            db.execute("INSERT INTO events(job_id,at,stage,message) VALUES(?,?,?,?)", (job_id, now(), stage, message[:300]))

    def claim(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            # Disabling an account also prevents its queued work from executing.
            db.execute("UPDATE jobs SET state='cancelled',updated_at=? WHERE state='queued' AND user_id IN (SELECT id FROM users WHERE active=0)", (now(),))
            row = db.execute("SELECT * FROM jobs WHERE state='queued' ORDER BY created_at LIMIT 1").fetchone()
            if not row:
                return None
            db.execute("UPDATE jobs SET state='running',updated_at=? WHERE id=?", (now(), row["id"]))
            self.event(row["id"], "running", "조사를 시작했습니다.", db)
            return dict(row)

    def cancel(self, user_id, job_id):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state FROM jobs WHERE user_id=? AND id=?", (user_id, job_id)).fetchone()
            if not row:
                raise Problem("조사를 찾을 수 없습니다.", 404)
            if row["state"] not in TERMINAL and row["state"] != "cancelling":
                state = "cancelled" if row["state"] == "queued" else "cancelling"
                db.execute("UPDATE jobs SET state=?,updated_at=? WHERE id=?", (state, now(), job_id))
                self.event(job_id, state, "중단을 요청했습니다.", db)
        return self.get(user_id, job_id)

    def should_cancel(self, job_id):
        with self.connect() as db:
            row = db.execute("SELECT j.state,u.active FROM jobs j JOIN users u ON j.user_id=u.id WHERE j.id=?", (job_id,)).fetchone()
            return not row or row["state"] == "cancelling" or not row["active"]

    def finish(self, job_id, state, result=None, error=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT j.state,u.active FROM jobs j JOIN users u ON j.user_id=u.id WHERE j.id=?", (job_id,)).fetchone()
            if row["state"] == "cancelling" or not row["active"]:
                state, result, error = "cancelled", None, None
            db.execute("UPDATE jobs SET state=?,result=?,error=?,updated_at=? WHERE id=?", (state, json.dumps(result, ensure_ascii=False) if result else None, error, now(), job_id))
            self.event(job_id, state, error or {"completed": "보고서가 완성되었습니다.", "insufficient_evidence": "확인된 근거가 부족합니다.", "cancelled": "실행을 중단했습니다."}.get(state, "작업이 종료되었습니다."), db)

    def recover(self):
        # The server owns a process lock: no live owner exists when this runs.
        with self.connect() as db:
            rows = db.execute("SELECT id FROM jobs WHERE state IN ('running','cancelling')").fetchall()
            for row in rows:
                db.execute("UPDATE jobs SET state='interrupted',error=?,updated_at=? WHERE id=?", ("서버가 재시작되어 실행 여부를 확인할 수 없습니다. 자동 재실행하지 않습니다.", now(), row["id"]))
                self.event(row["id"], "interrupted", "서버 재시작으로 조사가 중단되었습니다.", db)


def demo_report(request):
    data = json.loads(SNAPSHOT.read_text())
    claims = [c for c in data["claims"] if c["domain"] == request["domain"]]
    ids = {s for c in claims for s in c["source_ids"]}
    return {
        "title": "정치·정책 사례 브리핑" if request["domain"] == "politics" else "연예·문화 사례 브리핑",
        "mode": "demo", "hermes_executed": False, "generated_at": now(),
        "reference_date": data["metadata"]["reference_date"],
        "summary": "2026-10-25에 작성한 기존 사례를 불러왔습니다. 새 질문에 대한 검색·Hermes 실행 결과가 아닙니다.",
        "claims": claims, "sources": [s for s in data["sources"] if s["id"] in ids],
        "limitations": data["metadata"]["limitations"], "usage": None,
        "validation": {"kind": "editorial_snapshot", "truth_accuracy_measured": False},
    }


def validate_report(draft, sources):
    """Never trust a model-supplied URL, evidence text, or validation flag."""
    if not isinstance(draft, dict):
        raise Problem("보고서 형식이 올바르지 않습니다.")
    for key, limit in (("title", 200), ("summary", 3000)):
        if not isinstance(draft.get(key), str) or not 1 <= len(draft[key]) <= limit:
            raise Problem("보고서 제목·요약 형식이 올바르지 않습니다.")
    if not isinstance(draft.get("limitations"), list) or len(draft["limitations"]) > 20 or any(not isinstance(x, str) or len(x) > 1000 for x in draft["limitations"]):
        raise Problem("보고서 한계 목록이 올바르지 않습니다.")
    claims = draft.get("claims")
    if not isinstance(claims, list) or len(claims) > 20:
        raise Problem("보고서는 최대 20개 주장으로 작성해야 합니다.")
    registry = {s["id"]: s for s in sources}
    accepted = []
    # Cap quotations across the entire report, per source. Short excerpts only.
    quoted = {}
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise Problem("주장 형식이 올바르지 않습니다.")
        text, evidence = claim.get("text"), claim.get("evidence")
        if not isinstance(text, str) or not 1 <= len(text) <= 1000 or not isinstance(evidence, list) or not 1 <= len(evidence) <= 3:
            raise Problem("모든 주장에 실제 원문 발췌가 필요합니다.")
        state = claim.get("state")
        if state not in {"announced", "proposed", "scheduled", "completed", "conditional", "unknown"}:
            raise Problem("주장 상태를 구분해야 합니다.")
        event_at = claim.get("event_at")
        if event_at is not None:
            try:
                if not isinstance(event_at, str) or date.fromisoformat(event_at).isoformat() != event_at:
                    raise ValueError()
            except ValueError:
                raise Problem("사건 날짜는 YYYY-MM-DD 또는 null이어야 합니다.") from None
        checked = []
        for item in evidence:
            if not isinstance(item, dict):
                raise Problem("발췌 형식이 올바르지 않습니다.")
            source, quote = registry.get(item.get("source_id")), item.get("quote")
            if not source or not isinstance(quote, str) or not 8 <= len(quote) <= 150 or quote not in source["text"]:
                raise Problem("주장의 출처 또는 원문 발췌를 확인할 수 없습니다.")
            sid = source["id"]
            quoted[sid] = quoted.get(sid, 0) + len(quote)
            if quoted[sid] > 500:
                raise Problem("출처별 발췌 분량을 줄여야 합니다.")
            checked.append({"source_id": sid, "quote": quote})
        accepted.append({"id": f"C{index+1}", "text": text, "state": state, "event_at": event_at, "evidence": checked, "source_ids": list(dict.fromkeys(e["source_id"] for e in checked))})
    used = {sid for c in accepted for sid in c["source_ids"]}
    return {
        "title": draft["title"], "summary": draft["summary"], "claims": accepted,
        "sources": [{k: v for k, v in s.items() if k != "text"} for s in sources if s["id"] in used],
        "limitations": [*draft["limitations"], "인용 ID·원문 발췌 일치는 기계 검사했습니다. 주장 의미의 적합성과 사실 진실성을 보증하지 않습니다."],
        "mode": "live", "hermes_executed": True, "generated_at": now(), "usage": None,
        "validation": {"kind": "source_id_and_exact_excerpt", "truth_accuracy_measured": False},
    }
