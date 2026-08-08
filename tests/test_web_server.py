from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from autoresearch.web_server import build_index_html, create_handler, discover_runs


def _write_run(output_root, slug: str, topic: str = "GUI agent benchmark") -> None:
    run_dir = output_root / slug
    run_dir.mkdir(parents=True)
    (run_dir / "dashboard.html").write_text("<html>dashboard</html>", encoding="utf-8")
    (run_dir / "search_result.json").write_text(
        json.dumps(
            {
                "topic": topic,
                "generated_at": "2026-08-08T00:00:00Z",
                "ranked_papers": [{"paper": {"title": "paper"}}],
                "gaps": [{"gap": "gap"}],
                "source_readiness": {"status": "ready_for_preliminary_gap_analysis"},
            }
        ),
        encoding="utf-8",
    )


def test_discover_runs_reads_dashboard_summaries(tmp_path):
    _write_run(tmp_path, "gui-agent-benchmark-real-world-workflow")

    runs = discover_runs(tmp_path)

    assert len(runs) == 1
    assert runs[0]["slug"] == "gui-agent-benchmark-real-world-workflow"
    assert runs[0]["topic"] == "GUI agent benchmark"
    assert runs[0]["paper_count"] == 1
    assert runs[0]["gap_count"] == 1
    assert runs[0]["readiness"] == "ready_for_preliminary_gap_analysis"


def test_index_html_mentions_missing_default_run(tmp_path):
    html = build_index_html(tmp_path, default_run="missing-run").decode("utf-8")

    assert "AutoResearch 调研看板" in html
    assert "默认 Run 不存在" in html


def test_web_server_redirects_and_serves_run_files(tmp_path):
    _write_run(tmp_path, "demo-run")
    handler = create_handler(tmp_path, default_run="demo-run")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/")
        response = conn.getresponse()
        response.read()
        assert response.status == 303
        assert response.getheader("Location") == "/runs/demo-run/dashboard.html#mainline"
        conn.close()

        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/runs/demo-run/dashboard.html")
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert "dashboard" in body
        conn.close()

        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/runs/../secret.txt")
        response = conn.getresponse()
        response.read()
        assert response.status == 404
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
