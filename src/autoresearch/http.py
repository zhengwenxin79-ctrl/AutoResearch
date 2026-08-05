from __future__ import annotations

import httpx


USER_AGENT = "AutoResearch/0.1 (https://github.com/zhengwenxin79-ctrl/AutoResearch)"


def get_client(timeout: float = 20.0) -> httpx.Client:
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )

