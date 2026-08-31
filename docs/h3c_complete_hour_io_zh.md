# H3C 完整 MZ Air 小时示例：工作记忆与可选状态经验

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
      "content": "角色\n为下一小时在各区域之间分配共享额度。\n\n决策\n在兼顾舒适的同时降低或优化能源成本。使用场地状态、预测、跨区域状态、工作记忆和先前利用率，只选择额度分配与优先顺序。为每个区域的分配给出理由。\n\n因果证据\n通过 causal_edge_ids 引用因果证据中的相关 ID。\n\n硬边界\n只分配共享的高耗能动作额度。它覆盖本小时已接受补丁造成的最坏新增高耗能设定点移动，不是当前残差、设定点或物理功率。区域理由只解释其额度或优先级，不得规定区域控制。\n\n输出\n返回一个符合 allocation contract 的裸 JSON 对象。不返回解释文字、Markdown 围栏或契约之外的字段。allocation_contract：Return exactly these keys, with no others: site_cap_c, zone_budgets_c, priority, rationale_per_zone, causal_edge_ids. Every listed key must be present; rationale_per_zone maps each zone to a nonempty string.\n",
      "role": "system"
    },
    {
      "content": "### CAUSAL EVIDENCE\ncommon:\n```json\n{\"target\":\"power_meters\",\"undirected\":false}\n```\nrows:\n| id | source | relation | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"Delayed\" | \"Weak Impact\" |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"Immediate\" | \"Strong Impact\" |\n\n### ALLOCATION LIMITS\n```json\n{\"zones\":[\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"],\"site_cap_c\":10.0,\"per_zone_cap_c\":5.0}\n```\n\n### CONTROL DOMAIN\n```json\n{\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n```\n\n### WORKING MEMORY\nhour: 41\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\ntime_semantics: decision interval 60 min; physical step 15 min; sample 0 is the hour-start state before action; samples 1-4 are post-action outcomes; current state is sample 4; each action precedes its same-step outcome.\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\nhourly_decision:\ncommon: {\"action\":{\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-hour fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0},\"lesson\":\"稳定占用状态与正向暖侧舒适余量同时出现。\",\"context\":{\"initial_observation\":{\"last_occupancy\":1.0}}}\ncurrent_state: recent_state_history sample 4, step 167\nrecent_state_history:\ncommon: {\"occupancy\":1.0,\"setpoint_c\":25.0}\ntime_axis:\n| sample | step |\n| --- | --- |\n| 0 | 163 |\n| 1 | 164 |\n| 2 | 165 |\n| 3 | 166 |\n| 4 | 167 |\nconstant_by_zone:\n{\"zone\":\"cor\",\"temp_c\":24.31,\"pmv\":0.34}\n{\"zone\":\"eas\",\"temp_c\":24.58,\"pmv\":0.43}\n{\"zone\":\"nor\",\"temp_c\":24.22,\"pmv\":0.31}\n{\"zone\":\"sou\",\"temp_c\":24.47,\"pmv\":0.39}\n{\"zone\":\"wes\",\"temp_c\":24.36,\"pmv\":0.36}\ncontrol_action_history:\ncommon: {\"regime\":\"steady_state_occupancy\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\",\"actuator_bounds\":false,\"setpoint_rate_limit\":false,\"comfort_recovery\":false}\nsteps: [164,165,166,167]\ndecision_time_occupancy_forecast:\ncommon: {\"occupancy\":1.0}\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\nsteps_ahead: [1,2,3,4]\nderived_features:\ncommon:\n```json\n{\"temp_delta_15min_c\":0.0,\"temp_delta_1h_c\":0.0,\"temp_slope_c_per_hour\":0.0,\"pmv_delta_15min\":0.0,\"pmv_delta_1h\":0.0,\"setpoint_delta_15min_c\":0.0,\"setpoint_delta_1h_c\":0.0,\"discomfort_zone_h\":0.0,\"discomfort_pmv_h\":0.0,\"setpoint_tv_c\":0.0,\"setpoint_reversals\":0}\n```\nrows:\n| zone | occupied_peak_abs_pmv |\n| --- | --- |\n| \"cor\" | 0.34 |\n| \"eas\" | 0.43 |\n| \"nor\" | 0.31 |\n| \"sou\" | 0.39 |\n| \"wes\" | 0.36 |\n\n### CROSS-ZONE STATUS\ncommon:\n```json\n{\"current_setpoint_c\":25.0,\"current_occupancy\":1.0,\"next_hour_occupancy\":1.0,\"temp_targets\":{\"precool_residual_c\":-5.0}}\n```\nrows:\n| zone | last_pmv | warmer_c | cooler_c | granted_c | used_c |\n| --- | --- | --- | --- | --- | --- |\n| \"cor\" | 0.34 | 0.62 | 2.45 | 1.0 | 0.0 |\n| \"eas\" | 0.43 | 0.34 | 2.72 | 2.0 | 0.3 |\n| \"nor\" | 0.31 | 0.72 | 2.36 | 1.0 | 0.0 |\n| \"sou\" | 0.39 | 0.45 | 2.61 | 1.0 | 0.0 |\n| \"wes\" | 0.36 | 0.57 | 2.5 | 1.0 | 0.0 |\n\n### PREVIOUS ALLOCATION AND UTILISATION\n```json\n{\"allocation\":{\"site_cap_c\":10.0,\"zone_budgets_c\":{\"cor\":1.0,\"eas\":2.0,\"nor\":1.0,\"sou\":1.0,\"wes\":1.0},\"priority\":[\"eas\",\"sou\",\"wes\",\"cor\",\"nor\"],\"rationale_per_zone\":{\"cor\":\"Core conditions were stable.\",\"eas\":\"East had the smallest warm-side headroom.\",\"nor\":\"North conditions were stable.\",\"sou\":\"South had moderate warm-side headroom.\",\"wes\":\"West had moderate warm-side headroom.\"}},\"utilisation\":{\"granted_c\":6.0,\"used_c\":0.3,\"utilisation\":0.05,\"site_cap_c\":10.0,\"group_remainder_at_the_start_c\":4.0,\"group_remainder_left_c\":3.7,\"residual_used_by\":{\"eas\":0.3}}}\n```\n\n### CURRENT SITE STATE\n```json\n{\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"price_next_hour\":0.16842,\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5}\n```\n\n### SITE FORECAST\nrows:\n| step_ahead | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 1 | 31.6 | 628.0 |\n| 2 | 31.8 | 646.0 |\n| 3 | 32.0 | 668.0 |\n| 4 | 32.2 | 628.0 |\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、舒适余量、因果证据、额度与 WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n通过 causal_edge_ids 引用因果证据中的相关 ID。\n\n硬边界\n额度覆盖本小时已接受补丁造成的最坏新增高耗能设定点移动，不是当前残差、设定点或物理功率。只能通过给定控制规格与操作契约工作；不得编写 Python、完整控制器或直接设定点。\n\n输出\n返回裸 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。包含一个操作。memory_refs 只引用实际使用的有效经验，也可为空。不返回解释文字、Markdown 围栏或额外字段。操作契约：\nroot：patch 是仅包含一个 operation 的列表。\n所有 operation 公共必填：op、rationale。\n所有修改类操作还必须包含 causal_edge_ids。\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule 必须包含 id、when、then。每个 when 条件必须包含 field、op、value。then 必须包含 op；set_residual 或 step_setpoint 还必须包含 value。\n",
      "role": "system"
    },
    {
      "content": "### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| \"precool_lead_steps\" | 4 | 0 | 4 | \"visible forecast horizon\" |\n| \"precool_residual_c\" | -5.0 | -5.0 | 5.0 | \"residual safety bound\" |\n| \"pmv_band_lo\" | 0.3 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_band_hi\" | 0.45 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_step_c\" | 0.3 | 0.0 | 5.0 | \"residual safety bound\" |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\n```json\n{\"undirected\":false}\n```\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Weak Impact\" |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"Immediate\" | \"Strong Impact\" |\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":1.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":4}}\n```\n\n### WORKING MEMORY\nhour: 41\nzones: [\"cor\"]\ntime_semantics: decision interval 60 min; physical step 15 min; sample 0 is the hour-start state before action; samples 1-4 are post-action outcomes; current state is sample 4; each action precedes its same-step outcome.\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\nhourly_decision:\ncommon: {\"action\":{\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-hour fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0},\"lesson\":\"稳定占用状态与正向暖侧舒适余量同时出现。\",\"context\":{\"initial_observation\":{\"last_occupancy\":1.0}}}\ncurrent_state: recent_state_history sample 4, step 167\nrecent_state_history:\ncommon: {\"temp_c\":24.31,\"pmv\":0.34,\"occupancy\":1.0,\"setpoint_c\":25.0}\ntime_axis:\n| sample | step |\n| --- | --- |\n| 0 | 163 |\n| 1 | 164 |\n| 2 | 165 |\n| 3 | 166 |\n| 4 | 167 |\ncontrol_action_history:\ncommon: {\"regime\":\"steady_state_occupancy\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\",\"actuator_bounds\":false,\"setpoint_rate_limit\":false,\"comfort_recovery\":false}\nsteps: [164,165,166,167]\ndecision_time_occupancy_forecast:\ncommon: {\"occupancy\":1.0}\nzones: [\"cor\"]\nsteps_ahead: [1,2,3,4]\nderived_features:\ncommon: {\"temp_delta_15min_c\":0.0,\"temp_delta_1h_c\":0.0,\"temp_slope_c_per_hour\":0.0,\"pmv_delta_15min\":0.0,\"pmv_delta_1h\":0.0,\"setpoint_delta_15min_c\":0.0,\"setpoint_delta_1h_c\":0.0,\"discomfort_zone_h\":0.0,\"discomfort_pmv_h\":0.0,\"occupied_peak_abs_pmv\":0.34,\"setpoint_tv_c\":0.0,\"setpoint_reversals\":0}\n\n### ACTIVE LONG-TERM EXPERIENCES\ncommon:\n```json\n{\"revision\":2,\"experience\":\"Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.\"}\n```\nrows:\n| regime |\n| --- |\n| \"steady_state_occupancy\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"zone_temp_c\":24.31,\"last_pmv\":0.34,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"zone_temperature_distance_to_comfort_edge_c\":{\"warmer_c\":0.62,\"cooler_c\":2.45},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5}\n```\n\n### ZONE FORECAST\ncommon:\n```json\n{\"occupancy\":1.0}\n```\nrows:\n| step_ahead | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 1 | 31.6 | 628.0 |\n| 2 | 31.8 | 646.0 |\n| 3 | 32.0 | 668.0 |\n| 4 | 32.2 | 628.0 |\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、舒适余量、因果证据、额度与 WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n通过 causal_edge_ids 引用因果证据中的相关 ID。\n\n硬边界\n额度覆盖本小时已接受补丁造成的最坏新增高耗能设定点移动，不是当前残差、设定点或物理功率。只能通过给定控制规格与操作契约工作；不得编写 Python、完整控制器或直接设定点。\n\n输出\n返回裸 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。包含一个操作。memory_refs 只引用实际使用的有效经验，也可为空。不返回解释文字、Markdown 围栏或额外字段。操作契约：\nroot：patch 是仅包含一个 operation 的列表。\n所有 operation 公共必填：op、rationale。\n所有修改类操作还必须包含 causal_edge_ids。\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule 必须包含 id、when、then。每个 when 条件必须包含 field、op、value。then 必须包含 op；set_residual 或 step_setpoint 还必须包含 value。\n",
      "role": "system"
    },
    {
      "content": "### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| \"precool_lead_steps\" | 4 | 0 | 4 | \"visible forecast horizon\" |\n| \"precool_residual_c\" | -5.0 | -5.0 | 5.0 | \"residual safety bound\" |\n| \"pmv_band_lo\" | 0.3 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_band_hi\" | 0.45 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_step_c\" | 0.3 | 0.0 | 5.0 | \"residual safety bound\" |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\n```json\n{\"undirected\":false}\n```\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Weak Impact\" |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"Immediate\" | \"Strong Impact\" |\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":2.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":1}}\n```\n\n### WORKING MEMORY\nhour: 41\nzones: [\"eas\"]\ntime_semantics: decision interval 60 min; physical step 15 min; sample 0 is the hour-start state before action; samples 1-4 are post-action outcomes; current state is sample 4; each action precedes its same-step outcome.\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\nhourly_decision:\ncommon: {\"action\":{\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-hour fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0},\"lesson\":\"稳定占用状态与正向暖侧舒适余量同时出现。\",\"context\":{\"initial_observation\":{\"last_occupancy\":1.0}}}\ncurrent_state: recent_state_history sample 4, step 167\nrecent_state_history:\ncommon: {\"temp_c\":24.58,\"pmv\":0.43,\"occupancy\":1.0,\"setpoint_c\":25.0}\ntime_axis:\n| sample | step |\n| --- | --- |\n| 0 | 163 |\n| 1 | 164 |\n| 2 | 165 |\n| 3 | 166 |\n| 4 | 167 |\ncontrol_action_history:\ncommon: {\"regime\":\"steady_state_occupancy\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\",\"actuator_bounds\":false,\"setpoint_rate_limit\":false,\"comfort_recovery\":false}\nsteps: [164,165,166,167]\ndecision_time_occupancy_forecast:\ncommon: {\"occupancy\":1.0}\nzones: [\"eas\"]\nsteps_ahead: [1,2,3,4]\nderived_features:\ncommon: {\"temp_delta_15min_c\":0.0,\"temp_delta_1h_c\":0.0,\"temp_slope_c_per_hour\":0.0,\"pmv_delta_15min\":0.0,\"pmv_delta_1h\":0.0,\"setpoint_delta_15min_c\":0.0,\"setpoint_delta_1h_c\":0.0,\"discomfort_zone_h\":0.0,\"discomfort_pmv_h\":0.0,\"occupied_peak_abs_pmv\":0.43,\"setpoint_tv_c\":0.0,\"setpoint_reversals\":0}\n\n### ACTIVE LONG-TERM EXPERIENCES\ncommon:\n```json\n{\"revision\":1,\"experience\":\"East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.\"}\n```\nrows:\n| regime |\n| --- |\n| \"steady_state_occupancy\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"zone_temp_c\":24.58,\"last_pmv\":0.43,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"zone_temperature_distance_to_comfort_edge_c\":{\"warmer_c\":0.34,\"cooler_c\":2.72},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5}\n```\n\n### ZONE FORECAST\ncommon:\n```json\n{\"occupancy\":1.0}\n```\nrows:\n| step_ahead | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 1 | 31.6 | 628.0 |\n| 2 | 31.8 | 646.0 |\n| 3 | 32.0 | 668.0 |\n| 4 | 32.2 | 628.0 |\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、舒适余量、因果证据、额度与 WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n通过 causal_edge_ids 引用因果证据中的相关 ID。\n\n硬边界\n额度覆盖本小时已接受补丁造成的最坏新增高耗能设定点移动，不是当前残差、设定点或物理功率。只能通过给定控制规格与操作契约工作；不得编写 Python、完整控制器或直接设定点。\n\n输出\n返回裸 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。包含一个操作。memory_refs 只引用实际使用的有效经验，也可为空。不返回解释文字、Markdown 围栏或额外字段。操作契约：\nroot：patch 是仅包含一个 operation 的列表。\n所有 operation 公共必填：op、rationale。\n所有修改类操作还必须包含 causal_edge_ids。\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule 必须包含 id、when、then。每个 when 条件必须包含 field、op、value。then 必须包含 op；set_residual 或 step_setpoint 还必须包含 value。\n",
      "role": "system"
    },
    {
      "content": "### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| \"precool_lead_steps\" | 4 | 0 | 4 | \"visible forecast horizon\" |\n| \"precool_residual_c\" | -5.0 | -5.0 | 5.0 | \"residual safety bound\" |\n| \"pmv_band_lo\" | 0.3 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_band_hi\" | 0.45 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_step_c\" | 0.3 | 0.0 | 5.0 | \"residual safety bound\" |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\n```json\n{\"undirected\":false}\n```\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Weak Impact\" |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"Immediate\" | \"Strong Impact\" |\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":1.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":5}}\n```\n\n### WORKING MEMORY\nhour: 41\nzones: [\"nor\"]\ntime_semantics: decision interval 60 min; physical step 15 min; sample 0 is the hour-start state before action; samples 1-4 are post-action outcomes; current state is sample 4; each action precedes its same-step outcome.\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\nhourly_decision:\ncommon: {\"action\":{\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-hour fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0},\"lesson\":\"稳定占用状态与正向暖侧舒适余量同时出现。\",\"context\":{\"initial_observation\":{\"last_occupancy\":1.0}}}\ncurrent_state: recent_state_history sample 4, step 167\nrecent_state_history:\ncommon: {\"temp_c\":24.22,\"pmv\":0.31,\"occupancy\":1.0,\"setpoint_c\":25.0}\ntime_axis:\n| sample | step |\n| --- | --- |\n| 0 | 163 |\n| 1 | 164 |\n| 2 | 165 |\n| 3 | 166 |\n| 4 | 167 |\ncontrol_action_history:\ncommon: {\"regime\":\"steady_state_occupancy\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\",\"actuator_bounds\":false,\"setpoint_rate_limit\":false,\"comfort_recovery\":false}\nsteps: [164,165,166,167]\ndecision_time_occupancy_forecast:\ncommon: {\"occupancy\":1.0}\nzones: [\"nor\"]\nsteps_ahead: [1,2,3,4]\nderived_features:\ncommon: {\"temp_delta_15min_c\":0.0,\"temp_delta_1h_c\":0.0,\"temp_slope_c_per_hour\":0.0,\"pmv_delta_15min\":0.0,\"pmv_delta_1h\":0.0,\"setpoint_delta_15min_c\":0.0,\"setpoint_delta_1h_c\":0.0,\"discomfort_zone_h\":0.0,\"discomfort_pmv_h\":0.0,\"occupied_peak_abs_pmv\":0.31,\"setpoint_tv_c\":0.0,\"setpoint_reversals\":0}\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"zone_temp_c\":24.22,\"last_pmv\":0.31,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"zone_temperature_distance_to_comfort_edge_c\":{\"warmer_c\":0.72,\"cooler_c\":2.36},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5}\n```\n\n### ZONE FORECAST\ncommon:\n```json\n{\"occupancy\":1.0}\n```\nrows:\n| step_ahead | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 1 | 31.6 | 628.0 |\n| 2 | 31.8 | 646.0 |\n| 3 | 32.0 | 668.0 |\n| 4 | 32.2 | 628.0 |\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、舒适余量、因果证据、额度与 WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n通过 causal_edge_ids 引用因果证据中的相关 ID。\n\n硬边界\n额度覆盖本小时已接受补丁造成的最坏新增高耗能设定点移动，不是当前残差、设定点或物理功率。只能通过给定控制规格与操作契约工作；不得编写 Python、完整控制器或直接设定点。\n\n输出\n返回裸 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。包含一个操作。memory_refs 只引用实际使用的有效经验，也可为空。不返回解释文字、Markdown 围栏或额外字段。操作契约：\nroot：patch 是仅包含一个 operation 的列表。\n所有 operation 公共必填：op、rationale。\n所有修改类操作还必须包含 causal_edge_ids。\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule 必须包含 id、when、then。每个 when 条件必须包含 field、op、value。then 必须包含 op；set_residual 或 step_setpoint 还必须包含 value。\n",
      "role": "system"
    },
    {
      "content": "### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| \"precool_lead_steps\" | 4 | 0 | 4 | \"visible forecast horizon\" |\n| \"precool_residual_c\" | -5.0 | -5.0 | 5.0 | \"residual safety bound\" |\n| \"pmv_band_lo\" | 0.3 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_band_hi\" | 0.45 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_step_c\" | 0.3 | 0.0 | 5.0 | \"residual safety bound\" |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\n```json\n{\"undirected\":false}\n```\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Weak Impact\" |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"Immediate\" | \"Strong Impact\" |\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":1.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":2}}\n```\n\n### WORKING MEMORY\nhour: 41\nzones: [\"sou\"]\ntime_semantics: decision interval 60 min; physical step 15 min; sample 0 is the hour-start state before action; samples 1-4 are post-action outcomes; current state is sample 4; each action precedes its same-step outcome.\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\nhourly_decision:\ncommon: {\"action\":{\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-hour fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0},\"lesson\":\"稳定占用状态与正向暖侧舒适余量同时出现。\",\"context\":{\"initial_observation\":{\"last_occupancy\":1.0}}}\ncurrent_state: recent_state_history sample 4, step 167\nrecent_state_history:\ncommon: {\"temp_c\":24.47,\"pmv\":0.39,\"occupancy\":1.0,\"setpoint_c\":25.0}\ntime_axis:\n| sample | step |\n| --- | --- |\n| 0 | 163 |\n| 1 | 164 |\n| 2 | 165 |\n| 3 | 166 |\n| 4 | 167 |\ncontrol_action_history:\ncommon: {\"regime\":\"steady_state_occupancy\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\",\"actuator_bounds\":false,\"setpoint_rate_limit\":false,\"comfort_recovery\":false}\nsteps: [164,165,166,167]\ndecision_time_occupancy_forecast:\ncommon: {\"occupancy\":1.0}\nzones: [\"sou\"]\nsteps_ahead: [1,2,3,4]\nderived_features:\ncommon: {\"temp_delta_15min_c\":0.0,\"temp_delta_1h_c\":0.0,\"temp_slope_c_per_hour\":0.0,\"pmv_delta_15min\":0.0,\"pmv_delta_1h\":0.0,\"setpoint_delta_15min_c\":0.0,\"setpoint_delta_1h_c\":0.0,\"discomfort_zone_h\":0.0,\"discomfort_pmv_h\":0.0,\"occupied_peak_abs_pmv\":0.39,\"setpoint_tv_c\":0.0,\"setpoint_reversals\":0}\n\n### ACTIVE LONG-TERM EXPERIENCES\ncommon:\n```json\n{\"revision\":2,\"experience\":\"South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.\"}\n```\nrows:\n| regime |\n| --- |\n| \"steady_state_occupancy\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"zone_temp_c\":24.47,\"last_pmv\":0.39,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"zone_temperature_distance_to_comfort_edge_c\":{\"warmer_c\":0.45,\"cooler_c\":2.61},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5}\n```\n\n### ZONE FORECAST\ncommon:\n```json\n{\"occupancy\":1.0}\n```\nrows:\n| step_ahead | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 1 | 31.6 | 628.0 |\n| 2 | 31.8 | 646.0 |\n| 3 | 32.0 | 668.0 |\n| 4 | 32.2 | 628.0 |\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、舒适余量、因果证据、额度与 WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n通过 causal_edge_ids 引用因果证据中的相关 ID。\n\n硬边界\n额度覆盖本小时已接受补丁造成的最坏新增高耗能设定点移动，不是当前残差、设定点或物理功率。只能通过给定控制规格与操作契约工作；不得编写 Python、完整控制器或直接设定点。\n\n输出\n返回裸 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。包含一个操作。memory_refs 只引用实际使用的有效经验，也可为空。不返回解释文字、Markdown 围栏或额外字段。操作契约：\nroot：patch 是仅包含一个 operation 的列表。\n所有 operation 公共必填：op、rationale。\n所有修改类操作还必须包含 causal_edge_ids。\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule 必须包含 id、when、then。每个 when 条件必须包含 field、op、value。then 必须包含 op；set_residual 或 step_setpoint 还必须包含 value。\n",
      "role": "system"
    },
    {
      "content": "### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| \"precool_lead_steps\" | 4 | 0 | 4 | \"visible forecast horizon\" |\n| \"precool_residual_c\" | -5.0 | -5.0 | 5.0 | \"residual safety bound\" |\n| \"pmv_band_lo\" | 0.3 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_band_hi\" | 0.45 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_step_c\" | 0.3 | 0.0 | 5.0 | \"residual safety bound\" |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\n```json\n{\"undirected\":false}\n```\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Weak Impact\" |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"Immediate\" | \"Strong Impact\" |\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":1.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":3}}\n```\n\n### WORKING MEMORY\nhour: 41\nzones: [\"wes\"]\ntime_semantics: decision interval 60 min; physical step 15 min; sample 0 is the hour-start state before action; samples 1-4 are post-action outcomes; current state is sample 4; each action precedes its same-step outcome.\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\nhourly_decision:\ncommon: {\"action\":{\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-hour fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0},\"lesson\":\"稳定占用状态与正向暖侧舒适余量同时出现。\",\"context\":{\"initial_observation\":{\"last_occupancy\":1.0}}}\ncurrent_state: recent_state_history sample 4, step 167\nrecent_state_history:\ncommon: {\"temp_c\":24.36,\"pmv\":0.36,\"occupancy\":1.0,\"setpoint_c\":25.0}\ntime_axis:\n| sample | step |\n| --- | --- |\n| 0 | 163 |\n| 1 | 164 |\n| 2 | 165 |\n| 3 | 166 |\n| 4 | 167 |\ncontrol_action_history:\ncommon: {\"regime\":\"steady_state_occupancy\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\",\"actuator_bounds\":false,\"setpoint_rate_limit\":false,\"comfort_recovery\":false}\nsteps: [164,165,166,167]\ndecision_time_occupancy_forecast:\ncommon: {\"occupancy\":1.0}\nzones: [\"wes\"]\nsteps_ahead: [1,2,3,4]\nderived_features:\ncommon: {\"temp_delta_15min_c\":0.0,\"temp_delta_1h_c\":0.0,\"temp_slope_c_per_hour\":0.0,\"pmv_delta_15min\":0.0,\"pmv_delta_1h\":0.0,\"setpoint_delta_15min_c\":0.0,\"setpoint_delta_1h_c\":0.0,\"discomfort_zone_h\":0.0,\"discomfort_pmv_h\":0.0,\"occupied_peak_abs_pmv\":0.36,\"setpoint_tv_c\":0.0,\"setpoint_reversals\":0}\n\n### ACTIVE LONG-TERM EXPERIENCES\ncommon:\n```json\n{\"revision\":1,\"experience\":\"West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.\"}\n```\nrows:\n| regime |\n| --- |\n| \"steady_state_occupancy\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"zone_temp_c\":24.36,\"last_pmv\":0.36,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"zone_temperature_distance_to_comfort_edge_c\":{\"warmer_c\":0.57,\"cooler_c\":2.5},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5}\n```\n\n### ZONE FORECAST\ncommon:\n```json\n{\"occupancy\":1.0}\n```\nrows:\n| step_ahead | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 1 | 31.6 | 628.0 |\n| 2 | 31.8 | 646.0 |\n| 3 | 32.0 | 668.0 |\n| 4 | 32.2 | 628.0 |\n",
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
## 5. 四个物理控制step

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
        "action_time_seconds": 17510400,
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
        "outcome_time_seconds": 17511300,
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
        "action_time_seconds": 17510400,
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
        "outcome_time_seconds": 17511300,
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
        "action_time_seconds": 17510400,
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
        "outcome_time_seconds": 17511300,
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
        "action_time_seconds": 17510400,
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
        "outcome_time_seconds": 17511300,
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
        "action_time_seconds": 17510400,
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
        "outcome_time_seconds": 17511300,
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
        "action_time_seconds": 17511300,
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
        "outcome_time_seconds": 17512200,
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
        "action_time_seconds": 17511300,
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
        "outcome_time_seconds": 17512200,
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
        "action_time_seconds": 17511300,
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
        "outcome_time_seconds": 17512200,
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
        "action_time_seconds": 17511300,
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
        "outcome_time_seconds": 17512200,
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
        "action_time_seconds": 17511300,
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
        "outcome_time_seconds": 17512200,
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
        "action_time_seconds": 17512200,
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
        "outcome_time_seconds": 17513100,
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
        "action_time_seconds": 17512200,
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
        "outcome_time_seconds": 17513100,
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
        "action_time_seconds": 17512200,
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
        "outcome_time_seconds": 17513100,
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
        "action_time_seconds": 17512200,
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
        "outcome_time_seconds": 17513100,
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
        "action_time_seconds": 17512200,
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
        "outcome_time_seconds": 17513100,
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
        "action_time_seconds": 17513100,
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
        "outcome_time_seconds": 17514000,
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
        "action_time_seconds": 17513100,
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
        "outcome_time_seconds": 17514000,
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
        "action_time_seconds": 17513100,
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
        "outcome_time_seconds": 17514000,
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
        "action_time_seconds": 17513100,
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
        "outcome_time_seconds": 17514000,
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
        "action_time_seconds": 17513100,
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
        "outcome_time_seconds": 17514000,
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
      "content": "角色\n解释刚刚结束小时的确定性结果。\n\n证据\n对每个区域，从已完成的 Context、Action 与 Outcome 中提炼一条有用的已观察关系或权衡；将其与展示的合格状态槽比较，并最多选择一个记忆操作。\n\n硬边界\nLesson 是基于证据的观察、关系或权衡，不是命令、目标或无依据结论。存储经验描述该区域在指定状态下贯穿运行的热响应、控制偏好或权衡。只修改展示的合格状态；replace/delete 使用其 revision。\n\n输出\n返回裸 JSON：{\"hourly_lessons\":[{\"zone\":...,\"lesson\":...}],\"memory_operations\":[...]}；每个给定区域在两个列表中各出现一次。每个记忆操作都需要 zone 与 op，额外必填字段：\n| op | 必填 |\n| --- | --- |\n| no_change | — |\n| add | regime, experience |\n| replace | regime, expected_revision, experience |\n| delete | regime, expected_revision |\n不返回解释文字、Markdown 围栏或额外字段。\n",
      "role": "system"
    },
    {
      "content": "### COMPLETED HOUR EVIDENCE\nhour: 42\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\ntime_semantics: decision interval 60 min; physical step 15 min; sample 0 is the hour-start state before action; samples 1-4 are post-action outcomes; current state is sample 4; each action precedes its same-step outcome.\nsite_result: {\"site_cost\":3.1214,\"site_energy_kwh\":21.9425}\nhourly_decision:\ncommon:\n```json\n{\"action\":{\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0},\"context\":{\"initial_observation\":{\"last_occupancy\":1.0}}}\n```\nrows:\n| zone | op | rationale | program_version_after |\n| --- | --- | --- | --- |\n| \"cor\" | \"no_change\" | \"当前程序保持了占用舒适余量，且没有证据支持有益修改。\" | 0 |\n| \"nor\" | \"no_change\" | \"当前程序与已观察到的稳定占用状态相匹配。\" | 0 |\n| \"sou\" | \"no_change\" | \"已观察舒适余量与当前程序不支持其他原子修改。\" | 0 |\n| \"wes\" | \"no_change\" | \"给定证据不支持在本小时修改可执行规格。\" | 0 |\n| zone | op | rationale | program_version_after | param | to |\n| --- | --- | --- | --- | --- | --- |\n| \"eas\" | \"set_param\" | \"East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。\" | 1 | \"pmv_band_hi\" | 0.4 |\ncurrent_state: recent_state_history sample 4, step 171\nrecent_state_history:\ncommon: {\"occupancy\":1.0}\ntime_axis:\n| sample | step |\n| --- | --- |\n| 0 | 167 |\n| 1 | 168 |\n| 2 | 169 |\n| 3 | 170 |\n| 4 | 171 |\nconstant_by_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0}\n{\"zone\":\"nor\",\"setpoint_c\":25.0}\n{\"zone\":\"sou\",\"setpoint_c\":25.0}\n{\"zone\":\"wes\",\"setpoint_c\":25.0}\ntime_varying_measurements:\n| sample | cor.temp_c | cor.pmv | eas.temp_c | eas.pmv | eas.setpoint_c | nor.temp_c | nor.pmv | sou.temp_c | sou.pmv | wes.temp_c | wes.pmv |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 0 | 24.31 | 0.34 | 24.58 | 0.43 | 25.0 | 24.22 | 0.31 | 24.47 | 0.39 | 24.36 | 0.36 |\n| 1 | 24.3 | 0.34 | 24.4 | 0.36 | 24.7 | 24.23 | 0.31 | 24.47 | 0.39 | 24.37 | 0.36 |\n| 2 | 24.32 | 0.35 | 24.25 | 0.3 | 24.7 | 24.24 | 0.32 | 24.49 | 0.4 | 24.38 | 0.37 |\n| 3 | 24.34 | 0.35 | 24.18 | 0.28 | 24.7 | 24.25 | 0.32 | 24.5 | 0.4 | 24.4 | 0.37 |\n| 4 | 24.35 | 0.36 | 24.24 | 0.31 | 25.0 | 24.27 | 0.33 | 24.52 | 0.41 | 24.41 | 0.38 |\ncontrol_action_history:\ncommon: {\"regime\":\"steady_state_occupancy\",\"actuator_bounds\":false,\"setpoint_rate_limit\":false,\"comfort_recovery\":false}\nconstant_by_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"nor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"sou\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"wes\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\ntime_varying_actions:\n| step | eas.setpoint_c | eas.matched_rule |\n| --- | --- | --- |\n| 168 | 24.7 | \"pmv_lower\" |\n| 169 | 24.7 | \"occupied_hold\" |\n| 170 | 24.7 | \"occupied_hold\" |\n| 171 | 25.0 | \"pmv_raise\" |\ndecision_time_occupancy_forecast:\ncommon: {\"occupancy\":1.0}\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\nsteps_ahead: [1,2,3,4]\nderived_features:\ncommon:\n```json\n{\"setpoint_delta_1h_c\":0.0,\"discomfort_zone_h\":0.0,\"discomfort_pmv_h\":0.0,\"setpoint_reversals\":0}\n```\nrows:\n| zone | temp_delta_15min_c | temp_delta_1h_c | temp_slope_c_per_hour | pmv_delta_15min | pmv_delta_1h | setpoint_delta_15min_c | occupied_peak_abs_pmv | setpoint_tv_c |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| \"cor\" | 0.01 | 0.04 | 0.04 | 0.01 | 0.02 | 0.0 | 0.36 | 0.0 |\n| \"eas\" | 0.06 | -0.34 | -0.34 | 0.03 | -0.12 | 0.3 | 0.36 | 0.3 |\n| \"nor\" | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.33 | 0.0 |\n| \"sou\" | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.41 | 0.0 |\n| \"wes\" | 0.01 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.38 | 0.0 |\n\n### ELIGIBLE LONG-TERM EXPERIENCE SLOTS\nrows:\n| zone | regime | revision | experience |\n| --- | --- | --- | --- |\n| \"cor\" | \"steady_state_occupancy\" | 2 | \"Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.\" |\n| \"eas\" | \"steady_state_occupancy\" | 1 | \"East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.\" |\n| \"sou\" | \"steady_state_occupancy\" | 2 | \"South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.\" |\n| \"wes\" | \"steady_state_occupancy\" | 1 | \"West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.\" |\n| zone | regime | state |\n| --- | --- | --- |\n| \"nor\" | \"steady_state_occupancy\" | \"empty\" |\n",
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
## 7. 完整小时记录与下一小时Working Memory

### Completed-hour records

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
### Next-hour Orchestrator working memory

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
### Next-hour East Executor working memory

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
## 9. 长期经验读取、CRUD与下一小时Executor输入

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
### Complete next-hour East Executor request

```json
{
  "messages": [
    {
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、舒适余量、因果证据、额度与 WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n通过 causal_edge_ids 引用因果证据中的相关 ID。\n\n硬边界\n额度覆盖本小时已接受补丁造成的最坏新增高耗能设定点移动，不是当前残差、设定点或物理功率。只能通过给定控制规格与操作契约工作；不得编写 Python、完整控制器或直接设定点。\n\n输出\n返回裸 JSON：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。包含一个操作。memory_refs 只引用实际使用的有效经验，也可为空。不返回解释文字、Markdown 围栏或额外字段。操作契约：\nroot：patch 是仅包含一个 operation 的列表。\n所有 operation 公共必填：op、rationale。\n所有修改类操作还必须包含 causal_edge_ids。\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule 必须包含 id、when、then。每个 when 条件必须包含 field、op、value。then 必须包含 op；set_residual 或 step_setpoint 还必须包含 value。\n",
      "role": "system"
    },
    {
      "content": "### CONTROL SPECIFICATION\nprogram_version: 1\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| \"precool_lead_steps\" | 4 | 0 | 4 | \"visible forecast horizon\" |\n| \"precool_residual_c\" | -5.0 | -5.0 | 5.0 | \"residual safety bound\" |\n| \"pmv_band_lo\" | 0.3 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_band_hi\" | 0.4 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_step_c\" | 0.3 | 0.0 | 5.0 | \"residual safety bound\" |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\n```json\n{\"undirected\":false}\n```\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Weak Impact\" |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"Immediate\" | \"Strong Impact\" |\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":1.7,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":1}}\n```\n\n### WORKING MEMORY\nhour: 42\nzones: [\"eas\"]\ntime_semantics: decision interval 60 min; physical step 15 min; sample 0 is the hour-start state before action; samples 1-4 are post-action outcomes; current state is sample 4; each action precedes its same-step outcome.\nsite_result: {\"site_cost\":3.1214,\"site_energy_kwh\":21.9425}\nhourly_decision:\ncommon: {\"action\":{\"proposal\":{\"op\":\"set_param\",\"rationale\":\"East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。\",\"param\":\"pmv_band_hi\",\"to\":0.4},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":1},\"lesson\":\"更紧的上侧阈值之后出现了有界制冷响应，同时占用 PMV 保持在舒适带内。\",\"context\":{\"initial_observation\":{\"last_occupancy\":1.0}}}\ncurrent_state: recent_state_history sample 4, step 171\nrecent_state_history:\ncommon: {\"occupancy\":1.0}\ntime_axis:\n| sample | step |\n| --- | --- |\n| 0 | 167 |\n| 1 | 168 |\n| 2 | 169 |\n| 3 | 170 |\n| 4 | 171 |\ntime_varying_measurements:\n| sample | eas.temp_c | eas.pmv | eas.setpoint_c |\n| --- | --- | --- | --- |\n| 0 | 24.58 | 0.43 | 25.0 |\n| 1 | 24.4 | 0.36 | 24.7 |\n| 2 | 24.25 | 0.3 | 24.7 |\n| 3 | 24.18 | 0.28 | 24.7 |\n| 4 | 24.24 | 0.31 | 25.0 |\ncontrol_action_history:\ncommon: {\"regime\":\"steady_state_occupancy\",\"actuator_bounds\":false,\"setpoint_rate_limit\":false,\"comfort_recovery\":false}\ntime_varying_actions:\n| step | eas.setpoint_c | eas.matched_rule |\n| --- | --- | --- |\n| 168 | 24.7 | \"pmv_lower\" |\n| 169 | 24.7 | \"occupied_hold\" |\n| 170 | 24.7 | \"occupied_hold\" |\n| 171 | 25.0 | \"pmv_raise\" |\ndecision_time_occupancy_forecast:\ncommon: {\"occupancy\":1.0}\nzones: [\"eas\"]\nsteps_ahead: [1,2,3,4]\nderived_features:\ncommon: {\"temp_delta_15min_c\":0.06,\"temp_delta_1h_c\":-0.34,\"temp_slope_c_per_hour\":-0.34,\"pmv_delta_15min\":0.03,\"pmv_delta_1h\":-0.12,\"setpoint_delta_15min_c\":0.3,\"setpoint_delta_1h_c\":0.0,\"discomfort_zone_h\":0.0,\"discomfort_pmv_h\":0.0,\"occupied_peak_abs_pmv\":0.36,\"setpoint_tv_c\":0.3,\"setpoint_reversals\":0}\n\n### ACTIVE LONG-TERM EXPERIENCES\ncommon:\n```json\n{\"revision\":2,\"experience\":\"East 在占用状态下反复表现出有限的暖侧舒适余量，并在更紧上侧阈值获准后呈现有界制冷响应。\"}\n```\nrows:\n| regime |\n| --- |\n| \"steady_state_occupancy\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"zone_temp_c\":24.24,\"last_pmv\":0.31,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"zone_temperature_distance_to_comfort_edge_c\":{\"warmer_c\":0.34,\"cooler_c\":2.72},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5}\n```\n\n### ZONE FORECAST\ncommon:\n```json\n{\"occupancy\":1.0}\n```\nrows:\n| step_ahead | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 1 | 31.6 | 628.0 |\n| 2 | 31.8 | 646.0 |\n| 3 | 32.0 | 668.0 |\n| 4 | 32.2 | 628.0 |\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、舒适余量、因果证据、额度与 WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n通过 causal_edge_ids 引用因果证据中的相关 ID。\n\n硬边界\n额度覆盖本小时已接受补丁造成的最坏新增高耗能设定点移动，不是当前残差、设定点或物理功率。只能通过给定控制规格与操作契约工作；不得编写 Python、完整控制器或直接设定点。\n\n输出\n只返回一个精确的 root JSON 对象：{\"patch\":[{...}]}。不要返回解释文字、Markdown 围栏或未知字段。操作契约：\nroot：patch 是仅包含一个 operation 的列表。\n所有 operation 公共必填：op、rationale。\n所有修改类操作还必须包含 causal_edge_ids。\n| op | additional required | optional |\n| --- | --- | --- |\n| no_change | — | — |\n| set_param | param, to | — |\n| add_rule | rule | index |\n| replace_rule | rule | — |\n| remove_rule | id | — |\n| move_rule | id, to_index | — |\nrule 必须包含 id、when、then。每个 when 条件必须包含 field、op、value。then 必须包含 op；set_residual 或 step_setpoint 还必须包含 value。\n",
      "role": "system"
    },
    {
      "content": "### CONTROL SPECIFICATION\nprogram_version: 0\nparameters:\n| param | current | min | max | source |\n| --- | --- | --- | --- | --- |\n| \"precool_lead_steps\" | 4 | 0 | 4 | \"visible forecast horizon\" |\n| \"precool_residual_c\" | -5.0 | -5.0 | 5.0 | \"residual safety bound\" |\n| \"pmv_band_lo\" | 0.3 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_band_hi\" | 0.45 | -0.5 | 0.5 | \"PMV evaluation range\" |\n| \"pmv_step_c\" | 0.3 | 0.0 | 5.0 | \"residual safety bound\" |\nrules:\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}\n{\"id\":\"precool\",\"when\":[{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}}\n{\"id\":\"unoccupied_hold\",\"when\":[],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\ncommon_when: {\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}\n{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}}\n{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}}\n{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}\n{\"id\":\"occupied_hold\",\"when\":[],\"then\":{\"op\":\"hold_setpoint\"}}\nrule_value_references: {\"param\":\"named parameter value\",\"neg_param\":\"negative named parameter value\"}\nrule_and_weather_limits: {\"new_rule\":{\"condition_fields\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"comparison_value\":\"number or parameter name\",\"action_types\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"max_rules\":8},\"weather_literals\":{\"must_be\":\"finite numbers\",\"parameter_refs\":\"forbidden\"}}\ncontrol_domain: {\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n\n### CAUSAL EVIDENCE\ncommon:\n```json\n{\"undirected\":false}\n```\nrows:\n| id | source | relation | target | tags_1 | tags_2 |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"Immediate\" | \"Strong Impact\" |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Weak Impact\" |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"Delayed\" | \"Strong Impact\" |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"Immediate\" | \"Strong Impact\" |\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":2.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":1}}\n```\n\n### WORKING MEMORY\nhour: 41\nzones: [\"eas\"]\ntime_semantics: decision interval 60 min; physical step 15 min; sample 0 is the hour-start state before action; samples 1-4 are post-action outcomes; current state is sample 4; each action precedes its same-step outcome.\nsite_result: {\"site_cost\":3.02,\"site_energy_kwh\":21.1}\nhourly_decision:\ncommon: {\"action\":{\"proposal\":{\"op\":\"no_change\",\"rationale\":\"completed-hour fixture\"},\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0,\"program_version_after\":0},\"lesson\":\"稳定占用状态与正向暖侧舒适余量同时出现。\",\"context\":{\"initial_observation\":{\"last_occupancy\":1.0}}}\ncurrent_state: recent_state_history sample 4, step 167\nrecent_state_history:\ncommon: {\"temp_c\":24.58,\"pmv\":0.43,\"occupancy\":1.0,\"setpoint_c\":25.0}\ntime_axis:\n| sample | step |\n| --- | --- |\n| 0 | 163 |\n| 1 | 164 |\n| 2 | 165 |\n| 3 | 166 |\n| 4 | 167 |\ncontrol_action_history:\ncommon: {\"regime\":\"steady_state_occupancy\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\",\"actuator_bounds\":false,\"setpoint_rate_limit\":false,\"comfort_recovery\":false}\nsteps: [164,165,166,167]\ndecision_time_occupancy_forecast:\ncommon: {\"occupancy\":1.0}\nzones: [\"eas\"]\nsteps_ahead: [1,2,3,4]\nderived_features:\ncommon: {\"temp_delta_15min_c\":0.0,\"temp_delta_1h_c\":0.0,\"temp_slope_c_per_hour\":0.0,\"pmv_delta_15min\":0.0,\"pmv_delta_1h\":0.0,\"setpoint_delta_15min_c\":0.0,\"setpoint_delta_1h_c\":0.0,\"discomfort_zone_h\":0.0,\"discomfort_pmv_h\":0.0,\"occupied_peak_abs_pmv\":0.43,\"setpoint_tv_c\":0.0,\"setpoint_reversals\":0}\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"zone_temp_c\":24.58,\"last_pmv\":0.43,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"zone_temperature_distance_to_comfort_edge_c\":{\"warmer_c\":0.34,\"cooler_c\":2.72},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5}\n```\n\n### ZONE FORECAST\ncommon:\n```json\n{\"occupancy\":1.0}\n```\nrows:\n| step_ahead | outdoor_temp_c | solar_irr |\n| --- | --- | --- |\n| 1 | 31.6 | 628.0 |\n| 2 | 31.8 | 646.0 |\n| 3 | 32.0 | 668.0 |\n| 4 | 32.2 | 628.0 |\n",
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
      "content": "角色\n解释刚刚结束小时的确定性结果。\n\n证据\n从每个区域已完成小时的 Context、Action 与 Outcome 中提炼一条 Lesson，概括对后续控制有意义的已观察关系或权衡。\n\n硬边界\n每条 Lesson 都应基于已完成小时证据，表达观察、关系或权衡，而不是动作命令、目标或无证据因果结论。\n\n输出\n返回形如 {\"hourly_lessons\":[{\"zone\":...,\"lesson\":...}]} 的裸 JSON 对象。每个给定区域必须恰好出现一次。不返回解释文字、Markdown 围栏或未知字段。\n",
      "role": "system"
    },
    {
      "content": "### COMPLETED HOUR EVIDENCE\nhour: 42\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\ntime_semantics: decision interval 60 min; physical step 15 min; sample 0 is the hour-start state before action; samples 1-4 are post-action outcomes; current state is sample 4; each action precedes its same-step outcome.\nsite_result: {\"site_cost\":3.1214,\"site_energy_kwh\":21.9425}\nhourly_decision:\ncommon:\n```json\n{\"action\":{\"admission\":{\"status\":\"accepted\"},\"program_version_before\":0},\"context\":{\"initial_observation\":{\"last_occupancy\":1.0}}}\n```\nrows:\n| zone | op | rationale | program_version_after |\n| --- | --- | --- | --- |\n| \"cor\" | \"no_change\" | \"当前程序保持了占用舒适余量，且没有证据支持有益修改。\" | 0 |\n| \"nor\" | \"no_change\" | \"当前程序与已观察到的稳定占用状态相匹配。\" | 0 |\n| \"sou\" | \"no_change\" | \"已观察舒适余量与当前程序不支持其他原子修改。\" | 0 |\n| \"wes\" | \"no_change\" | \"给定证据不支持在本小时修改可执行规格。\" | 0 |\n| zone | op | rationale | program_version_after | param | to |\n| --- | --- | --- | --- | --- | --- |\n| \"eas\" | \"set_param\" | \"East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。\" | 1 | \"pmv_band_hi\" | 0.4 |\ncurrent_state: recent_state_history sample 4, step 171\nrecent_state_history:\ncommon: {\"occupancy\":1.0}\ntime_axis:\n| sample | step |\n| --- | --- |\n| 0 | 167 |\n| 1 | 168 |\n| 2 | 169 |\n| 3 | 170 |\n| 4 | 171 |\nconstant_by_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0}\n{\"zone\":\"nor\",\"setpoint_c\":25.0}\n{\"zone\":\"sou\",\"setpoint_c\":25.0}\n{\"zone\":\"wes\",\"setpoint_c\":25.0}\ntime_varying_measurements:\n| sample | cor.temp_c | cor.pmv | eas.temp_c | eas.pmv | eas.setpoint_c | nor.temp_c | nor.pmv | sou.temp_c | sou.pmv | wes.temp_c | wes.pmv |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 0 | 24.31 | 0.34 | 24.58 | 0.43 | 25.0 | 24.22 | 0.31 | 24.47 | 0.39 | 24.36 | 0.36 |\n| 1 | 24.3 | 0.34 | 24.4 | 0.36 | 24.7 | 24.23 | 0.31 | 24.47 | 0.39 | 24.37 | 0.36 |\n| 2 | 24.32 | 0.35 | 24.25 | 0.3 | 24.7 | 24.24 | 0.32 | 24.49 | 0.4 | 24.38 | 0.37 |\n| 3 | 24.34 | 0.35 | 24.18 | 0.28 | 24.7 | 24.25 | 0.32 | 24.5 | 0.4 | 24.4 | 0.37 |\n| 4 | 24.35 | 0.36 | 24.24 | 0.31 | 25.0 | 24.27 | 0.33 | 24.52 | 0.41 | 24.41 | 0.38 |\ncontrol_action_history:\ncommon: {\"regime\":\"steady_state_occupancy\",\"actuator_bounds\":false,\"setpoint_rate_limit\":false,\"comfort_recovery\":false}\nconstant_by_zone:\n{\"zone\":\"cor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"nor\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"sou\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\n{\"zone\":\"wes\",\"setpoint_c\":25.0,\"matched_rule\":\"occupied_hold\"}\ntime_varying_actions:\n| step | eas.setpoint_c | eas.matched_rule |\n| --- | --- | --- |\n| 168 | 24.7 | \"pmv_lower\" |\n| 169 | 24.7 | \"occupied_hold\" |\n| 170 | 24.7 | \"occupied_hold\" |\n| 171 | 25.0 | \"pmv_raise\" |\ndecision_time_occupancy_forecast:\ncommon: {\"occupancy\":1.0}\nzones: [\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"]\nsteps_ahead: [1,2,3,4]\nderived_features:\ncommon:\n```json\n{\"setpoint_delta_1h_c\":0.0,\"discomfort_zone_h\":0.0,\"discomfort_pmv_h\":0.0,\"setpoint_reversals\":0}\n```\nrows:\n| zone | temp_delta_15min_c | temp_delta_1h_c | temp_slope_c_per_hour | pmv_delta_15min | pmv_delta_1h | setpoint_delta_15min_c | occupied_peak_abs_pmv | setpoint_tv_c |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| \"cor\" | 0.01 | 0.04 | 0.04 | 0.01 | 0.02 | 0.0 | 0.36 | 0.0 |\n| \"eas\" | 0.06 | -0.34 | -0.34 | 0.03 | -0.12 | 0.3 | 0.36 | 0.3 |\n| \"nor\" | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.33 | 0.0 |\n| \"sou\" | 0.02 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.41 | 0.0 |\n| \"wes\" | 0.01 | 0.05 | 0.05 | 0.01 | 0.02 | 0.0 | 0.38 | 0.0 |\n",
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

