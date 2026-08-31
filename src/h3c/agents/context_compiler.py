"""Lossless typed-context compiler for compact Agent and expanded audit views."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias, cast

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
SectionKind = Literal["json", "common_rows", "working_memory", "control_specification"]

_STEP_ARRAY_PATHS = {
    "/action/actual_setpoints_c": "actual_setpoint_c",
    "/action/matched_rules": "matched_rule",
    "/outcome/zone_temperatures_c": "zone_temperature_c",
    "/outcome/pmv": "pmv",
    "/outcome/effective_occupancy": "effective_occupancy",
}
_DERIVED_OUTCOME_FIELDS = (
    "discomfort_zone_hours",
    "discomfort_pmv_hours",
    "occupied_peak_absolute_pmv",
    "setpoint_total_variation_c",
    "setpoint_direction_reversals",
)


def _normalize(value: Any) -> JsonValue:
    """Normalize mappings while omitting unavailable values and preserving empty collections."""
    if isinstance(value, Mapping):
        normalized: dict[str, JsonValue] = {}
        for raw_key, raw_item in value.items():
            if raw_item is None:
                continue
            normalized[str(raw_key)] = _normalize(raw_item)
        return normalized
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"context value is not JSON-compatible: {type(value).__name__}")


def normalized_context(value: Any) -> JsonValue:
    """Return the exact canonical representation used by the compiler."""
    return copy.deepcopy(_normalize(value))


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _pointer_unescape(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _pointer(parts: Sequence[str]) -> str:
    return "/" + "/".join(_pointer_escape(part) for part in parts)


def _parts(pointer: str) -> tuple[str, ...]:
    if not pointer.startswith("/"):
        raise ValueError(f"invalid field pointer: {pointer}")
    return tuple(_pointer_unescape(part) for part in pointer[1:].split("/"))


def _flatten(value: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    leaves: dict[str, JsonValue] = {}

    def visit(item: JsonValue, path: tuple[str, ...]) -> None:
        if isinstance(item, dict) and item:
            for key, child in item.items():
                visit(child, (*path, key))
            return
        leaves[_pointer(path)] = copy.deepcopy(item)

    for key, child in value.items():
        visit(child, (key,))
    return leaves


def _put(root: dict[str, JsonValue], pointer: str, value: JsonValue) -> None:
    parts = _parts(pointer)
    if not parts:
        raise ValueError("root field cannot be assigned by pointer")
    cursor = root
    for part in parts[:-1]:
        current = cursor.get(part)
        if current is None:
            child: dict[str, JsonValue] = {}
            cursor[part] = child
            cursor = child
        elif isinstance(current, dict):
            cursor = current
        else:
            raise ValueError(f"field owner conflict at {pointer}")
    leaf = parts[-1]
    if leaf in cursor and cursor[leaf] != value:
        raise ValueError(f"field owner conflict at {pointer}")
    cursor[leaf] = copy.deepcopy(value)


def _nested(leaves: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for pointer, value in leaves.items():
        _put(result, pointer, value)
    return result


def _is_scalar(value: JsonValue) -> bool:
    return not isinstance(value, (dict, list))


def factor_common_rows(
    records: Sequence[Mapping[str, Any]], *, identity_fields: Sequence[str]
) -> dict[str, JsonValue]:
    """Factor structurally identical paths while keeping row cells scalar-only."""
    normalized = cast(list[dict[str, JsonValue]], _normalize(list(records)))
    if not normalized:
        return {
            "kind": "common_rows",
            "identity_fields": list(identity_fields),
            "common": {},
            "columns": [],
            "rows": [],
            "details": [],
        }
    identities = set(identity_fields)
    if not identities:
        raise ValueError("common+rows requires at least one identity field")
    flattened = [_flatten(record) for record in normalized]
    identity_pointers = {_pointer((field,)) for field in identity_fields}
    for index, leaves in enumerate(flattened):
        missing = identity_pointers - set(leaves)
        if missing:
            raise ValueError(f"row {index} lacks identity fields: {sorted(missing)}")
        if any(not _is_scalar(leaves[pointer]) for pointer in identity_pointers):
            raise ValueError("identity fields must be scalar")

    first_paths = list(flattened[0])
    common_paths = [
        path
        for path in first_paths
        if path not in identity_pointers
        and all(path in row and row[path] == flattened[0][path] for row in flattened[1:])
    ]
    common_set = set(common_paths)
    row_columns: list[str] = []
    for flattened_row in flattened:
        for path, value in flattened_row.items():
            if path in identity_pointers or path in common_set or not _is_scalar(value):
                continue
            if path not in row_columns:
                row_columns.append(path)

    compact_rows: list[JsonValue] = []
    details: list[JsonValue] = []
    for leaves in flattened:
        compact_row: dict[str, JsonValue] = {
            field: copy.deepcopy(leaves[_pointer((field,))]) for field in identity_fields
        }
        values: dict[str, JsonValue] = {}
        nested_values: dict[str, JsonValue] = {}
        for path, value in leaves.items():
            if path in identity_pointers or path in common_set:
                continue
            if _is_scalar(value):
                values[path] = copy.deepcopy(value)
            else:
                nested_values[path] = copy.deepcopy(value)
        compact_row["values"] = values
        compact_rows.append(compact_row)
        if nested_values:
            detail: dict[str, JsonValue] = {
                field: copy.deepcopy(leaves[_pointer((field,))]) for field in identity_fields
            }
            detail["values"] = _nested(nested_values)
            details.append(detail)

    view: dict[str, JsonValue] = {
        "kind": "common_rows",
        "identity_fields": cast(JsonValue, list(identity_fields)),
        "common": _nested({path: flattened[0][path] for path in common_paths}),
        "columns": cast(JsonValue, row_columns),
        "rows": compact_rows,
        "details": details,
    }
    if decode_common_rows(view) != normalized:
        raise ValueError("common+rows round-trip failed")
    return view


def decode_common_rows(view: Mapping[str, Any]) -> list[dict[str, JsonValue]]:
    """Recover normalized records from a common+rows compact view."""
    identity_fields = [str(field) for field in view["identity_fields"]]
    common = cast(dict[str, JsonValue], _normalize(view["common"]))
    details_index: dict[tuple[JsonScalar, ...], dict[str, JsonValue]] = {}
    for raw_detail in cast(Sequence[Mapping[str, Any]], view["details"]):
        key = tuple(cast(JsonScalar, raw_detail[field]) for field in identity_fields)
        if key in details_index:
            raise ValueError("duplicate details identity")
        details_index[key] = cast(dict[str, JsonValue], _normalize(raw_detail["values"]))

    decoded: list[dict[str, JsonValue]] = []
    for raw_row in cast(Sequence[Mapping[str, Any]], view["rows"]):
        record = copy.deepcopy(common)
        identity = tuple(cast(JsonScalar, raw_row[field]) for field in identity_fields)
        for field, value in zip(identity_fields, identity, strict=True):
            _put(record, _pointer((field,)), value)
        values = cast(Mapping[str, Any], raw_row["values"])
        for path, value in values.items():
            _put(record, str(path), _normalize(value))
        detail = details_index.pop(identity, None)
        if detail is not None:
            for path, detail_value in _flatten(detail).items():
                _put(record, path, detail_value)
        decoded.append(record)
    if details_index:
        raise ValueError("details row has no matching scalar row")
    return decoded


def _pop_path(record: dict[str, JsonValue], pointer: str) -> JsonValue | None:
    parts = _parts(pointer)
    cursor: dict[str, JsonValue] = record
    for part in parts[:-1]:
        child = cursor.get(part)
        if not isinstance(child, dict):
            return None
        cursor = child
    value = cursor.pop(parts[-1], None)
    for depth in range(len(parts) - 1, 0, -1):
        parent = record
        for part in parts[: depth - 1]:
            child = parent[part]
            if not isinstance(child, dict):
                raise ValueError("invalid nested context")
            parent = child
        child = parent.get(parts[depth - 1])
        if isinstance(child, dict) and not child:
            parent.pop(parts[depth - 1])
    return value


def compile_working_memory(records: Sequence[Mapping[str, Any]]) -> dict[str, JsonValue]:
    """Compile completed records into time, state, action, and derived-feature layers."""
    canonical = cast(list[dict[str, JsonValue]], _normalize(list(records)))
    grouped: dict[int, list[dict[str, JsonValue]]] = {}
    for record in canonical:
        hour = record.get("hour")
        zone = record.get("zone")
        if not isinstance(hour, int) or isinstance(hour, bool) or not isinstance(zone, str):
            raise ValueError("working-memory records require integer hour and string zone")
        grouped.setdefault(hour, []).append(copy.deepcopy(record))

    hours: list[JsonValue] = []
    for hour, hour_records in grouped.items():
        base_records: list[dict[str, JsonValue]] = []
        state_history_rows: list[dict[str, JsonValue]] = []
        action_history_rows: list[dict[str, JsonValue]] = []
        current_state_rows: list[dict[str, JsonValue]] = []
        derived_feature_rows: list[dict[str, JsonValue]] = []
        forecast_rows: list[JsonValue] = []
        site_result: dict[str, JsonValue] | None = None
        for record in hour_records:
            zone = cast(str, record["zone"])
            base = copy.deepcopy(record)
            arrays: dict[str, list[JsonValue]] = {}
            for path, column in _STEP_ARRAY_PATHS.items():
                value = _pop_path(base, path)
                if not isinstance(value, list) or len(value) != 4:
                    raise ValueError(f"working-memory field {path} must contain four steps")
                arrays[column] = value
            shield_raw = _pop_path(base, "/action/shield")
            if not isinstance(shield_raw, list) or len(shield_raw) != 4:
                raise ValueError("working-memory shield must contain four steps")
            regime_raw = _pop_path(base, "/context/regime_step_coverage")
            if not isinstance(regime_raw, dict):
                raise ValueError("working-memory regime coverage is missing")
            regimes_by_step: dict[int, str] = {}
            for regime, covered_steps in regime_raw.items():
                if not isinstance(covered_steps, list):
                    raise ValueError("regime coverage must be a step list")
                for covered_step in covered_steps:
                    step_number = int(cast(int | float, covered_step))
                    if step_number in regimes_by_step:
                        raise ValueError("a physical step has more than one regime owner")
                    regimes_by_step[step_number] = regime
            initial_raw = _pop_path(base, "/context/initial_observation")
            if not isinstance(initial_raw, dict):
                raise ValueError("working-memory initial observation is missing")
            initial = copy.deepcopy(initial_raw)
            forecast_raw = initial.pop("occupancy_next_steps", None)
            if not isinstance(forecast_raw, list) or len(forecast_raw) != 4:
                raise ValueError("working-memory occupancy forecast must contain four steps")
            for step_ahead, occupancy in enumerate(forecast_raw, start=1):
                forecast_rows.append(
                    {"zone": zone, "step_ahead": step_ahead, "occupancy": occupancy}
                )

            required_initial = {
                "zone_temperature_c",
                "current_occupancy",
                "last_occupancy",
                "last_pmv",
                "last_setpoint_c",
            }
            if not required_initial <= set(initial):
                raise ValueError("working-memory initial state is incomplete")
            initial_temperature = float(cast(int | float, initial.pop("zone_temperature_c")))
            initial_occupancy = initial.pop("current_occupancy")
            initial_pmv = float(cast(int | float, initial.pop("last_pmv")))
            initial_setpoint = float(cast(int | float, initial.pop("last_setpoint_c")))
            if initial:
                _put(base, "/context/initial_observation", initial)

            current_site = {
                "site_cost": _pop_path(base, "/outcome/site_cost"),
                "site_energy_kwh": _pop_path(base, "/outcome/site_energy_kwh"),
            }
            if any(value is None for value in current_site.values()):
                raise ValueError("working-memory site result is incomplete")
            if site_result is None:
                site_result = current_site
            elif site_result != current_site:
                raise ValueError("repeated site-result owners disagree across zones")

            first_step = cast(dict[str, JsonValue], shield_raw[0]).get("step")
            if not isinstance(first_step, int) or isinstance(first_step, bool):
                raise ValueError("working-memory first physical step is invalid")
            state_history_rows.append(
                {
                    "zone": zone,
                    "sample_index": 0,
                    "physical_step": first_step - 1,
                    "state_time": "hour_start_before_first_action",
                    "zone_temperature_c": initial_temperature,
                    "pmv": initial_pmv,
                    "effective_occupancy": initial_occupancy,
                    "setpoint_c": initial_setpoint,
                }
            )
            for index, raw_shield in enumerate(shield_raw):
                if not isinstance(raw_shield, dict):
                    raise ValueError("working-memory shield row must be an object")
                step = raw_shield.get("step")
                if not isinstance(step, int) or isinstance(step, bool):
                    raise ValueError("working-memory shield step must be an integer")
                if step not in regimes_by_step:
                    raise ValueError("regime coverage does not own every physical step")
                state_row: dict[str, JsonValue] = {
                    "zone": zone,
                    "sample_index": index + 1,
                    "physical_step": step,
                    "state_time": "outcome_after_applied_step",
                    "zone_temperature_c": arrays["zone_temperature_c"][index],
                    "pmv": arrays["pmv"][index],
                    "effective_occupancy": arrays["effective_occupancy"][index],
                    "setpoint_c": arrays["actual_setpoint_c"][index],
                }
                action_row: dict[str, JsonValue] = {
                    "zone": zone,
                    "physical_step": step,
                    "regime": regimes_by_step[step],
                    "actual_setpoint_c": arrays["actual_setpoint_c"][index],
                    "matched_rule": arrays["matched_rule"][index],
                    "actuator_bounds": raw_shield.get("actuator_bounds"),
                    "setpoint_rate_limit": raw_shield.get("setpoint_rate_limit"),
                    "comfort_recovery": raw_shield.get("comfort_recovery"),
                }
                if any(value is None for value in (*state_row.values(), *action_row.values())):
                    raise ValueError("working-memory history row is incomplete")
                state_history_rows.append(state_row)
                action_history_rows.append(action_row)

            final_state = state_history_rows[-1]
            current_state_rows.append(
                {
                    "zone": zone,
                    "last_completed_step": final_state["physical_step"],
                    "zone_temperature_c": final_state["zone_temperature_c"],
                    "pmv": final_state["pmv"],
                    "effective_occupancy": final_state["effective_occupancy"],
                    "setpoint_c": final_state["setpoint_c"],
                }
            )
            source_metrics: dict[str, JsonValue] = {}
            for name in _DERIVED_OUTCOME_FIELDS:
                value = _pop_path(base, f"/outcome/{name}")
                if value is None:
                    raise ValueError(f"working-memory derived metric {name} is missing")
                source_metrics[name] = value
            temperatures = [
                float(cast(int | float, row["zone_temperature_c"]))
                for row in state_history_rows[-5:]
            ]
            pmv_values = [float(cast(int | float, row["pmv"])) for row in state_history_rows[-5:]]
            setpoints = [
                float(cast(int | float, row["setpoint_c"])) for row in state_history_rows[-5:]
            ]
            derived_feature_rows.append(
                {
                    "zone": zone,
                    "zone_temperature_change_last_step_c": round(
                        temperatures[-1] - temperatures[-2], 6
                    ),
                    "zone_temperature_change_hour_c": round(temperatures[-1] - temperatures[0], 6),
                    "zone_temperature_slope_c_per_hour": round(
                        temperatures[-1] - temperatures[0], 6
                    ),
                    "pmv_change_last_step": round(pmv_values[-1] - pmv_values[-2], 6),
                    "pmv_change_hour": round(pmv_values[-1] - pmv_values[0], 6),
                    "setpoint_change_last_step_c": round(setpoints[-1] - setpoints[-2], 6),
                    "setpoint_change_hour_c": round(setpoints[-1] - setpoints[0], 6),
                    **source_metrics,
                }
            )
            base_records.append(base)
        hours.append(
            {
                "hour": hour,
                "time_semantics": {
                    "agent_decision_interval_minutes": 60,
                    "physical_step_interval_minutes": 15,
                    "current_state": "last completed outcome",
                    "state_history": (
                        "hour-start state followed by four post-action physical outcomes"
                    ),
                    "action_history": "setpoint and assurance applied before each outcome",
                },
                "site_result": site_result or {},
                "hourly_decision": factor_common_rows(base_records, identity_fields=("zone",)),
                "current_state": factor_common_rows(current_state_rows, identity_fields=("zone",)),
                "recent_state_history": factor_common_rows(
                    state_history_rows, identity_fields=("zone", "sample_index")
                ),
                "action_history": factor_common_rows(
                    action_history_rows, identity_fields=("zone", "physical_step")
                ),
                "occupancy_forecast": factor_common_rows(
                    cast(Sequence[Mapping[str, Any]], forecast_rows),
                    identity_fields=("zone", "step_ahead"),
                ),
                "derived_features": factor_common_rows(
                    derived_feature_rows, identity_fields=("zone",)
                ),
            }
        )
    view: dict[str, JsonValue] = {"kind": "working_memory", "hours": hours}
    if decode_working_memory(view) != canonical:
        raise ValueError("working-memory round-trip failed")
    return view


def decode_working_memory(view: Mapping[str, Any]) -> list[dict[str, JsonValue]]:
    """Recover normalized completed-hour records from a compact working-memory view."""
    decoded: list[dict[str, JsonValue]] = []
    for raw_hour in cast(Sequence[Mapping[str, Any]], view["hours"]):
        hour = int(raw_hour["hour"])
        records = decode_common_rows(cast(Mapping[str, Any], raw_hour["hourly_decision"]))
        forecast_index: dict[str, list[Mapping[str, Any]]] = {}
        forecast_rows = decode_common_rows(cast(Mapping[str, Any], raw_hour["occupancy_forecast"]))
        for row in forecast_rows:
            forecast_index.setdefault(str(row["zone"]), []).append(row)
        state_index: dict[str, list[Mapping[str, Any]]] = {}
        for row in decode_common_rows(cast(Mapping[str, Any], raw_hour["recent_state_history"])):
            state_index.setdefault(str(row["zone"]), []).append(row)
        action_index: dict[str, list[Mapping[str, Any]]] = {}
        for row in decode_common_rows(cast(Mapping[str, Any], raw_hour["action_history"])):
            action_index.setdefault(str(row["zone"]), []).append(row)
        derived_index = {
            str(row["zone"]): row
            for row in decode_common_rows(cast(Mapping[str, Any], raw_hour["derived_features"]))
        }
        site_result = cast(Mapping[str, JsonValue], raw_hour["site_result"])
        for record in records:
            zone = str(record["zone"])
            forecast = sorted(forecast_index.pop(zone), key=lambda row: int(row["step_ahead"]))
            states = sorted(state_index.pop(zone), key=lambda row: int(row["sample_index"]))
            actions = sorted(action_index.pop(zone), key=lambda row: int(row["physical_step"]))
            derived = derived_index.pop(zone)
            if len(forecast) != 4 or len(states) != 5 or len(actions) != 4:
                raise ValueError("working-memory compact view lost a four-step sequence")
            _put(
                record,
                "/context/initial_observation/occupancy_next_steps",
                [cast(JsonValue, row["occupancy"]) for row in forecast],
            )
            initial = states[0]
            _put(
                record,
                "/context/initial_observation/zone_temperature_c",
                cast(JsonValue, initial["zone_temperature_c"]),
            )
            _put(
                record,
                "/context/initial_observation/current_occupancy",
                cast(JsonValue, initial["effective_occupancy"]),
            )
            _put(
                record,
                "/context/initial_observation/last_pmv",
                cast(JsonValue, initial["pmv"]),
            )
            _put(
                record,
                "/context/initial_observation/last_setpoint_c",
                cast(JsonValue, initial["setpoint_c"]),
            )
            coverage: dict[str, JsonValue] = {}
            for decoded_action in actions:
                regime = str(decoded_action["regime"])
                physical_step = decoded_action["physical_step"]
                if not isinstance(physical_step, int) or isinstance(physical_step, bool):
                    raise ValueError("action-history physical step is invalid")
                cast(list[JsonValue], coverage.setdefault(regime, [])).append(physical_step)
            _put(record, "/context/regime_step_coverage", coverage)
            _put(
                record,
                "/action/actual_setpoints_c",
                [cast(JsonValue, row["actual_setpoint_c"]) for row in actions],
            )
            _put(
                record,
                "/action/matched_rules",
                [cast(JsonValue, row["matched_rule"]) for row in actions],
            )
            _put(
                record,
                "/outcome/zone_temperatures_c",
                [cast(JsonValue, row["zone_temperature_c"]) for row in states[1:]],
            )
            _put(record, "/outcome/pmv", [cast(JsonValue, row["pmv"]) for row in states[1:]])
            _put(
                record,
                "/outcome/effective_occupancy",
                [cast(JsonValue, row["effective_occupancy"]) for row in states[1:]],
            )
            _put(
                record,
                "/action/shield",
                [
                    {
                        "step": int(row["physical_step"]),
                        "actuator_bounds": row["actuator_bounds"],
                        "setpoint_rate_limit": row["setpoint_rate_limit"],
                        "comfort_recovery": row["comfort_recovery"],
                    }
                    for row in actions
                ],
            )
            for name in _DERIVED_OUTCOME_FIELDS:
                _put(record, f"/outcome/{name}", derived[name])
            _put(record, "/outcome/site_cost", site_result["site_cost"])
            _put(record, "/outcome/site_energy_kwh", site_result["site_energy_kwh"])
            decoded.append(record)
        if forecast_index or state_index or action_index or derived_index:
            raise ValueError("working-memory step rows have no matching zone record")
        record_hours = [record["hour"] for record in records]
        if any(
            not isinstance(record_hour, int) or isinstance(record_hour, bool) or record_hour != hour
            for record_hour in record_hours
        ):
            raise ValueError("working-memory hour owner conflict")
    return decoded


def _cell(value: JsonValue) -> str:
    if not _is_scalar(value):
        raise ValueError("table cells must be scalar")
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("|", "\\u007c")


def _table(rows: Sequence[Mapping[str, JsonValue]], columns: Sequence[str]) -> str:
    if not rows:
        return ""
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(_cell(row.get(column)) for column in columns) + " |" for row in rows]
    return "\n".join((header, separator, *body))


_DISPLAY_FIELD_ALIASES = {
    "sample_index": "sample",
    "physical_step": "step",
    "effective_occupancy": "occupancy",
    "actual_setpoint_c": "setpoint_c",
    "zone_temperature_c": "temp_c",
    "zone_temperature_change_last_step_c": "temp_delta_15min_c",
    "zone_temperature_change_hour_c": "temp_delta_1h_c",
    "zone_temperature_slope_c_per_hour": "temp_slope_c_per_hour",
    "pmv_change_last_step": "pmv_delta_15min",
    "pmv_change_hour": "pmv_delta_1h",
    "setpoint_change_last_step_c": "setpoint_delta_15min_c",
    "setpoint_change_hour_c": "setpoint_delta_1h_c",
    "discomfort_zone_hours": "discomfort_zone_h",
    "discomfort_pmv_hours": "discomfort_pmv_h",
    "occupied_peak_absolute_pmv": "occupied_peak_abs_pmv",
    "setpoint_total_variation_c": "setpoint_tv_c",
    "setpoint_direction_reversals": "setpoint_reversals",
}


def _short_column_names(paths: Sequence[str], *, reserved: Sequence[str] = ()) -> list[str]:
    """Choose the shortest unambiguous, self-describing suffix for model-facing tables."""
    split = [_parts(path) for path in paths]
    chosen: list[str] = []
    reserved_set = set(reserved)
    for index, parts in enumerate(split):
        candidate = parts[-1]
        depth = 1
        while (
            candidate in reserved_set
            or candidate in chosen
            or any(
                other_index != index and ".".join(other[-depth:]) == candidate
                for other_index, other in enumerate(split)
            )
        ):
            depth += 1
            if depth > len(parts):
                candidate = "/".join(parts)
                break
            candidate = ".".join(parts[-depth:])
        chosen.append(_DISPLAY_FIELD_ALIASES.get(candidate, candidate))
    if len(set(chosen)) != len(chosen):
        raise ValueError("model-facing field aliases are ambiguous")
    return chosen


def render_common_rows(view: Mapping[str, Any]) -> str:
    """Render explicit common data, scalar rows, and separately typed nested details."""
    identities = [str(value) for value in view["identity_fields"]]
    paths = [str(value) for value in view["columns"]]
    common = cast(Mapping[str, JsonValue], view["common"])
    display_paths = _short_column_names(paths, reserved=identities)
    rows: list[dict[str, JsonValue]] = []
    row_by_identity: dict[tuple[JsonScalar, ...], dict[str, JsonValue]] = {}
    for raw_row in cast(Sequence[Mapping[str, Any]], view["rows"]):
        values = cast(Mapping[str, JsonValue], raw_row["values"])
        row = {field: cast(JsonValue, raw_row[field]) for field in identities}
        row.update(
            {
                display: values[path]
                for path, display in zip(paths, display_paths, strict=True)
                if path in values
            }
        )
        rows.append(row)
        row_by_identity[tuple(cast(JsonScalar, raw_row[field]) for field in identities)] = row
    remaining_details: list[JsonValue] = []
    for raw_detail in cast(Sequence[Mapping[str, Any]], view["details"]):
        detail_values = cast(Mapping[str, JsonValue], raw_detail["values"])
        expandable = bool(detail_values) and all(
            isinstance(value, list) and value and all(_is_scalar(item) for item in value)
            for value in detail_values.values()
        )
        identity = tuple(cast(JsonScalar, raw_detail[field]) for field in identities)
        target = row_by_identity.get(identity)
        if expandable and target is not None:
            for field, raw_values in detail_values.items():
                detail_items = cast(list[JsonValue], raw_values)
                for index, value in enumerate(detail_items, start=1):
                    target[f"{field}_{index}"] = value
        else:
            remaining_details.append(cast(JsonValue, copy.deepcopy(dict(raw_detail))))
    parts: list[str] = []
    if common:
        rendered_common: Mapping[str, JsonValue] = common
        if all(not isinstance(value, (dict, list)) for value in common.values()):
            rendered_common = {
                _DISPLAY_FIELD_ALIASES.get(field, field): value for field, value in common.items()
            }
        parts.append(
            "common:\n```json\n"
            + json.dumps(rendered_common, ensure_ascii=False, separators=(",", ":"))
            + "\n```"
        )
    grouped_rows: dict[tuple[str, ...], list[dict[str, JsonValue]]] = {}
    for row in rows:
        columns = tuple(row)
        grouped_rows.setdefault(columns, []).append(row)
    row_tables = [_table(group, columns) for columns, group in grouped_rows.items()]
    if row_tables:
        parts.append("rows:\n" + "\n".join(row_tables))
    if remaining_details:
        parts.append(
            "details:\n```json\n"
            + json.dumps(remaining_details, ensure_ascii=False, separators=(",", ":"))
            + "\n```"
        )
    return "\n".join(parts)


def _assert_group_value(rows: Sequence[Mapping[str, JsonValue]], field: str) -> JsonValue:
    values = [row[field] for row in rows]
    if not values or any(value != values[0] for value in values[1:]):
        raise ValueError(f"working-memory shared axis disagrees for {field}")
    return values[0]


def _direct_common(view: Mapping[str, Any]) -> dict[str, JsonValue]:
    common = cast(Mapping[str, JsonValue], view["common"])
    if any(isinstance(value, (dict, list)) for value in common.values()):
        raise ValueError("working-memory layer common fields must be direct scalars")
    return {
        _DISPLAY_FIELD_ALIASES.get(field, field): copy.deepcopy(value)
        for field, value in common.items()
    }


def _zone_constant_partition(
    records: Sequence[Mapping[str, JsonValue]],
    *,
    zones: Sequence[str],
    fields: Sequence[str],
    axis_field: str,
) -> tuple[list[dict[str, JsonValue]], list[str], list[dict[str, JsonValue]]]:
    """Extract per-zone constants and leave only time-varying values in axis rows."""
    constant_rows: list[dict[str, JsonValue]] = []
    variable_pairs: list[tuple[str, str]] = []
    for zone in zones:
        zone_records = [record for record in records if str(record["zone"]) == zone]
        constant_row: dict[str, JsonValue] = {"zone": zone}
        for field in fields:
            values = [record[field] for record in zone_records]
            if values and all(value == values[0] for value in values[1:]):
                constant_row[_DISPLAY_FIELD_ALIASES.get(field, field)] = values[0]
            else:
                variable_pairs.append((zone, field))
        if len(constant_row) > 1:
            constant_rows.append(constant_row)

    grouped: dict[int, list[Mapping[str, JsonValue]]] = {}
    for record in records:
        grouped.setdefault(cast(int, record[axis_field]), []).append(record)
    variable_rows: list[dict[str, JsonValue]] = []
    for axis_value, axis_records in grouped.items():
        row: dict[str, JsonValue] = {_DISPLAY_FIELD_ALIASES.get(axis_field, axis_field): axis_value}
        by_zone = {str(record["zone"]): record for record in axis_records}
        if set(by_zone) != set(zones):
            raise ValueError("working-memory time axis has an incomplete zone axis")
        for zone, field in variable_pairs:
            display_field = _DISPLAY_FIELD_ALIASES.get(field, field)
            row[f"{zone}.{display_field}"] = by_zone[zone][field]
        variable_rows.append(row)
    variable_columns = [
        _DISPLAY_FIELD_ALIASES.get(axis_field, axis_field),
        *(f"{zone}.{_DISPLAY_FIELD_ALIASES.get(field, field)}" for zone, field in variable_pairs),
    ]
    return constant_rows, variable_columns, variable_rows


def _render_history(view: Mapping[str, Any]) -> str:
    records = decode_common_rows(view)
    grouped: dict[int, list[dict[str, JsonValue]]] = {}
    for record in records:
        grouped.setdefault(cast(int, record["sample_index"]), []).append(record)
    zones = list(dict.fromkeys(str(record["zone"]) for record in records))
    common = _direct_common(view)
    source_fields = (
        "zone_temperature_c",
        "pmv",
        "effective_occupancy",
        "setpoint_c",
    )
    variable_fields = tuple(
        field for field in source_fields if _DISPLAY_FIELD_ALIASES.get(field, field) not in common
    )
    constants, variable_columns, variable_rows = _zone_constant_partition(
        records,
        zones=zones,
        fields=variable_fields,
        axis_field="sample_index",
    )
    axis_rows: list[dict[str, JsonValue]] = []
    for sample, sample_records in grouped.items():
        axis_rows.append(
            {
                "sample": sample,
                "step": _assert_group_value(sample_records, "physical_step"),
            }
        )
    parts = []
    if common:
        parts.append("common: " + json.dumps(common, ensure_ascii=False, separators=(",", ":")))
    parts.append("time_axis:\n" + _table(axis_rows, ("sample", "step")))
    if constants:
        parts.append(
            "constant_by_zone:\n"
            + "\n".join(
                json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in constants
            )
        )
    if len(variable_columns) > 1:
        parts.append("time_varying_measurements:\n" + _table(variable_rows, variable_columns))
    return "\n".join(parts)


def _render_action_history(view: Mapping[str, Any]) -> str:
    records = decode_common_rows(view)
    grouped: dict[int, list[dict[str, JsonValue]]] = {}
    for record in records:
        grouped.setdefault(cast(int, record["physical_step"]), []).append(record)
    zones = list(dict.fromkeys(str(record["zone"]) for record in records))
    common = _direct_common(view)
    source_fields = (
        "regime",
        "actual_setpoint_c",
        "matched_rule",
        "actuator_bounds",
        "setpoint_rate_limit",
        "comfort_recovery",
    )
    variable_fields = tuple(
        field for field in source_fields if _DISPLAY_FIELD_ALIASES.get(field, field) not in common
    )
    constants, variable_columns, variable_rows = _zone_constant_partition(
        records,
        zones=zones,
        fields=variable_fields,
        axis_field="physical_step",
    )
    parts = []
    if common:
        parts.append("common: " + json.dumps(common, ensure_ascii=False, separators=(",", ":")))
    if constants:
        parts.append(
            "constant_by_zone:\n"
            + "\n".join(
                json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in constants
            )
        )
    if len(variable_columns) > 1:
        parts.append("time_varying_actions:\n" + _table(variable_rows, variable_columns))
    else:
        parts.append(
            "steps: " + json.dumps(list(grouped), ensure_ascii=False, separators=(",", ":"))
        )
    return "\n".join(parts)


def _render_occupancy_forecast(view: Mapping[str, Any]) -> str:
    records = decode_common_rows(view)
    grouped: dict[int, list[dict[str, JsonValue]]] = {}
    for record in records:
        grouped.setdefault(cast(int, record["step_ahead"]), []).append(record)
    zones = list(dict.fromkeys(str(record["zone"]) for record in records))
    common = _direct_common(view)
    if "occupancy" in common:
        return (
            "common: "
            + json.dumps(common, ensure_ascii=False, separators=(",", ":"))
            + "\nzones: "
            + json.dumps(zones, ensure_ascii=False, separators=(",", ":"))
            + "\nsteps_ahead: "
            + json.dumps(list(grouped), ensure_ascii=False, separators=(",", ":"))
        )
    rows: list[dict[str, JsonValue]] = []
    for step_ahead, step_records in grouped.items():
        by_zone = {str(record["zone"]): record for record in step_records}
        if set(by_zone) != set(zones):
            raise ValueError("working-memory occupancy forecast has an incomplete zone axis")
        row: dict[str, JsonValue] = {"step_ahead": step_ahead}
        row.update({zone: by_zone[zone]["occupancy"] for zone in zones})
        rows.append(row)
    return _table(rows, ["step_ahead", *zones])


def _render_scoped_common_rows(view: Mapping[str, Any], *, omit_common: Sequence[str] = ()) -> str:
    display_view = copy.deepcopy(dict(view))
    common = cast(dict[str, JsonValue], display_view["common"])
    for field in omit_common:
        common.pop(field, None)
    rows = cast(Sequence[Mapping[str, Any]], display_view["rows"])
    details = cast(Sequence[JsonValue], display_view["details"])
    if rows and not details and all(not cast(Mapping[str, Any], row["values"]) for row in rows):
        if common:
            rendered_common: Mapping[str, JsonValue] = common
            if all(not isinstance(value, (dict, list)) for value in common.values()):
                rendered_common = {
                    _DISPLAY_FIELD_ALIASES.get(field, field): value
                    for field, value in common.items()
                }
            return "common: " + json.dumps(
                rendered_common, ensure_ascii=False, separators=(",", ":")
            )
        return ""
    return render_common_rows(display_view)


def _working_decision_agent_view(
    records: Sequence[Mapping[str, JsonValue]],
) -> dict[str, JsonValue]:
    """Project audit-only proof detail out of the next decision's model-facing history."""
    projected: list[dict[str, JsonValue]] = []
    audit_only_paths = (
        "/action/admission/completed_validation_stages",
        "/action/proposal/causal_edge_ids",
        "/action/proposal/expected_effects",
        "/action/proposal/consistent_program_direction_proof",
    )
    for source in records:
        record = copy.deepcopy(dict(source))
        for path in audit_only_paths:
            _pop_path(record, path)
        projected.append(record)
    return factor_common_rows(projected, identity_fields=("zone",))


