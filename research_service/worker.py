import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import time

from research_service.core import ROOT, demo_report


def live_configuration():
    provider = os.environ.get("RESEARCH_PROVIDER", "openrouter")
    checks = {
        "HERMES_SOURCE": (Path(os.environ.get("HERMES_SOURCE", "/nonexistent")) / "run_agent.py").is_file(),
        "HERMES_PYTHON": Path(os.environ.get("HERMES_PYTHON", "/nonexistent")).is_file() and os.access(os.environ.get("HERMES_PYTHON", ""), os.X_OK),
        "HERMES_RESEARCH_MODEL": bool(os.environ.get("HERMES_RESEARCH_MODEL")),
        "RESEARCH_PROVIDER": provider in {"openrouter", "openai"},
        "OPENROUTER_API_KEY" if provider == "openrouter" else "OPENAI_API_KEY": bool(os.environ.get("OPENROUTER_API_KEY" if provider == "openrouter" else "OPENAI_API_KEY")),
        "TAVILY_API_KEY": bool(os.environ.get("TAVILY_API_KEY")),
    }
    return {"configured": all(checks.values()), "missing": [k for k, v in checks.items() if not v]}


class Worker:
    def __init__(self, store):
        self.store = store
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def start(self):
        self.store.recover()
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join(timeout=20)

    def loop(self):
        while not self.stop.is_set():
            job = self.store.claim()
            if not job:
                self.stop.wait(0.2)
                continue
            try:
                request = json.loads(job["request"])
                if request["mode"] == "demo":
                    self.store.event(job["id"], "reading", "기존 사례 스냅샷을 읽습니다. 새 검색은 실행하지 않습니다.")
                    report = demo_report(request)
                else:
                    report = self.live(job["id"], request)
                if report is None:
                    self.store.finish(job["id"], "cancelled")
                else:
                    self.store.finish(job["id"], "completed" if report["claims"] else "insufficient_evidence", report)
            except Exception:
                # Worker must remain available for subsequent jobs; do not expose internals.
                self.store.finish(job["id"], "failed", error="실행 환경 또는 결과 검증에 실패했습니다. 설정과 출처를 확인한 뒤 새 조사를 시작하세요.")

    def live(self, job_id, request):
        if not live_configuration()["configured"]:
            raise RuntimeError("Missing configuration")
        with tempfile.TemporaryDirectory(prefix="research-", dir=self.store.path.parent) as tmp:
            work = Path(tmp)
            (work / "request.json").write_text(json.dumps(request, ensure_ascii=False))
            # A fresh Hermes home prevents loading personal history, MCP or cron settings.
            (work / "home").mkdir()
            env = {name: os.environ[name] for name in ("PATH", "LANG", "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE") if name in os.environ}
            for name in ("HERMES_SOURCE", "HERMES_RESEARCH_MODEL", "TAVILY_API_KEY", "RESEARCH_PROVIDER"):
                if name in os.environ:
                    env[name] = os.environ[name]
            provider = os.environ.get("RESEARCH_PROVIDER", "openrouter")
            key_name = "OPENROUTER_API_KEY" if provider == "openrouter" else "OPENAI_API_KEY"
            env[key_name] = os.environ[key_name]
            env.update({"HOME": str(work / "home"), "HERMES_HOME": str(work / "home"), "PYTHONPATH": str(ROOT), "PYTHONUNBUFFERED": "1", "RESEARCH_PARENT_PID": str(os.getpid())})
            command = [os.environ["HERMES_PYTHON"], "-m", "research_service.hermes_bridge", str(work / "request.json"), str(work / "result.json"), str(work / "events.jsonl")]
            process = subprocess.Popen(command, cwd=work, env=env, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline, seen = time.monotonic() + 300, 0
            try:
                while process.poll() is None:
                    if self.stop.is_set() or self.store.should_cancel(job_id):
                        return None
                    if time.monotonic() > deadline:
                        raise TimeoutError()
                    if (work / "events.jsonl").exists():
                        lines = (work / "events.jsonl").read_text().splitlines()
                        for line in lines[seen:]:
                            try:
                                event = json.loads(line)
                                if event["stage"] in {"searching", "reading", "validating"}:
                                    self.store.event(job_id, event["stage"], event["message"])
                            except (ValueError, KeyError):
                                pass
                        seen = len(lines)
                    self.stop.wait(0.2)
                if self.store.should_cancel(job_id) or self.stop.is_set():
                    return None
                if process.returncode != 0 or not (work / "result.json").exists():
                    raise RuntimeError("Hermes runtime failed")
                response = json.loads((work / "result.json").read_text())
                if "error" in response:
                    raise RuntimeError("Hermes report rejected")
                return response["report"]
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=3)
