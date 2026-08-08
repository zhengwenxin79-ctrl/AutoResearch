from __future__ import annotations

import json
import mimetypes
import os
import re
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

DEFAULT_PORT = 8766
DEFAULT_RUN = "gui-agent-benchmark-real-world-workflow"
RUN_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def discover_runs(output_root: Path) -> list[dict[str, Any]]:
    root = output_root.resolve()
    if not root.exists():
        return []

    runs: list[dict[str, Any]] = []
    for run_dir in root.iterdir():
        if not run_dir.is_dir() or not (run_dir / "dashboard.html").is_file():
            continue
        summary = _read_run_summary(run_dir)
        dashboard_mtime = (run_dir / "dashboard.html").stat().st_mtime
        summary.update(
            {
                "slug": run_dir.name,
                "mtime": dashboard_mtime,
                "dashboard_path": run_dir / "dashboard.html",
            }
        )
        runs.append(summary)
    return sorted(runs, key=lambda item: item["mtime"], reverse=True)


def build_index_html(output_root: Path, default_run: str = "") -> bytes:
    runs = discover_runs(output_root)
    default_html = ""
    if default_run:
        default_exists = any(run["slug"] == default_run for run in runs)
        default_html = (
            f'<p class="hint">默认展示 Run：<code>{escape(default_run)}</code></p>'
            if default_exists
            else f'<p class="warning">默认 Run 不存在：<code>{escape(default_run)}</code></p>'
        )

    rows = "\n".join(_run_row(run) for run in runs)
    if not rows:
        rows = (
            "<tr><td colspan=\"6\">还没有可展示的输出。请先运行 "
            "<code>autoresearch search ...</code>，或把本地 outputs 同步到服务器。</td></tr>"
        )

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AutoResearch Runs</title>
  <style>
    :root {{
      --bg: #f7f7f4;
      --panel: #fff;
      --text: #202522;
      --muted: #68716d;
      --line: #d9dfdc;
      --teal: #176b5b;
      --red: #9c3d35;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 32px 24px; }}
    header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
      padding-bottom: 18px;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0; font-size: 34px; letter-spacing: 0; }}
    p {{ margin: 8px 0 0; color: var(--muted); }}
    code {{
      background: #eef1ef;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 2px 6px;
    }}
    .panel {{
      margin-top: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{
      padding: 13px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    tr:last-child td {{ border-bottom: 0; }}
    a {{ color: var(--teal); text-decoration: none; font-weight: 650; }}
    a:hover {{ text-decoration: underline; }}
    .hint {{ color: var(--muted); }}
    .warning {{ color: var(--red); }}
    .topic {{ min-width: 260px; }}
    @media (max-width: 760px) {{
      header {{ display: block; }}
      th:nth-child(3), td:nth-child(3), th:nth-child(4), td:nth-child(4) {{ display: none; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>AutoResearch 调研看板</h1>
        <p>这里展示已经生成的 Search / MOC / Gap 证据链结果。</p>
        {default_html}
      </div>
      <p><a href="/healthz">服务状态</a></p>
    </header>
    <section class="panel">
      <table>
        <thead>
          <tr>
            <th>Run</th>
            <th>研究主题</th>
            <th>论文数</th>
            <th>Gap 数</th>
            <th>证据状态</th>
            <th>打开</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
    return html.encode("utf-8")


def create_handler(output_root: Path, default_run: str = "") -> type[BaseHTTPRequestHandler]:
    root = output_root.resolve()
    selected_default_run = default_run.strip()

    class AutoResearchHandler(BaseHTTPRequestHandler):
        server_version = "AutoResearchHTTP/0.1"

        def do_HEAD(self) -> None:
            self._handle_request(send_body=False)

        def do_GET(self) -> None:
            self._handle_request(send_body=True)

        def _handle_request(self, send_body: bool) -> None:
            parsed = urlparse(self.path)
            path = unquote(parsed.path)
            if path == "/healthz":
                self._send_json(self._health(), send_body=send_body)
                return
            if path in {"/", "/index.html"}:
                if selected_default_run and _run_dashboard(root, selected_default_run).is_file():
                    self._redirect(f"/runs/{selected_default_run}/dashboard.html#mainline")
                    return
                self._send_html(build_index_html(root, selected_default_run), send_body=send_body)
                return
            if path in {"/runs", "/runs/"}:
                self._send_html(build_index_html(root, selected_default_run), send_body=send_body)
                return
            if path.startswith("/runs/"):
                self._serve_run_file(path, send_body=send_body)
                return
            self._send_text("Not found", status=404, send_body=send_body)

        def log_message(self, format: str, *args: object) -> None:
            print(f"{self.address_string()} - {format % args}")

        def _health(self) -> dict[str, Any]:
            runs = discover_runs(root)
            return {
                "ok": True,
                "output_root": str(root),
                "run_count": len(runs),
                "default_run": selected_default_run,
                "default_run_exists": bool(
                    selected_default_run and _run_dashboard(root, selected_default_run).is_file()
                ),
                "runs": [run["slug"] for run in runs],
            }

        def _serve_run_file(self, path: str, send_body: bool = True) -> None:
            tail = path.removeprefix("/runs/")
            if not tail:
                self._send_html(build_index_html(root, selected_default_run), send_body=send_body)
                return

            if "/" not in tail:
                slug = tail.rstrip("/")
                if not _valid_run_slug(slug):
                    self._send_text("Not found", status=404, send_body=send_body)
                    return
                self._redirect(f"/runs/{slug}/dashboard.html#mainline")
                return

            slug, relative = tail.split("/", 1)
            if not _valid_run_slug(slug):
                self._send_text("Not found", status=404, send_body=send_body)
                return
            if not relative:
                self._redirect(f"/runs/{slug}/dashboard.html#mainline")
                return

            base = (root / slug).resolve()
            target = (base / relative).resolve()
            if not _is_safe_child(base, target) or not target.is_file():
                self._send_text("Not found", status=404, send_body=send_body)
                return

            payload = target.read_bytes()
            content_type = _content_type(target)
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if send_body:
                self.wfile.write(payload)

        def _redirect(self, location: str) -> None:
            self.send_response(303)
            self.send_header("Location", location)
            self.end_headers()

        def _send_json(
            self,
            payload: dict[str, Any],
            status: int = 200,
            send_body: bool = True,
        ) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if send_body:
                self.wfile.write(body)

        def _send_html(self, payload: bytes, status: int = 200, send_body: bool = True) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if send_body:
                self.wfile.write(payload)

        def _send_text(self, payload: str, status: int = 200, send_body: bool = True) -> None:
            body = payload.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if send_body:
                self.wfile.write(body)

    return AutoResearchHandler


def run_server(host: str, port: int, output_root: Path, default_run: str = "") -> None:
    handler = create_handler(output_root, default_run=default_run)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"AutoResearch web server running at http://{host}:{port}")
    print(f"Output root: {output_root.resolve()}")
    if default_run:
        print(f"Default run: {default_run}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping AutoResearch web server")
    finally:
        server.server_close()


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", os.environ.get("AUTORESEARCH_PORT", str(DEFAULT_PORT))))
    output_root = Path(os.environ.get("AUTORESEARCH_OUTPUT_DIR", "outputs"))
    default_run = os.environ.get("AUTORESEARCH_DEFAULT_RUN", DEFAULT_RUN)
    run_server(host=host, port=port, output_root=output_root, default_run=default_run)


def _read_run_summary(run_dir: Path) -> dict[str, Any]:
    payload = _read_search_result(run_dir / "search_result.json")
    readiness = payload.get("source_readiness") or {}
    return {
        "topic": payload.get("topic") or run_dir.name,
        "generated_at": payload.get("generated_at") or "",
        "paper_count": len(payload.get("ranked_papers") or []),
        "gap_count": len(payload.get("gaps") or []),
        "readiness": readiness.get("status") or "unknown",
    }


def _read_search_result(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _run_row(run: dict[str, Any]) -> str:
    slug = escape(str(run["slug"]))
    topic = escape(str(run.get("topic") or run["slug"]))
    paper_count = escape(str(run.get("paper_count", 0)))
    gap_count = escape(str(run.get("gap_count", 0)))
    readiness = escape(str(run.get("readiness") or "unknown"))
    return (
        "<tr>"
        f"<td><code>{slug}</code></td>"
        f"<td class=\"topic\">{topic}</td>"
        f"<td>{paper_count}</td>"
        f"<td>{gap_count}</td>"
        f"<td>{readiness}</td>"
        f"<td><a href=\"/runs/{slug}/dashboard.html#mainline\">Dashboard</a></td>"
        "</tr>"
    )


def _run_dashboard(output_root: Path, slug: str) -> Path:
    return output_root / slug / "dashboard.html"


def _valid_run_slug(slug: str) -> bool:
    return bool(RUN_SLUG_RE.match(slug)) and slug not in {".", ".."}


def _is_safe_child(base: Path, target: Path) -> bool:
    try:
        target.relative_to(base)
    except ValueError:
        return False
    return True


def _content_type(path: Path) -> str:
    if path.suffix == ".html":
        return "text/html; charset=utf-8"
    if path.suffix == ".json":
        return "application/json; charset=utf-8"
    if path.suffix == ".md":
        return "text/markdown; charset=utf-8"
    if path.suffix == ".txt":
        return "text/plain; charset=utf-8"
    return mimetypes.guess_type(str(path))[0] or "application/octet-stream"