### CAUSAL EVIDENCE
```json
[
  {
    "id": "ce_e8f5f362",
    "source": "outdoor_temp",
    "relation": "Positive Corr",
    "target": "power_meters",
    "tags": [
      "Delayed",
      "Strong Impact"
    ],
    "undirected": false
  },
  {
    "id": "ce_5a968228",
    "source": "solar_irr",
    "relation": "Positive Corr",
    "target": "power_meters",
    "tags": [
      "Delayed",
      "Weak Impact"
    ],
    "undirected": false
  },
  {
    "id": "ce_00f91137",
    "source": "occupancy",
    "relation": "Positive Corr",
    "target": "power_meters",
    "tags": [
      "Delayed",
      "Strong Impact"
    ],
    "undirected": false
  },
  {
    "id": "ce_660795c7",
    "source": "cooling_setpoint",
    "relation": "Negative Corr",
    "target": "power_meters",
    "tags": [
      "Immediate",
      "Strong Impact"
    ],
    "undirected": false
  }
]
```

### ALLOCATION LIMITS
```json
{
  "zones": [
    "cor",
    "eas",
    "nor",
    "sou",
    "wes"
  ],
  "site_cap_c": 10.0,
  "per_zone_cap_c": 5.0
}
```

### CONTROL DOMAIN
```json
{
  "domain_id": "cooling",
  "controlled_setpoint": "zone cooling setpoint",
  "unit": "degC",
  "hard_bounds_c": [
    20.0,
    30.0
  ],
  "occupied_base_c": 25.0,
  "unoccupied_base_c": 30.0,
  "pmv_comfort_band": [
    0.3,
    0.45
  ],
  "preconditioning": {
    "label": "precool",
    "lead_steps": 4,
    "target_c": 25.0
  },
  "energy_intensive_setpoint_direction": "decrease"
}
```

