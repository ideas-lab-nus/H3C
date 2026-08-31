# H3C complete MZ Air control interval: working memory and optional regime experience

This is one frozen, non-executed documentation fixture. Every prompt is produced by the production renderer and every deterministic transition below is evaluated by production validation, program, assurance, working-memory and CRUD owners. It is not a reported experimental result.

## 1. Exact API request settings

```json
{
  "model": "deepseek-v4-flash",
  "provider_call_is_stateless": true,
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "temperature_present": false,
  "thinking": {
    "type": "enabled"
  },
  "top_p_present": false
}
```
## 2. Orchestrator complete request, output and validation

### Complete serialized request body

```json
{
  "messages": [
    {
      "content": "ROLE\nAllocate cross-zone allowance over action_times in control_interval.\n\nDECISION\nBalance comfort and energy cost from the supplied state, forecast, working memory and previous Budget use. Output allocation, priority and per-zone rationales.\n\nHARD BOUNDARIES\nFor accepted program changes, charge_c = max over proof states of max(0, setpoint_before_c - setpoint_after_c); not cumulative action, power or pre-cooling offset.\n\nOUTPUT\nBare JSON only. Keys exactly: site_cap_c, zone_budgets_c, priority, rationale_per_zone, causal_edge_ids. site_cap_c=input. zone_budgets_c: keys=zones; each finite in [0,5]; sum≤cap; unused allowed. priority=permutation(zones), highest first. rationale_per_zone: keys=zones; values nonempty. causal_edge_ids: unique, nonempty, visible-ID subset including a site edge.\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT SITE STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\nprice_at_interval_end: 0.16842\n\n### SITE FORECAST\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CURRENT ZONE STATE\ncommon:\noccupancy: 1.0\nsetpoint_c: 25.0\nrows:\n| zone | temp_c | pmv | temp_rise_to_warm_pmv_edge_c | temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- |\n| cor | 24.31 | 0.34 | 0.62 | 2.45 |\n| eas | 24.58 | 0.43 | 0.34 | 2.72 |\n| nor | 24.22 | 0.31 | 0.72 | 2.36 |\n| sou | 24.47 | 0.39 | 0.45 | 2.61 |\n| wes | 24.36 | 0.36 | 0.57 | 2.5 |\n\n### ZONE CONTROL CONTEXT\ncommon:\noccupancy_at_interval_end: 1.0\nprecool_offset_from_unoccupied_base_c: -5.0\nresulting_precool_setpoint_c: 25.0\nrows:\n| zone |\n| --- |\n| cor |\n| eas |\n| nor |\n| sou |\n| wes |\n\n### CAUSAL EVIDENCE\ncommon:\ntarget: power_meters\nundirected: false\nrows:\n| id | source | relation | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | Immediate | Strong Impact |\n\n### ALLOCATION LIMITS\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\nsite_cap_c: 10.0\nper_zone_cap_c: 5.0\n\n### CONTROL DOMAIN\ndomain_id: cooling\ncontrolled_setpoint: zone cooling setpoint\nunit: degC\nhard_bounds_c: [20.0,30.0]\noccupied_base_c: 25.0\nunoccupied_base_c: 30.0\nabs_pmv_score_limit: 0.5\npreconditioning: {\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0}\nenergy_intensive_setpoint_direction: decrease\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\ncommon:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: Stable occupied conditions coincided with positive warm-side comfort headroom.\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nrecent_state_history:\ncommon:\noccupancy: 1.0\nsetpoint_c: 25.0\nconstant_by_zone:\n{\"zone\":\"cor\",\"temp_c\":24.31,\"pmv\":0.34}\n{\"zone\":\"eas\",\"temp_c\":24.58,\"pmv\":0.43}\n{\"zone\":\"nor\",\"temp_c\":24.22,\"pmv\":0.31}\n{\"zone\":\"sou\",\"temp_c\":24.47,\"pmv\":0.39}\n{\"zone\":\"wes\",\"temp_c\":24.36,\"pmv\":0.36}\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\ncontrol_action_history:\ncommon:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nterminal_outcome_state: shown once in the current-state section at 14:00\nprevious_decision_forecast:\ncommon:\noccupancy: 1.0\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\ncommon:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\nrows:\n| zone | occupied_peak_abs_pmv |\n| --- | --- |\n| cor | 0.34 |\n| eas | 0.43 |\n| nor | 0.31 |\n| sou | 0.39 |\n| wes | 0.36 |\n\n### PREVIOUS BUDGET USE\nsite_cap_c: 10.0\nreserved_allowance_by_zone_c: {\"cor\":1.0,\"eas\":2.0,\"nor\":1.0,\"sou\":1.0,\"wes\":1.0}\nreserved_consumption_by_zone_c: {\"cor\":0.0,\"eas\":2.0,\"nor\":0.0,\"sou\":0.0,\"wes\":0.0}\ntotal_reserved_allowance_c: 6.0\ntotal_reserved_consumption_c: 2.0\nreserved_utilisation: 0.3333\ninitial_shared_unreserved_pool_c: 4.0\nshared_pool_consumption_by_zone_c: {\"eas\":0.3}\nremaining_shared_unreserved_pool_c: 3.7\nprevious_priority: [\"eas\",\"sou\",\"wes\",\"cor\",\"nor\"]\nprevious_rationale_per_zone: {\"cor\":\"Core conditions were stable.\",\"eas\":\"East had the smallest warm-side headroom.\",\"nor\":\"North conditions were stable.\",\"sou\":\"South had moderate warm-side headroom.\",\"wes\":\"West had moderate warm-side headroom.\"}\n",
      "role": "user"
    }
  ],
  "model": "deepseek-v4-flash",
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "thinking": {
    "type": "enabled"
  }
}
```
### Model output

```json
{
  "causal_edge_ids": [
    "ce_660795c7"
  ],
  "priority": [
    "eas",
    "sou",
    "wes",
    "cor",
    "nor"
  ],
  "rationale_per_zone": {
    "cor": "Stable core conditions require a bounded share.",
    "eas": "East has the smallest warm-side comfort headroom and receives first priority.",
    "nor": "Stable north conditions require a bounded share.",
    "sou": "South has moderate warm-side headroom and receives second priority.",
    "wes": "West has moderate warm-side headroom and receives third priority."
  },
  "site_cap_c": 10.0,
  "zone_budgets_c": {
    "cor": 1.0,
    "eas": 2.0,
    "nor": 1.0,
    "sou": 1.0,
    "wes": 1.0
  }
}
```
### Deterministic validation

```json
{
  "accepted": true,
  "site_edge_id": "ce_660795c7",
  "zones": [
    "cor",
    "eas",
    "nor",
    "sou",
    "wes"
  ]
}
```
## 3. Five Executor complete requests, outputs and settlement

### Executor `cor` — Complete serialized request body

```json
{
  "messages": [
    {
      "content": "ROLE\nMaintain one zone's control specification.\n\nDECISION\nUse the current observation, comfort headroom, causal evidence, allowance and WORKING MEMORY to propose one atomic operation. Seek energy savings with |PMV| ≤ 0.5. Do not predict interpreter output.\n\nHARD BOUNDARIES\nFor an accepted program change, charge_c = max over proof states of max(0, setpoint_before_c - setpoint_after_c); it is not cumulative action, power or pre-cooling offset. Edit only through the control specification and operation contract; do not output a direct setpoint.\n\nOUTPUT\nReturn bare JSON {\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}. memory_refs cites only active experiences used and may be empty. No prose, fence or extra fields. Operation contract:\npatch: list of exactly one operation.\nCommon required fields: op, rationale.\nModifying operation also requires causal_edge_ids.\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule: id, when, then. when item: field, op, value. then: op, plus value for set_residual or step_setpoint.\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: cor\nzone_temperature_c: 24.31\npmv: 0.34\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.62\ntemp_drop_to_cool_pmv_edge_c: 2.45\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\ncommon:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":1.0,\"shared_unreserved_allowance_c\":4.0,\"shared_priority_rank\":4}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"cor\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\ncommon:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: Stable occupied conditions coincided with positive warm-side comfort headroom.\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nrecent_state_history:\ncommon:\ntemp_c: 24.31\npmv: 0.34\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\ncontrol_action_history:\ncommon:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nterminal_outcome_state: shown once in the current-state section at 14:00\nprevious_decision_forecast:\ncommon:\noccupancy: 1.0\nzones: [\"cor\"]\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\ncommon:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.34\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n\n### ACTIVE LONG-TERM EXPERIENCES\ncommon:\nrevision: 2\nexperience: Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.\nrows:\n| regime |\n| --- |\n| steady_state_occupancy |\n",
      "role": "user"
    }
  ],
  "model": "deepseek-v4-flash",
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "thinking": {
    "type": "enabled"
  }
}
```
### Executor `cor` — Model output

```json
{
  "memory_refs": [],
  "patch": [
    {
      "op": "no_change",
      "rationale": "The current program retained occupied comfort headroom without an evidenced beneficial edit."
    }
  ]
}
```
### Executor `cor` — deterministic memory-reference audit

```json
{
  "exposed": [
    {
      "experience": "Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.",
      "regime": "steady_state_occupancy",
      "revision": 2
    }
  ],
  "invalid": [],
  "reported": [],
  "valid": []
}
```
### Executor `eas` — Complete serialized request body

```json
{
  "messages": [
    {
      "content": "ROLE\nMaintain one zone's control specification.\n\nDECISION\nUse the current observation, comfort headroom, causal evidence, allowance and WORKING MEMORY to propose one atomic operation. Seek energy savings with |PMV| ≤ 0.5. Do not predict interpreter output.\n\nHARD BOUNDARIES\nFor an accepted program change, charge_c = max over proof states of max(0, setpoint_before_c - setpoint_after_c); it is not cumulative action, power or pre-cooling offset. Edit only through the control specification and operation contract; do not output a direct setpoint.\n\nOUTPUT\nReturn bare JSON {\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}. memory_refs cites only active experiences used and may be empty. No prose, fence or extra fields. Operation contract:\npatch: list of exactly one operation.\nCommon required fields: op, rationale.\nModifying operation also requires causal_edge_ids.\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule: id, when, then. when item: field, op, value. then: op, plus value for set_residual or step_setpoint.\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: eas\nzone_temperature_c: 24.58\npmv: 0.43\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.34\ntemp_drop_to_cool_pmv_edge_c: 2.72\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\ncommon:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":2.0,\"shared_unreserved_allowance_c\":4.0,\"shared_priority_rank\":1}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"eas\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\ncommon:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: Stable occupied conditions coincided with positive warm-side comfort headroom.\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nrecent_state_history:\ncommon:\ntemp_c: 24.58\npmv: 0.43\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\ncontrol_action_history:\ncommon:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nterminal_outcome_state: shown once in the current-state section at 14:00\nprevious_decision_forecast:\ncommon:\noccupancy: 1.0\nzones: [\"eas\"]\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\ncommon:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.43\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n\n### ACTIVE LONG-TERM EXPERIENCES\ncommon:\nrevision: 1\nexperience: East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.\nrows:\n| regime |\n| --- |\n| steady_state_occupancy |\n",
      "role": "user"
    }
  ],
  "model": "deepseek-v4-flash",
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "thinking": {
    "type": "enabled"
  }
}
```
### Executor `eas` — Model output

```json
{
  "memory_refs": [
    {
      "regime": "steady_state_occupancy",
      "revision": 1
    }
  ],
  "patch": [
    {
      "causal_edge_ids": [
        "ce_ebd13728"
      ],
      "op": "set_param",
      "param": "pmv_band_hi",
      "rationale": "Tighten the active upper PMV threshold while East has the smallest warm-side headroom.",
      "to": 0.4
    }
  ]
}
```
### Executor `eas` — deterministic memory-reference audit

```json
{
  "exposed": [
    {
      "experience": "East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.",
      "regime": "steady_state_occupancy",
      "revision": 1
    }
  ],
  "invalid": [],
  "reported": [
    {
      "regime": "steady_state_occupancy",
      "revision": 1
    }
  ],
  "valid": [
    {
      "regime": "steady_state_occupancy",
      "revision": 1
    }
  ]
}
```
### Executor `nor` — Complete serialized request body

```json
{
  "messages": [
    {
      "content": "ROLE\nMaintain one zone's control specification.\n\nDECISION\nUse the current observation, comfort headroom, causal evidence, allowance and WORKING MEMORY to propose one atomic operation. Seek energy savings with |PMV| ≤ 0.5. Do not predict interpreter output.\n\nHARD BOUNDARIES\nFor an accepted program change, charge_c = max over proof states of max(0, setpoint_before_c - setpoint_after_c); it is not cumulative action, power or pre-cooling offset. Edit only through the control specification and operation contract; do not output a direct setpoint.\n\nOUTPUT\nReturn bare JSON {\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}. memory_refs cites only active experiences used and may be empty. No prose, fence or extra fields. Operation contract:\npatch: list of exactly one operation.\nCommon required fields: op, rationale.\nModifying operation also requires causal_edge_ids.\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule: id, when, then. when item: field, op, value. then: op, plus value for set_residual or step_setpoint.\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: nor\nzone_temperature_c: 24.22\npmv: 0.31\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.72\ntemp_drop_to_cool_pmv_edge_c: 2.36\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\ncommon:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":1.0,\"shared_unreserved_allowance_c\":4.0,\"shared_priority_rank\":5}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"nor\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\ncommon:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: Stable occupied conditions coincided with positive warm-side comfort headroom.\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nrecent_state_history:\ncommon:\ntemp_c: 24.22\npmv: 0.31\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\ncontrol_action_history:\ncommon:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nterminal_outcome_state: shown once in the current-state section at 14:00\nprevious_decision_forecast:\ncommon:\noccupancy: 1.0\nzones: [\"nor\"]\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\ncommon:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.31\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n",
      "role": "user"
    }
  ],
  "model": "deepseek-v4-flash",
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "thinking": {
    "type": "enabled"
  }
}
```
### Executor `nor` — Model output

