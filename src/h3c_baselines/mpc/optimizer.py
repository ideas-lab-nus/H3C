"""Two-level, receding-horizon MPC over the shared vector ARX model."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import osqp  # type: ignore[import-untyped]
from numpy.typing import NDArray
from scipy import sparse  # type: ignore[import-untyped]

from h3c.runtime.comfort import COMFORT_BAND, ComfortModel
from h3c_baselines.mpc.vector_arx import FittedArxModel

PMV_LIMIT = 0.70
PMV_LINEARIZATION_DELTA_C = 0.05
QP_TOLERANCE = 1e-5


@dataclass(frozen=True)
class MpcDecision:
    setpoints_c: dict[str, float]
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class _ComfortLine:
    slope: float
    intercept: float
    occupied: bool


@dataclass(frozen=True)
class _UpperPlan:
    controls: NDArray[np.float64]
    predicted_outputs: NDArray[np.float64]
    comfort_lines: tuple[_ComfortLine, ...]


def _difference_matrix(horizon: int, zones: int) -> NDArray[np.float64]:
    matrix = np.zeros((horizon * zones, horizon * zones), dtype=np.float64)
    for step in range(horizon):
        for zone in range(zones):
            row = step * zones + zone
            matrix[row, row] = 1.0
            if step:
                matrix[row, (step - 1) * zones + zone] = -1.0
    return matrix


def _solve_qp(
    quadratic: NDArray[np.float64],
    linear: NDArray[np.float64],
    rows: list[NDArray[np.float64]],
    lower: list[float],
    upper: list[float],
    warm_start: NDArray[np.float64],
) -> tuple[NDArray[np.float64], float, int]:
    solver = osqp.OSQP()
    solver.setup(
        P=sparse.csc_matrix(quadratic),
        q=linear,
        A=sparse.csc_matrix(np.vstack(rows)),
        l=np.asarray(lower, dtype=np.float64),
        u=np.asarray(upper, dtype=np.float64),
        eps_abs=QP_TOLERANCE,
        eps_rel=QP_TOLERANCE,
        max_iter=10_000,
        polishing=True,
        adaptive_rho=False,
        verbose=False,
    )
    solver.warm_start(x=warm_start)
    result = solver.solve(raise_error=False)
    if str(result.info.status).lower() != "solved" or result.x is None:
        raise ValueError(f"OSQP did not solve the registered QP: {result.info.status}")
    solution = np.asarray(result.x, dtype=np.float64)
    if np.any(~np.isfinite(solution)):
        raise ValueError("OSQP returned a non-finite solution")
    return solution, float(result.info.obj_val), int(result.info.iter)


def _linearized_comfort(
    *,
    warm_predictions: NDArray[np.float64],
    occupancy: NDArray[np.float64],
    action_times: Sequence[int],
    daily_outdoor_means_c: Sequence[float],
    comfort: ComfortModel,
) -> tuple[_ComfortLine, ...]:
    horizon, zone_count = occupancy.shape
    predicted_comfort = copy.deepcopy(comfort)
    lines: list[_ComfortLine] = []
    for step in range(horizon):
        predicted_comfort.update_clothing(
            float(action_times[step]), float(daily_outdoor_means_c[step])
        )
        for zone in range(zone_count):
            temperature = float(warm_predictions[step, zone])
            low = predicted_comfort.pmv(temperature - PMV_LINEARIZATION_DELTA_C)
            high = predicted_comfort.pmv(temperature + PMV_LINEARIZATION_DELTA_C)
            slope = (high - low) / (2.0 * PMV_LINEARIZATION_DELTA_C)
            intercept = predicted_comfort.pmv(temperature) - slope * temperature
            if not np.isfinite(slope) or not np.isfinite(intercept) or slope <= 0:
                raise ValueError("PMV linearization is invalid")
            lines.append(_ComfortLine(slope, intercept, bool(float(occupancy[step, zone]) > 0)))
    return tuple(lines)


def _add_comfort_constraints(
    *,
    variable_count: int,
    control_slice: slice,
    excess_slice: slice,
    temperature_offset: NDArray[np.float64],
    temperature_response: NDArray[np.float64],
    comfort_lines: Sequence[_ComfortLine],
    rows: list[NDArray[np.float64]],
    lower: list[float],
    upper: list[float],
) -> None:
    for index, line in enumerate(comfort_lines):
        excess_row = np.zeros(variable_count, dtype=np.float64)
        excess_row[excess_slice.start + index] = 1.0
        if not line.occupied:
            rows.append(excess_row)
            lower.append(0.0)
            upper.append(0.0)
            continue
        pmv_response = line.slope * temperature_response[index]
        pmv_offset = line.slope * temperature_offset[index] + line.intercept
        hot = excess_row.copy()
        hot[control_slice] -= pmv_response
        rows.append(hot)
        lower.append(pmv_offset - COMFORT_BAND)
        upper.append(np.inf)
        cold = excess_row.copy()
        cold[control_slice] += pmv_response
        rows.append(cold)
        lower.append(-pmv_offset - COMFORT_BAND)
        upper.append(np.inf)
        rows.append(excess_row)
        lower.append(0.0)
        upper.append(np.inf)
        pmv_row = np.zeros(variable_count, dtype=np.float64)
        pmv_row[control_slice] = pmv_response
        rows.append(pmv_row)
        lower.append(-PMV_LIMIT - pmv_offset)
        upper.append(PMV_LIMIT - pmv_offset)


class BuildingCoordinator:
    """Solve the registered whole-building objective once per hour."""

    def __init__(self, model: FittedArxModel, objective: Mapping[str, Any]) -> None:
        self.model = model
        self.objective = dict(objective)

    def solve(
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
        previous_setpoints: NDArray[np.float64],
        warm_plan: NDArray[np.float64],
    ) -> _UpperPlan:
        layout = self.model.layout
        horizon = layout.horizon_steps
        zones = layout.control_dimension
        control_count = horizon * zones
        if prices.shape != (horizon,) or np.any(~np.isfinite(prices)) or np.any(prices <= 0):
            raise ValueError("MPC prices must be finite and strictly positive")
        if occupancy.shape != (horizon, zones) or warm_plan.shape != (horizon, zones):
            raise ValueError("MPC coordinator horizon has the wrong shape")
        offset, response = self.model.affine_rollout(output_history, control_history, disturbances)
        output_dimension = layout.output_dimension
        temperature_rows = np.asarray(
            [step * output_dimension + zone for step in range(horizon) for zone in range(zones)]
        )
        power_rows = np.asarray([step * output_dimension + zones for step in range(horizon)])
        temperature_offset = offset[temperature_rows]
        temperature_response = response[temperature_rows]
        power_offset = offset[power_rows]
        power_response = response[power_rows]
        warm_predictions = self.model.rollout_unclipped(
            output_history, control_history, warm_plan, disturbances
        )
        comfort_lines = _linearized_comfort(
            warm_predictions=warm_predictions,
            occupancy=occupancy,
            action_times=action_times,
            daily_outdoor_means_c=daily_outdoor_means_c,
            comfort=comfort,
        )

        power_slice = slice(control_count, control_count + horizon)
        excess_slice = slice(power_slice.stop, power_slice.stop + control_count)
        smooth_slice = slice(excess_slice.stop, excess_slice.stop + control_count)
        variable_count = smooth_slice.stop
        quadratic = np.zeros((variable_count, variable_count), dtype=np.float64)
        linear = np.zeros(variable_count, dtype=np.float64)
        energy_factor = (
            float(self.objective["energy_weight"])
            * float(self.objective["energy_scale"])
            * 0.25
            / 1000.0
            / zones
        )
        comfort_factor = (
            float(self.objective["comfort_weight"]) * float(self.objective["comfort_scale"]) / zones
        )
        smoothness_factor = (
            float(self.objective["smoothness_weight"])
            * float(self.objective["smoothness_scale"])
            / zones
        )
        linear[power_slice] = energy_factor * prices
        quadratic[excess_slice, excess_slice] = np.eye(control_count) * 2 * comfort_factor
        linear[smooth_slice] = smoothness_factor

        rows: list[NDArray[np.float64]] = []
        lower: list[float] = []
        upper: list[float] = []
        for index in range(control_count):
            row = np.zeros(variable_count, dtype=np.float64)
            row[index] = 1.0
            rows.append(row)
            lower.append(20.0)
            upper.append(30.0)
        for step in range(horizon):
            raw_power = np.zeros(variable_count, dtype=np.float64)
            raw_power[:control_count] = power_response[step]
            rows.append(raw_power)
            lower.append(-float(power_offset[step]))
            upper.append(np.inf)
            envelope = -raw_power
            envelope[power_slice.start + step] = 1.0
            rows.append(envelope)
            lower.append(float(power_offset[step]))
            upper.append(np.inf)
            nonnegative = np.zeros(variable_count, dtype=np.float64)
            nonnegative[power_slice.start + step] = 1.0
            rows.append(nonnegative)
            lower.append(0.0)
            upper.append(np.inf)

        difference = _difference_matrix(horizon, zones)
        difference_offset = np.zeros(control_count, dtype=np.float64)
        difference_offset[:zones] = -previous_setpoints
        for index in range(control_count):
            for sign in (-1.0, 1.0):
                row = np.zeros(variable_count, dtype=np.float64)
                row[:control_count] = sign * difference[index]
                row[smooth_slice.start + index] = 1.0
                rows.append(row)
                lower.append(float(sign * -difference_offset[index]))
                upper.append(np.inf)
            row = np.zeros(variable_count, dtype=np.float64)
            row[smooth_slice.start + index] = 1.0
            rows.append(row)
            lower.append(0.0)
            upper.append(np.inf)
        _add_comfort_constraints(
            variable_count=variable_count,
            control_slice=slice(0, control_count),
            excess_slice=excess_slice,
            temperature_offset=temperature_offset,
            temperature_response=temperature_response,
            comfort_lines=comfort_lines,
            rows=rows,
            lower=lower,
            upper=upper,
        )
        warm_pmv = np.asarray(
            [
                line.slope * warm_predictions.reshape(-1)[temperature_rows[index]] + line.intercept
                for index, line in enumerate(comfort_lines)
            ]
        )
        warm_excess = np.asarray(
            [
                max(0.0, abs(value) - COMFORT_BAND) if line.occupied else 0.0
                for value, line in zip(warm_pmv, comfort_lines, strict=True)
            ]
        )
        warm_smooth = np.abs(difference @ warm_plan.reshape(-1) + difference_offset)
        warm_start = np.concatenate(
            (
                warm_plan.reshape(-1),
                np.maximum(0.0, warm_predictions[:, -1]),
                warm_excess,
                warm_smooth,
            )
        )
        solution, _, _ = _solve_qp(quadratic, linear, rows, lower, upper, warm_start)
        controls = solution[:control_count].reshape(horizon, zones)
        predictions = self.model.rollout_unclipped(
            output_history, control_history, controls, disturbances
        )
        return _UpperPlan(controls, predictions, comfort_lines)


class ZoneMpcOptimizer:
    """Resolve zone plans inside the coordinator's power contribution budget."""

    def __init__(self, model: FittedArxModel, objective: Mapping[str, Any]) -> None:
        self.model = model
        self.objective = dict(objective)

    def solve(
        self,
        *,
        zone_index: int,
        upper_plan: _UpperPlan,
        offset: NDArray[np.float64],
        response: NDArray[np.float64],
        previous_setpoint: float,
    ) -> NDArray[np.float64]:
        layout = self.model.layout
        horizon = layout.horizon_steps
        zones = layout.control_dimension
        output_dimension = layout.output_dimension
        columns = np.asarray([step * zones + zone_index for step in range(horizon)])
        fixed = upper_plan.controls.reshape(-1).copy()
        fixed[columns] = 0.0
        temperature_rows = np.asarray(
            [step * output_dimension + zone_index for step in range(horizon)]
        )
        power_rows = np.asarray([step * output_dimension + zones for step in range(horizon)])
        temperature_response = response[np.ix_(temperature_rows, columns)]
        temperature_offset = offset[temperature_rows] + response[temperature_rows] @ fixed
        power_response = response[np.ix_(power_rows, columns)]
        power_budget = np.asarray(
            [power_response[step] @ upper_plan.controls[:, zone_index] for step in range(horizon)]
        )
        excess_slice = slice(horizon, horizon * 2)
        smooth_slice = slice(horizon * 2, horizon * 3)
        variable_count = horizon * 3
        quadratic = np.zeros((variable_count, variable_count), dtype=np.float64)
        linear = np.zeros(variable_count, dtype=np.float64)
        comfort_factor = (
            float(self.objective["comfort_weight"]) * float(self.objective["comfort_scale"]) / zones
        )
        smoothness_factor = (
            float(self.objective["smoothness_weight"])
            * float(self.objective["smoothness_scale"])
            / zones
        )
        quadratic[excess_slice, excess_slice] = np.eye(horizon) * 2 * comfort_factor
        linear[smooth_slice] = smoothness_factor
        rows: list[NDArray[np.float64]] = []
        lower: list[float] = []
        upper: list[float] = []
        for index in range(horizon):
            row = np.zeros(variable_count, dtype=np.float64)
            row[index] = 1.0
            rows.append(row)
            lower.append(20.0)
            upper.append(30.0)
            budget = np.zeros(variable_count, dtype=np.float64)
            budget[:horizon] = power_response[index]
            rows.append(budget)
            lower.append(-np.inf)
            upper.append(float(power_budget[index]))
        difference = _difference_matrix(horizon, 1)
        difference_offset = np.zeros(horizon, dtype=np.float64)
        difference_offset[0] = -previous_setpoint
        for index in range(horizon):
            for sign in (-1.0, 1.0):
                row = np.zeros(variable_count, dtype=np.float64)
                row[:horizon] = sign * difference[index]
                row[smooth_slice.start + index] = 1.0
                rows.append(row)
                lower.append(float(sign * -difference_offset[index]))
                upper.append(np.inf)
            row = np.zeros(variable_count, dtype=np.float64)
            row[smooth_slice.start + index] = 1.0
            rows.append(row)
            lower.append(0.0)
            upper.append(np.inf)
        zone_lines = tuple(
            upper_plan.comfort_lines[step * zones + zone_index] for step in range(horizon)
        )
        _add_comfort_constraints(
            variable_count=variable_count,
            control_slice=slice(0, horizon),
            excess_slice=excess_slice,
            temperature_offset=temperature_offset,
            temperature_response=temperature_response,
            comfort_lines=zone_lines,
            rows=rows,
            lower=lower,
            upper=upper,
        )
        warm = upper_plan.controls[:, zone_index]
        warm_temperature = temperature_offset + temperature_response @ warm
        warm_pmv = np.asarray(
            [
                line.slope * warm_temperature[step] + line.intercept
                for step, line in enumerate(zone_lines)
            ]
        )
        warm_excess = np.asarray(
            [
                max(0.0, abs(value) - COMFORT_BAND) if line.occupied else 0.0
                for value, line in zip(warm_pmv, zone_lines, strict=True)
            ]
        )
        warm_smooth = np.abs(difference @ warm + difference_offset)
        solution, _, _ = _solve_qp(
            quadratic,
            linear,
            rows,
            lower,
            upper,
            np.concatenate((warm, warm_excess, warm_smooth)),
        )
        return solution[:horizon]


