"""Deterministic receding-horizon optimizer over the shared vector ARX model."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import minimize  # type: ignore[import-untyped]

from h3c.runtime.comfort import ComfortModel, step_reward
from h3c_baselines.mpc.vector_arx import FittedArxModel


@dataclass(frozen=True)
class MpcDecision:
    setpoints_c: dict[str, float]
    diagnostics: dict[str, Any]


class LinearMpcController:
    def __init__(self, model: FittedArxModel, objective: Mapping[str, Any]) -> None:
        self.model = model
        self.objective = dict(objective)

    def decide(
        self,
        *,
        output_history: NDArray[np.float64],
        control_history: NDArray[np.float64],
        disturbances: NDArray[np.float64],
        prices: NDArray[np.float64],
        occupancy: NDArray[np.float64],
        action_times: Sequence[int],
        daily_outdoor_means_c: Sequence[float],
        comfort: ComfortModel,
        previous_setpoints_c: Mapping[str, float],
        enhanced_rbc_warm_start: Mapping[str, float],
    ) -> MpcDecision:
        zones = self.model.layout.zones
        horizon = self.model.layout.horizon_steps
        if prices.shape != (horizon,) or occupancy.shape != (horizon, len(zones)):
            raise ValueError("MPC price or occupancy horizon has the wrong shape")
        if len(action_times) != horizon or len(daily_outdoor_means_c) != horizon:
            raise ValueError("MPC comfort horizon has the wrong length")
        warm = np.vstack([[float(enhanced_rbc_warm_start[zone]) for zone in zones]] * horizon)

        def objective(candidate: NDArray[np.float64]) -> float:
            controls = np.asarray(candidate, dtype=np.float64).reshape(horizon, len(zones))
            predictions, _ = self.model.rollout(
                output_history, control_history, controls, disturbances
            )
            predicted_comfort = copy.deepcopy(comfort)
            total = 0.0
            previous = np.asarray([previous_setpoints_c[zone] for zone in zones], dtype=float)
            for index in range(horizon):
                predicted_comfort.update_clothing(
                    float(action_times[index]), float(daily_outdoor_means_c[index])
                )
                pmv = [predicted_comfort.pmv(value) for value in predictions[index, :-1]]
                power = max(0.0, float(predictions[index, -1]))
                cost = power * 0.25 / 1000.0 * float(prices[index])
                total -= step_reward(
                    cost=cost,
                    pmv=pmv,
                    occupancy=occupancy[index].tolist(),
                    setpoints_c=controls[index].tolist(),
                    previous_setpoints_c=previous.tolist(),
                    objective=self.objective,
                )
                previous = controls[index]
            return float(total)

        try:
            result = minimize(
                objective,
                warm.reshape(-1),
                method="SLSQP",
                bounds=[(20.0, 30.0)] * warm.size,
                options={"maxiter": 100, "ftol": 1e-8, "disp": False},
            )
            solution = np.asarray(result.x, dtype=np.float64).reshape(horizon, len(zones))
            success = (
                bool(result.success)
                and np.all(np.isfinite(solution))
                and bool(np.all((solution >= 20.0) & (solution <= 30.0)))
            )
        except Exception as error:
            return MpcDecision(
                dict(enhanced_rbc_warm_start),
                {
                    "status": "fallback",
                    "method_degraded": True,
                    "reason": f"optimizer_exception:{type(error).__name__}",
                },
            )
        if not success:
            return MpcDecision(
                dict(enhanced_rbc_warm_start),
                {
                    "status": "fallback",
                    "method_degraded": True,
                    "reason": f"optimizer_unsuccessful:{result.message}",
                    "iterations": int(result.nit),
                },
            )
        predictions, negative_power_count = self.model.rollout(
            output_history, control_history, solution, disturbances
        )
        return MpcDecision(
            {zone: float(solution[0, index]) for index, zone in enumerate(zones)},
            {
                "status": "optimized",
                "method_degraded": False,
                "objective": float(result.fun),
                "iterations": int(result.nit),
                "negative_power_prediction_count": negative_power_count,
                "planned_setpoints_c": solution.tolist(),
                "predicted_outputs": predictions.tolist(),
            },
        )