def render_working_memory(view: Mapping[str, Any]) -> str:
    """Render explicit time semantics, current state, history, actions, and features."""
    parts: list[str] = []
    for raw_hour in cast(Sequence[Mapping[str, Any]], view["hours"]):
        parts.append(f"hour: {int(raw_hour['hour'])}")
        decision_records = decode_common_rows(cast(Mapping[str, Any], raw_hour["hourly_decision"]))
        zones = list(dict.fromkeys(str(record["zone"]) for record in decision_records))
        parts.append("zones: " + json.dumps(zones, ensure_ascii=False, separators=(",", ":")))
        semantics = cast(Mapping[str, JsonValue], raw_hour["time_semantics"])
        decision_interval = semantics["agent_decision_interval_minutes"]
        step_interval = semantics["physical_step_interval_minutes"]
        parts.append(
            f"time_semantics: decision interval {decision_interval} min; physical step "
            f"{step_interval} min; sample 0 is "
            "the hour-start state before action; samples 1-4 are post-action outcomes; "
            "current state is sample 4; each action precedes its same-step outcome."
        )
        site = cast(Mapping[str, JsonValue], raw_hour["site_result"])
        parts.append("site_result: " + json.dumps(site, ensure_ascii=False, separators=(",", ":")))
        parts.append(
            "hourly_decision:\n"
            + _render_scoped_common_rows(
                _working_decision_agent_view(decision_records), omit_common=("hour",)
            )
        )
        current_records = decode_common_rows(cast(Mapping[str, Any], raw_hour["current_state"]))
        current_step = _assert_group_value(current_records, "last_completed_step")
        parts.append(f"current_state: recent_state_history sample 4, step {current_step}")
        parts.append(
            "recent_state_history:\n"
            + _render_history(cast(Mapping[str, Any], raw_hour["recent_state_history"]))
        )
        parts.append(
            "control_action_history:\n"
            + _render_action_history(cast(Mapping[str, Any], raw_hour["action_history"]))
        )
        parts.append(
            "decision_time_occupancy_forecast:\n"
            + _render_occupancy_forecast(cast(Mapping[str, Any], raw_hour["occupancy_forecast"]))
        )
        parts.append(
            "derived_features:\n"
            + _render_scoped_common_rows(cast(Mapping[str, Any], raw_hour["derived_features"]))
        )
    return "\n".join(part for part in parts if part and not part.endswith(":\n"))