```json
{
  "memory_refs": [],
  "patch": [
    {
      "op": "no_change",
      "rationale": "The current program matched the observed stable occupied conditions."
    }
  ]
}
```
### Executor `nor` — deterministic memory-reference audit

```json
{
  "exposed": [],
  "invalid": [],
  "reported": [],
  "valid": []
}
```
### Executor `sou` — Complete serialized request body

```json
{
  "messages": [
    {
      "content": "ROLE\nMaintain one zone's control specification.\n\nDECISION\nUse the current observation, comfort headroom, causal evidence, allowance and WORKING MEMORY to propose one atomic operation. Seek energy savings with |PMV| ≤ 0.5. Do not predict interpreter output.\n\nHARD BOUNDARIES\nFor an accepted program change, charge_c = max over proof states of max(0, setpoint_before_c - setpoint_after_c); it is not cumulative action, power or pre-cooling offset. Edit only through the control specification and operation contract; do not output a direct setpoint.\n\nOUTPUT\nReturn bare JSON {\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}. memory_refs cites only active experiences used and may be empty. No prose, fence or extra fields. Operation contract:\npatch: list of exactly one operation.\nCommon required fields: op, rationale.\nModifying operation also requires causal_edge_ids.\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule: id, when, then. when item: field, op, value. then: op, plus value for set_residual or step_setpoint.\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: sou\nzone_temperature_c: 24.47\npmv: 0.39\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.45\ntemp_drop_to_cool_pmv_edge_c: 2.61\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\ncommon:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":1.0,\"shared_unreserved_allowance_c\":4.0,\"shared_priority_rank\":2}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"sou\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\ncommon:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: Stable occupied conditions coincided with positive warm-side comfort headroom.\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nrecent_state_history:\ncommon:\ntemp_c: 24.47\npmv: 0.39\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\ncontrol_action_history:\ncommon:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nterminal_outcome_state: shown once in the current-state section at 14:00\nprevious_decision_forecast:\ncommon:\noccupancy: 1.0\nzones: [\"sou\"]\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\ncommon:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.39\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n\n### ACTIVE LONG-TERM EXPERIENCES\ncommon:\nrevision: 2\nexperience: South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.\nrows:\n| regime |\n| --- |\n| steady_state_occupancy |\n",
      "role": "user"
    }
  ],
  "model": "deepseek-v4-flash",
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "thinking": {
    "type": "enabled"
  }
}
```
### Executor `sou` — Model output

```json
{
  "memory_refs": [],
  "patch": [
    {
      "op": "no_change",
      "rationale": "Observed comfort headroom and the current program did not support a different atomic edit."
    }
  ]
}
```
### Executor `sou` — deterministic memory-reference audit

```json
{
  "exposed": [
    {
      "experience": "South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.",
      "regime": "steady_state_occupancy",
      "revision": 2
    }
  ],
  "invalid": [],
  "reported": [],
  "valid": []
}
```
### Executor `wes` — Complete serialized request body

```json
{
  "messages": [
    {
      "content": "ROLE\nMaintain one zone's control specification.\n\nDECISION\nUse the current observation, comfort headroom, causal evidence, allowance and WORKING MEMORY to propose one atomic operation. Seek energy savings with |PMV| ≤ 0.5. Do not predict interpreter output.\n\nHARD BOUNDARIES\nFor an accepted program change, charge_c = max over proof states of max(0, setpoint_before_c - setpoint_after_c); it is not cumulative action, power or pre-cooling offset. Edit only through the control specification and operation contract; do not output a direct setpoint.\n\nOUTPUT\nReturn bare JSON {\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}. memory_refs cites only active experiences used and may be empty. No prose, fence or extra fields. Operation contract:\npatch: list of exactly one operation.\nCommon required fields: op, rationale.\nModifying operation also requires causal_edge_ids.\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule: id, when, then. when item: field, op, value. then: op, plus value for set_residual or step_setpoint.\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: wes\nzone_temperature_c: 24.36\npmv: 0.36\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.57\ntemp_drop_to_cool_pmv_edge_c: 2.5\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\ncommon:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":1.0,\"shared_unreserved_allowance_c\":4.0,\"shared_priority_rank\":3}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"wes\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\ncommon:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: Stable occupied conditions coincided with positive warm-side comfort headroom.\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nrecent_state_history:\ncommon:\ntemp_c: 24.36\npmv: 0.36\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\ncontrol_action_history:\ncommon:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nterminal_outcome_state: shown once in the current-state section at 14:00\nprevious_decision_forecast:\ncommon:\noccupancy: 1.0\nzones: [\"wes\"]\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\ncommon:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.36\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n\n### ACTIVE LONG-TERM EXPERIENCES\ncommon:\nrevision: 1\nexperience: West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.\nrows:\n| regime |\n| --- |\n| steady_state_occupancy |\n",
      "role": "user"
    }
  ],
  "model": "deepseek-v4-flash",
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "thinking": {
    "type": "enabled"
  }
}
```
### Executor `wes` — Model output

```json
{
  "memory_refs": [],
  "patch": [
    {
      "op": "no_change",
      "rationale": "The supplied evidence did not support changing the executable specification this hour."
    }
  ]
}
```
### Executor `wes` — deterministic memory-reference audit

```json
{
  "exposed": [
    {
      "experience": "West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.",
      "regime": "steady_state_occupancy",
      "revision": 1
    }
  ],
  "invalid": [],
  "reported": [],
  "valid": []
}
```
## 4. Deterministic priority settlement

```json
{
  "priority": [
    "eas",
    "sou",
    "wes",
    "cor",
    "nor"
  ],
  "settled_updates": [
    {
      "completed_validation_stages": [
        "program_validation",
        "causal_admissibility",
        "consistent_program_direction_proof",
        "energy_budget_validation"
      ],
      "current_program_hash": "9f2b6c157da545bd3a6e19355a4f3f39128d1a0af41ea8c22fd960af2f7453ba",
      "current_program_version": 1,
      "hour": 42,
      "memory_refs": {
        "exposed": [
          {
            "experience": "East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.",
            "regime": "steady_state_occupancy",
            "revision": 1
          }
        ],
        "invalid": [],
        "reported": [
          {
            "regime": "steady_state_occupancy",
            "revision": 1
          }
        ],
        "valid": [
          {
            "regime": "steady_state_occupancy",
            "revision": 1
          }
        ]
      },
      "patch": {
        "causal_edge_ids": [
          "ce_ebd13728",
          "ce_660795c7"
        ],
        "consistent_program_direction_proof": {
          "cited_edge_ids": [
            "ce_ebd13728",
            "ce_660795c7"
          ],
          "expected_effects": [
            {
              "direction": "up",
              "node": "power_meters"
            },
            {
              "direction": "down",
              "node": "zone_temp"
            }
          ],
          "mode": "global",
          "program_direction": "down",
          "witness_count": 180
        },
        "expected_effects": [
          {
            "direction": "up",
            "node": "power_meters"
          },
          {
            "direction": "down",
            "node": "zone_temp"
          }
        ],
        "op": "set_param",
        "param": "pmv_band_hi",
        "rationale": "Tighten the active upper PMV threshold while East has the smallest warm-side headroom.",
        "to": 0.4
      },
      "program_hash_after": "9f2b6c157da545bd3a6e19355a4f3f39128d1a0af41ea8c22fd960af2f7453ba",
      "program_hash_before": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "program_version_after": 1,
      "program_version_before": 0,
      "rejection": null,
      "status": "accepted",
      "step": 168,
      "zone": "eas"
    },
    {
      "completed_validation_stages": [
        "program_validation",
        "causal_admissibility",
        "consistent_program_direction_proof",
        "energy_budget_validation"
      ],
      "current_program_hash": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "current_program_version": 0,
      "hour": 42,
      "memory_refs": {
        "exposed": [
          {
            "experience": "South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.",
            "regime": "steady_state_occupancy",
            "revision": 2
          }
        ],
        "invalid": [],
        "reported": [],
        "valid": []
      },
      "patch": {
        "op": "no_change",
        "rationale": "Observed comfort headroom and the current program did not support a different atomic edit."
      },
      "program_hash_after": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "program_hash_before": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "program_version_after": 0,
      "program_version_before": 0,
      "rejection": null,
      "status": "accepted",
      "step": 168,
      "zone": "sou"
    },
    {
      "completed_validation_stages": [
        "program_validation",
        "causal_admissibility",
        "consistent_program_direction_proof",
        "energy_budget_validation"
      ],
      "current_program_hash": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "current_program_version": 0,
      "hour": 42,
      "memory_refs": {
        "exposed": [
          {
            "experience": "West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.",
            "regime": "steady_state_occupancy",
            "revision": 1
          }
        ],
        "invalid": [],
        "reported": [],
        "valid": []
      },
      "patch": {
        "op": "no_change",
        "rationale": "The supplied evidence did not support changing the executable specification this hour."
      },
      "program_hash_after": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "program_hash_before": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "program_version_after": 0,
      "program_version_before": 0,
      "rejection": null,
      "status": "accepted",
      "step": 168,
      "zone": "wes"
    },
    {
      "completed_validation_stages": [
        "program_validation",
        "causal_admissibility",
        "consistent_program_direction_proof",
        "energy_budget_validation"
      ],
      "current_program_hash": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "current_program_version": 0,
      "hour": 42,
      "memory_refs": {
        "exposed": [
          {
            "experience": "Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.",
            "regime": "steady_state_occupancy",
            "revision": 2
          }
        ],
        "invalid": [],
        "reported": [],
        "valid": []
      },
      "patch": {
        "op": "no_change",
        "rationale": "The current program retained occupied comfort headroom without an evidenced beneficial edit."
      },
      "program_hash_after": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "program_hash_before": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "program_version_after": 0,
      "program_version_before": 0,
      "rejection": null,
      "status": "accepted",
      "step": 168,
      "zone": "cor"
    },
    {
      "completed_validation_stages": [
        "program_validation",
        "causal_admissibility",
        "consistent_program_direction_proof",
        "energy_budget_validation"
      ],
      "current_program_hash": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "current_program_version": 0,
      "hour": 42,
      "memory_refs": {
        "exposed": [],
        "invalid": [],
        "reported": [],
        "valid": []
      },
      "patch": {
        "op": "no_change",
        "rationale": "The current program matched the observed stable occupied conditions."
      },
      "program_hash_after": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "program_hash_before": "148991b618bd78876809d302dfbcf3b2564abb5dd76b40327e4181f49b773ba8",
      "program_version_after": 0,
      "program_version_before": 0,
      "rejection": null,
      "status": "accepted",
      "step": 168,
      "zone": "nor"
    }
  ]
}
```
## 5. Four executed actions and resulting observations

