from __future__ import annotations

from types import SimpleNamespace
from typing import TypedDict

import numpy as np
import pytest
from numpy.typing import NDArray

import h3c_baselines.mpc.optimizer as optimizer
from h3c.runtime.comfort import ComfortModel
from h3c_baselines.mpc.optimizer import HierarchicalMpcController
from h3c_baselines.mpc.vector_arx import (
    ArxLayout,
    FittedArxModel,
    Scaling,
    build_dataset,
    fit_vector_arx,
)

CONTROL_SUPPORT = {
    "occupied_bounds_c": [23.5, 26.5],
    "unoccupied_bounds_c": [20.0, 30.0],
}


class _DecisionArguments(TypedDict):
    output_history: NDArray[np.float64]
    control_history: NDArray[np.float64]
    disturbances: NDArray[np.float64]
    prices: NDArray[np.float64]
    occupancy: NDArray[np.float64]
    terminal_occupancy: dict[str, float]
    action_times: list[int]
    daily_outdoor_means_c: list[float]
    comfort: ComfortModel
    previous_setpoints_c: dict[str, float]
    enhanced_rbc_warm_start: dict[str, float]


class _DecisionArgumentsWithoutOccupancy(TypedDict):
    output_history: NDArray[np.float64]
    control_history: NDArray[np.float64]
    disturbances: NDArray[np.float64]
    prices: NDArray[np.float64]
    action_times: list[int]
    daily_outdoor_means_c: list[float]
    comfort: ComfortModel
    previous_setpoints_c: dict[str, float]
    enhanced_rbc_warm_start: dict[str, float]


def test_osqp_uses_deterministic_adaptive_rho_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings: dict[str, object] = {}

    class FakeSolver:
        def __init__(self) -> None:
            self.warm: NDArray[np.float64] = np.zeros(1, dtype=np.float64)

        def setup(self, **kwargs: object) -> None:
            settings.update(kwargs)

        def warm_start(self, *, x: NDArray[np.float64]) -> None:
            self.warm = x.copy()

        def solve(self, *, raise_error: bool) -> SimpleNamespace:
            assert raise_error is False
            return SimpleNamespace(
                x=self.warm.copy(),
                info=SimpleNamespace(
                    status="solved",
                    obj_val=0.0,
                    iter=1,
                    prim_res=0.0,
                    dual_res=0.0,
                ),
            )

    monkeypatch.setattr("h3c_baselines.mpc.optimizer.osqp.OSQP", FakeSolver)
    optimizer._solve_qp(
        np.eye(1),
        np.zeros(1),
        [np.ones(1)],
        [0.0],
        [1.0],
        np.asarray([0.5]),
    )

    assert settings["adaptive_rho"] is True
    assert settings["adaptive_rho_interval"] == 100
    assert settings["max_iter"] == 50_000


def test_osqp_solved_inaccurate_remains_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InaccurateSolver:
        def setup(self, **_kwargs: object) -> None:
            pass

        def warm_start(self, *, x: NDArray[np.float64]) -> None:
            self.warm = x.copy()

        def solve(self, *, raise_error: bool) -> SimpleNamespace:
            assert raise_error is False
            return SimpleNamespace(
                x=self.warm.copy(),
                info=SimpleNamespace(
                    status="solved inaccurate",
                    obj_val=0.0,
                    iter=50_000,
                    prim_res=2e-5,
                    dual_res=3e-5,
                ),
            )

    monkeypatch.setattr("h3c_baselines.mpc.optimizer.osqp.OSQP", InaccurateSolver)
    with pytest.raises(optimizer.MpcSolverError) as captured:
        optimizer._solve_qp(
            np.eye(1),
            np.zeros(1),
            [np.ones(1)],
            [0.0],
            [1.0],
            np.asarray([0.5]),
        )

    assert captured.value.status == "solved inaccurate"
    assert captured.value.iterations == 50_000
    assert captured.value.primal_residual == pytest.approx(2e-5)
    assert captured.value.dual_residual == pytest.approx(3e-5)