def render_control_specification(view: Mapping[str, Any]) -> str:
    """Render the executable program and its edit limits without repeated record keys."""
    specification = copy.deepcopy(dict(view))
    version = specification.pop("program_version")
    parameters = cast(Sequence[Mapping[str, JsonValue]], specification.pop("parameters"))
    rules = cast(Sequence[Mapping[str, JsonValue]], specification.pop("rules"))
    parts = [f"program_version: {_cell(cast(JsonValue, version))}"]
    parameter_rows: list[dict[str, JsonValue]] = []
    for parameter in parameters:
        row = {
            "param": copy.deepcopy(parameter["param"]),
            "current": copy.deepcopy(parameter["current"]),
            "min": copy.deepcopy(parameter["min"]),
            "max": copy.deepcopy(parameter["max"]),
            "source": copy.deepcopy(parameter["bounds_source"]),
        }
        parameter_rows.append(row)
    parts.append(
        "parameters:\n" + _table(parameter_rows, ("param", "current", "min", "max", "source"))
    )

    rule_groups: dict[str, tuple[dict[str, JsonValue], list[dict[str, JsonValue]]]] = {}
    for raw_rule in rules:
        rule = copy.deepcopy(dict(raw_rule))
        when = cast(list[dict[str, JsonValue]], rule["when"])
        first = when[0] if when else {}
        group_key = json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if group_key not in rule_groups:
            rule_groups[group_key] = (copy.deepcopy(first), [])
        rule["when"] = [cast(JsonValue, condition) for condition in when[1:]]
        rule_groups[group_key][1].append(rule)
    rule_blocks: list[str] = []
    for common_when, grouped_rules in rule_groups.values():
        rule_blocks.append(
            "common_when: " + json.dumps(common_when, ensure_ascii=False, separators=(",", ":"))
        )
        rule_blocks.extend(
            json.dumps(rule, ensure_ascii=False, separators=(",", ":")) for rule in grouped_rules
        )
    parts.append("rules:\n" + "\n".join(rule_blocks))
    display_text = {
        "use the named parameter value": "named parameter value",
        "use the opposite sign of the named parameter value": "negative named parameter value",
        "a number, or the name of a parameter above": "number or parameter name",
        "finite numeric literals": "finite numbers",
        "not allowed": "forbidden",
    }
    display_fields = {
        "a_rule_you_add": "new_rule",
        "conditions_may_test": "condition_fields",
        "compared_against": "comparison_value",
        "actions": "action_types",
        "most_rules_at_once": "max_rules",
        "weather_condition_values": "weather_literals",
        "parameter_references": "parameter_refs",
    }

    def concise(value: JsonValue) -> JsonValue:
        if isinstance(value, dict):
            return {display_fields.get(key, key): concise(child) for key, child in value.items()}
        if isinstance(value, list):
            return [concise(child) for child in value]
        if isinstance(value, str):
            return display_text.get(value, value)
        return value

    for field, value in specification.items():
        parts.append(
            f"{field}: "
            + json.dumps(concise(cast(JsonValue, value)), ensure_ascii=False, separators=(",", ":"))
        )
    return "\n".join(parts)