```json
[
  {
    "step": 168,
    "zones": {
      "cor": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17503200,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.45,
            "warmer_c": 0.62
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.34,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.31
        },
        "outcome": {
          "cost": 0.7639,
          "effective_occupancy": 1.0,
          "pmv": 0.34,
          "power_w": 21480.0,
          "zone_temperature_c": 24.3
        },
        "outcome_time_seconds": 17504100,
        "step": 168,
        "zone": "cor"
      },
      "eas": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 24.7,
          "comfort_recovery_output_setpoint": 24.7,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 24.7,
          "interpreter_setpoint": 24.7,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": -0.3000000000000007,
          "setpoint_rate_limit_output_setpoint": 24.7,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17503200,
        "final_setpoint_c": 24.7,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_lower",
          "exempt_rate": false,
          "matched_rule": "pmv_lower",
          "residual": -0.3000000000000007,
          "rules_fired": [
            "pmv_lower"
          ],
          "setpoint": 24.7
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.72,
            "warmer_c": 0.34
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.43,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.58
        },
        "outcome": {
          "cost": 0.7639,
          "effective_occupancy": 1.0,
          "pmv": 0.36,
          "power_w": 21480.0,
          "zone_temperature_c": 24.4
        },
        "outcome_time_seconds": 17504100,
        "step": 168,
        "zone": "eas"
      },
      "nor": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17503200,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.36,
            "warmer_c": 0.72
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.31,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.22
        },
        "outcome": {
          "cost": 0.7639,
          "effective_occupancy": 1.0,
          "pmv": 0.31,
          "power_w": 21480.0,
          "zone_temperature_c": 24.23
        },
        "outcome_time_seconds": 17504100,
        "step": 168,
        "zone": "nor"
      },
      "sou": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17503200,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.61,
            "warmer_c": 0.45
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.39,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.47
        },
        "outcome": {
          "cost": 0.7639,
          "effective_occupancy": 1.0,
          "pmv": 0.39,
          "power_w": 21480.0,
          "zone_temperature_c": 24.47
        },
        "outcome_time_seconds": 17504100,
        "step": 168,
        "zone": "sou"
      },
      "wes": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17503200,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.5,
            "warmer_c": 0.57
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.36,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.36
        },
        "outcome": {
          "cost": 0.7639,
          "effective_occupancy": 1.0,
          "pmv": 0.36,
          "power_w": 21480.0,
          "zone_temperature_c": 24.37
        },
        "outcome_time_seconds": 17504100,
        "step": 168,
        "zone": "wes"
      }
    }
  },
  {
    "step": 169,
    "zones": {
      "cor": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17504100,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.45,
            "warmer_c": 0.62
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.34,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.3
        },
        "outcome": {
          "cost": 0.776,
          "effective_occupancy": 1.0,
          "pmv": 0.35,
          "power_w": 21820.0,
          "zone_temperature_c": 24.32
        },
        "outcome_time_seconds": 17505000,
        "step": 169,
        "zone": "cor"
      },
      "eas": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 24.7,
          "comfort_recovery_output_setpoint": 24.7,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 24.7,
          "interpreter_setpoint": 24.7,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 24.7,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17504100,
        "final_setpoint_c": 24.7,
        "hour": 42,
        "interpreter": {
          "base": 24.7,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": -0.3000000000000007,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 24.7
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.72,
            "warmer_c": 0.34
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.36,
          "last_setpoint": 24.7,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.4
        },
        "outcome": {
          "cost": 0.776,
          "effective_occupancy": 1.0,
          "pmv": 0.3,
          "power_w": 21820.0,
          "zone_temperature_c": 24.25
        },
        "outcome_time_seconds": 17505000,
        "step": 169,
        "zone": "eas"
      },
      "nor": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17504100,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.36,
            "warmer_c": 0.72
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.31,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.23
        },
        "outcome": {
          "cost": 0.776,
          "effective_occupancy": 1.0,
          "pmv": 0.32,
          "power_w": 21820.0,
          "zone_temperature_c": 24.24
        },
        "outcome_time_seconds": 17505000,
        "step": 169,
        "zone": "nor"
      },
      "sou": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17504100,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.61,
            "warmer_c": 0.45
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.39,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.47
        },
        "outcome": {
          "cost": 0.776,
          "effective_occupancy": 1.0,
          "pmv": 0.4,
          "power_w": 21820.0,
          "zone_temperature_c": 24.49
        },
        "outcome_time_seconds": 17505000,
        "step": 169,
        "zone": "sou"
      },
      "wes": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17504100,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.5,
            "warmer_c": 0.57
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.36,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.37
        },
        "outcome": {
          "cost": 0.776,
          "effective_occupancy": 1.0,
          "pmv": 0.37,
          "power_w": 21820.0,
          "zone_temperature_c": 24.38
        },
        "outcome_time_seconds": 17505000,
        "step": 169,
        "zone": "wes"
      }
    }
  },
  {
    "step": 170,
    "zones": {
      "cor": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17505000,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.45,
            "warmer_c": 0.62
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.35,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.32
        },
        "outcome": {
          "cost": 0.7863,
          "effective_occupancy": 1.0,
          "pmv": 0.35,
          "power_w": 22110.0,
          "zone_temperature_c": 24.34
        },
        "outcome_time_seconds": 17505900,
        "step": 170,
        "zone": "cor"
      },
      "eas": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 24.7,
          "comfort_recovery_output_setpoint": 24.7,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 24.7,
          "interpreter_setpoint": 24.7,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 24.7,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17505000,
        "final_setpoint_c": 24.7,
        "hour": 42,
        "interpreter": {
          "base": 24.7,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": -0.3000000000000007,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 24.7
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.72,
            "warmer_c": 0.34
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.3,
          "last_setpoint": 24.7,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.25
        },
        "outcome": {
          "cost": 0.7863,
          "effective_occupancy": 1.0,
          "pmv": 0.28,
          "power_w": 22110.0,
          "zone_temperature_c": 24.18
        },
        "outcome_time_seconds": 17505900,
        "step": 170,
        "zone": "eas"
      },
      "nor": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17505000,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.36,
            "warmer_c": 0.72
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.32,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.24
        },
        "outcome": {
          "cost": 0.7863,
          "effective_occupancy": 1.0,
          "pmv": 0.32,
          "power_w": 22110.0,
          "zone_temperature_c": 24.25
        },
        "outcome_time_seconds": 17505900,
        "step": 170,
        "zone": "nor"
      },
      "sou": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17505000,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.61,
            "warmer_c": 0.45
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.4,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.49
        },
        "outcome": {
          "cost": 0.7863,
          "effective_occupancy": 1.0,
          "pmv": 0.4,
          "power_w": 22110.0,
          "zone_temperature_c": 24.5
        },
        "outcome_time_seconds": 17505900,
        "step": 170,
        "zone": "sou"
      },
      "wes": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17505000,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.5,
            "warmer_c": 0.57
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.37,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.38
        },
        "outcome": {
          "cost": 0.7863,
          "effective_occupancy": 1.0,
          "pmv": 0.37,
          "power_w": 22110.0,
          "zone_temperature_c": 24.4
        },
        "outcome_time_seconds": 17505900,
        "step": 170,
        "zone": "wes"
      }
    }
  },
  {
    "step": 171,
    "zones": {
      "cor": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17505900,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.45,
            "warmer_c": 0.62
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.35,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.34
        },
        "outcome": {
          "cost": 0.7952,
          "effective_occupancy": 1.0,
          "pmv": 0.36,
          "power_w": 22360.0,
          "zone_temperature_c": 24.35
        },
        "outcome_time_seconds": 17506800,
        "step": 171,
        "zone": "cor"
      },
      "eas": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.3000000000000007,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17505900,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 24.7,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_raise",
          "exempt_rate": false,
          "matched_rule": "pmv_raise",
          "residual": 0.0,
          "rules_fired": [
            "pmv_raise"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.72,
            "warmer_c": 0.34
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.28,
          "last_setpoint": 24.7,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.18
        },
        "outcome": {
          "cost": 0.7952,
          "effective_occupancy": 1.0,
          "pmv": 0.31,
          "power_w": 22360.0,
          "zone_temperature_c": 24.24
        },
        "outcome_time_seconds": 17506800,
        "step": 171,
        "zone": "eas"
      },
      "nor": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17505900,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.36,
            "warmer_c": 0.72
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.32,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.25
        },
        "outcome": {
          "cost": 0.7952,
          "effective_occupancy": 1.0,
          "pmv": 0.33,
          "power_w": 22360.0,
          "zone_temperature_c": 24.27
        },
        "outcome_time_seconds": 17506800,
        "step": 171,
        "zone": "nor"
      },
      "sou": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17505900,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.61,
            "warmer_c": 0.45
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.4,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.5
        },
        "outcome": {
          "cost": 0.7952,
          "effective_occupancy": 1.0,
          "pmv": 0.41,
          "power_w": 22360.0,
          "zone_temperature_c": 24.52
        },
        "outcome_time_seconds": 17506800,
        "step": 171,
        "zone": "sou"
      },
      "wes": {
        "action_assurance": {
          "actuator_bound": null,
          "actuator_bounds_triggered": false,
          "comfort_recovery_input_setpoint": 25.0,
          "comfort_recovery_output_setpoint": 25.0,
          "comfort_recovery_reason": null,
          "comfort_recovery_triggered": false,
          "final_setpoint": 25.0,
          "interpreter_setpoint": 25.0,
          "order": [
            "comfort_recovery",
            "setpoint_rate_limit",
            "actuator_bounds"
          ],
          "setpoint_rate_limit_delta_before_c": 0.0,
          "setpoint_rate_limit_output_setpoint": 25.0,
          "setpoint_rate_limit_triggered": false
        },
        "action_time_seconds": 17505900,
        "final_setpoint_c": 25.0,
        "hour": 42,
        "interpreter": {
          "base": 25.0,
          "base_setpoint": 25.0,
          "branch": "occupied_pmv_in_band",
          "exempt_rate": false,
          "matched_rule": "occupied_hold",
          "residual": 0.0,
          "rules_fired": [
            "occupied_hold"
          ],
          "setpoint": 25.0
        },
        "observation": {
          "comfort_headroom_c": {
            "cooler_c": 2.5,
            "warmer_c": 0.57
          },
          "current_occupancy": 1.0,
          "electricity_price": 0.14231,
          "last_occupancy": 1.0,
          "last_pmv": 0.37,
          "last_setpoint": 25.0,
          "next_hour_occupancy": 1.0,
          "occ_ahead": [
            1.0,
            1.0,
            1.0,
            1.0
          ],
          "outdoor_temp_c": 31.4,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 612.0,
          "solar_irr_max_next_1h_w_m2": 668.0,
          "solar_irr_mean_next_1h_w_m2": 642.5,
          "solar_irr_threshold_candidates_w_m2": [
            500.0,
            650.0
          ],
          "weather_next_steps": [
            {
              "outdoor_temp_c": 31.6,
              "solar_irr": 628.0,
              "step_ahead": 1
            },
            {
              "outdoor_temp_c": 31.8,
              "solar_irr": 646.0,
              "step_ahead": 2
            },
            {
              "outdoor_temp_c": 32.0,
              "solar_irr": 668.0,
              "step_ahead": 3
            },
            {
              "outdoor_temp_c": 32.2,
              "solar_irr": 628.0,
              "step_ahead": 4
            }
          ],
          "zone_temperature_c": 24.4
        },
        "outcome": {
          "cost": 0.7952,
          "effective_occupancy": 1.0,
          "pmv": 0.38,
          "power_w": 22360.0,
          "zone_temperature_c": 24.41
        },
        "outcome_time_seconds": 17506800,
        "step": 171,
        "zone": "wes"
      }
    }
  }
]
```
## 6. Reflector complete request and output

### Complete serialized request body

```json
{
  "messages": [
    {
      "content": "ROLE\nInterpret the deterministic results for the supplied completed control interval.\n\nEVIDENCE\nFor each zone, derive one useful observed relationship or trade-off from completed Context, Action and Outcome. Compare it with shown eligible regime slots; select at most one memory operation.\n\nHARD BOUNDARIES\nLessons are evidence-grounded observations, relationships or trade-offs, not commands, targets or unsupported claims. Experiences describe the zone's run-wide thermal response, control preference or trade-off for the named regime. Modify only a shown eligible regime; replace/delete uses its revision.\n\nOUTPUT\nBare JSON only: {\"hourly_lessons\":[{\"zone\":...,\"lesson\":...}],\"memory_operations\":[...]}. Each zone appears once per list. Every memory operation requires zone and op; additional fields:\n| op | required |\n| --- | --- |\n| no_change | — |\n| add | regime, experience |\n| replace | regime, expected_revision, experience |\n| delete | regime, expected_revision |\nNo prose, fence or extra fields.\n",
      "role": "system"
    },
    {
      "content": "### COMPLETED CONTROL INTERVAL\ninterval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\noutcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.1214,\"site_energy_kwh\":21.9425}\ncompleted_decision:\ncommon:\naction: {\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0}\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nrows:\n| zone | op | rationale | program_version_after |\n| --- | --- | --- | --- |\n| cor | no_change | The current program retained occupied comfort headroom without an evidenced beneficial edit. | 0 |\n| nor | no_change | The current program matched the observed stable occupied conditions. | 0 |\n| sou | no_change | Observed comfort headroom and the current program did not support a different atomic edit. | 0 |\n| wes | no_change | The supplied evidence did not support changing the executable specification this hour. | 0 |\n| zone | op | rationale | program_version_after | param | to |\n| --- | --- | --- | --- | --- | --- |\n| eas | set_param | Tighten the active upper PMV threshold while East has the smallest warm-side headroom. | 1 | pmv_band_hi | 0.4 |\nrecent_state_history:\ncommon:\noccupancy: 1.0\nconstant_by_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0}\n{\"zone\":\"nor\",\"setpoint_c\":25.0}\n{\"zone\":\"sou\",\"setpoint_c\":25.0}\n{\"zone\":\"wes\",\"setpoint_c\":25.0}\nstate_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ntime_varying_measurements:\n| state_time | cor.temp_c | cor.pmv | eas.temp_c | eas.pmv | eas.setpoint_c | nor.temp_c | nor.pmv | sou.temp_c | sou.pmv | wes.temp_c | wes.pmv |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 14:00 | 24.31 | 0.34 | 24.58 | 0.43 | 25.0 | 24.22 | 0.31 | 24.47 | 0.39 | 24.36 | 0.36 |\n| 14:15 | 24.3 | 0.34 | 24.4 | 0.36 | 24.7 | 24.23 | 0.31 | 24.47 | 0.39 | 24.37 | 0.36 |\n| 14:30 | 24.32 | 0.35 | 24.25 | 0.3 | 24.7 | 24.24 | 0.32 | 24.49 | 0.4 | 24.38 | 0.37 |\n| 14:45 | 24.34 | 0.35 | 24.18 | 0.28 | 24.7 | 24.25 | 0.32 | 24.5 | 0.4 | 24.4 | 0.37 |\n| 15:00 | 24.35 | 0.36 | 24.24 | 0.31 | 25.0 | 24.27 | 0.33 | 24.52 | 0.41 | 24.41 | 0.38 |\ncontrol_action_history:\ncommon:\nregime: steady_state_occupancy\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\nconstant_by_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"nor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"sou\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"wes\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\ntime_varying_actions:\n| action_time | outcome_time | eas.setpoint_c | eas.matched_rule |\n| --- | --- | --- | --- |\n| 14:00 | 14:15 | 24.7 | pmv_lower |\n| 14:15 | 14:30 | 24.7 | occupied_hold |\n| 14:30 | 14:45 | 24.7 | occupied_hold |\n| 14:45 | 15:00 | 25.0 | pmv_raise |\nprevious_decision_forecast:\ncommon:\noccupancy: 1.0\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\noutcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\nderived_feature_interval: [14:00, 15:00)\nderived_features:\ncommon:\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\nsetpoint_reversals: 0\nrows:\n| zone | temp_delta_15min_c | temp_delta_1h_c | temp_slope_c_per_hour | pmv_delta_15min | pmv_delta_1h | setpoint_delta_15min_c | occupied_peak_abs_pmv | setpoint_tv_c |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| cor | 0.01 | 0.04 | 0.04 | 0.01 | 0.02 | 0.0 | 0.36 | 0.0 |\n| eas | 0.06 | -0.34 | -0.34 | 0.03 | -0.12 | 0.3 | 0.36 | 0.3 |\n| nor | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.33 | 0.0 |\n| sou | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.41 | 0.0 |\n| wes | 0.01 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.38 | 0.0 |\n\n### ACTIVE LONG-TERM EXPERIENCE SLOTS\nrows:\n| zone | regime | revision | experience |\n| --- | --- | --- | --- |\n| cor | steady_state_occupancy | 2 | Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive. |\n| eas | steady_state_occupancy | 1 | East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone. |\n| sou | steady_state_occupancy | 2 | South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions. |\n| wes | steady_state_occupancy | 1 | West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions. |\n\n### EMPTY LONG-TERM EXPERIENCE SLOTS\nrows:\n| zone | regime |\n| --- | --- |\n| nor | steady_state_occupancy |\n",
      "role": "user"
    }
  ],
  "model": "deepseek-v4-flash",
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "thinking": {
    "type": "enabled"
  }
}
```
### Model output

