from __future__ import annotations

import numpy as np

from h3c.runtime.comfort import ComfortModel
from h3c_baselines.mpc.optimizer import LinearMpcController
from h3c_baselines.mpc.vector_arx import (
    ArxLayout,
    FittedArxModel,
    Scaling,
    build_dataset,
    fit_vector_arx,
)


def _dataset() -> tuple[ArxLayout, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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
        features,
        targets,
        validation_rows=24,
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


def test_mpc_falls_back_deterministically_on_invalid_solver_result(monkeypatch: object) -> None:
    layout, times, outputs, controls, disturbances = _dataset()
    features, targets, _ = build_dataset(layout, times, outputs, controls, disturbances)
    model, _ = fit_vector_arx(
        layout, features, targets, validation_rows=24, alpha_candidates=(0.01,)
    )

    def fail(*args: object, **kwargs: object) -> object:
        raise RuntimeError("solver failed")

    monkeypatch.setattr("h3c_baselines.mpc.optimizer.minimize", fail)  # type: ignore[attr-defined]
    controller = LinearMpcController(
        model,
        {
            "energy_weight": 1.0,
            "energy_scale": 1.0,
            "comfort_weight": 1.0,
            "comfort_scale": 1.0,
            "smoothness_weight": 1.0,
            "smoothness_scale": 1.0,
        },
    )
    decision = controller.decide(
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