def _field_manifest(value: JsonValue, prefix: tuple[str, ...] = ()) -> list[str]:
    if isinstance(value, dict):
        if not value:
            return [_pointer(prefix)]
        result: list[str] = []
        for key, item in value.items():
            result.extend(_field_manifest(item, (*prefix, key)))
        return result
    if isinstance(value, list):
        if not value:
            return [_pointer((*prefix, "[]"))]
        result = []
        for item in value:
            result.extend(_field_manifest(item, (*prefix, "[]")))
        return list(dict.fromkeys(result))
    return [_pointer(prefix)]


def _hash(value: JsonValue) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CompiledContext:
    agent_view: str
    human_view: str
    canonical_ir: dict[str, JsonValue]
    compact_view: list[dict[str, JsonValue]]
    audit_view: dict[str, JsonValue]


class ContextBuilder:
    """Build three deterministic views from one canonical typed context."""

    def __init__(self) -> None:
        self._sections: list[dict[str, JsonValue]] = []
        self._canonical: dict[str, JsonValue] = {}

    def add_json(self, title: str, value: Any) -> None:
        if value is None:
            return
        canonical = _normalize(value)
        self._add(title, "json", canonical, canonical)

    def add_common_rows(
        self, title: str, records: Sequence[Mapping[str, Any]], *, identity_fields: Sequence[str]
    ) -> None:
        canonical = _normalize(list(records))
        compact = factor_common_rows(records, identity_fields=identity_fields)
        self._add(title, "common_rows", canonical, cast(JsonValue, compact))

    def add_working_memory(self, title: str, records: Sequence[Mapping[str, Any]]) -> None:
        canonical = _normalize(list(records))
        compact = compile_working_memory(records)
        self._add(title, "working_memory", canonical, cast(JsonValue, compact))

    def add_control_specification(self, title: str, specification: Mapping[str, Any]) -> None:
        canonical = _normalize(specification)
        if not isinstance(canonical, dict):
            raise ValueError("control specification must be an object")
        self._add(title, "control_specification", canonical, canonical)

    def _add(self, title: str, kind: SectionKind, canonical: JsonValue, compact: JsonValue) -> None:
        if title in self._canonical:
            raise ValueError(f"duplicate context-section owner: {title}")
        self._canonical[title] = canonical
        self._sections.append({"title": title, "kind": kind, "view": compact})

    def build(self) -> CompiledContext:
        decoded = decode_compact_context(self._sections)
        if decoded != self._canonical:
            raise ValueError("compiled context is not lossless")
        agent_parts: list[str] = []
        human_parts: list[str] = []
        manifest: dict[str, JsonValue] = {}
        for section in self._sections:
            title = cast(str, section["title"])
            kind = cast(SectionKind, section["kind"])
            view = section["view"]
            if kind == "json":
                rendered = (
                    "```json\n"
                    + json.dumps(view, ensure_ascii=False, separators=(",", ":"))
                    + "\n```"
                )
            elif kind == "common_rows":
                rendered = render_common_rows(cast(Mapping[str, Any], view))
            elif kind == "working_memory":
                rendered = render_working_memory(cast(Mapping[str, Any], view))
            else:
                rendered = render_control_specification(cast(Mapping[str, Any], view))
            agent_parts.append(f"### {title}\n{rendered}")
            human_parts.append(
                f"### {title}\n```json\n"
                + json.dumps(self._canonical[title], ensure_ascii=False, indent=2)
                + "\n```"
            )
            manifest[title] = cast(JsonValue, _field_manifest(self._canonical[title]))
        audit: dict[str, JsonValue] = {
            "schema": "h3c_context_audit_v1",
            "canonical_sha256": _hash(self._canonical),
            "compact_sha256": _hash(cast(JsonValue, self._sections)),
            "field_manifest": manifest,
            "round_trip_equal": True,
        }
        return CompiledContext(
            agent_view="\n\n".join(agent_parts) + ("\n" if agent_parts else ""),
            human_view="\n\n".join(human_parts) + ("\n" if human_parts else ""),
            canonical_ir=copy.deepcopy(self._canonical),
            compact_view=copy.deepcopy(self._sections),
            audit_view=audit,
        )


def decode_compact_context(sections: Sequence[Mapping[str, Any]]) -> dict[str, JsonValue]:
    """Decode all compact sections to their canonical typed values."""
    decoded: dict[str, JsonValue] = {}
    for section in sections:
        title = str(section["title"])
        if title in decoded:
            raise ValueError(f"duplicate context-section owner: {title}")
        kind = str(section["kind"])
        view = section["view"]
        if kind == "json":
            decoded[title] = _normalize(view)
        elif kind == "common_rows":
            decoded[title] = cast(JsonValue, decode_common_rows(cast(Mapping[str, Any], view)))
        elif kind == "working_memory":
            decoded[title] = cast(JsonValue, decode_working_memory(cast(Mapping[str, Any], view)))
        elif kind == "control_specification":
            decoded[title] = _normalize(view)
        else:
            raise ValueError(f"unknown compact section kind: {kind}")
    return decoded
