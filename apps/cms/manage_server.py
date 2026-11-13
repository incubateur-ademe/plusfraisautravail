"""HTTP entry point of the cms-manage container (Serverless Containers run HTTP servers).

The private cms-manage container runs the CMS image with this command instead
of gunicorn. It replaces a Serverless Job: Jobs cannot join the database's
Private Network.

GET /     health check, answers the BUILD_SHA of the image: cms.yml waits for
          the image it has just rolled out.
POST /run runs manage_jobs.sh (migrate, createcachetable) and answers once it
          is over: 200 if it succeeded, 500 otherwise, with its stdout only.
          Errors can quote a row (DETAIL: Key (email)=...): they stay in the
          container logs, never in the deploy log.
One run at a time: a second POST during a run gets 409.
"""

import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MANAGE_JOBS = Path(__file__).with_name("manage_jobs.sh")
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
        self._answer(200, os.environ.get("BUILD_SHA", "unknown"))

    def do_POST(self) -> None:
        if self.path != "/run":
            self._answer(404, "POST /run\n")
            return
        if not running.acquire(blocking=False):
            self._answer(409, "manage_jobs.sh is already running.\n")
            return
        try:
            result = subprocess.run([str(MANAGE_JOBS)], stdout=subprocess.PIPE, text=True)
        finally:
            running.release()
        if result.returncode == 0:
            self._answer(200, result.stdout)
        else:
            self._answer(500, result.stdout + "Failed: see the container logs (Cockpit).\n")


if __name__ == "__main__":
    ThreadingHTTPServer(("", 8080), Handler).serve_forever()