```json
{
  "hourly_lessons": [
    {
      "lesson": "Stable setpoints coincided with steady occupied PMV and positive warm-side headroom.",
      "zone": "cor"
    },
    {
      "lesson": "A tighter upper threshold preceded a bounded cooling response while occupied PMV stayed within the comfort band.",
      "zone": "eas"
    },
    {
      "lesson": "The occupied hold branch coincided with small temperature and PMV changes.",
      "zone": "nor"
    },
    {
      "lesson": "The occupied hold branch retained positive warm-side headroom under elevated solar input.",
      "zone": "sou"
    },
    {
      "lesson": "Stable actions coincided with a gradual occupied temperature response and bounded PMV.",
      "zone": "wes"
    }
  ],
  "memory_operations": [
    {
      "op": "no_change",
      "zone": "cor"
    },
    {
      "expected_revision": 1,
      "experience": "East has repeatedly shown limited occupied warm-side comfort headroom and a bounded cooling response after tighter upper-threshold admission.",
      "op": "replace",
      "regime": "steady_state_occupancy",
      "zone": "eas"
    },
    {
      "experience": "North has shown slow occupied temperature and PMV changes under stable setpoints.",
      "op": "add",
      "regime": "steady_state_occupancy",
      "zone": "nor"
    },
    {
      "op": "no_change",
      "zone": "sou"
    },
    {
      "op": "no_change",
      "zone": "wes"
    }
  ]
}
```
## 7. Completed-interval record and next-interval working memory

### Completed-interval records

```json
[
  {
    "action": {
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "program_version_after": 0,
      "program_version_before": 0,
      "proposal": {
        "op": "no_change",
        "rationale": "The current program retained occupied comfort headroom without an evidenced beneficial edit."
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.34,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.31
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "Stable setpoints coincided with steady occupied PMV and positive warm-side headroom.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.36,
      "pmv": [
        0.34,
        0.35,
        0.35,
        0.36
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.0,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.3,
        24.32,
        24.34,
        24.35
      ]
    },
    "zone": "cor"
  },
  {
    "action": {
      "actual_setpoints_c": [
        24.7,
        24.7,
        24.7,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "pmv_lower",
        "occupied_hold",
        "occupied_hold",
        "pmv_raise"
      ],
      "program_version_after": 1,
      "program_version_before": 0,
      "proposal": {
        "causal_edge_ids": [
          "ce_ebd13728",
          "ce_660795c7"
        ],
        "consistent_program_direction_proof": {
          "cited_edge_ids": [
            "ce_ebd13728",
            "ce_660795c7"
          ],
          "expected_effects": [
            {
              "direction": "up",
              "node": "power_meters"
            },
            {
              "direction": "down",
              "node": "zone_temp"
            }
          ],
          "mode": "global",
          "program_direction": "down",
          "witness_count": 180
        },
        "expected_effects": [
          {
            "direction": "up",
            "node": "power_meters"
          },
          {
            "direction": "down",
            "node": "zone_temp"
          }
        ],
        "op": "set_param",
        "param": "pmv_band_hi",
        "rationale": "Tighten the active upper PMV threshold while East has the smallest warm-side headroom.",
        "to": 0.4
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.43,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.58
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "A tighter upper threshold preceded a bounded cooling response while occupied PMV stayed within the comfort band.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.36,
      "pmv": [
        0.36,
        0.3,
        0.28,
        0.31
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.3,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.4,
        24.25,
        24.18,
        24.24
      ]
    },
    "zone": "eas"
  },
  {
    "action": {
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "program_version_after": 0,
      "program_version_before": 0,
      "proposal": {
        "op": "no_change",
        "rationale": "The current program matched the observed stable occupied conditions."
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.31,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.22
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "The occupied hold branch coincided with small temperature and PMV changes.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.33,
      "pmv": [
        0.31,
        0.32,
        0.32,
        0.33
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.0,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.23,
        24.24,
        24.25,
        24.27
      ]
    },
    "zone": "nor"
  },
  {
    "action": {
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "program_version_after": 0,
      "program_version_before": 0,
      "proposal": {
        "op": "no_change",
        "rationale": "Observed comfort headroom and the current program did not support a different atomic edit."
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.39,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.47
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "The occupied hold branch retained positive warm-side headroom under elevated solar input.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.41,
      "pmv": [
        0.39,
        0.4,
        0.4,
        0.41
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.0,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.47,
        24.49,
        24.5,
        24.52
      ]
    },
    "zone": "sou"
  },
  {
    "action": {
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "program_version_after": 0,
      "program_version_before": 0,
      "proposal": {
        "op": "no_change",
        "rationale": "The supplied evidence did not support changing the executable specification this hour."
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.36,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.36
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "Stable actions coincided with a gradual occupied temperature response and bounded PMV.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.38,
      "pmv": [
        0.36,
        0.37,
        0.37,
        0.38
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.0,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.37,
        24.38,
        24.4,
        24.41
      ]
    },
    "zone": "wes"
  }
]
```
### Next-interval Orchestrator working memory

```json
[
  {
    "action": {
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "program_version_after": 0,
      "program_version_before": 0,
      "proposal": {
        "op": "no_change",
        "rationale": "The current program retained occupied comfort headroom without an evidenced beneficial edit."
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.34,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.31
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "Stable setpoints coincided with steady occupied PMV and positive warm-side headroom.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.36,
      "pmv": [
        0.34,
        0.35,
        0.35,
        0.36
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.0,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.3,
        24.32,
        24.34,
        24.35
      ]
    },
    "zone": "cor"
  },
  {
    "action": {
      "actual_setpoints_c": [
        24.7,
        24.7,
        24.7,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "pmv_lower",
        "occupied_hold",
        "occupied_hold",
        "pmv_raise"
      ],
      "program_version_after": 1,
      "program_version_before": 0,
      "proposal": {
        "causal_edge_ids": [
          "ce_ebd13728",
          "ce_660795c7"
        ],
        "consistent_program_direction_proof": {
          "cited_edge_ids": [
            "ce_ebd13728",
            "ce_660795c7"
          ],
          "expected_effects": [
            {
              "direction": "up",
              "node": "power_meters"
            },
            {
              "direction": "down",
              "node": "zone_temp"
            }
          ],
          "mode": "global",
          "program_direction": "down",
          "witness_count": 180
        },
        "expected_effects": [
          {
            "direction": "up",
            "node": "power_meters"
          },
          {
            "direction": "down",
            "node": "zone_temp"
          }
        ],
        "op": "set_param",
        "param": "pmv_band_hi",
        "rationale": "Tighten the active upper PMV threshold while East has the smallest warm-side headroom.",
        "to": 0.4
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.43,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.58
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "A tighter upper threshold preceded a bounded cooling response while occupied PMV stayed within the comfort band.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.36,
      "pmv": [
        0.36,
        0.3,
        0.28,
        0.31
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.3,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.4,
        24.25,
        24.18,
        24.24
      ]
    },
    "zone": "eas"
  },
  {
    "action": {
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "program_version_after": 0,
      "program_version_before": 0,
      "proposal": {
        "op": "no_change",
        "rationale": "The current program matched the observed stable occupied conditions."
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.31,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.22
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "The occupied hold branch coincided with small temperature and PMV changes.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.33,
      "pmv": [
        0.31,
        0.32,
        0.32,
        0.33
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.0,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.23,
        24.24,
        24.25,
        24.27
      ]
    },
    "zone": "nor"
  },
  {
    "action": {
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "program_version_after": 0,
      "program_version_before": 0,
      "proposal": {
        "op": "no_change",
        "rationale": "Observed comfort headroom and the current program did not support a different atomic edit."
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.39,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.47
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "The occupied hold branch retained positive warm-side headroom under elevated solar input.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.41,
      "pmv": [
        0.39,
        0.4,
        0.4,
        0.41
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.0,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.47,
        24.49,
        24.5,
        24.52
      ]
    },
    "zone": "sou"
  },
  {
    "action": {
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "program_version_after": 0,
      "program_version_before": 0,
      "proposal": {
        "op": "no_change",
        "rationale": "The supplied evidence did not support changing the executable specification this hour."
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.36,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.36
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "Stable actions coincided with a gradual occupied temperature response and bounded PMV.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.38,
      "pmv": [
        0.36,
        0.37,
        0.37,
        0.38
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.0,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.37,
        24.38,
        24.4,
        24.41
      ]
    },
    "zone": "wes"
  }
]
```
### Next-interval East Executor working memory

```json
[
  {
    "action": {
      "actual_setpoints_c": [
        24.7,
        24.7,
        24.7,
        25.0
      ],
      "admission": {
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ],
        "status": "accepted"
      },
      "matched_rules": [
        "pmv_lower",
        "occupied_hold",
        "occupied_hold",
        "pmv_raise"
      ],
      "program_version_after": 1,
      "program_version_before": 0,
      "proposal": {
        "causal_edge_ids": [
          "ce_ebd13728",
          "ce_660795c7"
        ],
        "consistent_program_direction_proof": {
          "cited_edge_ids": [
            "ce_ebd13728",
            "ce_660795c7"
          ],
          "expected_effects": [
            {
              "direction": "up",
              "node": "power_meters"
            },
            {
              "direction": "down",
              "node": "zone_temp"
            }
          ],
          "mode": "global",
          "program_direction": "down",
          "witness_count": 180
        },
        "expected_effects": [
          {
            "direction": "up",
            "node": "power_meters"
          },
          {
            "direction": "down",
            "node": "zone_temp"
          }
        ],
        "op": "set_param",
        "param": "pmv_band_hi",
        "rationale": "Tighten the active upper PMV threshold while East has the smallest warm-side headroom.",
        "to": 0.4
      },
      "shield": [
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 168
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 169
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 170
        },
        {
          "actuator_bounds": false,
          "comfort_recovery": false,
          "setpoint_rate_limit": false,
          "step": 171
        }
      ]
    },
    "context": {
      "initial_observation": {
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "last_pmv": 0.43,
        "last_setpoint_c": 25.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "zone_temperature_c": 24.58
      },
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      }
    },
    "hour": 42,
    "lesson": "A tighter upper threshold preceded a bounded cooling response while occupied PMV stayed within the comfort band.",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "occupied_peak_absolute_pmv": 0.36,
      "pmv": [
        0.36,
        0.3,
        0.28,
        0.31
      ],
      "setpoint_direction_reversals": 0,
      "setpoint_total_variation_c": 0.3,
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "zone_temperatures_c": [
        24.4,
        24.25,
        24.18,
        24.24
      ]
    },
    "zone": "eas"
  }
]
```
## 8. Three-regime classification

