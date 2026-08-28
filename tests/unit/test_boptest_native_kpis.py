from __future__ import annotations

from typing import Any

import pytest

from h3c.runtime import clients
from h3c.runtime.clients import BoptestHttpClient, TransportError


def test_native_kpis_use_the_live_test_id(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def request(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        calls.append((method, url))
        return {"payload": {"cost_tot": 1.5}}

    monkeypatch.setattr(clients, "_request_json", request)
    client = BoptestHttpClient("http://example")
    client.test_id = "test-1"
    assert client.get_kpis() == {"cost_tot": 1.5}
    assert calls == [("GET", "http://example/kpi/test-1")]


def test_native_kpis_fail_before_initialize() -> None:
    with pytest.raises(TransportError, match="before initialize"):
        BoptestHttpClient("http://example").get_kpis()
