"""HTTP entry point of the e2e dump container (Serverless Containers run HTTP servers).

GET /     health check.
POST /run runs dump.sh and answers once it is over: 200 if the anonymised dump
          was uploaded, 500 otherwise. The body carries only dump.sh's progress
          lines (stdout). Its errors (stderr) go to the container logs only.
One dump at a time: a second POST during a run gets 409.
"""

import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DUMP = Path(__file__).with_name("dump.sh")
running = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def _answer(self, status: int, body: str) -> None:
        payload = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        self._answer(200, "ok\n")

    def do_POST(self) -> None:
        if self.path != "/run":
            self._answer(404, "POST /run\n")
            return
        if not running.acquire(blocking=False):
            self._answer(409, "A dump is already running.\n")
            return
        try:
            result = subprocess.run([str(DUMP)], stdout=subprocess.PIPE, text=True)
        finally:
            running.release()
        if result.returncode == 0:
            self._answer(200, result.stdout)
        else:
            self._answer(500, result.stdout + "Failed: see the container logs.\n")


if __name__ == "__main__":
    ThreadingHTTPServer(("", 8080), Handler).serve_forever()