```json
{
  "observed_by_zone": {
    "cor": [
      "steady_state_occupancy"
    ],
    "eas": [
      "steady_state_occupancy"
    ],
    "nor": [
      "steady_state_occupancy"
    ],
    "sou": [
      "steady_state_occupancy"
    ],
    "wes": [
      "steady_state_occupancy"
    ]
  },
  "registered_regimes": [
    "unoccupied",
    "occupancy_transition",
    "steady_state_occupancy"
  ]
}
```
## 9. Long-term experience read, CRUD and next-interval Executor input

### Store before CRUD

```json
{
  "cor": {
    "occupancy_transition": null,
    "steady_state_occupancy": {
      "experience": "Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.",
      "regime": "steady_state_occupancy",
      "revision": 2
    },
    "unoccupied": null
  },
  "eas": {
    "occupancy_transition": null,
    "steady_state_occupancy": {
      "experience": "East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.",
      "regime": "steady_state_occupancy",
      "revision": 1
    },
    "unoccupied": null
  },
  "nor": {
    "occupancy_transition": null,
    "steady_state_occupancy": null,
    "unoccupied": null
  },
  "sou": {
    "occupancy_transition": null,
    "steady_state_occupancy": {
      "experience": "South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.",
      "regime": "steady_state_occupancy",
      "revision": 2
    },
    "unoccupied": null
  },
  "wes": {
    "occupancy_transition": null,
    "steady_state_occupancy": {
      "experience": "West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.",
      "regime": "steady_state_occupancy",
      "revision": 1
    },
    "unoccupied": null
  }
}
```
### Append-only CRUD audit

```json
[
  {
    "after": {
      "occupancy_transition": null,
      "steady_state_occupancy": {
        "experience": "Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.",
        "regime": "steady_state_occupancy",
        "revision": 2
      },
      "unoccupied": null
    },
    "before": {
      "occupancy_transition": null,
      "steady_state_occupancy": {
        "experience": "Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.",
        "regime": "steady_state_occupancy",
        "revision": 2
      },
      "unoccupied": null
    },
    "hour": 42,
    "requested_operation": {
      "op": "no_change",
      "zone": "cor"
    },
    "status": "accepted",
    "zone": "cor"
  },
  {
    "after": {
      "occupancy_transition": null,
      "steady_state_occupancy": {
        "experience": "East has repeatedly shown limited occupied warm-side comfort headroom and a bounded cooling response after tighter upper-threshold admission.",
        "regime": "steady_state_occupancy",
        "revision": 2
      },
      "unoccupied": null
    },
    "before": {
      "occupancy_transition": null,
      "steady_state_occupancy": {
        "experience": "East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.",
        "regime": "steady_state_occupancy",
        "revision": 1
      },
      "unoccupied": null
    },
    "hour": 42,
    "requested_operation": {
      "expected_revision": 1,
      "experience": "East has repeatedly shown limited occupied warm-side comfort headroom and a bounded cooling response after tighter upper-threshold admission.",
      "op": "replace",
      "regime": "steady_state_occupancy",
      "zone": "eas"
    },
    "status": "accepted",
    "zone": "eas"
  },
  {
    "after": {
      "occupancy_transition": null,
      "steady_state_occupancy": {
        "experience": "North has shown slow occupied temperature and PMV changes under stable setpoints.",
        "regime": "steady_state_occupancy",
        "revision": 1
      },
      "unoccupied": null
    },
    "before": {
      "occupancy_transition": null,
      "steady_state_occupancy": null,
      "unoccupied": null
    },
    "hour": 42,
    "requested_operation": {
      "experience": "North has shown slow occupied temperature and PMV changes under stable setpoints.",
      "op": "add",
      "regime": "steady_state_occupancy",
      "zone": "nor"
    },
    "status": "accepted",
    "zone": "nor"
  },
  {
    "after": {
      "occupancy_transition": null,
      "steady_state_occupancy": {
        "experience": "South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.",
        "regime": "steady_state_occupancy",
        "revision": 2
      },
      "unoccupied": null
    },
    "before": {
      "occupancy_transition": null,
      "steady_state_occupancy": {
        "experience": "South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.",
        "regime": "steady_state_occupancy",
        "revision": 2
      },
      "unoccupied": null
    },
    "hour": 42,
    "requested_operation": {
      "op": "no_change",
      "zone": "sou"
    },
    "status": "accepted",
    "zone": "sou"
  },
  {
    "after": {
      "occupancy_transition": null,
      "steady_state_occupancy": {
        "experience": "West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.",
        "regime": "steady_state_occupancy",
        "revision": 1
      },
      "unoccupied": null
    },
    "before": {
      "occupancy_transition": null,
      "steady_state_occupancy": {
        "experience": "West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.",
        "regime": "steady_state_occupancy",
        "revision": 1
      },
      "unoccupied": null
    },
    "hour": 42,
    "requested_operation": {
      "op": "no_change",
      "zone": "wes"
    },
    "status": "accepted",
    "zone": "wes"
  }
]
```
### Store after CRUD

```json
{
  "cor": {
    "occupancy_transition": null,
    "steady_state_occupancy": {
      "experience": "Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.",
      "regime": "steady_state_occupancy",
      "revision": 2
    },
    "unoccupied": null
  },
  "eas": {
    "occupancy_transition": null,
    "steady_state_occupancy": {
      "experience": "East has repeatedly shown limited occupied warm-side comfort headroom and a bounded cooling response after tighter upper-threshold admission.",
      "regime": "steady_state_occupancy",
      "revision": 2
    },
    "unoccupied": null
  },
  "nor": {
    "occupancy_transition": null,
    "steady_state_occupancy": {
      "experience": "North has shown slow occupied temperature and PMV changes under stable setpoints.",
      "regime": "steady_state_occupancy",
      "revision": 1
    },
    "unoccupied": null
  },
  "sou": {
    "occupancy_transition": null,
    "steady_state_occupancy": {
      "experience": "South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.",
      "regime": "steady_state_occupancy",
      "revision": 2
    },
    "unoccupied": null
  },
  "wes": {
    "occupancy_transition": null,
    "steady_state_occupancy": {
      "experience": "West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.",
      "regime": "steady_state_occupancy",
      "revision": 1
    },
    "unoccupied": null
  }
}
```
### Complete next-interval East Executor request

```json
{
  "messages": [
    {
      "content": "ROLE\nMaintain one zone's control specification.\n\nDECISION\nUse the current observation, comfort headroom, causal evidence, allowance and WORKING MEMORY to propose one atomic operation. Seek energy savings with |PMV| ≤ 0.5. Do not predict interpreter output.\n\nHARD BOUNDARIES\nFor an accepted program change, charge_c = max over proof states of max(0, setpoint_before_c - setpoint_after_c); it is not cumulative action, power or pre-cooling offset. Edit only through the control specification and operation contract; do not output a direct setpoint.\n\nOUTPUT\nReturn bare JSON {\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}. memory_refs cites only active experiences used and may be empty. No prose, fence or extra fields. Operation contract:\npatch: list of exactly one operation.\nCommon required fields: op, rationale.\nModifying operation also requires causal_edge_ids.\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule: id, when, then. when item: field, op, value. then: op, plus value for set_residual or step_setpoint.\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 15:00\ncontrol_interval: [15:00, 16:00)\naction_times: [\"15:00\",\"15:15\",\"15:30\",\"15:45\"]\nforecast_outcome_times: [\"15:15\",\"15:30\",\"15:45\",\"16:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: eas\nzone_temperature_c: 24.24\npmv: 0.31\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.34\ntemp_drop_to_cool_pmv_edge_c: 2.72\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\ncommon:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 15:15 | 31.6 | 628.0 |\n| 15:30 | 31.8 | 646.0 |\n| 15:45 | 32.0 | 668.0 |\n| 16:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 1\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.4 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":1.7,\"shared_unreserved_allowance_c\":4.0,\"shared_priority_rank\":1}\n\n### WORKING MEMORY\ncompleted_interval: [14:00, 15:00)\nzones: [\"eas\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.1214,\"site_energy_kwh\":21.9425}\ncompleted_decision:\ncommon:\naction: {\"proposal\":{\"op\":\"set_param\",\"rationale\":\"Tighten the active upper PMV threshold while East has the smallest warm-side headroom.\",\"param\":\"pmv_band_hi\",\"to\":0.4},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":1}\nlesson: A tighter upper threshold preceded a bounded cooling response while occupied PMV stayed within the comfort band.\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nrecent_state_history:\ncommon:\noccupancy: 1.0\nstate_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\ntime_varying_measurements:\n| state_time | eas.temp_c | eas.pmv | eas.setpoint_c |\n| --- | --- | --- | --- |\n| 14:00 | 24.58 | 0.43 | 25.0 |\n| 14:15 | 24.4 | 0.36 | 24.7 |\n| 14:30 | 24.25 | 0.3 | 24.7 |\n| 14:45 | 24.18 | 0.28 | 24.7 |\ncontrol_action_history:\ncommon:\nregime: steady_state_occupancy\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time | eas.setpoint_c | eas.matched_rule |\n| --- | --- | --- | --- |\n| 14:00 | 14:15 | 24.7 | pmv_lower |\n| 14:15 | 14:30 | 24.7 | occupied_hold |\n| 14:30 | 14:45 | 24.7 | occupied_hold |\n| 14:45 | 15:00 | 25.0 | pmv_raise |\nterminal_outcome_state: shown once in the current-state section at 15:00\nprevious_decision_forecast:\ncommon:\noccupancy: 1.0\nzones: [\"eas\"]\noutcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\nderived_feature_interval: [14:00, 15:00)\nderived_features:\ncommon:\ntemp_delta_15min_c: 0.06\ntemp_delta_1h_c: -0.34\ntemp_slope_c_per_hour: -0.34\npmv_delta_15min: 0.03\npmv_delta_1h: -0.12\nsetpoint_delta_15min_c: 0.3\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.36\nsetpoint_tv_c: 0.3\nsetpoint_reversals: 0\n\n### ACTIVE LONG-TERM EXPERIENCES\ncommon:\nrevision: 2\nexperience: East has repeatedly shown limited occupied warm-side comfort headroom and a bounded cooling response after tighter upper-threshold admission.\nrows:\n| regime |\n| --- |\n| steady_state_occupancy |\n",
      "role": "user"
    }
  ],
  "model": "deepseek-v4-flash",
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "thinking": {
    "type": "enabled"
  }
}
```
## 10. Memory-off exact contract and disappearing fields

```json
{
  "executor_output_removed": [
    "memory_refs"
  ],
  "executor_system_removed": [
    "long-term experience semantics",
    "memory_refs"
  ],
  "executor_user_removed": [
    "ACTIVE LONG-TERM EXPERIENCES"
  ],
  "orchestrator_removed": [],
  "reflector_output_removed": [
    "memory_operations"
  ],
  "reflector_system_removed": [
    "three-regime comparison",
    "CRUD operation contract"
  ],
  "reflector_user_removed": [
    "ELIGIBLE LONG-TERM EXPERIENCE SLOTS"
  ],
  "runtime_output_removed": [
    "long-term CRUD rows",
    "Executor memory-reference audit"
  ],
  "working_memory_retained": true
}
```
### Memory-off East Executor complete request

```json
{
  "messages": [
    {
      "content": "ROLE\nMaintain one zone's control specification.\n\nDECISION\nUse the current observation, comfort headroom, causal evidence, allowance and WORKING MEMORY to propose one atomic operation. Seek energy savings with |PMV| ≤ 0.5. Do not predict interpreter output.\n\nHARD BOUNDARIES\nFor an accepted program change, charge_c = max over proof states of max(0, setpoint_before_c - setpoint_after_c); it is not cumulative action, power or pre-cooling offset. Edit only through the control specification and operation contract; do not output a direct setpoint.\n\nOUTPUT\nReturn exactly one bare root JSON object: {\"patch\":[{...}]}. Return no prose, Markdown fence or unknown fields. Operation contract:\npatch: list of exactly one operation.\nCommon required fields: op, rationale.\nModifying operation also requires causal_edge_ids.\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule: id, when, then. when item: field, op, value. then: op, plus value for set_residual or step_setpoint.\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: eas\nzone_temperature_c: 24.58\npmv: 0.43\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.34\ntemp_drop_to_cool_pmv_edge_c: 2.72\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\ncommon:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":2.0,\"shared_unreserved_allowance_c\":4.0,\"shared_priority_rank\":1}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"eas\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\ncommon:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: Stable occupied conditions coincided with positive warm-side comfort headroom.\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nrecent_state_history:\ncommon:\ntemp_c: 24.58\npmv: 0.43\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\ncontrol_action_history:\ncommon:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nterminal_outcome_state: shown once in the current-state section at 14:00\nprevious_decision_forecast:\ncommon:\noccupancy: 1.0\nzones: [\"eas\"]\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\ncommon:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.43\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n",
      "role": "user"
    }
  ],
  "model": "deepseek-v4-flash",
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "thinking": {
    "type": "enabled"
  }
}
```
### Memory-off East Executor output