def _dataset() -> tuple[
    ArxLayout,
    NDArray[np.int64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    layout = ArxLayout(("z",), ("outdoor", "solar", "occupancy", "sin", "cos"))
    times = np.arange(0, 150 * 900, 900, dtype=np.int64)
    controls = np.full((150, 1), 25.0)
    disturbances = np.column_stack(
        (np.full(150, 20.0), np.arange(150), np.ones(150), np.zeros(150), np.ones(150))
    )
    outputs = np.zeros((150, 2))
    outputs[0] = [24.0, 100.0]
    for index in range(149):
        outputs[index + 1, 0] = 0.9 * outputs[index, 0] + 0.1 * controls[index, 0]
        outputs[index + 1, 1] = 50.0 + 2.0 * controls[index, 0]
    return layout, times, outputs, controls, disturbances


def test_dataset_uses_current_control_to_predict_next_output() -> None:
    layout, times, outputs, controls, disturbances = _dataset()
    features, targets, target_times = build_dataset(layout, times, outputs, controls, disturbances)
    assert target_times[0] == times[4]
    assert features[0, : layout.output_dimension].tolist() == outputs[3].tolist()
    control_offset = layout.lag_count * layout.output_dimension
    assert features[0, control_offset] == controls[3, 0]
    assert targets[0].tolist() == outputs[4].tolist()


def test_ridge_selection_and_four_step_rollout_are_finite() -> None:
    layout, times, outputs, controls, disturbances = _dataset()
    features, targets, _ = build_dataset(layout, times, outputs, controls, disturbances)
    model, report = fit_vector_arx(
        layout,
        features[:-24],
        targets[:-24],
        holdout_features=features[-24:],
        holdout_outputs=targets[-24:],
        alpha_candidates=(1e-6, 1e-4, 1e-2, 1.0, 100.0),
    )
    prediction, _ = model.rollout(
        outputs[146:150][::-1],
        controls[146:150][::-1],
        np.full((4, 1), 25.0),
        disturbances[146:150],
    )
    assert prediction.shape == (4, 2)
    assert np.all(np.isfinite(prediction))
    assert report["selected_alpha"] in (1e-6, 1e-4, 1e-2, 1.0, 100.0)


def test_affine_rollout_matches_recursive_unclipped_rollout() -> None:
    layout, times, outputs, controls, disturbances = _dataset()
    features, targets, _ = build_dataset(layout, times, outputs, controls, disturbances)
    model, _ = fit_vector_arx(
        layout,
        features[:-24],
        targets[:-24],
        holdout_features=features[-24:],
        holdout_outputs=targets[-24:],
        alpha_candidates=(0.01,),
    )
    future_controls = np.asarray([[24.0], [25.0], [26.0], [25.5]])
    history_outputs = outputs[146:150][::-1]
    history_controls = controls[146:150][::-1]
    future_disturbances = disturbances[146:150]
    offset, response = model.affine_rollout(history_outputs, history_controls, future_disturbances)
    lifted = (offset + response @ future_controls.reshape(-1)).reshape(4, 2)
    recursive = model.rollout_unclipped(
        history_outputs, history_controls, future_controls, future_disturbances
    )
    assert lifted == pytest.approx(recursive)


def test_mpc_falls_back_deterministically_on_invalid_solver_result(
    monkeypatch: object,
) -> None:
    layout, times, outputs, controls, disturbances = _dataset()
    features, targets, _ = build_dataset(layout, times, outputs, controls, disturbances)
    model, _ = fit_vector_arx(
        layout,
        features[:-24],
        targets[:-24],
        holdout_features=features[-24:],
        holdout_outputs=targets[-24:],
        alpha_candidates=(0.01,),
    )

    def fail(*args: object, **kwargs: object) -> object:
        raise RuntimeError("solver failed")

    monkeypatch.setattr("h3c_baselines.mpc.optimizer._solve_qp", fail)  # type: ignore[attr-defined]
    controller = HierarchicalMpcController(
        model,
        {
            "energy_weight": 1.0,
            "energy_scale": 1.0,
            "comfort_weight": 1.0,
            "comfort_scale": 1.0,
            "smoothness_weight": 1.0,
            "smoothness_scale": 1.0,
        },
        CONTROL_SUPPORT,
    )
    decision = controller.decide(
        step=0,
        output_history=outputs[146:150][::-1],
        control_history=controls[146:150][::-1],
        disturbances=disturbances[146:150],
        prices=np.ones(4) * 0.1,
        occupancy=np.ones((4, 1)),
        action_times=[0, 900, 1800, 2700],
        daily_outdoor_means_c=[20.0] * 4,
        comfort=ComfortModel(
            {
                "dynamic_clothing": False,
                "metabolic_rate": 1.1,
                "relative_humidity_percent": 50.0,
                "air_velocity_m_s": 0.1,
                "winter_clothing_insulation": 1.0,
                "summer_clothing_insulation": 0.5,
                "clothing_transition_low_c": 10.0,
                "clothing_transition_high_c": 26.0,
            }
        ),
        previous_setpoints_c={"z": 25.0},
        enhanced_rbc_warm_start={"z": 25.0},
    )
    assert decision.setpoints_c == {"z": 25.0}
    assert decision.diagnostics["method_degraded"] is True
    assert decision.diagnostics["reason_detail"] == "solver failed"
    assert decision.diagnostics["failure_stage"] == "building_coordinator"


def test_hierarchical_mpc_runs_upper_hourly_and_lower_each_step() -> None:
    layout = ArxLayout(("z",), ("outdoor", "solar", "occupancy", "sin", "cos"))
    model = FittedArxModel(
        layout=layout,
        intercept=np.asarray([24.0, 100.0]),
        coefficients=np.zeros((layout.feature_dimension, 2)),
        scaling=Scaling(
            feature_mean=np.zeros(layout.feature_dimension),
            feature_scale=np.ones(layout.feature_dimension),
            output_mean=np.zeros(2),
            output_scale=np.ones(2),
        ),
        ridge_alpha=1.0,
        identity="synthetic-constant-model",
    )
    controller = HierarchicalMpcController(
        model,
        {
            "energy_weight": 1.0,
            "energy_scale": 1.0,
            "comfort_weight": 1.0,
            "comfort_scale": 1.0,
            "smoothness_weight": 1.0,
            "smoothness_scale": 1.0,
        },
        CONTROL_SUPPORT,
    )
    comfort = ComfortModel(
        {
            "dynamic_clothing": False,
            "metabolic_rate": 1.1,
            "relative_humidity_percent": 50.0,
            "air_velocity_m_s": 0.1,
            "winter_clothing_insulation": 1.0,
            "summer_clothing_insulation": 0.5,
            "clothing_transition_low_c": 10.0,
            "clothing_transition_high_c": 26.0,
        }
    )
    arguments: _DecisionArguments = {
        "output_history": np.vstack([[24.0, 100.0]] * 4),
        "control_history": np.vstack([[25.0]] * 4),
        "disturbances": np.zeros((4, 5)),
        "prices": np.full(4, 0.1),
        "occupancy": np.zeros((4, 1)),
        "terminal_occupancy": {"z": 0.0},
        "action_times": [0, 900, 1800, 2700],
        "daily_outdoor_means_c": [20.0] * 4,
        "comfort": comfort,
        "previous_setpoints_c": {"z": 25.0},
        "enhanced_rbc_warm_start": {"z": 25.0},
    }
    first = controller.decide(step=0, **arguments)
    second = controller.decide(step=1, **arguments)

    assert first.diagnostics["status"] == second.diagnostics["status"] == "optimized"
    assert first.diagnostics["coordinator_updated"] is True
    assert second.diagnostics["coordinator_updated"] is False
    assert isinstance(first.diagnostics["coordinator_iterations"], int)
    assert first.diagnostics["coordinator_iterations"] > 0
    assert first.diagnostics["zone_iterations"]["z"] > 0
    assert first.diagnostics["feedback_iterations"] in {0, 1}
    assert second.diagnostics["feedback_iterations"] in {0, 1}
    assert 20.0 <= first.setpoints_c["z"] <= 30.0
    assert 20.0 <= second.setpoints_c["z"] <= 30.0


def test_coordinator_scales_power_auxiliary_variables_to_kw(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = ArxLayout(("z",), ("outdoor", "solar", "occupancy", "sin", "cos"))
    model = FittedArxModel(
        layout=layout,
        intercept=np.asarray([24.0, 100_000.0]),
        coefficients=np.zeros((layout.feature_dimension, 2)),
        scaling=Scaling(
            feature_mean=np.zeros(layout.feature_dimension),
            feature_scale=np.ones(layout.feature_dimension),
            output_mean=np.zeros(2),
            output_scale=np.ones(2),
        ),
        ridge_alpha=1.0,
        identity="synthetic-power-scaling-model",
    )
    calls: list[dict[str, NDArray[np.float64]]] = []

    def capture(
        quadratic: NDArray[np.float64],
        linear: NDArray[np.float64],
        rows: list[NDArray[np.float64]],
        lower: list[float],
        upper: list[float],
        warm_start: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], float, int]:
        calls.append(
            {
                "linear": linear.copy(),
                "rows": np.vstack(rows),
                "lower": np.asarray(lower),
                "upper": np.asarray(upper),
                "warm_start": warm_start.copy(),
            }
        )
        return warm_start.copy(), 0.0, 1

    monkeypatch.setattr("h3c_baselines.mpc.optimizer._solve_qp", capture)
    controller = HierarchicalMpcController(
        model,
        {
            "energy_weight": 1.0,
            "energy_scale": 1.0,
            "comfort_weight": 1.0,
            "comfort_scale": 1.0,
            "smoothness_weight": 1.0,
            "smoothness_scale": 1.0,
        },
        CONTROL_SUPPORT,
    )
    decision = controller.decide(
        step=0,
        output_history=np.vstack([[24.0, 100_000.0]] * 4),
        control_history=np.vstack([[25.0]] * 4),
        disturbances=np.zeros((4, 5)),
        prices=np.full(4, 0.1),
        occupancy=np.zeros((4, 1)),
        action_times=[0, 900, 1800, 2700],
        daily_outdoor_means_c=[20.0] * 4,
        comfort=ComfortModel(
            {
                "dynamic_clothing": False,
                "metabolic_rate": 1.1,
                "relative_humidity_percent": 50.0,
                "air_velocity_m_s": 0.1,
                "winter_clothing_insulation": 1.0,
                "summer_clothing_insulation": 0.5,
                "clothing_transition_low_c": 10.0,
                "clothing_transition_high_c": 26.0,
            }
        ),
        previous_setpoints_c={"z": 25.0},
        enhanced_rbc_warm_start={"z": 25.0},
    )

    assert decision.diagnostics["status"] == "optimized"
    coordinator = calls[0]
    assert coordinator["warm_start"][4:8].tolist() == [100.0] * 4
    assert coordinator["linear"][4:8].tolist() == pytest.approx([0.025] * 4)


def test_negative_power_is_clipped_without_making_the_qp_infeasible() -> None:
    layout = ArxLayout(("z",), ("outdoor", "solar", "occupancy", "sin", "cos"))
    model = FittedArxModel(
        layout=layout,
        intercept=np.asarray([24.0, -100.0]),
        coefficients=np.zeros((layout.feature_dimension, 2)),
        scaling=Scaling(
            feature_mean=np.zeros(layout.feature_dimension),
            feature_scale=np.ones(layout.feature_dimension),
            output_mean=np.zeros(2),
            output_scale=np.ones(2),
        ),
        ridge_alpha=1.0,
        identity="synthetic-negative-power-controller-model",
    )
    controller = HierarchicalMpcController(
        model,
        {
            "energy_weight": 1.0,
            "energy_scale": 1.0,
            "comfort_weight": 1.0,
            "comfort_scale": 1.0,
            "smoothness_weight": 1.0,
            "smoothness_scale": 1.0,
        },
        CONTROL_SUPPORT,
    )
    arguments: _DecisionArguments = {
        "output_history": np.vstack([[24.0, 0.0]] * 4),
        "control_history": np.vstack([[25.0]] * 4),
        "disturbances": np.zeros((4, 5)),
        "prices": np.full(4, 0.1),
        "occupancy": np.zeros((4, 1)),
        "terminal_occupancy": {"z": 0.0},
        "action_times": [0, 900, 1800, 2700],
        "daily_outdoor_means_c": [20.0] * 4,
        "comfort": ComfortModel(
            {
                "dynamic_clothing": False,
                "metabolic_rate": 1.1,
                "relative_humidity_percent": 50.0,
                "air_velocity_m_s": 0.1,
                "winter_clothing_insulation": 1.0,
                "summer_clothing_insulation": 0.5,
                "clothing_transition_low_c": 10.0,
                "clothing_transition_high_c": 26.0,
            }
        ),
        "previous_setpoints_c": {"z": 25.0},
        "enhanced_rbc_warm_start": {"z": 25.0},
    }

    first = controller.decide(step=0, **arguments)
    second = controller.decide(step=1, **arguments)

    assert first.diagnostics["status"] == second.diagnostics["status"] == "optimized"
    assert first.diagnostics["negative_power_predictions_clipped"] == 4
    assert second.diagnostics["negative_power_predictions_clipped"] == 4
    assert np.asarray(first.diagnostics["predicted_outputs"])[:, -1].tolist() == [0.0] * 4


def test_occupied_controls_stay_inside_identification_support() -> None:
    layout = ArxLayout(("z",), ("outdoor", "solar", "occupancy", "sin", "cos"))
    model = FittedArxModel(
        layout=layout,
        intercept=np.asarray([30.0, 0.0]),
        coefficients=np.zeros((layout.feature_dimension, 2)),
        scaling=Scaling(
            feature_mean=np.zeros(layout.feature_dimension),
            feature_scale=np.ones(layout.feature_dimension),
            output_mean=np.zeros(2),
            output_scale=np.ones(2),
        ),
        ridge_alpha=1.0,
        identity="synthetic-unresponsive-hot-zone-model",
    )
    controller = HierarchicalMpcController(
        model,
        {
            "energy_weight": 1.0,
            "energy_scale": 1.0,
            "comfort_weight": 1.0,
            "comfort_scale": 1.0,
            "smoothness_weight": 1.0,
            "smoothness_scale": 1.0,
        },
        CONTROL_SUPPORT,
    )
    decision = controller.decide(
        step=0,
        output_history=np.vstack([[30.0, 0.0]] * 4),
        control_history=np.vstack([[25.0]] * 4),
        disturbances=np.zeros((4, 5)),
        prices=np.full(4, 0.1),
        occupancy=np.ones((4, 1)),
        action_times=[0, 900, 1800, 2700],
        daily_outdoor_means_c=[20.0] * 4,
        comfort=ComfortModel(
            {
                "dynamic_clothing": False,
                "metabolic_rate": 1.1,
                "relative_humidity_percent": 50.0,
                "air_velocity_m_s": 0.1,
                "winter_clothing_insulation": 1.0,
                "summer_clothing_insulation": 0.5,
                "clothing_transition_low_c": 10.0,
                "clothing_transition_high_c": 26.0,
            }
        ),
        previous_setpoints_c={"z": 25.0},
        enhanced_rbc_warm_start={"z": 25.0},
    )

    assert decision.diagnostics["status"] == "optimized"
    assert 23.5 <= decision.setpoints_c["z"] <= 26.5
    assert decision.diagnostics["predicted_peak_absolute_pmv"] > 0.70


@pytest.mark.parametrize(
    ("occupancy_k_plus_3", "occupancy_k_plus_4", "expected_terminal_reference"),
    [(0.0, 1.0, 25.0), (1.0, 0.0, 30.0)],
)
def test_shifted_hourly_reference_respects_new_terminal_occupancy(
    occupancy_k_plus_3: float,
    occupancy_k_plus_4: float,
    expected_terminal_reference: float,
) -> None:
    layout = ArxLayout(("z",), ("outdoor", "solar", "occupancy", "sin", "cos"))
    model = FittedArxModel(
        layout=layout,
        intercept=np.asarray([24.0, 100.0]),
        coefficients=np.zeros((layout.feature_dimension, 2)),
        scaling=Scaling(
            feature_mean=np.zeros(layout.feature_dimension),
            feature_scale=np.ones(layout.feature_dimension),
            output_mean=np.zeros(2),
            output_scale=np.ones(2),
        ),
        ridge_alpha=1.0,
        identity="synthetic-occupancy-transition-model",
    )
    controller = HierarchicalMpcController(
        model,
        {
            "energy_weight": 1.0,
            "energy_scale": 1.0,
            "comfort_weight": 1.0,
            "comfort_scale": 1.0,
            "smoothness_weight": 1.0,
            "smoothness_scale": 1.0,
        },
        CONTROL_SUPPORT,
    )
    comfort = ComfortModel(
        {
            "dynamic_clothing": False,
            "metabolic_rate": 1.1,
            "relative_humidity_percent": 50.0,
            "air_velocity_m_s": 0.1,
            "winter_clothing_insulation": 1.0,
            "summer_clothing_insulation": 0.5,
            "clothing_transition_low_c": 10.0,
            "clothing_transition_high_c": 26.0,
        }
    )
    common: _DecisionArgumentsWithoutOccupancy = {
        "output_history": np.vstack([[24.0, 100.0]] * 4),
        "control_history": np.vstack([[30.0]] * 4),
        "disturbances": np.zeros((4, 5)),
        "prices": np.full(4, 0.1),
        "action_times": [0, 900, 1800, 2700],
        "daily_outdoor_means_c": [20.0] * 4,
        "comfort": comfort,
        "previous_setpoints_c": {"z": 30.0},
        "enhanced_rbc_warm_start": {"z": 30.0},
    }
    first = controller.decide(
        step=0,
        occupancy=np.zeros((4, 1)),
        terminal_occupancy={"z": 0.0},
        **common,
    )
    second = controller.decide(
        step=1,
        occupancy=np.asarray([[0.0], [0.0], [0.0], [occupancy_k_plus_3]]),
        terminal_occupancy={"z": occupancy_k_plus_4},
        **common,
    )

    assert first.diagnostics["status"] == second.diagnostics["status"] == "optimized"
    terminal_reference = second.diagnostics["upper_reference_setpoints_c"][-1][0]
    assert terminal_reference == expected_terminal_reference


def test_rollout_clamps_negative_power_before_recursive_use() -> None:
    layout = ArxLayout(("z",), ("outdoor", "solar", "occupancy", "sin", "cos"))
    model = FittedArxModel(
        layout=layout,
        intercept=np.asarray([24.0, -10.0]),
        coefficients=np.zeros((layout.feature_dimension, 2)),
        scaling=Scaling(
            feature_mean=np.zeros(layout.feature_dimension),
            feature_scale=np.ones(layout.feature_dimension),
            output_mean=np.zeros(2),
            output_scale=np.ones(2),
        ),
        ridge_alpha=1.0,
        identity="synthetic-negative-power-model",
    )
    predictions, count = model.rollout(
        np.zeros((4, 2)),
        np.full((4, 1), 25.0),
        np.full((4, 1), 25.0),
        np.zeros((4, 5)),
    )
    assert count == 4
    assert predictions[:, -1].tolist() == [0.0, 0.0, 0.0, 0.0]
