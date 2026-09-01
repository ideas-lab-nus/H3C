# H3C 完整 MZ Air 控制时段示例：工作记忆与可选状态经验

这是一个冻结且不执行API/BOPTEST的文档fixture。全部Prompt由生产renderer生成；下方所有确定性转换均由生产validation、program、assurance、working-memory和CRUD owner计算。它不是实验结果。

## 1. 精确API请求设置

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
## 2. Orchestrator完整请求、输出与验证

### 完整序列化请求体

```json
{
  "messages": [
    {
      "content": "角色\n在 control_interval 的 action_times 上分配跨区域共享额度。\n\n目标\n在维持舒适的同时尽可能降低能耗花费。已完成时段的 reward 是冻结评价函数对能耗花费、舒适度和动作平滑性的量化参考；累计 reward 越高，表示上述同一目标的综合结果越好。\n\n决策\n使用当前状态、预测、工作记忆与上一时段 Budget，在舒适和能源成本间权衡。输出额度、优先级及每区一条额度或优先级理由。\n\n硬边界\nBudget 只覆盖 control_interval 内获准的程序修改。charge_c = 证明状态空间中 max(0, 修改前设定点 - 修改后设定点) 的最大值；不是累计动作、功率或预冷偏移。\n\n输出\n仅返回裸 JSON。 字段仅限：site_cap_c, zone_budgets_c, priority, rationale_per_zone, causal_edge_ids. site_cap_c = 输入值。budgets/rationales 的区域键 = 配置区域。每区额度：有限且在 [0,per_zone_reserved_cap_c]；总和 ≤ cap，允许未用满。priority：区域全排列，优先级从高到低。理由不能为空。 causal_edge_ids：可见 ID 的无重复非空子集，且至少包含一条 target=power_meters 的可见边。\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT SITE STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\nprice_at_interval_end: 0.16842\n\n### SITE FORECAST\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CURRENT ZONE STATE\nvalues_shared_by_all_rows:\noccupancy: 1.0\nsetpoint_c: 25.0\nrows:\n| zone | temp_c | pmv | temp_rise_to_warm_pmv_edge_c | temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- |\n| cor | 24.31 | 0.34 | 0.62 | 2.45 |\n| eas | 24.58 | 0.43 | 0.34 | 2.72 |\n| nor | 24.22 | 0.31 | 0.72 | 2.36 |\n| sou | 24.47 | 0.39 | 0.45 | 2.61 |\n| wes | 24.36 | 0.36 | 0.57 | 2.5 |\n\n### ZONE CONTROL CONTEXT\nvalues_shared_by_all_rows:\noccupancy_at_interval_end: 1.0\nprecool_offset_from_unoccupied_base_c: -5.0\nresulting_precool_setpoint_c: 25.0\nrows:\n| zone |\n| --- |\n| cor |\n| eas |\n| nor |\n| sou |\n| wes |\n\n### CAUSAL EVIDENCE\nvalues_shared_by_all_rows:\ntarget: power_meters\nundirected: false\nrows:\n| id | source | relation | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | Immediate | Strong Impact |\n\n### ALLOCATION LIMITS\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\nsite_cap_c: 10.0\nper_zone_reserved_cap_c: 5.0\n\n### CONTROL DOMAIN\ndomain_id: cooling\ncontrolled_setpoint: zone cooling setpoint\nunit: degC\nhard_bounds_c: [20.0,30.0]\noccupied_base_c: 25.0\nunoccupied_base_c: 30.0\nabs_pmv_score_limit: 0.5\npreconditioning: {\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0}\nenergy_intensive_setpoint_direction: decrease\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\nvalues_shared_by_all_rows:\naction: {\"proposal\":{\"op\":\"no_change\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: 稳定占用状态与正向暖侧舒适余量同时出现。\nrecent_state_history:\nvalues_shared_by_all_rows:\noccupancy: 1.0\nsetpoint_c: 25.0\nvalues_constant_within_each_zone:\n{\"zone\":\"cor\",\"temp_c\":24.31,\"pmv\":0.34}\n{\"zone\":\"eas\",\"temp_c\":24.58,\"pmv\":0.43}\n{\"zone\":\"nor\",\"temp_c\":24.22,\"pmv\":0.31}\n{\"zone\":\"sou\",\"temp_c\":24.47,\"pmv\":0.39}\n{\"zone\":\"wes\",\"temp_c\":24.36,\"pmv\":0.36}\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\nOBSERVED CONTEXT HISTORY:\nabs_pmv_score_limit: 0.5\n| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | cor.temp_rise_to_warm_pmv_edge_c | cor.temp_drop_to_cool_pmv_edge_c | eas.temp_rise_to_warm_pmv_edge_c | eas.temp_drop_to_cool_pmv_edge_c | nor.temp_rise_to_warm_pmv_edge_c | nor.temp_drop_to_cool_pmv_edge_c | sou.temp_rise_to_warm_pmv_edge_c | sou.temp_drop_to_cool_pmv_edge_c | wes.temp_rise_to_warm_pmv_edge_c | wes.temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 13:00 | 31.4 | 612.0 | 0.14231 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\n| 13:15 | 31.4 | 612.0 | 0.14231 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\n| 13:30 | 31.4 | 612.0 | 0.14231 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\n| 13:45 | 31.4 | 612.0 | 0.14231 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\ncontrol_action_history:\nvalues_shared_by_all_rows:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nprevious_decision_forecast:\nvalues_shared_by_all_rows:\noccupancy: 1.0\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\nvalues_shared_by_all_rows:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\nrows:\n| zone | occupied_peak_abs_pmv |\n| --- | --- |\n| cor | 0.34 |\n| eas | 0.43 |\n| nor | 0.31 |\n| sou | 0.39 |\n| wes | 0.36 |\n\n### PREVIOUS BUDGET USE\nsite_cap_c: 10.0\nreserved_allowance_by_zone_c: {\"cor\":1.0,\"eas\":2.0,\"nor\":1.0,\"sou\":1.0,\"wes\":1.0}\nreserved_consumption_by_zone_c: {\"cor\":0.0,\"eas\":2.0,\"nor\":0.0,\"sou\":0.0,\"wes\":0.0}\ntotal_reserved_allowance_c: 6.0\ntotal_reserved_consumption_c: 2.0\nreserved_utilisation: 0.3333\ninitial_shared_unreserved_pool_c: 4.0\nshared_pool_consumption_by_zone_c: {\"eas\":0.3}\nremaining_shared_unreserved_pool_c: 3.7\nprevious_priority: [\"eas\",\"sou\",\"wes\",\"cor\",\"nor\"]\n",
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
### 模型输出

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
    "cor": "Core 状态稳定，需要有界额度。",
    "eas": "East 的暖侧舒适余量最小，因此优先级最高。",
    "nor": "North 状态稳定，需要有界额度。",
    "sou": "South 的暖侧余量中等，因此优先级第二。",
    "wes": "West 的暖侧余量中等，因此优先级第三。"
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
## 3. 五个Executor完整请求、输出与结算

### Executor `cor` — 完整序列化请求体

```json
{
  "messages": [
    {
      "content": "角色\n维护一个区域的可执行控制规格。\n\n目标\n在维持舒适的同时尽可能降低能耗花费。已完成时段的 reward 是冻结评价函数对能耗花费、舒适度和动作平滑性的量化参考；累计 reward 越高，表示上述同一目标的综合结果越好。\n\n决策\n根据当前状态、舒适余量、因果证据、额度与 WORKING MEMORY，选择一个原子规格操作，权衡能耗与 |PMV| ≤ 0.5。\n\n硬边界\ncharge_c=证明状态中 max(0,修改前设定点-修改后设定点) 的最大值，不含累计动作、功率或预冷偏移。保留额度仅属本区；站点共享池在全部提案后按 shared_settlement_priority_rank 升序结算。只修改给定规格，不输出直接设定点。\n\n输出\n只返回 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。memory_refs 只列出实际使用的已展示有效经验，每条最多一次；允许 []，无额外字段。\n根对象必须精确为 {\"patch\":[{...}]}；patch 是仅含一个 operation 的列表；operation 公共字段：op、rationale。\n修改类操作还需 causal_edge_ids：当前可见 ID 的无重复非空列表。\nOperations:\nset_param: required=param,to\nadd_rule: required=rule; optional=index\nreplace_rule: required=rule\nremove_rule: required=id\nmove_rule: required=id,to_index\nno_change: required=none\nrule={id,when:[{field,op,value}],then:{op,value?}}。 ID：add 用新 rule.id；replace 用已有 rule.id；remove/move 用已有 id。索引从 0 开始：add index 为 0..N（默认 N）；move to_index 为 0..N-1。then.value：有限数值 | {\"param\":name} | {\"neg_param\":name}；hold_setpoint 省略 value。\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: cor\nzone_temperature_c: 24.31\npmv: 0.34\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.62\ntemp_drop_to_cool_pmv_edge_c: 2.45\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\nvalues_shared_by_all_rows:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\n{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}}\n{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\nvalues_shared_by_all_rows:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":1.0,\"shared_pool_available_before_settlement_c\":4.0,\"shared_settlement_priority_rank\":4}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"cor\"]\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\nvalues_shared_by_all_rows:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: 稳定占用状态与正向暖侧舒适余量同时出现。\nrecent_state_history:\nvalues_shared_by_all_rows:\ntemp_c: 24.31\npmv: 0.34\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\nOBSERVED CONTEXT HISTORY:\nabs_pmv_score_limit: 0.5\n| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | cor.temp_rise_to_warm_pmv_edge_c | cor.temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- | --- |\n| 13:00 | 31.4 | 612.0 | 0.1423 | 0.62 | 2.45 |\n| 13:15 | 31.4 | 612.0 | 0.1423 | 0.62 | 2.45 |\n| 13:30 | 31.4 | 612.0 | 0.1423 | 0.62 | 2.45 |\n| 13:45 | 31.4 | 612.0 | 0.1423 | 0.62 | 2.45 |\ncontrol_action_history:\nvalues_shared_by_all_rows:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nprevious_decision_forecast:\nvalues_shared_by_all_rows:\noccupancy: 1.0\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\nvalues_shared_by_all_rows:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.34\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n\n### ACTIVE LONG-TERM EXPERIENCE SLOTS\nvalues_shared_by_all_rows:\nrevision: 2\nexperience: Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.\nrows:\n| regime |\n| --- |\n| steady_state_occupancy |\n",
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
### Executor `cor` — 模型输出

```json
{
  "memory_refs": [],
  "patch": [
    {
      "op": "no_change",
      "rationale": "当前程序保持了占用舒适余量，且没有证据支持有益修改。"
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
### Executor `eas` — 完整序列化请求体

```json
{
  "messages": [
    {
      "content": "角色\n维护一个区域的可执行控制规格。\n\n目标\n在维持舒适的同时尽可能降低能耗花费。已完成时段的 reward 是冻结评价函数对能耗花费、舒适度和动作平滑性的量化参考；累计 reward 越高，表示上述同一目标的综合结果越好。\n\n决策\n根据当前状态、舒适余量、因果证据、额度与 WORKING MEMORY，选择一个原子规格操作，权衡能耗与 |PMV| ≤ 0.5。\n\n硬边界\ncharge_c=证明状态中 max(0,修改前设定点-修改后设定点) 的最大值，不含累计动作、功率或预冷偏移。保留额度仅属本区；站点共享池在全部提案后按 shared_settlement_priority_rank 升序结算。只修改给定规格，不输出直接设定点。\n\n输出\n只返回 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。memory_refs 只列出实际使用的已展示有效经验，每条最多一次；允许 []，无额外字段。\n根对象必须精确为 {\"patch\":[{...}]}；patch 是仅含一个 operation 的列表；operation 公共字段：op、rationale。\n修改类操作还需 causal_edge_ids：当前可见 ID 的无重复非空列表。\nOperations:\nset_param: required=param,to\nadd_rule: required=rule; optional=index\nreplace_rule: required=rule\nremove_rule: required=id\nmove_rule: required=id,to_index\nno_change: required=none\nrule={id,when:[{field,op,value}],then:{op,value?}}。 ID：add 用新 rule.id；replace 用已有 rule.id；remove/move 用已有 id。索引从 0 开始：add index 为 0..N（默认 N）；move to_index 为 0..N-1。then.value：有限数值 | {\"param\":name} | {\"neg_param\":name}；hold_setpoint 省略 value。\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: eas\nzone_temperature_c: 24.58\npmv: 0.43\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.34\ntemp_drop_to_cool_pmv_edge_c: 2.72\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\nvalues_shared_by_all_rows:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\n{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}}\n{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\nvalues_shared_by_all_rows:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":2.0,\"shared_pool_available_before_settlement_c\":4.0,\"shared_settlement_priority_rank\":1}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"eas\"]\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\nvalues_shared_by_all_rows:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: 稳定占用状态与正向暖侧舒适余量同时出现。\nrecent_state_history:\nvalues_shared_by_all_rows:\ntemp_c: 24.58\npmv: 0.43\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\nOBSERVED CONTEXT HISTORY:\nabs_pmv_score_limit: 0.5\n| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | eas.temp_rise_to_warm_pmv_edge_c | eas.temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- | --- |\n| 13:00 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |\n| 13:15 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |\n| 13:30 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |\n| 13:45 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |\ncontrol_action_history:\nvalues_shared_by_all_rows:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nprevious_decision_forecast:\nvalues_shared_by_all_rows:\noccupancy: 1.0\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\nvalues_shared_by_all_rows:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.43\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n\n### ACTIVE LONG-TERM EXPERIENCE SLOTS\nvalues_shared_by_all_rows:\nrevision: 1\nexperience: East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.\nrows:\n| regime |\n| --- |\n| steady_state_occupancy |\n",
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
### Executor `eas` — 模型输出

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
      "rationale": "East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。",
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
### Executor `nor` — 完整序列化请求体

```json
{
  "messages": [
    {
      "content": "角色\n维护一个区域的可执行控制规格。\n\n目标\n在维持舒适的同时尽可能降低能耗花费。已完成时段的 reward 是冻结评价函数对能耗花费、舒适度和动作平滑性的量化参考；累计 reward 越高，表示上述同一目标的综合结果越好。\n\n决策\n根据当前状态、舒适余量、因果证据、额度与 WORKING MEMORY，选择一个原子规格操作，权衡能耗与 |PMV| ≤ 0.5。\n\n硬边界\ncharge_c=证明状态中 max(0,修改前设定点-修改后设定点) 的最大值，不含累计动作、功率或预冷偏移。保留额度仅属本区；站点共享池在全部提案后按 shared_settlement_priority_rank 升序结算。只修改给定规格，不输出直接设定点。\n\n输出\n只返回 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。memory_refs 只列出实际使用的已展示有效经验，每条最多一次；允许 []，无额外字段。\n根对象必须精确为 {\"patch\":[{...}]}；patch 是仅含一个 operation 的列表；operation 公共字段：op、rationale。\n修改类操作还需 causal_edge_ids：当前可见 ID 的无重复非空列表。\nOperations:\nset_param: required=param,to\nadd_rule: required=rule; optional=index\nreplace_rule: required=rule\nremove_rule: required=id\nmove_rule: required=id,to_index\nno_change: required=none\nrule={id,when:[{field,op,value}],then:{op,value?}}。 ID：add 用新 rule.id；replace 用已有 rule.id；remove/move 用已有 id。索引从 0 开始：add index 为 0..N（默认 N）；move to_index 为 0..N-1。then.value：有限数值 | {\"param\":name} | {\"neg_param\":name}；hold_setpoint 省略 value。\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: nor\nzone_temperature_c: 24.22\npmv: 0.31\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.72\ntemp_drop_to_cool_pmv_edge_c: 2.36\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\nvalues_shared_by_all_rows:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\n{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}}\n{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\nvalues_shared_by_all_rows:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":1.0,\"shared_pool_available_before_settlement_c\":4.0,\"shared_settlement_priority_rank\":5}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"nor\"]\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\nvalues_shared_by_all_rows:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: 稳定占用状态与正向暖侧舒适余量同时出现。\nrecent_state_history:\nvalues_shared_by_all_rows:\ntemp_c: 24.22\npmv: 0.31\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\nOBSERVED CONTEXT HISTORY:\nabs_pmv_score_limit: 0.5\n| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | nor.temp_rise_to_warm_pmv_edge_c | nor.temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- | --- |\n| 13:00 | 31.4 | 612.0 | 0.1423 | 0.72 | 2.36 |\n| 13:15 | 31.4 | 612.0 | 0.1423 | 0.72 | 2.36 |\n| 13:30 | 31.4 | 612.0 | 0.1423 | 0.72 | 2.36 |\n| 13:45 | 31.4 | 612.0 | 0.1423 | 0.72 | 2.36 |\ncontrol_action_history:\nvalues_shared_by_all_rows:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nprevious_decision_forecast:\nvalues_shared_by_all_rows:\noccupancy: 1.0\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\nvalues_shared_by_all_rows:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.31\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n",
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
### Executor `nor` — 模型输出

```json
{
  "memory_refs": [],
  "patch": [
    {
      "op": "no_change",
      "rationale": "当前程序与已观察到的稳定占用状态相匹配。"
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
### Executor `sou` — 完整序列化请求体

```json
{
  "messages": [
    {
      "content": "角色\n维护一个区域的可执行控制规格。\n\n目标\n在维持舒适的同时尽可能降低能耗花费。已完成时段的 reward 是冻结评价函数对能耗花费、舒适度和动作平滑性的量化参考；累计 reward 越高，表示上述同一目标的综合结果越好。\n\n决策\n根据当前状态、舒适余量、因果证据、额度与 WORKING MEMORY，选择一个原子规格操作，权衡能耗与 |PMV| ≤ 0.5。\n\n硬边界\ncharge_c=证明状态中 max(0,修改前设定点-修改后设定点) 的最大值，不含累计动作、功率或预冷偏移。保留额度仅属本区；站点共享池在全部提案后按 shared_settlement_priority_rank 升序结算。只修改给定规格，不输出直接设定点。\n\n输出\n只返回 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。memory_refs 只列出实际使用的已展示有效经验，每条最多一次；允许 []，无额外字段。\n根对象必须精确为 {\"patch\":[{...}]}；patch 是仅含一个 operation 的列表；operation 公共字段：op、rationale。\n修改类操作还需 causal_edge_ids：当前可见 ID 的无重复非空列表。\nOperations:\nset_param: required=param,to\nadd_rule: required=rule; optional=index\nreplace_rule: required=rule\nremove_rule: required=id\nmove_rule: required=id,to_index\nno_change: required=none\nrule={id,when:[{field,op,value}],then:{op,value?}}。 ID：add 用新 rule.id；replace 用已有 rule.id；remove/move 用已有 id。索引从 0 开始：add index 为 0..N（默认 N）；move to_index 为 0..N-1。then.value：有限数值 | {\"param\":name} | {\"neg_param\":name}；hold_setpoint 省略 value。\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: sou\nzone_temperature_c: 24.47\npmv: 0.39\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.45\ntemp_drop_to_cool_pmv_edge_c: 2.61\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\nvalues_shared_by_all_rows:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\n{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}}\n{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\nvalues_shared_by_all_rows:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":1.0,\"shared_pool_available_before_settlement_c\":4.0,\"shared_settlement_priority_rank\":2}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"sou\"]\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\nvalues_shared_by_all_rows:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: 稳定占用状态与正向暖侧舒适余量同时出现。\nrecent_state_history:\nvalues_shared_by_all_rows:\ntemp_c: 24.47\npmv: 0.39\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\nOBSERVED CONTEXT HISTORY:\nabs_pmv_score_limit: 0.5\n| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | sou.temp_rise_to_warm_pmv_edge_c | sou.temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- | --- |\n| 13:00 | 31.4 | 612.0 | 0.1423 | 0.45 | 2.61 |\n| 13:15 | 31.4 | 612.0 | 0.1423 | 0.45 | 2.61 |\n| 13:30 | 31.4 | 612.0 | 0.1423 | 0.45 | 2.61 |\n| 13:45 | 31.4 | 612.0 | 0.1423 | 0.45 | 2.61 |\ncontrol_action_history:\nvalues_shared_by_all_rows:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nprevious_decision_forecast:\nvalues_shared_by_all_rows:\noccupancy: 1.0\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\nvalues_shared_by_all_rows:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.39\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n\n### ACTIVE LONG-TERM EXPERIENCE SLOTS\nvalues_shared_by_all_rows:\nrevision: 2\nexperience: South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.\nrows:\n| regime |\n| --- |\n| steady_state_occupancy |\n",
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
### Executor `sou` — 模型输出

```json
{
  "memory_refs": [],
  "patch": [
    {
      "op": "no_change",
      "rationale": "已观察舒适余量与当前程序不支持其他原子修改。"
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
### Executor `wes` — 完整序列化请求体

```json
{
  "messages": [
    {
      "content": "角色\n维护一个区域的可执行控制规格。\n\n目标\n在维持舒适的同时尽可能降低能耗花费。已完成时段的 reward 是冻结评价函数对能耗花费、舒适度和动作平滑性的量化参考；累计 reward 越高，表示上述同一目标的综合结果越好。\n\n决策\n根据当前状态、舒适余量、因果证据、额度与 WORKING MEMORY，选择一个原子规格操作，权衡能耗与 |PMV| ≤ 0.5。\n\n硬边界\ncharge_c=证明状态中 max(0,修改前设定点-修改后设定点) 的最大值，不含累计动作、功率或预冷偏移。保留额度仅属本区；站点共享池在全部提案后按 shared_settlement_priority_rank 升序结算。只修改给定规格，不输出直接设定点。\n\n输出\n只返回 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。memory_refs 只列出实际使用的已展示有效经验，每条最多一次；允许 []，无额外字段。\n根对象必须精确为 {\"patch\":[{...}]}；patch 是仅含一个 operation 的列表；operation 公共字段：op、rationale。\n修改类操作还需 causal_edge_ids：当前可见 ID 的无重复非空列表。\nOperations:\nset_param: required=param,to\nadd_rule: required=rule; optional=index\nreplace_rule: required=rule\nremove_rule: required=id\nmove_rule: required=id,to_index\nno_change: required=none\nrule={id,when:[{field,op,value}],then:{op,value?}}。 ID：add 用新 rule.id；replace 用已有 rule.id；remove/move 用已有 id。索引从 0 开始：add index 为 0..N（默认 N）；move to_index 为 0..N-1。then.value：有限数值 | {\"param\":name} | {\"neg_param\":name}；hold_setpoint 省略 value。\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: wes\nzone_temperature_c: 24.36\npmv: 0.36\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.57\ntemp_drop_to_cool_pmv_edge_c: 2.5\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\nvalues_shared_by_all_rows:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\n{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}}\n{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\nvalues_shared_by_all_rows:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":1.0,\"shared_pool_available_before_settlement_c\":4.0,\"shared_settlement_priority_rank\":3}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"wes\"]\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\nvalues_shared_by_all_rows:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: 稳定占用状态与正向暖侧舒适余量同时出现。\nrecent_state_history:\nvalues_shared_by_all_rows:\ntemp_c: 24.36\npmv: 0.36\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\nOBSERVED CONTEXT HISTORY:\nabs_pmv_score_limit: 0.5\n| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | wes.temp_rise_to_warm_pmv_edge_c | wes.temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- | --- |\n| 13:00 | 31.4 | 612.0 | 0.1423 | 0.57 | 2.5 |\n| 13:15 | 31.4 | 612.0 | 0.1423 | 0.57 | 2.5 |\n| 13:30 | 31.4 | 612.0 | 0.1423 | 0.57 | 2.5 |\n| 13:45 | 31.4 | 612.0 | 0.1423 | 0.57 | 2.5 |\ncontrol_action_history:\nvalues_shared_by_all_rows:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nprevious_decision_forecast:\nvalues_shared_by_all_rows:\noccupancy: 1.0\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\nvalues_shared_by_all_rows:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.36\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n\n### ACTIVE LONG-TERM EXPERIENCE SLOTS\nvalues_shared_by_all_rows:\nrevision: 1\nexperience: West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.\nrows:\n| regime |\n| --- |\n| steady_state_occupancy |\n",
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
### Executor `wes` — 模型输出

```json
{
  "memory_refs": [],
  "patch": [
    {
      "op": "no_change",
      "rationale": "给定证据不支持在本小时修改可执行规格。"
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
## 4. 确定性优先级结算

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
        "rationale": "East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。",
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
        "rationale": "已观察舒适余量与当前程序不支持其他原子修改。"
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
        "rationale": "给定证据不支持在本小时修改可执行规格。"
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
        "rationale": "当前程序保持了占用舒适余量，且没有证据支持有益修改。"
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
        "rationale": "当前程序与已观察到的稳定占用状态相匹配。"
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
## 5. 四次已执行动作及其结果观测

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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.83144454516,
            "site_smoothness_penalty": 0.0023215920000000056,
            "site_step_reward": -2.83376613716,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.83144454516,
            "site_smoothness_penalty": 0.0023215920000000056,
            "site_step_reward": -2.83376613716,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0023215920000000056
          },
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.83144454516,
            "site_smoothness_penalty": 0.0023215920000000056,
            "site_step_reward": -2.83376613716,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.83144454516,
            "site_smoothness_penalty": 0.0023215920000000056,
            "site_step_reward": -2.83376613716,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.83144454516,
            "site_smoothness_penalty": 0.0023215920000000056,
            "site_step_reward": -2.83376613716,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 31.6,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 628.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.8762939744000002,
            "site_smoothness_penalty": 0.0,
            "site_step_reward": -2.8762939744000002,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 31.6,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 628.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.8762939744000002,
            "site_smoothness_penalty": 0.0,
            "site_step_reward": -2.8762939744000002,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 31.6,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 628.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.8762939744000002,
            "site_smoothness_penalty": 0.0,
            "site_step_reward": -2.8762939744000002,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 31.6,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 628.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.8762939744000002,
            "site_smoothness_penalty": 0.0,
            "site_step_reward": -2.8762939744000002,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 31.6,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 628.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.8762939744000002,
            "site_smoothness_penalty": 0.0,
            "site_step_reward": -2.8762939744000002,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 31.8,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 646.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.91447158772,
            "site_smoothness_penalty": 0.0,
            "site_step_reward": -2.91447158772,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 31.8,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 646.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.91447158772,
            "site_smoothness_penalty": 0.0,
            "site_step_reward": -2.91447158772,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 31.8,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 646.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.91447158772,
            "site_smoothness_penalty": 0.0,
            "site_step_reward": -2.91447158772,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 31.8,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 646.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.91447158772,
            "site_smoothness_penalty": 0.0,
            "site_step_reward": -2.91447158772,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 31.8,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 646.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.91447158772,
            "site_smoothness_penalty": 0.0,
            "site_step_reward": -2.91447158772,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 32.0,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 668.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.94746001088,
            "site_smoothness_penalty": 0.0023215920000000056,
            "site_step_reward": -2.94978160288,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 32.0,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 668.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.94746001088,
            "site_smoothness_penalty": 0.0023215920000000056,
            "site_step_reward": -2.94978160288,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0023215920000000056
          },
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
          "outdoor_temp_c": 32.0,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 668.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.94746001088,
            "site_smoothness_penalty": 0.0023215920000000056,
            "site_step_reward": -2.94978160288,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 32.0,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 668.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.94746001088,
            "site_smoothness_penalty": 0.0023215920000000056,
            "site_step_reward": -2.94978160288,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
          "outdoor_temp_c": 32.0,
          "outdoor_temp_change_next_1h_c": 0.8,
          "outdoor_temp_threshold_candidates_c": [
            30.0,
            32.0
          ],
          "solar_irr": 668.0,
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
          "objective_feedback": {
            "site_comfort_penalty": 0.0,
            "site_energy_penalty": 2.94746001088,
            "site_smoothness_penalty": 0.0023215920000000056,
            "site_step_reward": -2.94978160288,
            "zone_comfort_penalty_contribution": 0.0,
            "zone_smoothness_penalty_contribution": 0.0
          },
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
## 6. Reflector完整请求与输出

### 完整序列化请求体

```json
{
  "messages": [
    {
      "content": "角色\n从已完成控制时段提炼每区 Lesson。\n\n目标\n在维持舒适的同时尽可能降低能耗花费。已完成时段的 reward 是冻结评价函数对能耗花费、舒适度和动作平滑性的量化参考；累计 reward 越高，表示上述同一目标的综合结果越好。\n\n证据\n每区从已完成的 Context、Action 与 Outcome 提炼一条已观察关系或权衡；比较展示的合格状态槽，最多选一个操作。\n\n硬边界\n已完成时段是 Lesson 唯一事实来源，经验槽只用于比较。经验按状态概括全程热响应、控制偏好或权衡，不写命令、目标或无证据结论。只修改展示状态；replace/delete 使用其 revision。\n\n输出\n返回裸 JSON：{\"hourly_lessons\":[{\"zone\":...,\"lesson\":...}],\"memory_operations\":[...]}；每个给定区域在两个列表中各出现一次。每个记忆操作都需要 zone 与 op，额外必填字段：\n| op | 必填 |\n| --- | --- |\n| no_change | — |\n| add | regime, experience |\n| replace | regime, expected_revision, experience |\n| delete | regime, expected_revision |\n不返回解释文字、Markdown 围栏或额外字段。\n",
      "role": "system"
    },
    {
      "content": "### COMPLETED CONTROL INTERVAL\ninterval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\noutcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.1214,\"site_energy_kwh\":21.9425}\nOBJECTIVE FEEDBACK:\ninterval_reward: -11.5744\nsite_reward_history:\n| action_time | outcome_time | site_step_reward | site_energy_penalty | site_comfort_penalty | site_smoothness_penalty |\n| --- | --- | --- | --- | --- | --- |\n| 14:00 | 14:15 | -2.8338 | 2.8314 | 0.0 | 0.0023 |\n| 14:15 | 14:30 | -2.8763 | 2.8763 | 0.0 | 0.0 |\n| 14:30 | 14:45 | -2.9145 | 2.9145 | 0.0 | 0.0 |\n| 14:45 | 15:00 | -2.9498 | 2.9475 | 0.0 | 0.0023 |\nzone_penalty_contributions:\n| zone | action_time | outcome_time | zone_comfort_penalty_contribution | zone_smoothness_penalty_contribution |\n| --- | --- | --- | --- | --- |\n| cor | 14:00 | 14:15 | 0.0 | 0.0 |\n| cor | 14:15 | 14:30 | 0.0 | 0.0 |\n| cor | 14:30 | 14:45 | 0.0 | 0.0 |\n| cor | 14:45 | 15:00 | 0.0 | 0.0 |\n| eas | 14:00 | 14:15 | 0.0 | 0.0023 |\n| eas | 14:15 | 14:30 | 0.0 | 0.0 |\n| eas | 14:30 | 14:45 | 0.0 | 0.0 |\n| eas | 14:45 | 15:00 | 0.0 | 0.0023 |\n| nor | 14:00 | 14:15 | 0.0 | 0.0 |\n| nor | 14:15 | 14:30 | 0.0 | 0.0 |\n| nor | 14:30 | 14:45 | 0.0 | 0.0 |\n| nor | 14:45 | 15:00 | 0.0 | 0.0 |\n| sou | 14:00 | 14:15 | 0.0 | 0.0 |\n| sou | 14:15 | 14:30 | 0.0 | 0.0 |\n| sou | 14:30 | 14:45 | 0.0 | 0.0 |\n| sou | 14:45 | 15:00 | 0.0 | 0.0 |\n| wes | 14:00 | 14:15 | 0.0 | 0.0 |\n| wes | 14:15 | 14:30 | 0.0 | 0.0 |\n| wes | 14:30 | 14:45 | 0.0 | 0.0 |\n| wes | 14:45 | 15:00 | 0.0 | 0.0 |\ncompleted_decision:\nvalues_shared_by_all_rows:\naction: {\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0}\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nno_change_rows:\n| zone | op | rationale | program_version_after |\n| --- | --- | --- | --- |\n| cor | no_change | 当前程序保持了占用舒适余量，且没有证据支持有益修改。 | 0 |\n| nor | no_change | 当前程序与已观察到的稳定占用状态相匹配。 | 0 |\n| sou | no_change | 已观察舒适余量与当前程序不支持其他原子修改。 | 0 |\n| wes | no_change | 给定证据不支持在本小时修改可执行规格。 | 0 |\nset_param_rows:\n| zone | op | rationale | program_version_after | param | to |\n| --- | --- | --- | --- | --- | --- |\n| eas | set_param | East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。 | 1 | pmv_band_hi | 0.4 |\nrecent_state_history:\nvalues_shared_by_all_rows:\noccupancy: 1.0\nvalues_constant_within_each_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0}\n{\"zone\":\"nor\",\"setpoint_c\":25.0}\n{\"zone\":\"sou\",\"setpoint_c\":25.0}\n{\"zone\":\"wes\",\"setpoint_c\":25.0}\nstate_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ntime_varying_measurements:\n| state_time | cor.temp_c | cor.pmv | eas.temp_c | eas.pmv | eas.setpoint_c | nor.temp_c | nor.pmv | sou.temp_c | sou.pmv | wes.temp_c | wes.pmv |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 14:00 | 24.31 | 0.34 | 24.58 | 0.43 | 25.0 | 24.22 | 0.31 | 24.47 | 0.39 | 24.36 | 0.36 |\n| 14:15 | 24.3 | 0.34 | 24.4 | 0.36 | 24.7 | 24.23 | 0.31 | 24.47 | 0.39 | 24.37 | 0.36 |\n| 14:30 | 24.32 | 0.35 | 24.25 | 0.3 | 24.7 | 24.24 | 0.32 | 24.49 | 0.4 | 24.38 | 0.37 |\n| 14:45 | 24.34 | 0.35 | 24.18 | 0.28 | 24.7 | 24.25 | 0.32 | 24.5 | 0.4 | 24.4 | 0.37 |\n| 15:00 | 24.35 | 0.36 | 24.24 | 0.31 | 25.0 | 24.27 | 0.33 | 24.52 | 0.41 | 24.41 | 0.38 |\nOBSERVED CONTEXT HISTORY:\nabs_pmv_score_limit: 0.5\n| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | cor.temp_rise_to_warm_pmv_edge_c | cor.temp_drop_to_cool_pmv_edge_c | eas.temp_rise_to_warm_pmv_edge_c | eas.temp_drop_to_cool_pmv_edge_c | nor.temp_rise_to_warm_pmv_edge_c | nor.temp_drop_to_cool_pmv_edge_c | sou.temp_rise_to_warm_pmv_edge_c | sou.temp_drop_to_cool_pmv_edge_c | wes.temp_rise_to_warm_pmv_edge_c | wes.temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 14:00 | 31.4 | 612.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\n| 14:15 | 31.6 | 628.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\n| 14:30 | 31.8 | 646.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\n| 14:45 | 32.0 | 668.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\ncontrol_action_history:\nvalues_shared_by_all_rows:\nregime: steady_state_occupancy\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\nvalues_constant_within_each_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"nor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"sou\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"wes\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\ntime_varying_actions:\n| action_time | outcome_time | eas.setpoint_c | eas.matched_rule |\n| --- | --- | --- | --- |\n| 14:00 | 14:15 | 24.7 | pmv_lower |\n| 14:15 | 14:30 | 24.7 | occupied_hold |\n| 14:30 | 14:45 | 24.7 | occupied_hold |\n| 14:45 | 15:00 | 25.0 | pmv_raise |\nprevious_decision_forecast:\nvalues_shared_by_all_rows:\noccupancy: 1.0\noutcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\nderived_feature_interval: [14:00, 15:00)\nderived_features:\nvalues_shared_by_all_rows:\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\nsetpoint_reversals: 0\nrows:\n| zone | temp_delta_15min_c | temp_delta_1h_c | temp_slope_c_per_hour | pmv_delta_15min | pmv_delta_1h | setpoint_delta_15min_c | occupied_peak_abs_pmv | setpoint_tv_c |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| cor | 0.01 | 0.04 | 0.04 | 0.01 | 0.02 | 0.0 | 0.36 | 0.0 |\n| eas | 0.06 | -0.34 | -0.34 | 0.03 | -0.12 | 0.3 | 0.36 | 0.3 |\n| nor | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.33 | 0.0 |\n| sou | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.41 | 0.0 |\n| wes | 0.01 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.38 | 0.0 |\n\n### ACTIVE LONG-TERM EXPERIENCE SLOTS\nrows:\n| zone | regime | revision | experience |\n| --- | --- | --- | --- |\n| cor | steady_state_occupancy | 2 | Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive. |\n| eas | steady_state_occupancy | 1 | East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone. |\n| sou | steady_state_occupancy | 2 | South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions. |\n| wes | steady_state_occupancy | 1 | West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions. |\n\n### EMPTY LONG-TERM EXPERIENCE SLOTS\nrows:\n| zone | regime |\n| --- | --- |\n| nor | steady_state_occupancy |\n",
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
### 模型输出

```json
{
  "hourly_lessons": [
    {
      "lesson": "稳定设定点与平稳的占用 PMV 及正向暖侧余量同时出现。",
      "zone": "cor"
    },
    {
      "lesson": "更紧的上侧阈值之后出现了有界制冷响应，同时占用 PMV 保持在舒适带内。",
      "zone": "eas"
    },
    {
      "lesson": "占用保持分支与较小的温度和 PMV 变化同时出现。",
      "zone": "nor"
    },
    {
      "lesson": "在较高太阳辐射下，占用保持分支仍保留了正向暖侧余量。",
      "zone": "sou"
    },
    {
      "lesson": "稳定动作与渐进的占用温度响应及有界 PMV 同时出现。",
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
      "experience": "East 在占用状态下反复表现出有限的暖侧舒适余量，并在更紧上侧阈值获准后呈现有界制冷响应。",
      "op": "replace",
      "regime": "steady_state_occupancy",
      "zone": "eas"
    },
    {
      "experience": "North 在稳定设定点下表现出缓慢的占用温度和 PMV 变化。",
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
## 7. 已完成控制时段记录与下一控制时段工作记忆

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
        "rationale": "当前程序保持了占用舒适余量，且没有证据支持有益修改。"
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.45,
          2.45,
          2.45,
          2.45
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.62,
          0.62,
          0.62,
          0.62
        ]
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
    "lesson": "稳定设定点与平稳的占用 PMV 及正向暖侧余量同时出现。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ]
      },
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
        "rationale": "East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。",
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.72,
          2.72,
          2.72,
          2.72
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.34,
          0.34,
          0.34,
          0.34
        ]
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
    "lesson": "更紧的上侧阈值之后出现了有界制冷响应，同时占用 PMV 保持在舒适带内。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ]
      },
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
        "rationale": "当前程序与已观察到的稳定占用状态相匹配。"
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.36,
          2.36,
          2.36,
          2.36
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.72,
          0.72,
          0.72,
          0.72
        ]
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
    "lesson": "占用保持分支与较小的温度和 PMV 变化同时出现。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ]
      },
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
        "rationale": "已观察舒适余量与当前程序不支持其他原子修改。"
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.61,
          2.61,
          2.61,
          2.61
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.45,
          0.45,
          0.45,
          0.45
        ]
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
    "lesson": "在较高太阳辐射下，占用保持分支仍保留了正向暖侧余量。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ]
      },
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
        "rationale": "给定证据不支持在本小时修改可执行规格。"
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.5,
          2.5,
          2.5,
          2.5
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.57,
          0.57,
          0.57,
          0.57
        ]
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
    "lesson": "稳定动作与渐进的占用温度响应及有界 PMV 同时出现。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ]
      },
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
        "rationale": "当前程序保持了占用舒适余量，且没有证据支持有益修改。"
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.45,
          2.45,
          2.45,
          2.45
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.62,
          0.62,
          0.62,
          0.62
        ]
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
    "lesson": "稳定设定点与平稳的占用 PMV 及正向暖侧余量同时出现。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ]
      },
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
        "rationale": "East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。",
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.72,
          2.72,
          2.72,
          2.72
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.34,
          0.34,
          0.34,
          0.34
        ]
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
    "lesson": "更紧的上侧阈值之后出现了有界制冷响应，同时占用 PMV 保持在舒适带内。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ]
      },
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
        "rationale": "当前程序与已观察到的稳定占用状态相匹配。"
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.36,
          2.36,
          2.36,
          2.36
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.72,
          0.72,
          0.72,
          0.72
        ]
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
    "lesson": "占用保持分支与较小的温度和 PMV 变化同时出现。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ]
      },
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
        "rationale": "已观察舒适余量与当前程序不支持其他原子修改。"
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.61,
          2.61,
          2.61,
          2.61
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.45,
          0.45,
          0.45,
          0.45
        ]
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
    "lesson": "在较高太阳辐射下，占用保持分支仍保留了正向暖侧余量。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ]
      },
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
        "rationale": "给定证据不支持在本小时修改可执行规格。"
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.5,
          2.5,
          2.5,
          2.5
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.57,
          0.57,
          0.57,
          0.57
        ]
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
    "lesson": "稳定动作与渐进的占用温度响应及有界 PMV 同时出现。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ]
      },
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
        "rationale": "East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。",
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
      "abs_pmv_score_limit": 0.5,
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
      "observed_context_history": {
        "electricity_price": [
          0.1423,
          0.1423,
          0.1423,
          0.1423
        ],
        "outdoor_temperature_c": [
          31.4,
          31.6,
          31.8,
          32.0
        ],
        "solar_irradiance_w_m2": [
          612.0,
          628.0,
          646.0,
          668.0
        ],
        "temp_drop_to_cool_pmv_edge_c": [
          2.72,
          2.72,
          2.72,
          2.72
        ],
        "temp_rise_to_warm_pmv_edge_c": [
          0.34,
          0.34,
          0.34,
          0.34
        ]
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
    "lesson": "更紧的上侧阈值之后出现了有界制冷响应，同时占用 PMV 保持在舒适带内。",
    "outcome": {
      "discomfort_pmv_hours": 0.0,
      "discomfort_zone_hours": 0.0,
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "objective_feedback": {
        "interval_reward": -11.5744,
        "site_comfort_penalty": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "site_energy_penalty": [
          2.8314,
          2.8763,
          2.9145,
          2.9475
        ],
        "site_smoothness_penalty": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ],
        "site_step_reward": [
          -2.8338,
          -2.8763,
          -2.9145,
          -2.9498
        ],
        "zone_comfort_penalty_contribution": [
          0.0,
          0.0,
          0.0,
          0.0
        ],
        "zone_smoothness_penalty_contribution": [
          0.0023,
          0.0,
          0.0,
          0.0023
        ]
      },
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
## 8. 三状态判定

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
## 9. 长期经验读取、CRUD与下一控制时段Executor输入

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
        "experience": "East 在占用状态下反复表现出有限的暖侧舒适余量，并在更紧上侧阈值获准后呈现有界制冷响应。",
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
      "experience": "East 在占用状态下反复表现出有限的暖侧舒适余量，并在更紧上侧阈值获准后呈现有界制冷响应。",
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
        "experience": "North 在稳定设定点下表现出缓慢的占用温度和 PMV 变化。",
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
      "experience": "North 在稳定设定点下表现出缓慢的占用温度和 PMV 变化。",
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
      "experience": "East 在占用状态下反复表现出有限的暖侧舒适余量，并在更紧上侧阈值获准后呈现有界制冷响应。",
      "regime": "steady_state_occupancy",
      "revision": 2
    },
    "unoccupied": null
  },
  "nor": {
    "occupancy_transition": null,
    "steady_state_occupancy": {
      "experience": "North 在稳定设定点下表现出缓慢的占用温度和 PMV 变化。",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n目标\n在维持舒适的同时尽可能降低能耗花费。已完成时段的 reward 是冻结评价函数对能耗花费、舒适度和动作平滑性的量化参考；累计 reward 越高，表示上述同一目标的综合结果越好。\n\n决策\n根据当前状态、舒适余量、因果证据、额度与 WORKING MEMORY，选择一个原子规格操作，权衡能耗与 |PMV| ≤ 0.5。\n\n硬边界\ncharge_c=证明状态中 max(0,修改前设定点-修改后设定点) 的最大值，不含累计动作、功率或预冷偏移。保留额度仅属本区；站点共享池在全部提案后按 shared_settlement_priority_rank 升序结算。只修改给定规格，不输出直接设定点。\n\n输出\n只返回 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。memory_refs 只列出实际使用的已展示有效经验，每条最多一次；允许 []，无额外字段。\n根对象必须精确为 {\"patch\":[{...}]}；patch 是仅含一个 operation 的列表；operation 公共字段：op、rationale。\n修改类操作还需 causal_edge_ids：当前可见 ID 的无重复非空列表。\nOperations:\nset_param: required=param,to\nadd_rule: required=rule; optional=index\nreplace_rule: required=rule\nremove_rule: required=id\nmove_rule: required=id,to_index\nno_change: required=none\nrule={id,when:[{field,op,value}],then:{op,value?}}。 ID：add 用新 rule.id；replace 用已有 rule.id；remove/move 用已有 id。索引从 0 开始：add index 为 0..N（默认 N）；move to_index 为 0..N-1。then.value：有限数值 | {\"param\":name} | {\"neg_param\":name}；hold_setpoint 省略 value。\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 15:00\ncontrol_interval: [15:00, 16:00)\naction_times: [\"15:00\",\"15:15\",\"15:30\",\"15:45\"]\nforecast_outcome_times: [\"15:15\",\"15:30\",\"15:45\",\"16:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: eas\nzone_temperature_c: 24.24\npmv: 0.31\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.34\ntemp_drop_to_cool_pmv_edge_c: 2.72\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\nvalues_shared_by_all_rows:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 15:15 | 31.6 | 628.0 |\n| 15:30 | 31.8 | 646.0 |\n| 15:45 | 32.0 | 668.0 |\n| 16:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 1\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.4 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\n{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}}\n{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\nvalues_shared_by_all_rows:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":1.7,\"shared_pool_available_before_settlement_c\":4.0,\"shared_settlement_priority_rank\":1}\n\n### WORKING MEMORY\ncompleted_interval: [14:00, 15:00)\nzones: [\"eas\"]\nsite_result: {\"site_cost\":3.1214,\"site_energy_kwh\":21.9425}\nOBJECTIVE FEEDBACK:\ninterval_reward: -11.5744\nsite_reward_history:\n| action_time | outcome_time | site_step_reward | site_energy_penalty | site_comfort_penalty | site_smoothness_penalty |\n| --- | --- | --- | --- | --- | --- |\n| 14:00 | 14:15 | -2.8338 | 2.8314 | 0.0 | 0.0023 |\n| 14:15 | 14:30 | -2.8763 | 2.8763 | 0.0 | 0.0 |\n| 14:30 | 14:45 | -2.9145 | 2.9145 | 0.0 | 0.0 |\n| 14:45 | 15:00 | -2.9498 | 2.9475 | 0.0 | 0.0023 |\nzone_penalty_contributions:\n| zone | action_time | outcome_time | zone_comfort_penalty_contribution | zone_smoothness_penalty_contribution |\n| --- | --- | --- | --- | --- |\n| eas | 14:00 | 14:15 | 0.0 | 0.0023 |\n| eas | 14:15 | 14:30 | 0.0 | 0.0 |\n| eas | 14:30 | 14:45 | 0.0 | 0.0 |\n| eas | 14:45 | 15:00 | 0.0 | 0.0023 |\ncompleted_decision:\nvalues_shared_by_all_rows:\naction: {\"proposal\":{\"op\":\"set_param\",\"rationale\":\"East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。\",\"param\":\"pmv_band_hi\",\"to\":0.4},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":1}\nlesson: 更紧的上侧阈值之后出现了有界制冷响应，同时占用 PMV 保持在舒适带内。\nrecent_state_history:\nvalues_shared_by_all_rows:\noccupancy: 1.0\nstate_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\ntime_varying_measurements:\n| state_time | eas.temp_c | eas.pmv | eas.setpoint_c |\n| --- | --- | --- | --- |\n| 14:00 | 24.58 | 0.43 | 25.0 |\n| 14:15 | 24.4 | 0.36 | 24.7 |\n| 14:30 | 24.25 | 0.3 | 24.7 |\n| 14:45 | 24.18 | 0.28 | 24.7 |\nOBSERVED CONTEXT HISTORY:\nabs_pmv_score_limit: 0.5\n| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | eas.temp_rise_to_warm_pmv_edge_c | eas.temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- | --- |\n| 14:00 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |\n| 14:15 | 31.6 | 628.0 | 0.1423 | 0.34 | 2.72 |\n| 14:30 | 31.8 | 646.0 | 0.1423 | 0.34 | 2.72 |\n| 14:45 | 32.0 | 668.0 | 0.1423 | 0.34 | 2.72 |\ncontrol_action_history:\nvalues_shared_by_all_rows:\nregime: steady_state_occupancy\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time | eas.setpoint_c | eas.matched_rule |\n| --- | --- | --- | --- |\n| 14:00 | 14:15 | 24.7 | pmv_lower |\n| 14:15 | 14:30 | 24.7 | occupied_hold |\n| 14:30 | 14:45 | 24.7 | occupied_hold |\n| 14:45 | 15:00 | 25.0 | pmv_raise |\nprevious_decision_forecast:\nvalues_shared_by_all_rows:\noccupancy: 1.0\noutcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\nderived_feature_interval: [14:00, 15:00)\nderived_features:\nvalues_shared_by_all_rows:\ntemp_delta_15min_c: 0.06\ntemp_delta_1h_c: -0.34\ntemp_slope_c_per_hour: -0.34\npmv_delta_15min: 0.03\npmv_delta_1h: -0.12\nsetpoint_delta_15min_c: 0.3\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.36\nsetpoint_tv_c: 0.3\nsetpoint_reversals: 0\n\n### ACTIVE LONG-TERM EXPERIENCE SLOTS\nvalues_shared_by_all_rows:\nrevision: 2\nexperience: East 在占用状态下反复表现出有限的暖侧舒适余量，并在更紧上侧阈值获准后呈现有界制冷响应。\nrows:\n| regime |\n| --- |\n| steady_state_occupancy |\n",
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
## 10. Memory-off精确契约与消失字段

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
    "ACTIVE LONG-TERM EXPERIENCE SLOTS"
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
    "ACTIVE LONG-TERM EXPERIENCE SLOTS",
    "EMPTY LONG-TERM EXPERIENCE SLOTS"
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n目标\n在维持舒适的同时尽可能降低能耗花费。已完成时段的 reward 是冻结评价函数对能耗花费、舒适度和动作平滑性的量化参考；累计 reward 越高，表示上述同一目标的综合结果越好。\n\n决策\n根据当前状态、舒适余量、因果证据、额度与 WORKING MEMORY，选择一个原子规格操作，权衡能耗与 |PMV| ≤ 0.5。\n\n硬边界\ncharge_c=证明状态中 max(0,修改前设定点-修改后设定点) 的最大值，不含累计动作、功率或预冷偏移。保留额度仅属本区；站点共享池在全部提案后按 shared_settlement_priority_rank 升序结算。只修改给定规格，不输出直接设定点。\n\n输出\n只返回一个精确的 root JSON 对象：{\"patch\":[{...}]}。不要返回解释文字、Markdown 围栏或未知字段。操作契约：\n根对象必须精确为 {\"patch\":[{...}]}；patch 是仅含一个 operation 的列表；operation 公共字段：op、rationale。\n修改类操作还需 causal_edge_ids：当前可见 ID 的无重复非空列表。\nOperations:\nset_param: required=param,to\nadd_rule: required=rule; optional=index\nreplace_rule: required=rule\nremove_rule: required=id\nmove_rule: required=id,to_index\nno_change: required=none\nrule={id,when:[{field,op,value}],then:{op,value?}}。 ID：add 用新 rule.id；replace 用已有 rule.id；remove/move 用已有 id。索引从 0 开始：add index 为 0..N（默认 N）；move to_index 为 0..N-1。then.value：有限数值 | {\"param\":name} | {\"neg_param\":name}；hold_setpoint 省略 value。\n",
      "role": "system"
    },
    {
      "content": "### DECISION WINDOW\ncurrent_time: 14:00\ncontrol_interval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\nforecast_outcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ncontrol_period: 15 min\ncoordination_period: 60 min\n\n### CURRENT DECISION STATE\nzone: eas\nzone_temperature_c: 24.58\npmv: 0.43\noccupancy: 1.0\nsetpoint_c: 25.0\ntemp_rise_to_warm_pmv_edge_c: 0.34\ntemp_drop_to_cool_pmv_edge_c: 2.72\n\n### OCCUPANCY TRANSITION CONTEXT\nprevious_occupancy: 1.0\n\n### CURRENT EXTERNAL STATE\noutdoor_temp_c: 31.4\nsolar_irr: 612.0\nprice_now: 0.14231\n\n### FORECAST SUMMARY\noutdoor_temp_change_next_1h_c: 0.8\nsolar_irr_max_next_1h_w_m2: 668.0\nsolar_irr_mean_next_1h_w_m2: 642.5\n\n### ZONE FORECAST\nvalues_shared_by_all_rows:\noccupancy: 1.0\nrows:\n| forecast_outcome_time | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 14:15 | 31.6 | 628.0 |\n| 14:30 | 31.8 | 646.0 |\n| 14:45 | 32.0 | 668.0 |\n| 15:00 | 32.2 | 628.0 |\n\n### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| precool_lead_steps | 4 | 0 | 4 | visible forecast horizon |\n| precool_residual_c | -5.0 | -5.0 | 5.0 | residual safety bound |\n| pmv_band_lo | 0.3 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_band_hi | 0.45 | -0.5 | 0.5 | PMV evaluation range |\n| pmv_step_c | 0.3 | 0.0 | 5.0 | residual safety bound |\nrules:\n{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}}\n{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"abs_pmv_score_limit\":0.5,\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\nvalues_shared_by_all_rows:\nundirected: false\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| ce_aa18e859 | outdoor_temp | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_fc68b8f7 | solar_irr | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_ebd13728 | cooling_setpoint | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_d8c6ee57 | occupancy | Positive Corr | zone_temp | Immediate | Strong Impact |\n| ce_e8f5f362 | outdoor_temp | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_5a968228 | solar_irr | Positive Corr | power_meters | Delayed | Weak Impact |\n| ce_00f91137 | occupancy | Positive Corr | power_meters | Delayed | Strong Impact |\n| ce_660795c7 | cooling_setpoint | Negative Corr | power_meters | Immediate | Strong Impact |\n\n### ALLOCATION\nallocation: {\"zone_reserved_allowance_c\":2.0,\"shared_pool_available_before_settlement_c\":4.0,\"shared_settlement_priority_rank\":1}\n\n### WORKING MEMORY\ncompleted_interval: [13:00, 14:00)\nzones: [\"eas\"]\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\ncompleted_decision:\nvalues_shared_by_all_rows:\naction: {\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-interval fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0}\nlesson: 稳定占用状态与正向暖侧舒适余量同时出现。\nrecent_state_history:\nvalues_shared_by_all_rows:\ntemp_c: 24.58\npmv: 0.43\noccupancy: 1.0\nsetpoint_c: 25.0\nstate_times: [\"13:00\",\"13:15\",\"13:30\",\"13:45\"]\nOBSERVED CONTEXT HISTORY:\nabs_pmv_score_limit: 0.5\n| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | eas.temp_rise_to_warm_pmv_edge_c | eas.temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- | --- |\n| 13:00 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |\n| 13:15 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |\n| 13:30 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |\n| 13:45 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |\ncontrol_action_history:\nvalues_shared_by_all_rows:\nregime: steady_state_occupancy\nsetpoint_c: 25.0\nmatched_rule: occupied_hold\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\ntime_varying_actions:\n| action_time | outcome_time |\n| --- | --- |\n| 13:00 | 13:15 |\n| 13:15 | 13:30 |\n| 13:30 | 13:45 |\n| 13:45 | 14:00 |\nprevious_decision_forecast:\nvalues_shared_by_all_rows:\noccupancy: 1.0\noutcome_times: [\"13:15\",\"13:30\",\"13:45\",\"14:00\"]\nderived_feature_interval: [13:00, 14:00)\nderived_features:\nvalues_shared_by_all_rows:\ntemp_delta_15min_c: 0.0\ntemp_delta_1h_c: 0.0\ntemp_slope_c_per_hour: 0.0\npmv_delta_15min: 0.0\npmv_delta_1h: 0.0\nsetpoint_delta_15min_c: 0.0\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\noccupied_peak_abs_pmv: 0.43\nsetpoint_tv_c: 0.0\nsetpoint_reversals: 0\n",
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
      "rationale": "East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。",
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
      "content": "角色\n从已完成控制时段提炼每区 Lesson。\n\n目标\n在维持舒适的同时尽可能降低能耗花费。已完成时段的 reward 是冻结评价函数对能耗花费、舒适度和动作平滑性的量化参考；累计 reward 越高，表示上述同一目标的综合结果越好。\n\n证据\n从每区已完成的 Context、Action 与 Outcome 中提炼一条有用的已观察关系或权衡。\n\n硬边界\nLesson 事实只来自已完成时段；表达观察或权衡，不写命令、目标或无证据结论。\n\n输出\n只返回裸 JSON：{\"hourly_lessons\":[{\"zone\":...,\"lesson\":...}]}。每区一次，无额外字段。\n",
      "role": "system"
    },
    {
      "content": "### COMPLETED CONTROL INTERVAL\ninterval: [14:00, 15:00)\naction_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\"]\noutcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\ncontrol_period: 15 min\nsite_result: {\"site_cost\":3.1214,\"site_energy_kwh\":21.9425}\nOBJECTIVE FEEDBACK:\ninterval_reward: -11.5744\nsite_reward_history:\n| action_time | outcome_time | site_step_reward | site_energy_penalty | site_comfort_penalty | site_smoothness_penalty |\n| --- | --- | --- | --- | --- | --- |\n| 14:00 | 14:15 | -2.8338 | 2.8314 | 0.0 | 0.0023 |\n| 14:15 | 14:30 | -2.8763 | 2.8763 | 0.0 | 0.0 |\n| 14:30 | 14:45 | -2.9145 | 2.9145 | 0.0 | 0.0 |\n| 14:45 | 15:00 | -2.9498 | 2.9475 | 0.0 | 0.0023 |\nzone_penalty_contributions:\n| zone | action_time | outcome_time | zone_comfort_penalty_contribution | zone_smoothness_penalty_contribution |\n| --- | --- | --- | --- | --- |\n| cor | 14:00 | 14:15 | 0.0 | 0.0 |\n| cor | 14:15 | 14:30 | 0.0 | 0.0 |\n| cor | 14:30 | 14:45 | 0.0 | 0.0 |\n| cor | 14:45 | 15:00 | 0.0 | 0.0 |\n| eas | 14:00 | 14:15 | 0.0 | 0.0023 |\n| eas | 14:15 | 14:30 | 0.0 | 0.0 |\n| eas | 14:30 | 14:45 | 0.0 | 0.0 |\n| eas | 14:45 | 15:00 | 0.0 | 0.0023 |\n| nor | 14:00 | 14:15 | 0.0 | 0.0 |\n| nor | 14:15 | 14:30 | 0.0 | 0.0 |\n| nor | 14:30 | 14:45 | 0.0 | 0.0 |\n| nor | 14:45 | 15:00 | 0.0 | 0.0 |\n| sou | 14:00 | 14:15 | 0.0 | 0.0 |\n| sou | 14:15 | 14:30 | 0.0 | 0.0 |\n| sou | 14:30 | 14:45 | 0.0 | 0.0 |\n| sou | 14:45 | 15:00 | 0.0 | 0.0 |\n| wes | 14:00 | 14:15 | 0.0 | 0.0 |\n| wes | 14:15 | 14:30 | 0.0 | 0.0 |\n| wes | 14:30 | 14:45 | 0.0 | 0.0 |\n| wes | 14:45 | 15:00 | 0.0 | 0.0 |\ncompleted_decision:\nvalues_shared_by_all_rows:\naction: {\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0}\ncontext: {\"initial_observation\":{\"last_occupancy\":1.0}}\nno_change_rows:\n| zone | op | rationale | program_version_after |\n| --- | --- | --- | --- |\n| cor | no_change | 当前程序保持了占用舒适余量，且没有证据支持有益修改。 | 0 |\n| nor | no_change | 当前程序与已观察到的稳定占用状态相匹配。 | 0 |\n| sou | no_change | 已观察舒适余量与当前程序不支持其他原子修改。 | 0 |\n| wes | no_change | 给定证据不支持在本小时修改可执行规格。 | 0 |\nset_param_rows:\n| zone | op | rationale | program_version_after | param | to |\n| --- | --- | --- | --- | --- | --- |\n| eas | set_param | East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。 | 1 | pmv_band_hi | 0.4 |\nrecent_state_history:\nvalues_shared_by_all_rows:\noccupancy: 1.0\nvalues_constant_within_each_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0}\n{\"zone\":\"nor\",\"setpoint_c\":25.0}\n{\"zone\":\"sou\",\"setpoint_c\":25.0}\n{\"zone\":\"wes\",\"setpoint_c\":25.0}\nstate_times: [\"14:00\",\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\ntime_varying_measurements:\n| state_time | cor.temp_c | cor.pmv | eas.temp_c | eas.pmv | eas.setpoint_c | nor.temp_c | nor.pmv | sou.temp_c | sou.pmv | wes.temp_c | wes.pmv |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 14:00 | 24.31 | 0.34 | 24.58 | 0.43 | 25.0 | 24.22 | 0.31 | 24.47 | 0.39 | 24.36 | 0.36 |\n| 14:15 | 24.3 | 0.34 | 24.4 | 0.36 | 24.7 | 24.23 | 0.31 | 24.47 | 0.39 | 24.37 | 0.36 |\n| 14:30 | 24.32 | 0.35 | 24.25 | 0.3 | 24.7 | 24.24 | 0.32 | 24.49 | 0.4 | 24.38 | 0.37 |\n| 14:45 | 24.34 | 0.35 | 24.18 | 0.28 | 24.7 | 24.25 | 0.32 | 24.5 | 0.4 | 24.4 | 0.37 |\n| 15:00 | 24.35 | 0.36 | 24.24 | 0.31 | 25.0 | 24.27 | 0.33 | 24.52 | 0.41 | 24.41 | 0.38 |\nOBSERVED CONTEXT HISTORY:\nabs_pmv_score_limit: 0.5\n| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | cor.temp_rise_to_warm_pmv_edge_c | cor.temp_drop_to_cool_pmv_edge_c | eas.temp_rise_to_warm_pmv_edge_c | eas.temp_drop_to_cool_pmv_edge_c | nor.temp_rise_to_warm_pmv_edge_c | nor.temp_drop_to_cool_pmv_edge_c | sou.temp_rise_to_warm_pmv_edge_c | sou.temp_drop_to_cool_pmv_edge_c | wes.temp_rise_to_warm_pmv_edge_c | wes.temp_drop_to_cool_pmv_edge_c |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 14:00 | 31.4 | 612.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\n| 14:15 | 31.6 | 628.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\n| 14:30 | 31.8 | 646.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\n| 14:45 | 32.0 | 668.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |\ncontrol_action_history:\nvalues_shared_by_all_rows:\nregime: steady_state_occupancy\nactuator_bounds: false\nsetpoint_rate_limit: false\ncomfort_recovery: false\nvalues_constant_within_each_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"nor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"sou\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"wes\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\ntime_varying_actions:\n| action_time | outcome_time | eas.setpoint_c | eas.matched_rule |\n| --- | --- | --- | --- |\n| 14:00 | 14:15 | 24.7 | pmv_lower |\n| 14:15 | 14:30 | 24.7 | occupied_hold |\n| 14:30 | 14:45 | 24.7 | occupied_hold |\n| 14:45 | 15:00 | 25.0 | pmv_raise |\nprevious_decision_forecast:\nvalues_shared_by_all_rows:\noccupancy: 1.0\noutcome_times: [\"14:15\",\"14:30\",\"14:45\",\"15:00\"]\nderived_feature_interval: [14:00, 15:00)\nderived_features:\nvalues_shared_by_all_rows:\nsetpoint_delta_1h_c: 0.0\ndiscomfort_zone_h: 0.0\ndiscomfort_pmv_h: 0.0\nsetpoint_reversals: 0\nrows:\n| zone | temp_delta_15min_c | temp_delta_1h_c | temp_slope_c_per_hour | pmv_delta_15min | pmv_delta_1h | setpoint_delta_15min_c | occupied_peak_abs_pmv | setpoint_tv_c |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| cor | 0.01 | 0.04 | 0.04 | 0.01 | 0.02 | 0.0 | 0.36 | 0.0 |\n| eas | 0.06 | -0.34 | -0.34 | 0.03 | -0.12 | 0.3 | 0.36 | 0.3 |\n| nor | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.33 | 0.0 |\n| sou | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.41 | 0.0 |\n| wes | 0.01 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.38 | 0.0 |\n",
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
      "lesson": "稳定设定点与平稳的占用 PMV 及正向暖侧余量同时出现。",
      "zone": "cor"
    },
    {
      "lesson": "更紧的上侧阈值之后出现了有界制冷响应，同时占用 PMV 保持在舒适带内。",
      "zone": "eas"
    },
    {
      "lesson": "占用保持分支与较小的温度和 PMV 变化同时出现。",
      "zone": "nor"
    },
    {
      "lesson": "在较高太阳辐射下，占用保持分支仍保留了正向暖侧余量。",
      "zone": "sou"
    },
    {
      "lesson": "稳定动作与渐进的占用温度响应及有界 PMV 同时出现。",
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
values_shared_by_all_rows:
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
values_shared_by_all_rows:
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
values_shared_by_all_rows:
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
per_zone_reserved_cap_c: 5.0

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
site_result: {"site_cost":3.02,"site_energy_kwh":21.1}
completed_decision:
values_shared_by_all_rows:
action: {"proposal":{"op":"no_change"},"admission":{"status":"accepted"},"program_version_before":0,"program_version_after":0}
lesson: 稳定占用状态与正向暖侧舒适余量同时出现。
recent_state_history:
values_shared_by_all_rows:
occupancy: 1.0
setpoint_c: 25.0
values_constant_within_each_zone:
{"zone":"cor","temp_c":24.31,"pmv":0.34}
{"zone":"eas","temp_c":24.58,"pmv":0.43}
{"zone":"nor","temp_c":24.22,"pmv":0.31}
{"zone":"sou","temp_c":24.47,"pmv":0.39}
{"zone":"wes","temp_c":24.36,"pmv":0.36}
state_times: ["13:00","13:15","13:30","13:45"]
OBSERVED CONTEXT HISTORY:
abs_pmv_score_limit: 0.5
| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | cor.temp_rise_to_warm_pmv_edge_c | cor.temp_drop_to_cool_pmv_edge_c | eas.temp_rise_to_warm_pmv_edge_c | eas.temp_drop_to_cool_pmv_edge_c | nor.temp_rise_to_warm_pmv_edge_c | nor.temp_drop_to_cool_pmv_edge_c | sou.temp_rise_to_warm_pmv_edge_c | sou.temp_drop_to_cool_pmv_edge_c | wes.temp_rise_to_warm_pmv_edge_c | wes.temp_drop_to_cool_pmv_edge_c |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13:00 | 31.4 | 612.0 | 0.14231 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |
| 13:15 | 31.4 | 612.0 | 0.14231 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |
| 13:30 | 31.4 | 612.0 | 0.14231 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |
| 13:45 | 31.4 | 612.0 | 0.14231 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |
control_action_history:
values_shared_by_all_rows:
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
previous_decision_forecast:
values_shared_by_all_rows:
occupancy: 1.0
outcome_times: ["13:15","13:30","13:45","14:00"]
derived_feature_interval: [13:00, 14:00)
derived_features:
values_shared_by_all_rows:
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
### Orchestrator audit view

```json
{
  "canonical_sha256": "4ec68fc66d9b11ef63a6fa390c8536162ce987866d6a1c8db8b4c48f99470089",
  "compact_sha256": "da0db35f51928b09e02b4799390ca8aa20541086861b56ec58c4893437d2320b",
  "field_manifest": {
    "ALLOCATION LIMITS": [
      "/zones/[]",
      "/site_cap_c",
      "/per_zone_reserved_cap_c"
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
      "/previous_priority/[]"
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
      "/[]/context/abs_pmv_score_limit",
      "/[]/context/observed_context_history/outdoor_temperature_c/[]",
      "/[]/context/observed_context_history/solar_irradiance_w_m2/[]",
      "/[]/context/observed_context_history/electricity_price/[]",
      "/[]/context/observed_context_history/temp_rise_to_warm_pmv_edge_c/[]",
      "/[]/context/observed_context_history/temp_drop_to_cool_pmv_edge_c/[]",
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
values_shared_by_all_rows:
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
{"id":"precool","when":[{"field":"occupied_now","op":"==","value":0},{"field":"precool_due","op":"==","value":1}],"then":{"op":"set_residual","value":{"param":"precool_residual_c"}}}
{"id":"pmv_raise","when":[{"field":"occupied_now","op":"==","value":1},{"field":"last_pmv","op":"<","value":{"param":"pmv_band_lo"}}],"then":{"op":"step_setpoint","value":{"param":"pmv_step_c"}}}
{"id":"pmv_lower","when":[{"field":"occupied_now","op":"==","value":1},{"field":"last_pmv","op":">","value":{"param":"pmv_band_hi"}}],"then":{"op":"step_setpoint","value":{"neg_param":"pmv_step_c"}}}
{"id":"anchor","when":[{"field":"occupied_now","op":"==","value":1},{"field":"occupied_last","op":"==","value":0}],"then":{"op":"set_residual","value":0.0}}
{"id":"occupied_hold","when":[{"field":"occupied_now","op":"==","value":1}],"then":{"op":"hold_setpoint"}}
{"id":"unoccupied_hold","when":[{"field":"occupied_now","op":"==","value":0}],"then":{"op":"set_residual","value":0.0}}
rule_and_weather_limits: {"new_rule":{"condition_fields":["last_pmv","occupied_last","occupied_now","outdoor_temp_change_next_1h_c","precool_due","solar_irr_max_next_1h_w_m2","solar_irr_mean_next_1h_w_m2"],"comparisons":["<","<=",">",">=","==","!="],"comparison_value":"number or parameter name","action_types":["set_residual","step_setpoint","hold_setpoint"],"max_rules":8},"weather_literals":{"must_be":"finite numbers","parameter_refs":"forbidden"}}
control_domain: {"domain_id":"cooling","controlled_setpoint":"zone cooling setpoint","unit":"degC","hard_bounds_c":[20.0,30.0],"occupied_base_c":25.0,"unoccupied_base_c":30.0,"abs_pmv_score_limit":0.5,"preconditioning":{"label":"precool","lead_steps":4,"target_c":25.0},"energy_intensive_setpoint_direction":"decrease"}

### CAUSAL EVIDENCE
values_shared_by_all_rows:
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
allocation: {"zone_reserved_allowance_c":2.0,"shared_pool_available_before_settlement_c":4.0,"shared_settlement_priority_rank":1}

### WORKING MEMORY
completed_interval: [13:00, 14:00)
zones: ["eas"]
site_result: {"site_cost":3.02,"site_energy_kwh":21.1}
completed_decision:
values_shared_by_all_rows:
action: {"proposal":{"op":"no_change","rationale":"completed-interval fixture"},"admission":{"status":"accepted"},"program_version_before":0,"program_version_after":0}
lesson: 稳定占用状态与正向暖侧舒适余量同时出现。
recent_state_history:
values_shared_by_all_rows:
temp_c: 24.58
pmv: 0.43
occupancy: 1.0
setpoint_c: 25.0
state_times: ["13:00","13:15","13:30","13:45"]
OBSERVED CONTEXT HISTORY:
abs_pmv_score_limit: 0.5
| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | eas.temp_rise_to_warm_pmv_edge_c | eas.temp_drop_to_cool_pmv_edge_c |
| --- | --- | --- | --- | --- | --- |
| 13:00 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |
| 13:15 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |
| 13:30 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |
| 13:45 | 31.4 | 612.0 | 0.1423 | 0.34 | 2.72 |
control_action_history:
values_shared_by_all_rows:
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
previous_decision_forecast:
values_shared_by_all_rows:
occupancy: 1.0
outcome_times: ["13:15","13:30","13:45","14:00"]
derived_feature_interval: [13:00, 14:00)
derived_features:
values_shared_by_all_rows:
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

### ACTIVE LONG-TERM EXPERIENCE SLOTS
values_shared_by_all_rows:
revision: 1
experience: East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.
rows:
| regime |
| --- |
| steady_state_occupancy |
### East Executor audit view

```json
{
  "canonical_sha256": "71f5a528864fa87d97c89ee9e38dc8aea315e8ffdc1386585725beeb7a72db5b",
  "compact_sha256": "d8d0b0ac8275511ca66bc01e045ad9d23762fdcc4eba7b56031566d5284be78f",
  "field_manifest": {
    "ACTIVE LONG-TERM EXPERIENCE SLOTS": [
      "/[]/regime",
      "/[]/revision",
      "/[]/experience"
    ],
    "ALLOCATION": [
      "/allocation/zone_reserved_allowance_c",
      "/allocation/shared_pool_available_before_settlement_c",
      "/allocation/shared_settlement_priority_rank"
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
      "/[]/context/abs_pmv_score_limit",
      "/[]/context/observed_context_history/outdoor_temperature_c/[]",
      "/[]/context/observed_context_history/solar_irradiance_w_m2/[]",
      "/[]/context/observed_context_history/electricity_price/[]",
      "/[]/context/observed_context_history/temp_rise_to_warm_pmv_edge_c/[]",
      "/[]/context/observed_context_history/temp_drop_to_cool_pmv_edge_c/[]",
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
OBJECTIVE FEEDBACK:
interval_reward: -11.5744
site_reward_history:
| action_time | outcome_time | site_step_reward | site_energy_penalty | site_comfort_penalty | site_smoothness_penalty |
| --- | --- | --- | --- | --- | --- |
| 14:00 | 14:15 | -2.8338 | 2.8314 | 0.0 | 0.0023 |
| 14:15 | 14:30 | -2.8763 | 2.8763 | 0.0 | 0.0 |
| 14:30 | 14:45 | -2.9145 | 2.9145 | 0.0 | 0.0 |
| 14:45 | 15:00 | -2.9498 | 2.9475 | 0.0 | 0.0023 |
zone_penalty_contributions:
| zone | action_time | outcome_time | zone_comfort_penalty_contribution | zone_smoothness_penalty_contribution |
| --- | --- | --- | --- | --- |
| cor | 14:00 | 14:15 | 0.0 | 0.0 |
| cor | 14:15 | 14:30 | 0.0 | 0.0 |
| cor | 14:30 | 14:45 | 0.0 | 0.0 |
| cor | 14:45 | 15:00 | 0.0 | 0.0 |
| eas | 14:00 | 14:15 | 0.0 | 0.0023 |
| eas | 14:15 | 14:30 | 0.0 | 0.0 |
| eas | 14:30 | 14:45 | 0.0 | 0.0 |
| eas | 14:45 | 15:00 | 0.0 | 0.0023 |
| nor | 14:00 | 14:15 | 0.0 | 0.0 |
| nor | 14:15 | 14:30 | 0.0 | 0.0 |
| nor | 14:30 | 14:45 | 0.0 | 0.0 |
| nor | 14:45 | 15:00 | 0.0 | 0.0 |
| sou | 14:00 | 14:15 | 0.0 | 0.0 |
| sou | 14:15 | 14:30 | 0.0 | 0.0 |
| sou | 14:30 | 14:45 | 0.0 | 0.0 |
| sou | 14:45 | 15:00 | 0.0 | 0.0 |
| wes | 14:00 | 14:15 | 0.0 | 0.0 |
| wes | 14:15 | 14:30 | 0.0 | 0.0 |
| wes | 14:30 | 14:45 | 0.0 | 0.0 |
| wes | 14:45 | 15:00 | 0.0 | 0.0 |
completed_decision:
values_shared_by_all_rows:
action: {"admission":{"status":"accepted"},"program_version_before":0}
context: {"initial_observation":{"last_occupancy":1.0}}
no_change_rows:
| zone | op | rationale | program_version_after |
| --- | --- | --- | --- |
| cor | no_change | 当前程序保持了占用舒适余量，且没有证据支持有益修改。 | 0 |
| nor | no_change | 当前程序与已观察到的稳定占用状态相匹配。 | 0 |
| sou | no_change | 已观察舒适余量与当前程序不支持其他原子修改。 | 0 |
| wes | no_change | 给定证据不支持在本小时修改可执行规格。 | 0 |
set_param_rows:
| zone | op | rationale | program_version_after | param | to |
| --- | --- | --- | --- | --- | --- |
| eas | set_param | East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。 | 1 | pmv_band_hi | 0.4 |
recent_state_history:
values_shared_by_all_rows:
occupancy: 1.0
values_constant_within_each_zone:
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
OBSERVED CONTEXT HISTORY:
abs_pmv_score_limit: 0.5
| action_time | outdoor_temperature_c | solar_irradiance_w_m2 | electricity_price | cor.temp_rise_to_warm_pmv_edge_c | cor.temp_drop_to_cool_pmv_edge_c | eas.temp_rise_to_warm_pmv_edge_c | eas.temp_drop_to_cool_pmv_edge_c | nor.temp_rise_to_warm_pmv_edge_c | nor.temp_drop_to_cool_pmv_edge_c | sou.temp_rise_to_warm_pmv_edge_c | sou.temp_drop_to_cool_pmv_edge_c | wes.temp_rise_to_warm_pmv_edge_c | wes.temp_drop_to_cool_pmv_edge_c |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14:00 | 31.4 | 612.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |
| 14:15 | 31.6 | 628.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |
| 14:30 | 31.8 | 646.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |
| 14:45 | 32.0 | 668.0 | 0.1423 | 0.62 | 2.45 | 0.34 | 2.72 | 0.72 | 2.36 | 0.45 | 2.61 | 0.57 | 2.5 |
control_action_history:
values_shared_by_all_rows:
regime: steady_state_occupancy
actuator_bounds: false
setpoint_rate_limit: false
comfort_recovery: false
values_constant_within_each_zone:
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
values_shared_by_all_rows:
occupancy: 1.0
outcome_times: ["14:15","14:30","14:45","15:00"]
derived_feature_interval: [14:00, 15:00)
derived_features:
values_shared_by_all_rows:
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
  "canonical_sha256": "9387841b8b51e9004439b94dbd14c605fe53b50fff525bdf40394f7df3d91279",
  "compact_sha256": "4b6ff1e3df6086f52551bb7a4f138b4a4b1b6aee59244c657ab3668073917da3",
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
      "/[]/context/abs_pmv_score_limit",
      "/[]/context/observed_context_history/outdoor_temperature_c/[]",
      "/[]/context/observed_context_history/solar_irradiance_w_m2/[]",
      "/[]/context/observed_context_history/electricity_price/[]",
      "/[]/context/observed_context_history/temp_rise_to_warm_pmv_edge_c/[]",
      "/[]/context/observed_context_history/temp_drop_to_cool_pmv_edge_c/[]",
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
      "/[]/outcome/objective_feedback/interval_reward",
      "/[]/outcome/objective_feedback/site_step_reward/[]",
      "/[]/outcome/objective_feedback/site_energy_penalty/[]",
      "/[]/outcome/objective_feedback/site_comfort_penalty/[]",
      "/[]/outcome/objective_feedback/site_smoothness_penalty/[]",
      "/[]/outcome/objective_feedback/zone_comfort_penalty_contribution/[]",
      "/[]/outcome/objective_feedback/zone_smoothness_penalty_contribution/[]",
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