```json
{
  "patch": [
    {
      "causal_edge_ids": [
        "ce_ebd13728"
      ],
      "op": "set_param",
      "param": "pmv_band_hi",
      "rationale": "Tighten the active upper PMV threshold while East has the smallest warm-side headroom.",
      "to": 0.4
    }
  ]
}
```
### Memory-off Reflector complete request

```json
{
  "messages": [
    {
      "content": "ROLE\nInterpret the deterministic results for the supplied completed control interval.\n\nEVIDENCE\nFrom each zone's completed Context, Action and Outcome, derive one Lesson that captures a useful observed relationship or trade-off for later control.\n\nHARD BOUNDARIES\nGround each Lesson in the completed-interval evidence. Express an observation, relationship or trade-off rather than an action command, target or unsupported causal claim.\n\nOUTPUT\nReturn one bare JSON object of the form {\"hourly_lessons\":[{\"zone\":...,\"lesson\":...}]}. Include every supplied zone exactly once. Return no prose, Markdown fence or unknown fields.\n",
      "role": "system"
    },
    {
      "content": "### COMPLETED CONTROL INTERVAL\ninterval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\noutcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.1214,\"site_energy_kwh\":21.9425}\ncompleted_decision:\ncommon:\naction: {\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0}\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nrows:\n| zone | op | rationale | program_version_after |\n| --- | --- | --- | --- |\n| cor | no_change | The current program retained occupied comfort headroom without an evidenced beneficial edit. | 0 |\n| nor | no_change | The current program matched the observed stable occupied conditions. | 0 |\n| sou | no_change | Observed comfort headroom and the current program did not support a different atomic edit. | 0 |\n| wes | no_change | The supplied evidence did not support changing the executable specification this hour. | 0 |\n| zone | op | rationale | program_version_after | param | to |\n| --- | --- | --- | --- | --- | --- |\n| eas | set_param | Tighten the active upper PMV threshold while East has the smallest warm-side headroom. | 1 | pmv_band_hi | 0.4 |\nrecent_state_history:\ncommon:\noccupancy: 1.0\nconstant_by_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0}\n{\"zone\":\"nor\",\"setpoint_c\":25.0}\n{\"zone\":\"sou\",\"setpoint_c\":25.0}\n{\"zone\":\"wes\",\"setpoint_c\":25.0}\nstate_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ntime_varying_measurements:\n| state_time | cor.temp_c | cor.pmv | eas.temp_c | eas.pmv | eas.setpoint_c | nor.temp_c | nor.pmv | sou.temp_c | sou.pmv | wes.temp_c | wes.pmv |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 14:00 | 24.31 | 0.34 | 24.58 | 0.43 | 25.0 | 24.22 | 0.31 | 24.47 | 0.39 | 24.36 | 0.36 |\n| 14:15 | 24.3 | 0.34 | 24.4 | 0.36 | 24.7 | 24.23 | 0.31 | 24.47 | 0.39 | 24.37 | 0.36 |\n| 14:30 | 24.32 | 0.35 | 24.25 | 0.3 | 24.7 | 24.24 | 0.32 | 24.49 | 0.4 | 24.38 | 0.37 |\n| 14:45 | 24.34 | 0.35 | 24.18 | 0.28 | 24.7 | 24.25 | 0.32 | 24.5 | 0.4 | 24.4 | 0.37 |\n| 15:00 | 24.35 | 0.36 | 24.24 | 0.31 | 25.0 | 24.27 | 0.33 | 24.52 | 0.41 | 24.41 | 0.38 |\ncontrol_action_history:\ncommon:\nregime: steady_state_occupancy\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\nconstant_by_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"nor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"sou\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"wes\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\ntime_varying_actions:\n| action_time | outcome_time | eas.setpoint_c | eas.matched_rule |\n| --- | --- | --- | --- |\n| 14:00 | 14:15 | 24.7 | pmv_lower |\n| 14:15 | 14:30 | 24.7 | occupied_hold |\n| 14:30 | 14:45 | 24.7 | occupied_hold |\n| 14:45 | 15:00 | 25.0 | pmv_raise |\nprevious_decision_forecast:\ncommon:\noccupancy: 1.0\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\noutcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\nderived_feature_interval: [14:00, 15:00)\nderived_features:\ncommon:\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\nsetpoint_reversals: 0\nrows:\n| zone | temp_delta_15min_c | temp_delta_1h_c | temp_slope_c_per_hour | pmv_delta_15min | pmv_delta_1h | setpoint_delta_15min_c | occupied_peak_abs_pmv | setpoint_tv_c |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| cor | 0.01 | 0.04 | 0.04 | 0.01 | 0.02 | 0.0 | 0.36 | 0.0 |\n| eas | 0.06 | -0.34 | -0.34 | 0.03 | -0.12 | 0.3 | 0.36 | 0.3 |\n| nor | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.33 | 0.0 |\n| sou | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.41 | 0.0 |\n| wes | 0.01 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.38 | 0.0 |\n",
      "role": "user"
    }
  ],
  "model": "deepseek-v4-flash",
  "reasoning_effort": "low",
  "response_format": {
    "type": "json_object"
  },
  "thinking": {
    "type": "enabled"
  }
}
```
### Memory-off Reflector output

```json
{
  "hourly_lessons": [
    {
      "lesson": "Stable setpoints coincided with steady occupied PMV and positive warm-side headroom.",
      "zone": "cor"
    },
    {
      "lesson": "A tighter upper threshold preceded a bounded cooling response while occupied PMV stayed within the comfort band.",
      "zone": "eas"
    },
    {
      "lesson": "The occupied hold branch coincided with small temperature and PMV changes.",
      "zone": "nor"
    },
    {
      "lesson": "The occupied hold branch retained positive warm-side headroom under elevated solar input.",
      "zone": "sou"
    },
    {
      "lesson": "Stable actions coincided with a gradual occupied temperature response and bounded PMV.",
      "zone": "wes"
    }
  ]
}
```
## 11. Canonical human views and audit hashes

### Orchestrator expanded canonical input

### DECISION WINDOW
current_time: 14:00
control_interval: [14:00, 15:00)
action_times: ["14:00","14:15","14:30","14:45"]
forecast_outcome_times: ["14:15","14:30","14:45","15:00"]
control_period: 15 min
coordination_period: 60 min

### CURRENT SITE STATE
outdoor_temp_c: 31.4
solar_irr: 612.0
price_now: 0.14231

### FORECAST SUMMARY
outdoor_temp_change_next_1h_c: 0.8
solar_irr_max_next_1h_w_m2: 668.0
solar_irr_mean_next_1h_w_m2: 642.5
price_at_interval_end: 0.16842

### SITE FORECAST
rows:
| forecast_outcome_time | outdoor_temp_c | solar_irr |
| --- | --- | --- |
| 14:15 | 31.6 | 628.0 |
| 14:30 | 31.8 | 646.0 |
| 14:45 | 32.0 | 668.0 |
| 15:00 | 32.2 | 628.0 |

### CURRENT ZONE STATE
common:
occupancy: 1.0
setpoint_c: 25.0
rows:
| zone | temp_c | pmv | temp_rise_to_warm_pmv_edge_c | temp_drop_to_cool_pmv_edge_c |
| --- | --- | --- | --- | --- |
| cor | 24.31 | 0.34 | 0.62 | 2.45 |
| eas | 24.58 | 0.43 | 0.34 | 2.72 |
| nor | 24.22 | 0.31 | 0.72 | 2.36 |
| sou | 24.47 | 0.39 | 0.45 | 2.61 |
| wes | 24.36 | 0.36 | 0.57 | 2.5 |

### ZONE CONTROL CONTEXT
common:
occupancy_at_interval_end: 1.0
precool_offset_from_unoccupied_base_c: -5.0
resulting_precool_setpoint_c: 25.0
rows:
| zone |
| --- |
| cor |
| eas |
| nor |
| sou |
| wes |

### CAUSAL EVIDENCE
common:
target: power_meters
undirected: false
rows:
| id | source | relation | tags_1 | tags_2 |
| --- | --- | --- | --- | --- |
| ce_e8f5f362 | outdoor_temp | Positive Corr | Delayed | Strong Impact |
| ce_5a968228 | solar_irr | Positive Corr | Delayed | Weak Impact |
| ce_00f91137 | occupancy | Positive Corr | Delayed | Strong Impact |
| ce_660795c7 | cooling_setpoint | Negative Corr | Immediate | Strong Impact |

### ALLOCATION LIMITS
zones: ["cor","eas","nor","sou","wes"]
site_cap_c: 10.0
per_zone_cap_c: 5.0

### CONTROL DOMAIN
domain_id: cooling
controlled_setpoint: zone cooling setpoint
unit: degC
hard_bounds_c: [20.0,30.0]
occupied_base_c: 25.0
unoccupied_base_c: 30.0
abs_pmv_score_limit: 0.5
preconditioning: {"label":"precool","lead_steps":4,"target_c":25.0}
energy_intensive_setpoint_direction: decrease

### WORKING MEMORY
completed_interval: [13:00, 14:00)
zones: ["cor","eas","nor","sou","wes"]
control_period: 15 min
site_result: {"site_cost":3.02,"site_energy_kwh":21.1}
completed_decision:
common:
action: {"proposal":{"op":"no_change","rationale":"completed-interval fixture"},"admission":{"status":"accepted"},"program_version_before":0,"program_version_after":0}
lesson: Stable occupied conditions coincided with positive warm-side comfort headroom.
context: {"initial_observation":{"last_occupancy":1.0}}
recent_state_history:
common:
occupancy: 1.0
setpoint_c: 25.0
constant_by_zone:
{"zone":"cor","temp_c":24.31,"pmv":0.34}
{"zone":"eas","temp_c":24.58,"pmv":0.43}
{"zone":"nor","temp_c":24.22,"pmv":0.31}
{"zone":"sou","temp_c":24.47,"pmv":0.39}
{"zone":"wes","temp_c":24.36,"pmv":0.36}
state_times: ["13:00","13:15","13:30","13:45"]
control_action_history:
common:
regime: steady_state_occupancy
setpoint_c: 25.0
matched_rule: occupied_hold
actuator_bounds: false
setpoint_rate_limit: false
comfort_recovery: false
time_varying_actions:
| action_time | outcome_time |
| --- | --- |
| 13:00 | 13:15 |
| 13:15 | 13:30 |
| 13:30 | 13:45 |
| 13:45 | 14:00 |
terminal_outcome_state: shown once in the current-state section at 14:00
previous_decision_forecast:
common:
occupancy: 1.0
zones: ["cor","eas","nor","sou","wes"]
outcome_times: ["13:15","13:30","13:45","14:00"]
derived_feature_interval: [13:00, 14:00)
derived_features:
common:
temp_delta_15min_c: 0.0
temp_delta_1h_c: 0.0
temp_slope_c_per_hour: 0.0
pmv_delta_15min: 0.0
pmv_delta_1h: 0.0
setpoint_delta_15min_c: 0.0
setpoint_delta_1h_c: 0.0
discomfort_zone_h: 0.0
discomfort_pmv_h: 0.0
setpoint_tv_c: 0.0
setpoint_reversals: 0
rows:
| zone | occupied_peak_abs_pmv |
| --- | --- |
| cor | 0.34 |
| eas | 0.43 |
| nor | 0.31 |
| sou | 0.39 |
| wes | 0.36 |

### PREVIOUS BUDGET USE
site_cap_c: 10.0
reserved_allowance_by_zone_c: {"cor":1.0,"eas":2.0,"nor":1.0,"sou":1.0,"wes":1.0}
reserved_consumption_by_zone_c: {"cor":0.0,"eas":2.0,"nor":0.0,"sou":0.0,"wes":0.0}
total_reserved_allowance_c: 6.0
total_reserved_consumption_c: 2.0
reserved_utilisation: 0.3333
initial_shared_unreserved_pool_c: 4.0
shared_pool_consumption_by_zone_c: {"eas":0.3}
remaining_shared_unreserved_pool_c: 3.7
previous_priority: ["eas","sou","wes","cor","nor"]
previous_rationale_per_zone: {"cor":"Core conditions were stable.","eas":"East had the smallest warm-side headroom.","nor":"North conditions were stable.","sou":"South had moderate warm-side headroom.","wes":"West had moderate warm-side headroom."}
### Orchestrator audit view