### WORKING MEMORY
```json
[
  {
    "hour": 41,
    "zone": "cor",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          164,
          165,
          166,
          167
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.31,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.34,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "no_change",
        "rationale": "completed-hour fixture"
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation",
          "program_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 0,
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "shield": [
        {
          "step": 164,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 165,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 166,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 167,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.31,
        24.31,
        24.31,
        24.31
      ],
      "pmv": [
        0.34,
        0.34,
        0.34,
        0.34
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.02,
      "site_energy_kwh": 21.1,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.34,
      "setpoint_total_variation_c": 0.0,
      "setpoint_direction_reversals": 0
    },
    "lesson": "稳定占用状态与正向暖侧舒适余量同时出现。"
  },
  {
    "hour": 41,
    "zone": "eas",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          164,
          165,
          166,
          167
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.58,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.43,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "no_change",
        "rationale": "completed-hour fixture"
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation",
          "program_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 0,
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "shield": [
        {
          "step": 164,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 165,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 166,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 167,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.58,
        24.58,
        24.58,
        24.58
      ],
      "pmv": [
        0.43,
        0.43,
        0.43,
        0.43
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.02,
      "site_energy_kwh": 21.1,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.43,
      "setpoint_total_variation_c": 0.0,
      "setpoint_direction_reversals": 0
    },
    "lesson": "稳定占用状态与正向暖侧舒适余量同时出现。"
  },
  {
    "hour": 41,
    "zone": "nor",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          164,
          165,
          166,
          167
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.22,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.31,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "no_change",
        "rationale": "completed-hour fixture"
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation",
          "program_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 0,
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "shield": [
        {
          "step": 164,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 165,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 166,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 167,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.22,
        24.22,
        24.22,
        24.22
      ],
      "pmv": [
        0.31,
        0.31,
        0.31,
        0.31
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.02,
      "site_energy_kwh": 21.1,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.31,
      "setpoint_total_variation_c": 0.0,
      "setpoint_direction_reversals": 0
    },
    "lesson": "稳定占用状态与正向暖侧舒适余量同时出现。"
  },
  {
    "hour": 41,
    "zone": "sou",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          164,
          165,
          166,
          167
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.47,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.39,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "no_change",
        "rationale": "completed-hour fixture"
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation",
          "program_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 0,
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "shield": [
        {
          "step": 164,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 165,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 166,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 167,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.47,
        24.47,
        24.47,
        24.47
      ],
      "pmv": [
        0.39,
        0.39,
        0.39,
        0.39
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.02,
      "site_energy_kwh": 21.1,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.39,
      "setpoint_total_variation_c": 0.0,
      "setpoint_direction_reversals": 0
    },
    "lesson": "稳定占用状态与正向暖侧舒适余量同时出现。"
  },
  {
    "hour": 41,
    "zone": "wes",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          164,
          165,
          166,
          167
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.36,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.36,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "no_change",
        "rationale": "completed-hour fixture"
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation",
          "program_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 0,
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "shield": [
        {
          "step": 164,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 165,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 166,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 167,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.36,
        24.36,
        24.36,
        24.36
      ],
      "pmv": [
        0.36,
        0.36,
        0.36,
        0.36
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.02,
      "site_energy_kwh": 21.1,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.36,
      "setpoint_total_variation_c": 0.0,
      "setpoint_direction_reversals": 0
    },
    "lesson": "稳定占用状态与正向暖侧舒适余量同时出现。"
  }
]
```

