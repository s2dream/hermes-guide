"""Local pilot API and same-origin UI. Intentionally binds only to 127.0.0.1."""
import argparse
import fcntl
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import signal
import threading
from urllib.parse import unquote, urlsplit

from research_service.core import ROOT, Problem, Store
from research_service.worker import Worker, live_configuration

DEFAULT_DB = ROOT / ".research/research.sqlite3"


class Handler(BaseHTTPRequestHandler):
    server_version = "HermesResearchPilot"

    def log_message(self, *args):
        pass  # Neither query strings nor tokens belong in access logs.

    @property
    def store(self):
        return self.server.store

    def session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            return cookie["research_session"].value if "research_session" in cookie else ""
        except CookieError:
            return ""

    def authenticate(self):
        authorization = self.headers.get("Authorization", "")
        user = self.store.user(authorization[7:]) if authorization.startswith("Bearer ") else self.store.user(self.session(), session=True)
        if not user:
            raise Problem("초대 토큰으로 로그인하세요.", 401)
        return user

    def send(self, data, status=200, *, mime="application/json; charset=utf-8", headers=None):
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        # Original guide has inline scripts; the application itself uses external JS only.
        if mime.startswith("application/json"):
            self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        if mime.startswith("text/html") and self.path.split("?")[0] in {"/", "/research.html"}:
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise Problem("application/json 요청이 필요합니다.", 415)
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise Problem("요청 크기가 올바르지 않습니다.") from None
        if not 1 <= size <= 16000 or self.headers.get("Transfer-Encoding"):
            raise Problem("요청은 16 KB 이하로 보내세요.", 413)
        try:
            return json.loads(self.rfile.read(size))
        except (ValueError, UnicodeError):
            raise Problem("JSON 요청을 확인하세요.") from None

    def dispatch(self, method):
        try:
            expected_host = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != expected_host:
                raise Problem("127.0.0.1 주소로 접속하세요.", 403)
            if method != "GET":
                origin = self.headers.get("Origin")
                if origin and origin != "http://" + expected_host:
                    raise Problem("다른 사이트에서 보낸 요청을 허용하지 않습니다.", 403)
                if self.headers.get("Sec-Fetch-Site") == "cross-site":
                    raise Problem("다른 사이트에서 보낸 요청을 허용하지 않습니다.", 403)
            path = urlsplit(self.path).path
            if method == "GET" and path == "/api/health":
                return self.send({"service": "hermes-research-pilot", "live": live_configuration(), "scheduler_enabled": False})
            if method == "POST" and path == "/api/login":
                data = self.read_json()
                session, user = self.store.login(data.get("token", "") if isinstance(data, dict) else "")
                return self.send({"user": user}, headers={"Set-Cookie": f"research_session={session}; HttpOnly; SameSite=Strict; Path=/api; Max-Age=43200"})
            if method == "POST" and path == "/api/logout":
                self.read_json()
                self.store.logout(self.session())
                return self.send({"ok": True}, headers={"Set-Cookie": "research_session=; HttpOnly; SameSite=Strict; Path=/api; Max-Age=0"})
            if path.startswith("/api/"):
                user = self.authenticate()
                if method == "GET" and path == "/api/me":
                    return self.send({"user": user})
                if path == "/api/research" and method == "GET":
                    return self.send({"jobs": self.store.listing(user["id"])})
                if path == "/api/research" and method == "POST":
                    data = self.read_json()
                    if isinstance(data, dict) and data.get("mode") == "live" and not live_configuration()["configured"]:
                        raise Problem("실제 조사에 필요한 서버 설정이 없습니다. 실행 안내를 확인하세요.", 503)
                    job, created = self.store.create(user["id"], data, self.headers.get("Idempotency-Key"))
                    return self.send(job, 201 if created else 200)
                match = re.fullmatch(r"/api/research/([a-f0-9]{32})(/cancel|/download)?", path)
                if match:
                    job_id, action = match.groups()
                    if method == "POST" and action == "/cancel":
                        self.read_json()
                        return self.send(self.store.cancel(user["id"], job_id))
                    if method == "GET" and action in {None, "/download"}:
                        job = self.store.get(user["id"], job_id)
                        return self.send(job, headers={"Content-Disposition": f'attachment; filename="research-{job_id}.json"'} if action == "/download" else None)
                raise Problem("API 경로를 찾을 수 없습니다.", 404)
            if method != "GET":
                raise Problem("경로를 찾을 수 없습니다.", 404)
            relative = unquote(path).lstrip("/") or "research.html"
            file = (ROOT / relative).resolve()
            allowed = file.parent == ROOT and file.suffix == ".html" or file.is_relative_to(ROOT / "assets") and file.suffix in {".js", ".css"} or file.is_relative_to(ROOT / "data") and file.suffix == ".json"
            if not allowed or not file.is_file():
                raise Problem("페이지를 찾을 수 없습니다.", 404)
            mime = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            return self.send(file.read_bytes(), mime=mime + "; charset=utf-8")
        except Problem as exc:
            self.close_connection = True  # An early error may leave an unread body.
            self.send({"error": str(exc)}, exc.status)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self.close_connection = True
            self.send({"error": "요청을 처리하지 못했습니다."}, 500)

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")


def make_server(store, port=8787):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.store = store
    return server


def main():
    parser = argparse.ArgumentParser(description="수동으로 시작하는 로컬 정보 탐색 파일럿")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("add-user", help="초대 토큰 발급")
    create.add_argument("name")
    disable = commands.add_parser("disable-user", help="계정과 토큰 비활성화")
    disable.add_argument("name")
    serve = commands.add_parser("serve", help="직접 중단할 때까지 로컬 UI·작업 큐 실행")
    serve.add_argument("--port", type=int, default=8787)
    commands.add_parser("doctor", help="값을 노출하지 않고 필수 설정 확인")
    args = parser.parse_args()
    os.umask(0o077)
    store = Store(args.db)
    try:
        if args.command == "add-user":
            print(store.add_user(args.name))
        elif args.command == "disable-user":
            store.disable_user(args.name)
            print("사용자를 비활성화했습니다.")
        elif args.command == "doctor":
            print(json.dumps(live_configuration(), ensure_ascii=False, indent=2))
        else:
            # Only one supervisor may recover/claim this database's jobs.
            with store.path.with_suffix(".lock").open("w") as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise Problem("이 데이터베이스를 사용하는 서버가 이미 실행 중입니다.") from None
                server = make_server(store, args.port)
                worker = Worker(store)
                worker.start()
                def shutdown(*_):
                    threading.Thread(target=server.shutdown, daemon=True).start()
                signal.signal(signal.SIGTERM, shutdown)
                signal.signal(signal.SIGINT, shutdown)
                print(f"정보 탐색 UI: http://127.0.0.1:{server.server_port}/research.html", flush=True)
                print("정기 실행 없음 · 중단: Ctrl+C", flush=True)
                try:
                    server.serve_forever()
                finally:
                    worker.close()
                    server.server_close()
    except (Problem, OSError) as exc:
        print(str(exc), file=__import__("sys").stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