```json
{
  "canonical_sha256": "1c7b71656e8a1be2985ebad11542f64a647f53e3b0e50342df7937be5415d9da",
  "compact_sha256": "6b4c33066de0356adb7bceb557fe67fabe06385f9165a120d7f4aa967ee96f93",
  "field_manifest": {
    "ALLOCATION LIMITS": [
      "/zones/[]",
      "/site_cap_c",
      "/per_zone_cap_c"
    ],
    "CAUSAL EVIDENCE": [
      "/[]/id",
      "/[]/source",
      "/[]/relation",
      "/[]/target",
      "/[]/tags/[]",
      "/[]/undirected"
    ],
    "CONTROL DOMAIN": [
      "/domain_id",
      "/controlled_setpoint",
      "/unit",
      "/hard_bounds_c/[]",
      "/occupied_base_c",
      "/unoccupied_base_c",
      "/abs_pmv_score_limit",
      "/preconditioning/label",
      "/preconditioning/lead_steps",
      "/preconditioning/target_c",
      "/energy_intensive_setpoint_direction"
    ],
    "CURRENT SITE STATE": [
      "/outdoor_temp_c",
      "/solar_irr",
      "/price_now"
    ],
    "CURRENT ZONE STATE": [
      "/[]/zone",
      "/[]/zone_temperature_c",
      "/[]/pmv",
      "/[]/occupancy",
      "/[]/setpoint_c",
      "/[]/temp_rise_to_warm_pmv_edge_c",
      "/[]/temp_drop_to_cool_pmv_edge_c"
    ],
    "DECISION WINDOW": [
      "/current_time",
      "/control_interval",
      "/action_times/[]",
      "/forecast_outcome_times/[]",
      "/control_period",
      "/coordination_period"
    ],
    "FORECAST SUMMARY": [
      "/outdoor_temp_change_next_1h_c",
      "/solar_irr_max_next_1h_w_m2",
      "/solar_irr_mean_next_1h_w_m2",
      "/price_at_interval_end"
    ],
    "PREVIOUS BUDGET USE": [
      "/site_cap_c",
      "/reserved_allowance_by_zone_c/cor",
      "/reserved_allowance_by_zone_c/eas",
      "/reserved_allowance_by_zone_c/nor",
      "/reserved_allowance_by_zone_c/sou",
      "/reserved_allowance_by_zone_c/wes",
      "/reserved_consumption_by_zone_c/cor",
      "/reserved_consumption_by_zone_c/eas",
      "/reserved_consumption_by_zone_c/nor",
      "/reserved_consumption_by_zone_c/sou",
      "/reserved_consumption_by_zone_c/wes",
      "/total_reserved_allowance_c",
      "/total_reserved_consumption_c",
      "/reserved_utilisation",
      "/initial_shared_unreserved_pool_c",
      "/shared_pool_consumption_by_zone_c/eas",
      "/remaining_shared_unreserved_pool_c",
      "/previous_priority/[]",
      "/previous_rationale_per_zone/cor",
      "/previous_rationale_per_zone/eas",
      "/previous_rationale_per_zone/nor",
      "/previous_rationale_per_zone/sou",
      "/previous_rationale_per_zone/wes"
    ],
    "SITE FORECAST": [
      "/[]/forecast_outcome_time",
      "/[]/outdoor_temp_c",
      "/[]/solar_irr"
    ],
    "WORKING MEMORY": [
      "/[]/hour",
      "/[]/zone",
      "/[]/context/regime_step_coverage/steady_state_occupancy/[]",
      "/[]/context/initial_observation/zone_temperature_c",
      "/[]/context/initial_observation/current_occupancy",
      "/[]/context/initial_observation/last_occupancy",
      "/[]/context/initial_observation/occupancy_next_steps/[]",
      "/[]/context/initial_observation/last_pmv",
      "/[]/context/initial_observation/last_setpoint_c",
      "/[]/action/proposal/op",
      "/[]/action/proposal/rationale",
      "/[]/action/admission/status",
      "/[]/action/admission/completed_validation_stages/[]",
      "/[]/action/program_version_before",
      "/[]/action/program_version_after",
      "/[]/action/actual_setpoints_c/[]",
      "/[]/action/matched_rules/[]",
      "/[]/action/shield/[]/step",
      "/[]/action/shield/[]/actuator_bounds",
      "/[]/action/shield/[]/setpoint_rate_limit",
      "/[]/action/shield/[]/comfort_recovery",
      "/[]/outcome/zone_temperatures_c/[]",
      "/[]/outcome/pmv/[]",
      "/[]/outcome/effective_occupancy/[]",
      "/[]/outcome/site_cost",
      "/[]/outcome/site_energy_kwh",
      "/[]/outcome/discomfort_zone_hours",
      "/[]/outcome/discomfort_pmv_hours",
      "/[]/outcome/occupied_peak_absolute_pmv",
      "/[]/outcome/setpoint_total_variation_c",
      "/[]/outcome/setpoint_direction_reversals",
      "/[]/lesson"
    ],
    "ZONE CONTROL CONTEXT": [
      "/[]/zone",
      "/[]/occupancy_at_interval_end",
      "/[]/precool_offset_from_unoccupied_base_c",
      "/[]/resulting_precool_setpoint_c"
    ]
  },
  "internal_context": {
    "decision_hour": 42,
    "decision_time_seconds": 17503200
  },
  "internal_coordinates": [
    {
      "path": "/WORKING MEMORY/[]/hour",
      "value": 41
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 164
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 165
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 166
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 167
    },
    {
      "path": "/WORKING MEMORY/[]/hour",
      "value": 41
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 164
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 165
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 166
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 167
    },
    {
      "path": "/WORKING MEMORY/[]/hour",
      "value": 41
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 164
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 165
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 166
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 167
    },
    {
      "path": "/WORKING MEMORY/[]/hour",
      "value": 41
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 164
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 165
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 166
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 167
    },
    {
      "path": "/WORKING MEMORY/[]/hour",
      "value": 41
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 164
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 165
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 166
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 167
    }
  ],
  "round_trip_equal": true,
  "schema": "h3c_context_audit_v1"
}
```
### East Executor expanded canonical input

### DECISION WINDOW
current_time: 14:00
control_interval: [14:00, 15:00)
action_times: ["14:00","14:15","14:30","14:45"]
forecast_outcome_times: ["14:15","14:30","14:45","15:00"]
control_period: 15 min
coordination_period: 60 min

### CURRENT DECISION STATE
zone: eas
zone_temperature_c: 24.58
pmv: 0.43
occupancy: 1.0
setpoint_c: 25.0
temp_rise_to_warm_pmv_edge_c: 0.34
temp_drop_to_cool_pmv_edge_c: 2.72

### OCCUPANCY TRANSITION CONTEXT
previous_occupancy: 1.0

### CURRENT EXTERNAL STATE
outdoor_temp_c: 31.4
solar_irr: 612.0
price_now: 0.14231

### FORECAST SUMMARY
outdoor_temp_change_next_1h_c: 0.8
solar_irr_max_next_1h_w_m2: 668.0
solar_irr_mean_next_1h_w_m2: 642.5

### ZONE FORECAST
common:
occupancy: 1.0
rows:
| forecast_outcome_time | outdoor_temp_c | solar_irr |
| --- | --- | --- |
| 14:15 | 31.6 | 628.0 |
| 14:30 | 31.8 | 646.0 |
| 14:45 | 32.0 | 668.0 |
| 15:00 | 32.2 | 628.0 |

### CONTROL SPECIFICATION
program_version: 0
parameters:
| param | current | min | max | source |
| --- | --- | --- | --- | --- |
| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |
| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |
| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |
| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |
| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |
rules:
common_when: {"field":"occupied_now","op":"==","value":0}
{"id":"precool","when":[{"field":"precool_due","op":"==","value":1}],"then":{"op":"set_residual","value":{"param":"precool_residual_c"}}}
{"id":"unoccupied_hold","when":[],"then":{"op":"set_residual","value":0.0}}
common_when: {"field":"occupied_now","op":"==","value":1}
{"id":"pmv_raise","when":[{"field":"last_pmv","op":"<","value":{"param":"pmv_band_lo"}}],"then":{"op":"step_setpoint","value":{"param":"pmv_step_c"}}}
{"id":"pmv_lower","when":[{"field":"last_pmv","op":">","value":{"param":"pmv_band_hi"}}],"then":{"op":"step_setpoint","value":{"neg_param":"pmv_step_c"}}}
{"id":"anchor","when":[{"field":"occupied_last","op":"==","value":0}],"then":{"op":"set_residual","value":0.0}}
{"id":"occupied_hold","when":[],"then":{"op":"hold_setpoint"}}
rule_value_references: {"param":"named parameter value","neg_param":"negative named parameter value"}
rule_and_weather_limits: {"new_rule":{"condition_fields":["last_pmv","occupied_last","occupied_now","outdoor_temp_change_next_1h_c","precool_due","solar_irr_max_next_1h_w_m2","solar_irr_mean_next_1h_w_m2"],"comparisons":["<","<=",">",">=","==","!="],"comparison_value":"number or parameter name","action_types":["set_residual","step_setpoint","hold_setpoint"],"max_rules":8},"weather_literals":{"must_be":"finite numbers","parameter_refs":"forbidden"}}
control_domain: {"domain_id":"cooling","controlled_setpoint":"zone cooling setpoint","unit":"degC","hard_bounds_c":[20.0,30.0],"occupied_base_c":25.0,"unoccupied_base_c":30.0,"abs_pmv_score_limit":0.5,"preconditioning":{"label":"precool","lead_steps":4,"target_c":25.0},"energy_intensive_setpoint_direction":"decrease"}

### CAUSAL EVIDENCE
common:
undirected: false
rows:
| id | source | relation | target | tags_1 | tags_2 |
| --- | --- | --- | --- | --- | --- |
| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |
| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |
| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |
| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |
| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |
| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |
| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |
| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |

### ALLOCATION
allocation: {"zone_reserved_allowance_c":2.0,"shared_unreserved_allowance_c":4.0,"shared_priority_rank":1}

### WORKING MEMORY
completed_interval: [13:00, 14:00)
zones: ["eas"]
control_period: 15 min
site_result: {"site_cost":3.02,"site_energy_kwh":21.1}
completed_decision:
common:
action: {"proposal":{"op":"no_change","rationale":"completed-interval fixture"},"admission":{"status":"accepted"},"program_version_before":0,"program_version_after":0}
lesson: Stable occupied conditions coincided with positive warm-side comfort headroom.
context: {"initial_observation":{"last_occupancy":1.0}}
recent_state_history:
common:
temp_c: 24.58
pmv: 0.43
occupancy: 1.0
setpoint_c: 25.0
state_times: ["13:00","13:15","13:30","13:45"]
control_action_history:
common:
regime: steady_state_occupancy
setpoint_c: 25.0
matched_rule: occupied_hold
actuator_bounds: false
setpoint_rate_limit: false
comfort_recovery: false
time_varying_actions:
| action_time | outcome_time |
| --- | --- |
| 13:00 | 13:15 |
| 13:15 | 13:30 |
| 13:30 | 13:45 |
| 13:45 | 14:00 |
terminal_outcome_state: shown once in the current-state section at 14:00
previous_decision_forecast:
common:
occupancy: 1.0
zones: ["eas"]
outcome_times: ["13:15","13:30","13:45","14:00"]
derived_feature_interval: [13:00, 14:00)
derived_features:
common:
temp_delta_15min_c: 0.0
temp_delta_1h_c: 0.0
temp_slope_c_per_hour: 0.0
pmv_delta_15min: 0.0
pmv_delta_1h: 0.0
setpoint_delta_15min_c: 0.0
setpoint_delta_1h_c: 0.0
discomfort_zone_h: 0.0
discomfort_pmv_h: 0.0
occupied_peak_abs_pmv: 0.43
setpoint_tv_c: 0.0
setpoint_reversals: 0

### ACTIVE LONG-TERM EXPERIENCES
common:
revision: 1
experience: East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.
rows:
| regime |
| --- |
| steady_state_occupancy |
### East Executor audit view