### CROSS-ZONE STATUS
```json
[
  {
    "zone": "cor",
    "current_setpoint_c": 25.0,
    "last_pmv": 0.34,
    "current_occupancy": 1.0,
    "next_hour_occupancy": 1.0,
    "temp_targets": {
      "precool_residual_c": -5.0
    },
    "zone_temperature_distance_to_comfort_edge_c": {
      "warmer_c": 0.62,
      "cooler_c": 2.45
    },
    "granted_c": 1.0,
    "used_c": 0.0
  },
  {
    "zone": "eas",
    "current_setpoint_c": 25.0,
    "last_pmv": 0.43,
    "current_occupancy": 1.0,
    "next_hour_occupancy": 1.0,
    "temp_targets": {
      "precool_residual_c": -5.0
    },
    "zone_temperature_distance_to_comfort_edge_c": {
      "warmer_c": 0.34,
      "cooler_c": 2.72
    },
    "granted_c": 2.0,
    "used_c": 0.3
  },
  {
    "zone": "nor",
    "current_setpoint_c": 25.0,
    "last_pmv": 0.31,
    "current_occupancy": 1.0,
    "next_hour_occupancy": 1.0,
    "temp_targets": {
      "precool_residual_c": -5.0
    },
    "zone_temperature_distance_to_comfort_edge_c": {
      "warmer_c": 0.72,
      "cooler_c": 2.36
    },
    "granted_c": 1.0,
    "used_c": 0.0
  },
  {
    "zone": "sou",
    "current_setpoint_c": 25.0,
    "last_pmv": 0.39,
    "current_occupancy": 1.0,
    "next_hour_occupancy": 1.0,
    "temp_targets": {
      "precool_residual_c": -5.0
    },
    "zone_temperature_distance_to_comfort_edge_c": {
      "warmer_c": 0.45,
      "cooler_c": 2.61
    },
    "granted_c": 1.0,
    "used_c": 0.0
  },
  {
    "zone": "wes",
    "current_setpoint_c": 25.0,
    "last_pmv": 0.36,
    "current_occupancy": 1.0,
    "next_hour_occupancy": 1.0,
    "temp_targets": {
      "precool_residual_c": -5.0
    },
    "zone_temperature_distance_to_comfort_edge_c": {
      "warmer_c": 0.57,
      "cooler_c": 2.5
    },
    "granted_c": 1.0,
    "used_c": 0.0
  }
]
```