class HierarchicalMpcController:
    """Coordinate hourly building plans and 15-minute zone optimization."""

    def __init__(self, model: FittedArxModel, objective: Mapping[str, Any]) -> None:
        self.model = model
        self.coordinator = BuildingCoordinator(model, objective)
        self.zone_optimizer = ZoneMpcOptimizer(model, objective)
        self._hourly_reference: NDArray[np.float64] | None = None

    def decide(
        self,
        *,
        step: int,
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
        warm = np.vstack([[float(enhanced_rbc_warm_start[zone]) for zone in zones]] * horizon)
        previous = np.asarray([previous_setpoints_c[zone] for zone in zones])
        coordinator_updated = step % 4 == 0 or self._hourly_reference is None
        try:
            if coordinator_updated:
                upper_plan = self.coordinator.solve(
                    output_history=output_history,
                    control_history=control_history,
                    disturbances=disturbances,
                    prices=prices,
                    occupancy=occupancy,
                    action_times=action_times,
                    daily_outdoor_means_c=daily_outdoor_means_c,
                    comfort=comfort,
                    previous_setpoints=previous,
                    warm_plan=warm,
                )
                self._hourly_reference = upper_plan.controls.copy()
            else:
                assert self._hourly_reference is not None
                shifted = np.vstack((self._hourly_reference[1:], self._hourly_reference[-1]))
                self._hourly_reference = shifted
                predictions = self.model.rollout_unclipped(
                    output_history, control_history, shifted, disturbances
                )
                lines = _linearized_comfort(
                    warm_predictions=predictions,
                    occupancy=occupancy,
                    action_times=action_times,
                    daily_outdoor_means_c=daily_outdoor_means_c,
                    comfort=comfort,
                )
                upper_plan = _UpperPlan(shifted, predictions, lines)
            offset, response = self.model.affine_rollout(
                output_history, control_history, disturbances
            )
            local = upper_plan.controls.copy()
            for zone_index in range(len(zones)):
                local[:, zone_index] = self.zone_optimizer.solve(
                    zone_index=zone_index,
                    upper_plan=upper_plan,
                    offset=offset,
                    response=response,
                    previous_setpoint=float(previous[zone_index]),
                )
            feedback_used = False
            if not self._combined_plan_is_admissible(local, upper_plan, offset, response):
                local = self._reconcile(local, upper_plan, offset, response)
                feedback_used = True
            predictions = self.model.rollout_unclipped(
                output_history, control_history, local, disturbances
            )
            self._validate_true_comfort(
                predictions,
                occupancy,
                action_times,
                daily_outdoor_means_c,
                comfort,
            )
            if np.any(predictions[:, -1] < -QP_TOLERANCE):
                raise ValueError("MPC final plan predicts negative site power")
        except Exception as error:
            return MpcDecision(
                dict(enhanced_rbc_warm_start),
                {
                    "status": "fallback",
                    "method_degraded": True,
                    "reason": f"hierarchical_mpc_failure:{type(error).__name__}",
                    "history_initialization": "repeat_boundary_state",
                },
            )
        return MpcDecision(
            {zone: float(local[0, index]) for index, zone in enumerate(zones)},
            {
                "status": "optimized",
                "method_degraded": False,
                "history_initialization": "repeat_boundary_state",
                "coordinator_updated": coordinator_updated,
                "feedback_iterations": int(feedback_used),
                "planned_setpoints_c": local.tolist(),
                "predicted_outputs": predictions.tolist(),
                "upper_reference_setpoints_c": upper_plan.controls.tolist(),
                "upper_predicted_site_power_w": upper_plan.predicted_outputs[:, -1].tolist(),
            },
        )

    def _combined_plan_is_admissible(
        self,
        controls: NDArray[np.float64],
        upper_plan: _UpperPlan,
        offset: NDArray[np.float64],
        response: NDArray[np.float64],
    ) -> bool:
        layout = self.model.layout
        output_dimension = layout.output_dimension
        flattened = controls.reshape(-1)
        upper_flattened = upper_plan.controls.reshape(-1)
        power_rows = [
            step * output_dimension + layout.control_dimension
            for step in range(layout.horizon_steps)
        ]
        combined_power = offset[power_rows] + response[power_rows] @ flattened
        upper_power = offset[power_rows] + response[power_rows] @ upper_flattened
        if np.any(combined_power > upper_power + QP_TOLERANCE):
            return False
        temperature_rows = [
            step * output_dimension + zone
            for step in range(layout.horizon_steps)
            for zone in range(layout.control_dimension)
        ]
        temperatures = offset[temperature_rows] + response[temperature_rows] @ flattened
        return all(
            not line.occupied
            or abs(line.slope * temperature + line.intercept) <= PMV_LIMIT + QP_TOLERANCE
            for temperature, line in zip(temperatures, upper_plan.comfort_lines, strict=True)
        )

    def _reconcile(
        self,
        local: NDArray[np.float64],
        upper_plan: _UpperPlan,
        offset: NDArray[np.float64],
        response: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        layout = self.model.layout
        variable_count = local.size
        quadratic = np.eye(variable_count, dtype=np.float64) * 2.0
        linear = -2.0 * local.reshape(-1)
        rows = [np.eye(variable_count, dtype=np.float64)[index] for index in range(variable_count)]
        lower = [20.0] * variable_count
        upper = [30.0] * variable_count
        output_dimension = layout.output_dimension
        power_rows = [
            step * output_dimension + layout.control_dimension
            for step in range(layout.horizon_steps)
        ]
        upper_flattened = upper_plan.controls.reshape(-1)
        upper_power = offset[power_rows] + response[power_rows] @ upper_flattened
        for step, row_index in enumerate(power_rows):
            rows.append(response[row_index].copy())
            lower.append(-float(offset[row_index]))
            upper.append(float(upper_power[step] - offset[row_index]))
        temperature_rows = [
            step * output_dimension + zone
            for step in range(layout.horizon_steps)
            for zone in range(layout.control_dimension)
        ]
        for row_index, line in zip(temperature_rows, upper_plan.comfort_lines, strict=True):
            if line.occupied:
                pmv_response = line.slope * response[row_index]
                pmv_offset = line.slope * offset[row_index] + line.intercept
                rows.append(pmv_response)
                lower.append(-PMV_LIMIT - pmv_offset)
                upper.append(PMV_LIMIT - pmv_offset)
        solution, _, _ = _solve_qp(
            quadratic,
            linear,
            rows,
            lower,
            upper,
            upper_plan.controls.reshape(-1),
        )
        return solution.reshape(layout.horizon_steps, layout.control_dimension)

    @staticmethod
    def _validate_true_comfort(
        predictions: NDArray[np.float64],
        occupancy: NDArray[np.float64],
        action_times: Sequence[int],
        daily_outdoor_means_c: Sequence[float],
        comfort: ComfortModel,
    ) -> None:
        predicted_comfort = copy.deepcopy(comfort)
        for step in range(len(predictions)):
            predicted_comfort.update_clothing(
                float(action_times[step]), float(daily_outdoor_means_c[step])
            )
            for zone in range(occupancy.shape[1]):
                if (
                    float(occupancy[step, zone]) > 0
                    and abs(predicted_comfort.pmv(float(predictions[step, zone]))) > PMV_LIMIT
                ):
                    raise ValueError("MPC true PMV validation failed")