```json
{
  "canonical_sha256": "6b507ee6816aaac96f0c368e7b3d91c5a960d144d54bb1d3bc4aa2c476bd053c",
  "compact_sha256": "d51b5ae3a515856eb253634a06a9eea8110b81c2a1a3594692de2d5147f6ff1b",
  "field_manifest": {
    "ACTIVE LONG-TERM EXPERIENCES": [
      "/[]/regime",
      "/[]/revision",
      "/[]/experience"
    ],
    "ALLOCATION": [
      "/allocation/zone_reserved_allowance_c",
      "/allocation/shared_unreserved_allowance_c",
      "/allocation/shared_priority_rank"
    ],
    "CAUSAL EVIDENCE": [
      "/[]/id",
      "/[]/source",
      "/[]/relation",
      "/[]/target",
      "/[]/tags/[]",
      "/[]/undirected"
    ],
    "CONTROL SPECIFICATION": [
      "/program_version",
      "/parameters/[]/param",
      "/parameters/[]/current",
      "/parameters/[]/min",
      "/parameters/[]/max",
      "/parameters/[]/bounds_source",
      "/rules/[]/id",
      "/rules/[]/when/[]/field",
      "/rules/[]/when/[]/op",
      "/rules/[]/when/[]/value",
      "/rules/[]/then/op",
      "/rules/[]/then/value/param",
      "/rules/[]/when/[]/value/param",
      "/rules/[]/then/value/neg_param",
      "/rules/[]/then/value",
      "/rule_value_references/param",
      "/rule_value_references/neg_param",
      "/rule_and_weather_limits/a_rule_you_add/conditions_may_test/[]",
      "/rule_and_weather_limits/a_rule_you_add/comparisons/[]",
      "/rule_and_weather_limits/a_rule_you_add/compared_against",
      "/rule_and_weather_limits/a_rule_you_add/actions/[]",
      "/rule_and_weather_limits/a_rule_you_add/most_rules_at_once",
      "/rule_and_weather_limits/weather_condition_values/must_be",
      "/rule_and_weather_limits/weather_condition_values/parameter_references",
      "/control_domain/domain_id",
      "/control_domain/controlled_setpoint",
      "/control_domain/unit",
      "/control_domain/hard_bounds_c/[]",
      "/control_domain/occupied_base_c",
      "/control_domain/unoccupied_base_c",
      "/control_domain/abs_pmv_score_limit",
      "/control_domain/preconditioning/label",
      "/control_domain/preconditioning/lead_steps",
      "/control_domain/preconditioning/target_c",
      "/control_domain/energy_intensive_setpoint_direction"
    ],
    "CURRENT DECISION STATE": [
      "/zone",
      "/zone_temperature_c",
      "/pmv",
      "/occupancy",
      "/setpoint_c",
      "/temp_rise_to_warm_pmv_edge_c",
      "/temp_drop_to_cool_pmv_edge_c"
    ],
    "CURRENT EXTERNAL STATE": [
      "/outdoor_temp_c",
      "/solar_irr",
      "/price_now"
    ],
    "DECISION WINDOW": [
      "/current_time",
      "/control_interval",
      "/action_times/[]",
      "/forecast_outcome_times/[]",
      "/control_period",
      "/coordination_period"
    ],
    "FORECAST SUMMARY": [
      "/outdoor_temp_change_next_1h_c",
      "/solar_irr_max_next_1h_w_m2",
      "/solar_irr_mean_next_1h_w_m2"
    ],
    "OCCUPANCY TRANSITION CONTEXT": [
      "/previous_occupancy"
    ],
    "WORKING MEMORY": [
      "/[]/hour",
      "/[]/zone",
      "/[]/context/regime_step_coverage/steady_state_occupancy/[]",
      "/[]/context/initial_observation/zone_temperature_c",
      "/[]/context/initial_observation/current_occupancy",
      "/[]/context/initial_observation/last_occupancy",
      "/[]/context/initial_observation/occupancy_next_steps/[]",
      "/[]/context/initial_observation/last_pmv",
      "/[]/context/initial_observation/last_setpoint_c",
      "/[]/action/proposal/op",
      "/[]/action/proposal/rationale",
      "/[]/action/admission/status",
      "/[]/action/admission/completed_validation_stages/[]",
      "/[]/action/program_version_before",
      "/[]/action/program_version_after",
      "/[]/action/actual_setpoints_c/[]",
      "/[]/action/matched_rules/[]",
      "/[]/action/shield/[]/step",
      "/[]/action/shield/[]/actuator_bounds",
      "/[]/action/shield/[]/setpoint_rate_limit",
      "/[]/action/shield/[]/comfort_recovery",
      "/[]/outcome/zone_temperatures_c/[]",
      "/[]/outcome/pmv/[]",
      "/[]/outcome/effective_occupancy/[]",
      "/[]/outcome/site_cost",
      "/[]/outcome/site_energy_kwh",
      "/[]/outcome/discomfort_zone_hours",
      "/[]/outcome/discomfort_pmv_hours",
      "/[]/outcome/occupied_peak_absolute_pmv",
      "/[]/outcome/setpoint_total_variation_c",
      "/[]/outcome/setpoint_direction_reversals",
      "/[]/lesson"
    ],
    "ZONE FORECAST": [
      "/[]/forecast_outcome_time",
      "/[]/occupancy",
      "/[]/outdoor_temp_c",
      "/[]/solar_irr"
    ]
  },
  "internal_context": {
    "decision_hour": 42,
    "decision_step": 168,
    "decision_time_seconds": 17503200,
    "zone": "eas"
  },
  "internal_coordinates": [
    {
      "path": "/WORKING MEMORY/[]/hour",
      "value": 41
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 164
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 165
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 166
    },
    {
      "path": "/WORKING MEMORY/[]/action/shield/[]/step",
      "value": 167
    }
  ],
  "round_trip_equal": true,
  "schema": "h3c_context_audit_v1"
}
```
### Reflector expanded canonical input

### COMPLETED CONTROL INTERVAL
interval: [14:00, 15:00)
action_times: ["14:00","14:15","14:30","14:45"]
outcome_times: ["14:15","14:30","14:45","15:00"]
zones: ["cor","eas","nor","sou","wes"]
control_period: 15 min
site_result: {"site_cost":3.1214,"site_energy_kwh":21.9425}
completed_decision:
common:
action: {"admission":{"status":"accepted"},"program_version_before":0}
context: {"initial_observation":{"last_occupancy":1.0}}
rows:
| zone | op | rationale | program_version_after |
| --- | --- | --- | --- |
| cor | no_change | The current program retained occupied comfort headroom without an evidenced beneficial edit. | 0 |
| nor | no_change | The current program matched the observed stable occupied conditions. | 0 |
| sou | no_change | Observed comfort headroom and the current program did not support a different atomic edit. | 0 |
| wes | no_change | The supplied evidence did not support changing the executable specification this hour. | 0 |
| zone | op | rationale | program_version_after | param | to |
| --- | --- | --- | --- | --- | --- |
| eas | set_param | Tighten the active upper PMV threshold while East has the smallest warm-side headroom. | 1 | pmv_band_hi | 0.4 |
recent_state_history:
common:
occupancy: 1.0
constant_by_zone:
{"zone":"cor","setpoint_c":25.0}
{"zone":"nor","setpoint_c":25.0}
{"zone":"sou","setpoint_c":25.0}
{"zone":"wes","setpoint_c":25.0}
state_times: ["14:00","14:15","14:30","14:45","15:00"]
time_varying_measurements:
| state_time | cor.temp_c | cor.pmv | eas.temp_c | eas.pmv | eas.setpoint_c | nor.temp_c | nor.pmv | sou.temp_c | sou.pmv | wes.temp_c | wes.pmv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14:00 | 24.31 | 0.34 | 24.58 | 0.43 | 25.0 | 24.22 | 0.31 | 24.47 | 0.39 | 24.36 | 0.36 |
| 14:15 | 24.3 | 0.34 | 24.4 | 0.36 | 24.7 | 24.23 | 0.31 | 24.47 | 0.39 | 24.37 | 0.36 |
| 14:30 | 24.32 | 0.35 | 24.25 | 0.3 | 24.7 | 24.24 | 0.32 | 24.49 | 0.4 | 24.38 | 0.37 |
| 14:45 | 24.34 | 0.35 | 24.18 | 0.28 | 24.7 | 24.25 | 0.32 | 24.5 | 0.4 | 24.4 | 0.37 |
| 15:00 | 24.35 | 0.36 | 24.24 | 0.31 | 25.0 | 24.27 | 0.33 | 24.52 | 0.41 | 24.41 | 0.38 |
control_action_history:
common:
regime: steady_state_occupancy
actuator_bounds: false
setpoint_rate_limit: false
comfort_recovery: false
constant_by_zone:
{"zone":"cor","setpoint_c":25.0,"matched_rule":"occupied_hold"}
{"zone":"nor","setpoint_c":25.0,"matched_rule":"occupied_hold"}
{"zone":"sou","setpoint_c":25.0,"matched_rule":"occupied_hold"}
{"zone":"wes","setpoint_c":25.0,"matched_rule":"occupied_hold"}
time_varying_actions:
| action_time | outcome_time | eas.setpoint_c | eas.matched_rule |
| --- | --- | --- | --- |
| 14:00 | 14:15 | 24.7 | pmv_lower |
| 14:15 | 14:30 | 24.7 | occupied_hold |
| 14:30 | 14:45 | 24.7 | occupied_hold |
| 14:45 | 15:00 | 25.0 | pmv_raise |
previous_decision_forecast:
common:
occupancy: 1.0
zones: ["cor","eas","nor","sou","wes"]
outcome_times: ["14:15","14:30","14:45","15:00"]
derived_feature_interval: [14:00, 15:00)
derived_features:
common:
setpoint_delta_1h_c: 0.0
discomfort_zone_h: 0.0
discomfort_pmv_h: 0.0
setpoint_reversals: 0
rows:
| zone | temp_delta_15min_c | temp_delta_1h_c | temp_slope_c_per_hour | pmv_delta_15min | pmv_delta_1h | setpoint_delta_15min_c | occupied_peak_abs_pmv | setpoint_tv_c |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cor | 0.01 | 0.04 | 0.04 | 0.01 | 0.02 | 0.0 | 0.36 | 0.0 |
| eas | 0.06 | -0.34 | -0.34 | 0.03 | -0.12 | 0.3 | 0.36 | 0.3 |
| nor | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.33 | 0.0 |
| sou | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.41 | 0.0 |
| wes | 0.01 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.38 | 0.0 |

### ACTIVE LONG-TERM EXPERIENCE SLOTS
rows:
| zone | regime | revision | experience |
| --- | --- | --- | --- |
| cor | steady_state_occupancy | 2 | Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive. |
| eas | steady_state_occupancy | 1 | East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone. |
| sou | steady_state_occupancy | 2 | South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions. |
| wes | steady_state_occupancy | 1 | West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions. |

### EMPTY LONG-TERM EXPERIENCE SLOTS
rows:
| zone | regime |
| --- | --- |
| nor | steady_state_occupancy |
### Reflector audit view

```json
{
  "canonical_sha256": "5d01672ba636a87a6c780caa79c4d9b17a79b97f2bb81a2b92ea4e597de42a6e",
  "compact_sha256": "bdd392dfa55e7285f989614368512621f34d02944319da8b2ff86cbc896435d1",
  "field_manifest": {
    "ACTIVE LONG-TERM EXPERIENCE SLOTS": [
      "/[]/zone",
      "/[]/regime",
      "/[]/revision",
      "/[]/experience"
    ],
    "COMPLETED CONTROL INTERVAL": [
      "/[]/hour",
      "/[]/zone",
      "/[]/context/regime_step_coverage/steady_state_occupancy/[]",
      "/[]/context/initial_observation/zone_temperature_c",
      "/[]/context/initial_observation/current_occupancy",
      "/[]/context/initial_observation/last_occupancy",
      "/[]/context/initial_observation/occupancy_next_steps/[]",
      "/[]/context/initial_observation/last_pmv",
      "/[]/context/initial_observation/last_setpoint_c",
      "/[]/action/proposal/op",
      "/[]/action/proposal/rationale",
      "/[]/action/admission/status",
      "/[]/action/admission/completed_validation_stages/[]",
      "/[]/action/program_version_before",
      "/[]/action/program_version_after",
      "/[]/action/actual_setpoints_c/[]",
      "/[]/action/matched_rules/[]",
      "/[]/action/shield/[]/step",
      "/[]/action/shield/[]/actuator_bounds",
      "/[]/action/shield/[]/setpoint_rate_limit",
      "/[]/action/shield/[]/comfort_recovery",
      "/[]/outcome/zone_temperatures_c/[]",
      "/[]/outcome/pmv/[]",
      "/[]/outcome/effective_occupancy/[]",
      "/[]/outcome/site_cost",
      "/[]/outcome/site_energy_kwh",
      "/[]/outcome/discomfort_zone_hours",
      "/[]/outcome/discomfort_pmv_hours",
      "/[]/outcome/occupied_peak_absolute_pmv",
      "/[]/outcome/setpoint_total_variation_c",
      "/[]/outcome/setpoint_direction_reversals",
      "/[]/action/proposal/param",
      "/[]/action/proposal/to",
      "/[]/action/proposal/causal_edge_ids/[]",
      "/[]/action/proposal/expected_effects/[]/node",
      "/[]/action/proposal/expected_effects/[]/direction",
      "/[]/action/proposal/consistent_program_direction_proof/mode",
      "/[]/action/proposal/consistent_program_direction_proof/program_direction",
      "/[]/action/proposal/consistent_program_direction_proof/expected_effects/[]/node",
      "/[]/action/proposal/consistent_program_direction_proof/expected_effects/[]/direction",
      "/[]/action/proposal/consistent_program_direction_proof/witness_count",
      "/[]/action/proposal/consistent_program_direction_proof/cited_edge_ids/[]"
    ],
    "EMPTY LONG-TERM EXPERIENCE SLOTS": [
      "/[]/zone",
      "/[]/regime"
    ]
  },
  "internal_context": {
    "completed_hour": 42,
    "interval_start_time_seconds": 17503200
  },
  "internal_coordinates": [
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/hour",
      "value": 42
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 168
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 169
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 170
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 171
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/hour",
      "value": 42
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 168
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 169
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 170
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 171
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/hour",
      "value": 42
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 168
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 169
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 170
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 171
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/hour",
      "value": 42
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 168
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 169
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 170
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 171
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/hour",
      "value": 42
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 168
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 169
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 170
    },
    {
      "path": "/COMPLETED CONTROL INTERVAL/[]/action/shield/[]/step",
      "value": 171
    }
  ],
  "round_trip_equal": true,
  "schema": "h3c_context_audit_v1"
}
```