### PREVIOUS ALLOCATION AND UTILISATION
```json
{
  "allocation": {
    "site_cap_c": 10.0,
    "zone_budgets_c": {
      "cor": 1.0,
      "eas": 2.0,
      "nor": 1.0,
      "sou": 1.0,
      "wes": 1.0
    },
    "priority": [
      "eas",
      "sou",
      "wes",
      "cor",
      "nor"
    ],
    "rationale_per_zone": {
      "cor": "Core conditions were stable.",
      "eas": "East had the smallest warm-side headroom.",
      "nor": "North conditions were stable.",
      "sou": "South had moderate warm-side headroom.",
      "wes": "West had moderate warm-side headroom."
    }
  },
  "utilisation": {
    "granted_c": 6.0,
    "used_c": 0.3,
    "utilisation": 0.05,
    "site_cap_c": 10.0,
    "group_remainder_at_the_start_c": 4.0,
    "group_remainder_left_c": 3.7,
    "residual_used_by": {
      "eas": 0.3
    }
  }
}
```

### CURRENT SITE STATE
```json
{
  "outdoor_temp_c": 31.4,
  "solar_irr": 612.0,
  "price_now": 0.14231,
  "price_next_hour": 0.16842,
  "outdoor_temp_change_next_1h_c": 0.8,
  "solar_irr_max_next_1h_w_m2": 668.0,
  "solar_irr_mean_next_1h_w_m2": 642.5
}
```

