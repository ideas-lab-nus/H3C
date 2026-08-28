from __future__ import annotations

import pytest

from h3c.causal.workflow import (
    GraphWorkflowError,
    confirm_graph,
    prepare_proposal,
    propose_graph,
    validate_proposal,
)


def test_workflow_preserves_source_schema_and_human_confirmation() -> None:
    prepared = prepare_proposal("Demo", ("north",), ("engineering source",))
    prepared["edges"] = [
        {
            "source": "cooling_setpoint",
            "relation": "Positive Corr",
            "target": "zone_temp",
            "tags": ["Immediate", "Strong Impact"],
            "timing": "immediate",
        }
    ]
    proposed = propose_graph(prepared)
    validate_proposal(proposed, required_status="proposed")
    graph = confirm_graph(proposed, reviewer="Building engineer", date="2026-08-27")
    resolved = graph.resolved()
    assert resolved["graph_schema"] == "confirmed_causal_graph"
    assert resolved["sources"] == ["engineering source"]
    assert resolved["confirmation"] == {
        "status": "confirmed",
        "reviewer": "Building engineer",
        "date": "2026-08-27",
    }
    assert resolved["edges"][0]["id"].startswith("ce_")


def test_proposal_without_edges_fails_closed() -> None:
    prepared = prepare_proposal("Demo", ("north",), ("engineering source",))
    with pytest.raises(GraphWorkflowError, match="at least one"):
        propose_graph(prepared)
