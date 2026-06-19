from __future__ import annotations

import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import click

from multi.app_api import (
    get_history_group_diff,
    get_project_detail,
    get_projects_summary,
    refresh_projects_summary,
)

logger = logging.getLogger(__name__)


class MultiServiceHandler(BaseHTTPRequestHandler):
    server_version = "multi-service/0.1"

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        return json.loads(raw_body.decode("utf-8"))

    def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("multi service: " + format, *args)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._write_json(HTTPStatus.OK, {"ok": True})
            return

        self._write_json(
            HTTPStatus.NOT_FOUND,
            {"error": f"Unknown route: {self.path}"},
        )

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._read_json()
        except json.JSONDecodeError as exc:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        try:
            if self.path == "/v1/projects/summary":
                repo_paths = body.get("repoPaths", [])
                if not isinstance(repo_paths, list) or not all(
                    isinstance(item, str) for item in repo_paths
                ):
                    raise ValueError("repoPaths must be a list of strings.")
                self._write_json(
                    HTTPStatus.OK,
                    {"projects": get_projects_summary(repo_paths)},
                )
                return

            if self.path == "/v1/projects/status":
                repo_paths = body.get("repoPaths", [])
                if not isinstance(repo_paths, list) or not all(
                    isinstance(item, str) for item in repo_paths
                ):
                    raise ValueError("repoPaths must be a list of strings.")
                self._write_json(
                    HTTPStatus.OK,
                    {"projects": refresh_projects_summary(repo_paths)},
                )
                return

            if self.path == "/v1/project/detail":
                repo_path = body.get("repoPath")
                if not isinstance(repo_path, str) or not repo_path:
                    raise ValueError("repoPath must be a non-empty string.")
                self._write_json(HTTPStatus.OK, get_project_detail(repo_path))
                return

            if self.path == "/v1/history/group-diff":
                commits = body.get("commits", [])
                if not isinstance(commits, list):
                    raise ValueError("commits must be a list.")
                self._write_json(
                    HTTPStatus.OK,
                    {"repoDiffs": get_history_group_diff(commits)},
                )
                return
        except ValueError as exc:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception("Service request failed")
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
            return

        self._write_json(
            HTTPStatus.NOT_FOUND,
            {"error": f"Unknown route: {self.path}"},
        )


@click.command(name="service")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=0, show_default=True, type=int)
def service_cmd(host: str, port: int) -> None:
    """Run the Multi local JSON service."""
    if host not in {"127.0.0.1", "localhost"}:
        raise click.ClickException("Service host must remain loopback-only.")

    server = ThreadingHTTPServer((host, port), MultiServiceHandler)
    actual_port = int(server.server_address[1])
    click.echo(json.dumps({"event": "ready", "port": actual_port}), err=False)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