### SITE FORECAST
```json
[
  {
    "step_ahead": 1,
    "outdoor_temp_c": 31.6,
    "solar_irr": 628.0
  },
  {
    "step_ahead": 2,
    "outdoor_temp_c": 31.8,
    "solar_irr": 646.0
  },
  {
    "step_ahead": 3,
    "outdoor_temp_c": 32.0,
    "solar_irr": 668.0
  },
  {
    "step_ahead": 4,
    "outdoor_temp_c": 32.2,
    "solar_irr": 628.0
  }
]
```
### Orchestrator audit view

```json
{
  "canonical_sha256": "0beb57b2fe71c6d428e5d0347ef26865406d9ad5a424ea6b9467f28d7acad25d",
  "compact_sha256": "48e2b1c34995e2717aa7e5fb2787bfcea350d24e78fdc0d0c4c4c0c5fce047e1",
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
      "/pmv_comfort_band/[]",
      "/preconditioning/label",
      "/preconditioning/lead_steps",
      "/preconditioning/target_c",
      "/energy_intensive_setpoint_direction"
    ],
    "CROSS-ZONE STATUS": [
      "/[]/zone",
      "/[]/current_setpoint_c",
      "/[]/last_pmv",
      "/[]/current_occupancy",
      "/[]/next_hour_occupancy",
      "/[]/temp_targets/precool_residual_c",
      "/[]/zone_temperature_distance_to_comfort_edge_c/warmer_c",
      "/[]/zone_temperature_distance_to_comfort_edge_c/cooler_c",
      "/[]/granted_c",
      "/[]/used_c"
    ],
    "CURRENT SITE STATE": [
      "/outdoor_temp_c",
      "/solar_irr",
      "/price_now",
      "/price_next_hour",
      "/outdoor_temp_change_next_1h_c",
      "/solar_irr_max_next_1h_w_m2",
      "/solar_irr_mean_next_1h_w_m2"
    ],
    "PREVIOUS ALLOCATION AND UTILISATION": [
      "/allocation/site_cap_c",
      "/allocation/zone_budgets_c/cor",
      "/allocation/zone_budgets_c/eas",
      "/allocation/zone_budgets_c/nor",
      "/allocation/zone_budgets_c/sou",
      "/allocation/zone_budgets_c/wes",
      "/allocation/priority/[]",
      "/allocation/rationale_per_zone/cor",
      "/allocation/rationale_per_zone/eas",
      "/allocation/rationale_per_zone/nor",
      "/allocation/rationale_per_zone/sou",
      "/allocation/rationale_per_zone/wes",
      "/utilisation/granted_c",
      "/utilisation/used_c",
      "/utilisation/utilisation",
      "/utilisation/site_cap_c",
      "/utilisation/group_remainder_at_the_start_c",
      "/utilisation/group_remainder_left_c",
      "/utilisation/residual_used_by/eas"
    ],
    "SITE FORECAST": [
      "/[]/step_ahead",
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
    ]
  },
  "round_trip_equal": true,
  "schema": "h3c_context_audit_v1"
}
```
### East Executor expanded canonical input

