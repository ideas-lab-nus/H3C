"""Focused tests for baseline report calculations."""

from h3c_baselines.outputs.reporting import _cumulative


def test_cumulative_cost_preserves_every_step() -> None:
    assert _cumulative([0.25, 0.5, 1.0]) == [0.25, 0.75, 1.75]
    assert _cumulative([]) == []