### CONTROL SPECIFICATION
```json
{
  "program_version": 0,
  "parameters": [
    {
      "param": "precool_lead_steps",
      "current": 4,
      "min": 0,
      "max": 4,
      "bounds_source": "visible forecast horizon"
    },
    {
      "param": "precool_residual_c",
      "current": -5.0,
      "min": -5.0,
      "max": 5.0,
      "bounds_source": "residual safety bound"
    },
    {
      "param": "pmv_band_lo",
      "current": 0.3,
      "min": -0.5,
      "max": 0.5,
      "bounds_source": "PMV evaluation range"
    },
    {
      "param": "pmv_band_hi",
      "current": 0.45,
      "min": -0.5,
      "max": 0.5,
      "bounds_source": "PMV evaluation range"
    },
    {
      "param": "pmv_step_c",
      "current": 0.3,
      "min": 0.0,
      "max": 5.0,
      "bounds_source": "residual safety bound"
    }
  ],
  "rules": [
    {
      "id": "precool",
      "when": [
        {
          "field": "occupied_now",
          "op": "==",
          "value": 0
        },
        {
          "field": "precool_due",
          "op": "==",
          "value": 1
        }
      ],
      "then": {
        "op": "set_residual",
        "value": {
          "param": "precool_residual_c"
        }
      }
    },
    {
      "id": "pmv_raise",
      "when": [
        {
          "field": "occupied_now",
          "op": "==",
          "value": 1
        },
        {
          "field": "last_pmv",
          "op": "<",
          "value": {
            "param": "pmv_band_lo"
          }
        }
      ],
      "then": {
        "op": "step_setpoint",
        "value": {
          "param": "pmv_step_c"
        }
      }
    },
    {
      "id": "pmv_lower",
      "when": [
        {
          "field": "occupied_now",
          "op": "==",
          "value": 1
        },
        {
          "field": "last_pmv",
          "op": ">",
          "value": {
            "param": "pmv_band_hi"
          }
        }
      ],
      "then": {
        "op": "step_setpoint",
        "value": {
          "neg_param": "pmv_step_c"
        }
      }
    },
    {
      "id": "anchor",
      "when": [
        {
          "field": "occupied_now",
          "op": "==",
          "value": 1
        },
        {
          "field": "occupied_last",
          "op": "==",
          "value": 0
        }
      ],
      "then": {
        "op": "set_residual",
        "value": 0.0
      }
    },
    {
      "id": "occupied_hold",
      "when": [
        {
          "field": "occupied_now",
          "op": "==",
          "value": 1
        }
      ],
      "then": {
        "op": "hold_setpoint"
      }
    },
    {
      "id": "unoccupied_hold",
      "when": [
        {
          "field": "occupied_now",
          "op": "==",
          "value": 0
        }
      ],
      "then": {
        "op": "set_residual",
        "value": 0.0
      }
    }
  ],
  "rule_value_references": {
    "param": "use the named parameter value",
    "neg_param": "use the opposite sign of the named parameter value"
  },
  "rule_and_weather_limits": {
    "a_rule_you_add": {
      "conditions_may_test": [
        "last_pmv",
        "occupied_last",
        "occupied_now",
        "outdoor_temp_change_next_1h_c",
        "precool_due",
        "solar_irr_max_next_1h_w_m2",
        "solar_irr_mean_next_1h_w_m2"
      ],
      "comparisons": [
        "<",
        "<=",
        ">",
        ">=",
        "==",
        "!="
      ],
      "compared_against": "a number, or the name of a parameter above",
      "actions": [
        "set_residual",
        "step_setpoint",
        "hold_setpoint"
      ],
      "most_rules_at_once": 8
    },
    "weather_condition_values": {
      "must_be": "finite numeric literals",
      "parameter_references": "not allowed"
    }
  },
  "control_domain": {
    "domain_id": "cooling",
    "controlled_setpoint": "zone cooling setpoint",
    "unit": "degC",
    "hard_bounds_c": [
      20.0,
      30.0
    ],
    "occupied_base_c": 25.0,
    "unoccupied_base_c": 30.0,
    "pmv_comfort_band": [
      0.3,
      0.45
    ],
    "preconditioning": {
      "label": "precool",
      "lead_steps": 4,
      "target_c": 25.0
    },
    "energy_intensive_setpoint_direction": "decrease"
  }
}
```

### CAUSAL EVIDENCE
```json
[
  {
    "id": "ce_aa18e859",
    "source": "outdoor_temp",
    "relation": "Positive Corr",
    "target": "zone_temp",
    "tags": [
      "Immediate",
      "Strong Impact"
    ],
    "undirected": false
  },
  {
    "id": "ce_fc68b8f7",
    "source": "solar_irr",
    "relation": "Positive Corr",
    "target": "zone_temp",
    "tags": [
      "Immediate",
      "Strong Impact"
    ],
    "undirected": false
  },
  {
    "id": "ce_ebd13728",
    "source": "cooling_setpoint",
    "relation": "Positive Corr",
    "target": "zone_temp",
    "tags": [
      "Immediate",
      "Strong Impact"
    ],
    "undirected": false
  },
  {
    "id": "ce_d8c6ee57",
    "source": "occupancy",
    "relation": "Positive Corr",
    "target": "zone_temp",
    "tags": [
      "Immediate",
      "Strong Impact"
    ],
    "undirected": false
  },
  {
    "id": "ce_e8f5f362",
    "source": "outdoor_temp",
    "relation": "Positive Corr",
    "target": "power_meters",
    "tags": [
      "Delayed",
      "Strong Impact"
    ],
    "undirected": false
  },
  {
    "id": "ce_5a968228",
    "source": "solar_irr",
    "relation": "Positive Corr",
    "target": "power_meters",
    "tags": [
      "Delayed",
      "Weak Impact"
    ],
    "undirected": false
  },
  {
    "id": "ce_00f91137",
    "source": "occupancy",
    "relation": "Positive Corr",
    "target": "power_meters",
    "tags": [
      "Delayed",
      "Strong Impact"
    ],
    "undirected": false
  },
  {
    "id": "ce_660795c7",
    "source": "cooling_setpoint",
    "relation": "Negative Corr",
    "target": "power_meters",
    "tags": [
      "Immediate",
      "Strong Impact"
    ],
    "undirected": false
  }
]
```

### ALLOCATION
```json
{
  "allocation": {
    "allowance_left_to_you_c": 2.0,
    "group_allowance_not_yet_handed_out_c": 4.0,
    "your_place_in_the_queue_for_the_remainder": 1
  }
}
```

### WORKING MEMORY
```json
[
  {
    "hour": 41,
    "zone": "eas",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          164,
          165,
          166,
          167
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.58,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.43,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "no_change",
        "rationale": "completed-hour fixture"
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation",
          "program_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 0,
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "shield": [
        {
          "step": 164,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 165,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 166,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 167,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.58,
        24.58,
        24.58,
        24.58
      ],
      "pmv": [
        0.43,
        0.43,
        0.43,
        0.43
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.02,
      "site_energy_kwh": 21.1,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.43,
      "setpoint_total_variation_c": 0.0,
      "setpoint_direction_reversals": 0
    },
    "lesson": "稳定占用状态与正向暖侧舒适余量同时出现。"
  }
]
```

### ACTIVE LONG-TERM EXPERIENCES
```json
[
  {
    "regime": "steady_state_occupancy",
    "revision": 1,
    "experience": "East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone."
  }
]
```

### ZONE OBSERVATION
```json
{
  "current_occupancy": 1.0,
  "last_occupancy": 1.0,
  "zone_temp_c": 24.58,
  "last_pmv": 0.43,
  "last_setpoint_c": 25.0,
  "outdoor_temp_c": 31.4,
  "solar_irr": 612.0,
  "price_now": 0.14231,
  "zone_temperature_distance_to_comfort_edge_c": {
    "warmer_c": 0.34,
    "cooler_c": 2.72
  },
  "outdoor_temp_change_next_1h_c": 0.8,
  "solar_irr_max_next_1h_w_m2": 668.0,
  "solar_irr_mean_next_1h_w_m2": 642.5
}
```

### ZONE FORECAST
```json
[
  {
    "step_ahead": 1,
    "occupancy": 1.0,
    "outdoor_temp_c": 31.6,
    "solar_irr": 628.0
  },
  {
    "step_ahead": 2,
    "occupancy": 1.0,
    "outdoor_temp_c": 31.8,
    "solar_irr": 646.0
  },
  {
    "step_ahead": 3,
    "occupancy": 1.0,
    "outdoor_temp_c": 32.0,
    "solar_irr": 668.0
  },
  {
    "step_ahead": 4,
    "occupancy": 1.0,
    "outdoor_temp_c": 32.2,
    "solar_irr": 628.0
  }
]
```
### East Executor audit view

```json
{
  "canonical_sha256": "4e486b09fcc9361272135d30f5699677cce2abee66d0c10531d5a33b7257886c",
  "compact_sha256": "a293ca8dc0c64d7ea9b719260bd0e306346fc1f5b7baf692f090954353bd5af0",
  "field_manifest": {
    "ACTIVE LONG-TERM EXPERIENCES": [
      "/[]/regime",
      "/[]/revision",
      "/[]/experience"
    ],
    "ALLOCATION": [
      "/allocation/allowance_left_to_you_c",
      "/allocation/group_allowance_not_yet_handed_out_c",
      "/allocation/your_place_in_the_queue_for_the_remainder"
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
      "/control_domain/pmv_comfort_band/[]",
      "/control_domain/preconditioning/label",
      "/control_domain/preconditioning/lead_steps",
      "/control_domain/preconditioning/target_c",
      "/control_domain/energy_intensive_setpoint_direction"
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
      "/[]/step_ahead",
      "/[]/occupancy",
      "/[]/outdoor_temp_c",
      "/[]/solar_irr"
    ],
    "ZONE OBSERVATION": [
      "/current_occupancy",
      "/last_occupancy",
      "/zone_temp_c",
      "/last_pmv",
      "/last_setpoint_c",
      "/outdoor_temp_c",
      "/solar_irr",
      "/price_now",
      "/zone_temperature_distance_to_comfort_edge_c/warmer_c",
      "/zone_temperature_distance_to_comfort_edge_c/cooler_c",
      "/outdoor_temp_change_next_1h_c",
      "/solar_irr_max_next_1h_w_m2",
      "/solar_irr_mean_next_1h_w_m2"
    ]
  },
  "round_trip_equal": true,
  "schema": "h3c_context_audit_v1"
}
```
### Reflector expanded canonical input

### COMPLETED HOUR EVIDENCE
```json
[
  {
    "hour": 42,
    "zone": "cor",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.31,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.34,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "no_change",
        "rationale": "当前程序保持了占用舒适余量，且没有证据支持有益修改。"
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 0,
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "shield": [
        {
          "step": 168,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 169,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 170,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 171,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.3,
        24.32,
        24.34,
        24.35
      ],
      "pmv": [
        0.34,
        0.35,
        0.35,
        0.36
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.36,
      "setpoint_total_variation_c": 0.0,
      "setpoint_direction_reversals": 0
    }
  },
  {
    "hour": 42,
    "zone": "eas",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.58,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.43,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "set_param",
        "rationale": "East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。",
        "param": "pmv_band_hi",
        "to": 0.4,
        "causal_edge_ids": [
          "ce_ebd13728",
          "ce_660795c7"
        ],
        "expected_effects": [
          {
            "node": "power_meters",
            "direction": "up"
          },
          {
            "node": "zone_temp",
            "direction": "down"
          }
        ],
        "consistent_program_direction_proof": {
          "mode": "global",
          "program_direction": "down",
          "expected_effects": [
            {
              "node": "power_meters",
              "direction": "up"
            },
            {
              "node": "zone_temp",
              "direction": "down"
            }
          ],
          "witness_count": 180,
          "cited_edge_ids": [
            "ce_ebd13728",
            "ce_660795c7"
          ]
        }
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 1,
      "actual_setpoints_c": [
        24.7,
        24.7,
        24.7,
        25.0
      ],
      "matched_rules": [
        "pmv_lower",
        "occupied_hold",
        "occupied_hold",
        "pmv_raise"
      ],
      "shield": [
        {
          "step": 168,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 169,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 170,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 171,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.4,
        24.25,
        24.18,
        24.24
      ],
      "pmv": [
        0.36,
        0.3,
        0.28,
        0.31
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.36,
      "setpoint_total_variation_c": 0.3,
      "setpoint_direction_reversals": 0
    }
  },
  {
    "hour": 42,
    "zone": "nor",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.22,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.31,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "no_change",
        "rationale": "当前程序与已观察到的稳定占用状态相匹配。"
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 0,
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "shield": [
        {
          "step": 168,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 169,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 170,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 171,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.23,
        24.24,
        24.25,
        24.27
      ],
      "pmv": [
        0.31,
        0.32,
        0.32,
        0.33
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.33,
      "setpoint_total_variation_c": 0.0,
      "setpoint_direction_reversals": 0
    }
  },
  {
    "hour": 42,
    "zone": "sou",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.47,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.39,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "no_change",
        "rationale": "已观察舒适余量与当前程序不支持其他原子修改。"
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 0,
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "shield": [
        {
          "step": 168,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 169,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 170,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 171,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.47,
        24.49,
        24.5,
        24.52
      ],
      "pmv": [
        0.39,
        0.4,
        0.4,
        0.41
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.41,
      "setpoint_total_variation_c": 0.0,
      "setpoint_direction_reversals": 0
    }
  },
  {
    "hour": 42,
    "zone": "wes",
    "context": {
      "regime_step_coverage": {
        "steady_state_occupancy": [
          168,
          169,
          170,
          171
        ]
      },
      "initial_observation": {
        "zone_temperature_c": 24.36,
        "current_occupancy": 1.0,
        "last_occupancy": 1.0,
        "occupancy_next_steps": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "last_pmv": 0.36,
        "last_setpoint_c": 25.0
      }
    },
    "action": {
      "proposal": {
        "op": "no_change",
        "rationale": "给定证据不支持在本小时修改可执行规格。"
      },
      "admission": {
        "status": "accepted",
        "completed_validation_stages": [
          "program_validation",
          "causal_admissibility",
          "consistent_program_direction_proof",
          "energy_budget_validation"
        ]
      },
      "program_version_before": 0,
      "program_version_after": 0,
      "actual_setpoints_c": [
        25.0,
        25.0,
        25.0,
        25.0
      ],
      "matched_rules": [
        "occupied_hold",
        "occupied_hold",
        "occupied_hold",
        "occupied_hold"
      ],
      "shield": [
        {
          "step": 168,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 169,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 170,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        },
        {
          "step": 171,
          "actuator_bounds": false,
          "setpoint_rate_limit": false,
          "comfort_recovery": false
        }
      ]
    },
    "outcome": {
      "zone_temperatures_c": [
        24.37,
        24.38,
        24.4,
        24.41
      ],
      "pmv": [
        0.36,
        0.37,
        0.37,
        0.38
      ],
      "effective_occupancy": [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "site_cost": 3.1214,
      "site_energy_kwh": 21.9425,
      "discomfort_zone_hours": 0.0,
      "discomfort_pmv_hours": 0.0,
      "occupied_peak_absolute_pmv": 0.38,
      "setpoint_total_variation_c": 0.0,
      "setpoint_direction_reversals": 0
    }
  }
]
```

### ELIGIBLE LONG-TERM EXPERIENCE SLOTS
```json
[
  {
    "zone": "cor",
    "regime": "steady_state_occupancy",
    "revision": 2,
    "experience": "Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive."
  },
  {
    "zone": "eas",
    "regime": "steady_state_occupancy",
    "revision": 1,
    "experience": "East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone."
  },
  {
    "zone": "nor",
    "regime": "steady_state_occupancy",
    "state": "empty"
  },
  {
    "zone": "sou",
    "regime": "steady_state_occupancy",
    "revision": 2,
    "experience": "South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions."
  },
  {
    "zone": "wes",
    "regime": "steady_state_occupancy",
    "revision": 1,
    "experience": "West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions."
  }
]
```
### Reflector audit view

```json
{
  "canonical_sha256": "21cb819b660e0a7e931b47e33ba09bce9841d1a106e3d6f67beb5fd7afd0b064",
  "compact_sha256": "d2afe23cbdf647ebbc8850e2bed141d260547879d196230f08256adf01ad6715",
  "field_manifest": {
    "COMPLETED HOUR EVIDENCE": [
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
    "ELIGIBLE LONG-TERM EXPERIENCE SLOTS": [
      "/[]/zone",
      "/[]/regime",
      "/[]/revision",
      "/[]/experience",
      "/[]/state"
    ]
  },
  "round_trip_equal": true,
  "schema": "h3c_context_audit_v1"
}
```
