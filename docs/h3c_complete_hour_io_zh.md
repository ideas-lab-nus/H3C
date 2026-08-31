# H3C 完整 MZ Air 小时示例：CAOL 工作记忆与可选状态经验

这是一个冻结且不执行API/BOPTEST的文档fixture。全部Prompt由生产renderer生成；下方所有确定性转换均由生产validation、program、assurance、CAOL和CRUD owner计算。它不是实验结果。

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
      "content": "角色\n为下一小时在各区域之间分配共享额度。\n\n决策\n在兼顾舒适的同时降低或优化能源成本。使用给定的场地状态、预测、区域耦合、CAOL 工作记忆和先前利用率，只选择额度分配与优先顺序。为每个区域的分配给出理由。\n\n因果证据\n只使用给定的结构化对象。通过 causal_edge_ids 引用给定 ID。不得复制或编造边文本。\n\n硬边界\n只负责跨区域资源与约束分配。额度是以给定单位表示的高耗能动作额度，只覆盖本小时已接受补丁带来的最坏新增高耗能设定点移动，不是当前残差、当前设定点或物理功率。区域理由只能解释分配或约束权衡，不得规定补丁、参数、残差、规则、动作或设定点。只使用给定证据，缺失的输入块整体省略。不得提及案例、标准名称或目标值。\n\n输出\n返回一个符合 allocation contract 的裸 JSON 对象。不返回解释文字、Markdown 围栏或契约之外的字段。allocation_contract：Return exactly these keys, with no others: site_cap_c, zone_budgets_c, priority, rationale_per_zone, causal_edge_ids. Every listed key must be present; rationale_per_zone maps each zone to a nonempty string.\n",
      "role": "system"
    },
    {
      "content": "\n### CAUSAL EVIDENCE\n| id | source | relation | target | tags | undirected |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Weak Impact\\\"]\" | false |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n\n### ALLOCATION LIMITS\n```json\n{\"zones\":[\"cor\",\"eas\",\"nor\",\"sou\",\"wes\"],\"site_cap_c\":10.0,\"per_zone_cap_c\":5.0}\n```\n\n### CONTROL DOMAIN\n```json\n{\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n```\n\n### WHAT SOME OF THE FIELD NAMES MEAN\ncomfort_headroom_c -- how far zone temperature would have to rise, or fall, to reach the band edge. Room in zone temperature, not in the setpoint; the edge of the score, not of what people feel\noutdoor_temp_change_next_1h_c -- outdoor dry-bulb temperature at the fourth future 15-minute step minus the current value, in degrees Celsius; it describes the forecast change and does not prescribe an action\nsolar_irr_max_next_1h_w_m2 -- the maximum forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\nsolar_irr_mean_next_1h_w_m2 -- the mean forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\n\n### CAOL WORKING MEMORY\n| hour | zone | context.regime_step_coverage.steady_state_occupancy | context.initial_observation.zone_temperature_c | context.initial_observation.current_occupancy | context.initial_observation.last_occupancy | context.initial_observation.occupancy_next_steps | context.initial_observation.last_pmv | context.initial_observation.last_setpoint_c | action.proposal.op | action.proposal.rationale | action.admission.status | action.admission.completed_validation_stages | action.program_version_before | action.program_version_after | action.actual_setpoints_c | action.matched_rules | action.shield | outcome.zone_temperatures_c | outcome.pmv | outcome.effective_occupancy | outcome.site_cost | outcome.site_energy_kwh | outcome.discomfort_zone_hours | outcome.discomfort_pmv_hours | outcome.occupied_peak_absolute_pmv | outcome.setpoint_total_variation_c | outcome.setpoint_direction_reversals | lesson |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 41 | \"cor\" | \"[164,165,166,167]\" | 24.31 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.34 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.31,24.31,24.31,24.31]\" | \"[0.34,0.34,0.34,0.34]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.34 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n| 41 | \"eas\" | \"[164,165,166,167]\" | 24.58 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.43 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.58,24.58,24.58,24.58]\" | \"[0.43,0.43,0.43,0.43]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.43 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n| 41 | \"nor\" | \"[164,165,166,167]\" | 24.22 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.31 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.22,24.22,24.22,24.22]\" | \"[0.31,0.31,0.31,0.31]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.31 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n| 41 | \"sou\" | \"[164,165,166,167]\" | 24.47 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.39 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.47,24.47,24.47,24.47]\" | \"[0.39,0.39,0.39,0.39]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.39 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n| 41 | \"wes\" | \"[164,165,166,167]\" | 24.36 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.36 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.36,24.36,24.36,24.36]\" | \"[0.36,0.36,0.36,0.36]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.36 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n\n### CROSS-ZONE CONSTRAINTS\nzone coupling:\n```json\n{\"cor\":{\"current_setpoint_c\":25.0,\"last_pmv\":0.34,\"current_occupancy\":1.0,\"next_hour_occupancy\":1.0,\"temp_targets\":{\"precool_residual_c\":-5.0},\"comfort_headroom_c\":{\"warmer_c\":0.62,\"cooler_c\":2.45},\"granted_c\":1.0,\"used_c\":0.0},\"eas\":{\"current_setpoint_c\":25.0,\"last_pmv\":0.43,\"current_occupancy\":1.0,\"next_hour_occupancy\":1.0,\"temp_targets\":{\"precool_residual_c\":-5.0},\"comfort_headroom_c\":{\"warmer_c\":0.34,\"cooler_c\":2.72},\"granted_c\":2.0,\"used_c\":0.3},\"nor\":{\"current_setpoint_c\":25.0,\"last_pmv\":0.31,\"current_occupancy\":1.0,\"next_hour_occupancy\":1.0,\"temp_targets\":{\"precool_residual_c\":-5.0},\"comfort_headroom_c\":{\"warmer_c\":0.72,\"cooler_c\":2.36},\"granted_c\":1.0,\"used_c\":0.0},\"sou\":{\"current_setpoint_c\":25.0,\"last_pmv\":0.39,\"current_occupancy\":1.0,\"next_hour_occupancy\":1.0,\"temp_targets\":{\"precool_residual_c\":-5.0},\"comfort_headroom_c\":{\"warmer_c\":0.45,\"cooler_c\":2.61},\"granted_c\":1.0,\"used_c\":0.0},\"wes\":{\"current_setpoint_c\":25.0,\"last_pmv\":0.36,\"current_occupancy\":1.0,\"next_hour_occupancy\":1.0,\"temp_targets\":{\"precool_residual_c\":-5.0},\"comfort_headroom_c\":{\"warmer_c\":0.57,\"cooler_c\":2.5},\"granted_c\":1.0,\"used_c\":0.0}}\n```\n\n### PREVIOUS ALLOCATION AND UTILISATION\nprevious allocation:\n```json\n{\"site_cap_c\":10.0,\"zone_budgets_c\":{\"cor\":1.0,\"eas\":2.0,\"nor\":1.0,\"sou\":1.0,\"wes\":1.0},\"priority\":[\"eas\",\"sou\",\"wes\",\"cor\",\"nor\"],\"rationale_per_zone\":{\"cor\":\"Core conditions were stable.\",\"eas\":\"East had the smallest warm-side headroom.\",\"nor\":\"North conditions were stable.\",\"sou\":\"South had moderate warm-side headroom.\",\"wes\":\"West had moderate warm-side headroom.\"}}\n```\nprevious utilisation:\n```json\n{\"granted_c\":6.0,\"used_c\":0.3,\"utilisation\":0.05,\"site_cap_c\":10.0,\"group_remainder_at_the_start_c\":4.0,\"group_remainder_left_c\":3.7,\"residual_used_by\":{\"eas\":0.3}}\n```\n\n### CURRENT SITE STATE AND FORECAST\n```json\n{\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"price_next_hour\":0.16842,\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5,\"weather_next_steps\":[{\"step_ahead\":1,\"outdoor_temp_c\":31.6,\"solar_irr\":628.0},{\"step_ahead\":2,\"outdoor_temp_c\":31.8,\"solar_irr\":646.0},{\"step_ahead\":3,\"outdoor_temp_c\":32.0,\"solar_irr\":668.0},{\"step_ahead\":4,\"outdoor_temp_c\":32.2,\"solar_irr\":628.0}]}\n```\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、已完成结果、舒适余量、给定的因果证据、额度与 CAOL WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n只使用给定的结构化对象。通过 causal_edge_ids 引用 ID。确定性验证器将派生作用并补齐必要的站点聚合边。不得复制或编造边文本。\n\n硬边界\n只使用当前区域输入以及按 k 提供的已完成 CAOL 历史。额度是以给定单位表示的高耗能动作额度，只覆盖本小时已接受补丁带来的最坏新增高耗能设定点移动，不是当前残差、当前设定点或物理功率。不得读取未提供的离线日志、未来数据、反事实、oracle 信号或给定 CAOL Lesson 之外的 Reflector 散文。可执行控制规格、操作名称、参数边界、动作词汇、预算收费、可达性、shield 和确定性解释器拥有最终权威。不得编写 Python、完整控制器、直接设定点或可执行规格之外的动作。缺失输入块整体省略。 启用的长期经验是本区域的观察，不是命令；它们不能覆盖可执行程序、验证、Budget 或 Safety。\n\n输出\n只返回一个精确的 root JSON 对象：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。patch 列表必须恰好包含一个操作。只引用实际使用的 active experience；空 memory_refs 列表合法。no_change 是一个可用操作，并与其他操作一样需要非空理由。不要返回解释文字、Markdown 围栏或未知字段。patch_contract：{\"causal_edge_ids\":\"stable IDs from the supplied structured edge objects\",\"operations\":{\"add_rule\":{\"optional\":[\"index\"],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"move_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"to_index\",\"causal_edge_ids\",\"rationale\"]},\"no_change\":{\"optional\":[],\"required\":[\"op\",\"rationale\"]},\"remove_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"causal_edge_ids\",\"rationale\"]},\"replace_rule\":{\"optional\":[],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"set_param\":{\"optional\":[],\"required\":[\"op\",\"param\",\"to\",\"causal_edge_ids\",\"rationale\"]}},\"rationale\":\"nonempty string\",\"root\":{\"patch\":\"list with exactly one operation\",\"required\":[\"patch\"]},\"rule\":{\"required\":[\"id\",\"when\",\"then\"],\"then\":{\"required\":[\"op\"],\"value_for\":[\"set_residual\",\"step_setpoint\"]},\"when_item\":{\"required\":[\"field\",\"op\",\"value\"]}}}\n",
      "role": "system"
    },
    {
      "content": "\n### CURRENT EXECUTABLE PROGRAM P_h\n```json\n{\"program_version\":0,\"params\":{\"precool_lead_steps\":4,\"precool_residual_c\":-5.0,\"pmv_band_lo\":0.3,\"pmv_band_hi\":0.45,\"pmv_step_c\":0.3},\"rules\":[{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}},{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}},{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}},{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}},{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}},{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}]}\n```\n\n### PARAMETER AND RULE LIMITS\n```json\n{\"precool_lead_steps\":{\"bounds\":[0,4],\"bounds_come_from\":\"visible forecast horizon\"},\"precool_residual_c\":{\"bounds\":[-5.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"pmv_band_lo\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_band_hi\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_step_c\":{\"bounds\":[0.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"a_rule_you_add\":{\"conditions_may_test\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"compared_against\":\"a number, or the name of a parameter above\",\"actions\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"most_rules_at_once\":8},\"weather_condition_values\":{\"must_be\":\"finite numeric literals\",\"parameter_references\":\"not allowed\"}}\n```\n\n### CAUSAL EVIDENCE\n| id | source | relation | target | tags | undirected |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Weak Impact\\\"]\" | false |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n\n### CONTROL DOMAIN\n```json\n{\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n```\n\n### WHAT SOME OF THE FIELD NAMES MEAN\nallowance_left_to_you_c -- the remaining cooling-budget amount for this hour's accepted patches, in the supplied budget units. It covers worst-case additional cooling only, not current residual, current setpoint or physical power\ncomfort_headroom_c -- how far zone temperature would have to rise, or fall, to reach the band edge. Room in zone temperature, not in the setpoint; the edge of the score, not of what people feel\nneg_param -- the name of a numeric parameter whose value is used with the opposite sign; it does not establish which action to take\noutdoor_temp_change_next_1h_c -- outdoor dry-bulb temperature at the fourth future 15-minute step minus the current value, in degrees Celsius; it describes the forecast change and does not prescribe an action\nprogram_version -- the program-version label recorded with a result; it does not establish result quality or control suitability\nsolar_irr_max_next_1h_w_m2 -- the maximum forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\nsolar_irr_mean_next_1h_w_m2 -- the mean forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":1.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":4}}\n```\n\n### CAOL WORKING MEMORY\n| hour | zone | context.regime_step_coverage.steady_state_occupancy | context.initial_observation.zone_temperature_c | context.initial_observation.current_occupancy | context.initial_observation.last_occupancy | context.initial_observation.occupancy_next_steps | context.initial_observation.last_pmv | context.initial_observation.last_setpoint_c | action.proposal.op | action.proposal.rationale | action.admission.status | action.admission.completed_validation_stages | action.program_version_before | action.program_version_after | action.actual_setpoints_c | action.matched_rules | action.shield | outcome.zone_temperatures_c | outcome.pmv | outcome.effective_occupancy | outcome.site_cost | outcome.site_energy_kwh | outcome.discomfort_zone_hours | outcome.discomfort_pmv_hours | outcome.occupied_peak_absolute_pmv | outcome.setpoint_total_variation_c | outcome.setpoint_direction_reversals | lesson |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 41 | \"cor\" | \"[164,165,166,167]\" | 24.31 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.34 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.31,24.31,24.31,24.31]\" | \"[0.34,0.34,0.34,0.34]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.34 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n\n### ACTIVE LONG-TERM EXPERIENCES\n| regime | revision | experience |\n| --- | --- | --- |\n| \"steady_state_occupancy\" | 2 | \"Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"occupancy_next_steps\":[1.0,1.0,1.0,1.0],\"zone_temp_c\":24.31,\"last_pmv\":0.34,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"comfort_headroom_c\":{\"warmer_c\":0.62,\"cooler_c\":2.45},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5,\"weather_next_steps\":[{\"step_ahead\":1,\"outdoor_temp_c\":31.6,\"solar_irr\":628.0},{\"step_ahead\":2,\"outdoor_temp_c\":31.8,\"solar_irr\":646.0},{\"step_ahead\":3,\"outdoor_temp_c\":32.0,\"solar_irr\":668.0},{\"step_ahead\":4,\"outdoor_temp_c\":32.2,\"solar_irr\":628.0}]}\n```\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、已完成结果、舒适余量、给定的因果证据、额度与 CAOL WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n只使用给定的结构化对象。通过 causal_edge_ids 引用 ID。确定性验证器将派生作用并补齐必要的站点聚合边。不得复制或编造边文本。\n\n硬边界\n只使用当前区域输入以及按 k 提供的已完成 CAOL 历史。额度是以给定单位表示的高耗能动作额度，只覆盖本小时已接受补丁带来的最坏新增高耗能设定点移动，不是当前残差、当前设定点或物理功率。不得读取未提供的离线日志、未来数据、反事实、oracle 信号或给定 CAOL Lesson 之外的 Reflector 散文。可执行控制规格、操作名称、参数边界、动作词汇、预算收费、可达性、shield 和确定性解释器拥有最终权威。不得编写 Python、完整控制器、直接设定点或可执行规格之外的动作。缺失输入块整体省略。 启用的长期经验是本区域的观察，不是命令；它们不能覆盖可执行程序、验证、Budget 或 Safety。\n\n输出\n只返回一个精确的 root JSON 对象：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。patch 列表必须恰好包含一个操作。只引用实际使用的 active experience；空 memory_refs 列表合法。no_change 是一个可用操作，并与其他操作一样需要非空理由。不要返回解释文字、Markdown 围栏或未知字段。patch_contract：{\"causal_edge_ids\":\"stable IDs from the supplied structured edge objects\",\"operations\":{\"add_rule\":{\"optional\":[\"index\"],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"move_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"to_index\",\"causal_edge_ids\",\"rationale\"]},\"no_change\":{\"optional\":[],\"required\":[\"op\",\"rationale\"]},\"remove_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"causal_edge_ids\",\"rationale\"]},\"replace_rule\":{\"optional\":[],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"set_param\":{\"optional\":[],\"required\":[\"op\",\"param\",\"to\",\"causal_edge_ids\",\"rationale\"]}},\"rationale\":\"nonempty string\",\"root\":{\"patch\":\"list with exactly one operation\",\"required\":[\"patch\"]},\"rule\":{\"required\":[\"id\",\"when\",\"then\"],\"then\":{\"required\":[\"op\"],\"value_for\":[\"set_residual\",\"step_setpoint\"]},\"when_item\":{\"required\":[\"field\",\"op\",\"value\"]}}}\n",
      "role": "system"
    },
    {
      "content": "\n### CURRENT EXECUTABLE PROGRAM P_h\n```json\n{\"program_version\":0,\"params\":{\"precool_lead_steps\":4,\"precool_residual_c\":-5.0,\"pmv_band_lo\":0.3,\"pmv_band_hi\":0.45,\"pmv_step_c\":0.3},\"rules\":[{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}},{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}},{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}},{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}},{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}},{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}]}\n```\n\n### PARAMETER AND RULE LIMITS\n```json\n{\"precool_lead_steps\":{\"bounds\":[0,4],\"bounds_come_from\":\"visible forecast horizon\"},\"precool_residual_c\":{\"bounds\":[-5.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"pmv_band_lo\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_band_hi\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_step_c\":{\"bounds\":[0.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"a_rule_you_add\":{\"conditions_may_test\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"compared_against\":\"a number, or the name of a parameter above\",\"actions\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"most_rules_at_once\":8},\"weather_condition_values\":{\"must_be\":\"finite numeric literals\",\"parameter_references\":\"not allowed\"}}\n```\n\n### CAUSAL EVIDENCE\n| id | source | relation | target | tags | undirected |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Weak Impact\\\"]\" | false |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n\n### CONTROL DOMAIN\n```json\n{\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n```\n\n### WHAT SOME OF THE FIELD NAMES MEAN\nallowance_left_to_you_c -- the remaining cooling-budget amount for this hour's accepted patches, in the supplied budget units. It covers worst-case additional cooling only, not current residual, current setpoint or physical power\ncomfort_headroom_c -- how far zone temperature would have to rise, or fall, to reach the band edge. Room in zone temperature, not in the setpoint; the edge of the score, not of what people feel\nneg_param -- the name of a numeric parameter whose value is used with the opposite sign; it does not establish which action to take\noutdoor_temp_change_next_1h_c -- outdoor dry-bulb temperature at the fourth future 15-minute step minus the current value, in degrees Celsius; it describes the forecast change and does not prescribe an action\nprogram_version -- the program-version label recorded with a result; it does not establish result quality or control suitability\nsolar_irr_max_next_1h_w_m2 -- the maximum forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\nsolar_irr_mean_next_1h_w_m2 -- the mean forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":2.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":1}}\n```\n\n### CAOL WORKING MEMORY\n| hour | zone | context.regime_step_coverage.steady_state_occupancy | context.initial_observation.zone_temperature_c | context.initial_observation.current_occupancy | context.initial_observation.last_occupancy | context.initial_observation.occupancy_next_steps | context.initial_observation.last_pmv | context.initial_observation.last_setpoint_c | action.proposal.op | action.proposal.rationale | action.admission.status | action.admission.completed_validation_stages | action.program_version_before | action.program_version_after | action.actual_setpoints_c | action.matched_rules | action.shield | outcome.zone_temperatures_c | outcome.pmv | outcome.effective_occupancy | outcome.site_cost | outcome.site_energy_kwh | outcome.discomfort_zone_hours | outcome.discomfort_pmv_hours | outcome.occupied_peak_absolute_pmv | outcome.setpoint_total_variation_c | outcome.setpoint_direction_reversals | lesson |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 41 | \"eas\" | \"[164,165,166,167]\" | 24.58 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.43 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.58,24.58,24.58,24.58]\" | \"[0.43,0.43,0.43,0.43]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.43 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n\n### ACTIVE LONG-TERM EXPERIENCES\n| regime | revision | experience |\n| --- | --- | --- |\n| \"steady_state_occupancy\" | 1 | \"East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"occupancy_next_steps\":[1.0,1.0,1.0,1.0],\"zone_temp_c\":24.58,\"last_pmv\":0.43,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"comfort_headroom_c\":{\"warmer_c\":0.34,\"cooler_c\":2.72},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5,\"weather_next_steps\":[{\"step_ahead\":1,\"outdoor_temp_c\":31.6,\"solar_irr\":628.0},{\"step_ahead\":2,\"outdoor_temp_c\":31.8,\"solar_irr\":646.0},{\"step_ahead\":3,\"outdoor_temp_c\":32.0,\"solar_irr\":668.0},{\"step_ahead\":4,\"outdoor_temp_c\":32.2,\"solar_irr\":628.0}]}\n```\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、已完成结果、舒适余量、给定的因果证据、额度与 CAOL WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n只使用给定的结构化对象。通过 causal_edge_ids 引用 ID。确定性验证器将派生作用并补齐必要的站点聚合边。不得复制或编造边文本。\n\n硬边界\n只使用当前区域输入以及按 k 提供的已完成 CAOL 历史。额度是以给定单位表示的高耗能动作额度，只覆盖本小时已接受补丁带来的最坏新增高耗能设定点移动，不是当前残差、当前设定点或物理功率。不得读取未提供的离线日志、未来数据、反事实、oracle 信号或给定 CAOL Lesson 之外的 Reflector 散文。可执行控制规格、操作名称、参数边界、动作词汇、预算收费、可达性、shield 和确定性解释器拥有最终权威。不得编写 Python、完整控制器、直接设定点或可执行规格之外的动作。缺失输入块整体省略。 启用的长期经验是本区域的观察，不是命令；它们不能覆盖可执行程序、验证、Budget 或 Safety。\n\n输出\n只返回一个精确的 root JSON 对象：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。patch 列表必须恰好包含一个操作。只引用实际使用的 active experience；空 memory_refs 列表合法。no_change 是一个可用操作，并与其他操作一样需要非空理由。不要返回解释文字、Markdown 围栏或未知字段。patch_contract：{\"causal_edge_ids\":\"stable IDs from the supplied structured edge objects\",\"operations\":{\"add_rule\":{\"optional\":[\"index\"],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"move_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"to_index\",\"causal_edge_ids\",\"rationale\"]},\"no_change\":{\"optional\":[],\"required\":[\"op\",\"rationale\"]},\"remove_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"causal_edge_ids\",\"rationale\"]},\"replace_rule\":{\"optional\":[],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"set_param\":{\"optional\":[],\"required\":[\"op\",\"param\",\"to\",\"causal_edge_ids\",\"rationale\"]}},\"rationale\":\"nonempty string\",\"root\":{\"patch\":\"list with exactly one operation\",\"required\":[\"patch\"]},\"rule\":{\"required\":[\"id\",\"when\",\"then\"],\"then\":{\"required\":[\"op\"],\"value_for\":[\"set_residual\",\"step_setpoint\"]},\"when_item\":{\"required\":[\"field\",\"op\",\"value\"]}}}\n",
      "role": "system"
    },
    {
      "content": "\n### CURRENT EXECUTABLE PROGRAM P_h\n```json\n{\"program_version\":0,\"params\":{\"precool_lead_steps\":4,\"precool_residual_c\":-5.0,\"pmv_band_lo\":0.3,\"pmv_band_hi\":0.45,\"pmv_step_c\":0.3},\"rules\":[{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}},{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}},{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}},{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}},{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}},{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}]}\n```\n\n### PARAMETER AND RULE LIMITS\n```json\n{\"precool_lead_steps\":{\"bounds\":[0,4],\"bounds_come_from\":\"visible forecast horizon\"},\"precool_residual_c\":{\"bounds\":[-5.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"pmv_band_lo\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_band_hi\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_step_c\":{\"bounds\":[0.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"a_rule_you_add\":{\"conditions_may_test\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"compared_against\":\"a number, or the name of a parameter above\",\"actions\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"most_rules_at_once\":8},\"weather_condition_values\":{\"must_be\":\"finite numeric literals\",\"parameter_references\":\"not allowed\"}}\n```\n\n### CAUSAL EVIDENCE\n| id | source | relation | target | tags | undirected |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Weak Impact\\\"]\" | false |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n\n### CONTROL DOMAIN\n```json\n{\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n```\n\n### WHAT SOME OF THE FIELD NAMES MEAN\nallowance_left_to_you_c -- the remaining cooling-budget amount for this hour's accepted patches, in the supplied budget units. It covers worst-case additional cooling only, not current residual, current setpoint or physical power\ncomfort_headroom_c -- how far zone temperature would have to rise, or fall, to reach the band edge. Room in zone temperature, not in the setpoint; the edge of the score, not of what people feel\nneg_param -- the name of a numeric parameter whose value is used with the opposite sign; it does not establish which action to take\noutdoor_temp_change_next_1h_c -- outdoor dry-bulb temperature at the fourth future 15-minute step minus the current value, in degrees Celsius; it describes the forecast change and does not prescribe an action\nprogram_version -- the program-version label recorded with a result; it does not establish result quality or control suitability\nsolar_irr_max_next_1h_w_m2 -- the maximum forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\nsolar_irr_mean_next_1h_w_m2 -- the mean forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":1.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":5}}\n```\n\n### CAOL WORKING MEMORY\n| hour | zone | context.regime_step_coverage.steady_state_occupancy | context.initial_observation.zone_temperature_c | context.initial_observation.current_occupancy | context.initial_observation.last_occupancy | context.initial_observation.occupancy_next_steps | context.initial_observation.last_pmv | context.initial_observation.last_setpoint_c | action.proposal.op | action.proposal.rationale | action.admission.status | action.admission.completed_validation_stages | action.program_version_before | action.program_version_after | action.actual_setpoints_c | action.matched_rules | action.shield | outcome.zone_temperatures_c | outcome.pmv | outcome.effective_occupancy | outcome.site_cost | outcome.site_energy_kwh | outcome.discomfort_zone_hours | outcome.discomfort_pmv_hours | outcome.occupied_peak_absolute_pmv | outcome.setpoint_total_variation_c | outcome.setpoint_direction_reversals | lesson |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 41 | \"nor\" | \"[164,165,166,167]\" | 24.22 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.31 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.22,24.22,24.22,24.22]\" | \"[0.31,0.31,0.31,0.31]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.31 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"occupancy_next_steps\":[1.0,1.0,1.0,1.0],\"zone_temp_c\":24.22,\"last_pmv\":0.31,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"comfort_headroom_c\":{\"warmer_c\":0.72,\"cooler_c\":2.36},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5,\"weather_next_steps\":[{\"step_ahead\":1,\"outdoor_temp_c\":31.6,\"solar_irr\":628.0},{\"step_ahead\":2,\"outdoor_temp_c\":31.8,\"solar_irr\":646.0},{\"step_ahead\":3,\"outdoor_temp_c\":32.0,\"solar_irr\":668.0},{\"step_ahead\":4,\"outdoor_temp_c\":32.2,\"solar_irr\":628.0}]}\n```\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、已完成结果、舒适余量、给定的因果证据、额度与 CAOL WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n只使用给定的结构化对象。通过 causal_edge_ids 引用 ID。确定性验证器将派生作用并补齐必要的站点聚合边。不得复制或编造边文本。\n\n硬边界\n只使用当前区域输入以及按 k 提供的已完成 CAOL 历史。额度是以给定单位表示的高耗能动作额度，只覆盖本小时已接受补丁带来的最坏新增高耗能设定点移动，不是当前残差、当前设定点或物理功率。不得读取未提供的离线日志、未来数据、反事实、oracle 信号或给定 CAOL Lesson 之外的 Reflector 散文。可执行控制规格、操作名称、参数边界、动作词汇、预算收费、可达性、shield 和确定性解释器拥有最终权威。不得编写 Python、完整控制器、直接设定点或可执行规格之外的动作。缺失输入块整体省略。 启用的长期经验是本区域的观察，不是命令；它们不能覆盖可执行程序、验证、Budget 或 Safety。\n\n输出\n只返回一个精确的 root JSON 对象：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。patch 列表必须恰好包含一个操作。只引用实际使用的 active experience；空 memory_refs 列表合法。no_change 是一个可用操作，并与其他操作一样需要非空理由。不要返回解释文字、Markdown 围栏或未知字段。patch_contract：{\"causal_edge_ids\":\"stable IDs from the supplied structured edge objects\",\"operations\":{\"add_rule\":{\"optional\":[\"index\"],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"move_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"to_index\",\"causal_edge_ids\",\"rationale\"]},\"no_change\":{\"optional\":[],\"required\":[\"op\",\"rationale\"]},\"remove_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"causal_edge_ids\",\"rationale\"]},\"replace_rule\":{\"optional\":[],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"set_param\":{\"optional\":[],\"required\":[\"op\",\"param\",\"to\",\"causal_edge_ids\",\"rationale\"]}},\"rationale\":\"nonempty string\",\"root\":{\"patch\":\"list with exactly one operation\",\"required\":[\"patch\"]},\"rule\":{\"required\":[\"id\",\"when\",\"then\"],\"then\":{\"required\":[\"op\"],\"value_for\":[\"set_residual\",\"step_setpoint\"]},\"when_item\":{\"required\":[\"field\",\"op\",\"value\"]}}}\n",
      "role": "system"
    },
    {
      "content": "\n### CURRENT EXECUTABLE PROGRAM P_h\n```json\n{\"program_version\":0,\"params\":{\"precool_lead_steps\":4,\"precool_residual_c\":-5.0,\"pmv_band_lo\":0.3,\"pmv_band_hi\":0.45,\"pmv_step_c\":0.3},\"rules\":[{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}},{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}},{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}},{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}},{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}},{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}]}\n```\n\n### PARAMETER AND RULE LIMITS\n```json\n{\"precool_lead_steps\":{\"bounds\":[0,4],\"bounds_come_from\":\"visible forecast horizon\"},\"precool_residual_c\":{\"bounds\":[-5.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"pmv_band_lo\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_band_hi\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_step_c\":{\"bounds\":[0.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"a_rule_you_add\":{\"conditions_may_test\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"compared_against\":\"a number, or the name of a parameter above\",\"actions\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"most_rules_at_once\":8},\"weather_condition_values\":{\"must_be\":\"finite numeric literals\",\"parameter_references\":\"not allowed\"}}\n```\n\n### CAUSAL EVIDENCE\n| id | source | relation | target | tags | undirected |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Weak Impact\\\"]\" | false |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n\n### CONTROL DOMAIN\n```json\n{\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n```\n\n### WHAT SOME OF THE FIELD NAMES MEAN\nallowance_left_to_you_c -- the remaining cooling-budget amount for this hour's accepted patches, in the supplied budget units. It covers worst-case additional cooling only, not current residual, current setpoint or physical power\ncomfort_headroom_c -- how far zone temperature would have to rise, or fall, to reach the band edge. Room in zone temperature, not in the setpoint; the edge of the score, not of what people feel\nneg_param -- the name of a numeric parameter whose value is used with the opposite sign; it does not establish which action to take\noutdoor_temp_change_next_1h_c -- outdoor dry-bulb temperature at the fourth future 15-minute step minus the current value, in degrees Celsius; it describes the forecast change and does not prescribe an action\nprogram_version -- the program-version label recorded with a result; it does not establish result quality or control suitability\nsolar_irr_max_next_1h_w_m2 -- the maximum forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\nsolar_irr_mean_next_1h_w_m2 -- the mean forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":1.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":2}}\n```\n\n### CAOL WORKING MEMORY\n| hour | zone | context.regime_step_coverage.steady_state_occupancy | context.initial_observation.zone_temperature_c | context.initial_observation.current_occupancy | context.initial_observation.last_occupancy | context.initial_observation.occupancy_next_steps | context.initial_observation.last_pmv | context.initial_observation.last_setpoint_c | action.proposal.op | action.proposal.rationale | action.admission.status | action.admission.completed_validation_stages | action.program_version_before | action.program_version_after | action.actual_setpoints_c | action.matched_rules | action.shield | outcome.zone_temperatures_c | outcome.pmv | outcome.effective_occupancy | outcome.site_cost | outcome.site_energy_kwh | outcome.discomfort_zone_hours | outcome.discomfort_pmv_hours | outcome.occupied_peak_absolute_pmv | outcome.setpoint_total_variation_c | outcome.setpoint_direction_reversals | lesson |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 41 | \"sou\" | \"[164,165,166,167]\" | 24.47 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.39 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.47,24.47,24.47,24.47]\" | \"[0.39,0.39,0.39,0.39]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.39 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n\n### ACTIVE LONG-TERM EXPERIENCES\n| regime | revision | experience |\n| --- | --- | --- |\n| \"steady_state_occupancy\" | 2 | \"South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"occupancy_next_steps\":[1.0,1.0,1.0,1.0],\"zone_temp_c\":24.47,\"last_pmv\":0.39,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"comfort_headroom_c\":{\"warmer_c\":0.45,\"cooler_c\":2.61},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5,\"weather_next_steps\":[{\"step_ahead\":1,\"outdoor_temp_c\":31.6,\"solar_irr\":628.0},{\"step_ahead\":2,\"outdoor_temp_c\":31.8,\"solar_irr\":646.0},{\"step_ahead\":3,\"outdoor_temp_c\":32.0,\"solar_irr\":668.0},{\"step_ahead\":4,\"outdoor_temp_c\":32.2,\"solar_irr\":628.0}]}\n```\n",
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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、已完成结果、舒适余量、给定的因果证据、额度与 CAOL WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n只使用给定的结构化对象。通过 causal_edge_ids 引用 ID。确定性验证器将派生作用并补齐必要的站点聚合边。不得复制或编造边文本。\n\n硬边界\n只使用当前区域输入以及按 k 提供的已完成 CAOL 历史。额度是以给定单位表示的高耗能动作额度，只覆盖本小时已接受补丁带来的最坏新增高耗能设定点移动，不是当前残差、当前设定点或物理功率。不得读取未提供的离线日志、未来数据、反事实、oracle 信号或给定 CAOL Lesson 之外的 Reflector 散文。可执行控制规格、操作名称、参数边界、动作词汇、预算收费、可达性、shield 和确定性解释器拥有最终权威。不得编写 Python、完整控制器、直接设定点或可执行规格之外的动作。缺失输入块整体省略。 启用的长期经验是本区域的观察，不是命令；它们不能覆盖可执行程序、验证、Budget 或 Safety。\n\n输出\n只返回一个精确的 root JSON 对象：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。patch 列表必须恰好包含一个操作。只引用实际使用的 active experience；空 memory_refs 列表合法。no_change 是一个可用操作，并与其他操作一样需要非空理由。不要返回解释文字、Markdown 围栏或未知字段。patch_contract：{\"causal_edge_ids\":\"stable IDs from the supplied structured edge objects\",\"operations\":{\"add_rule\":{\"optional\":[\"index\"],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"move_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"to_index\",\"causal_edge_ids\",\"rationale\"]},\"no_change\":{\"optional\":[],\"required\":[\"op\",\"rationale\"]},\"remove_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"causal_edge_ids\",\"rationale\"]},\"replace_rule\":{\"optional\":[],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"set_param\":{\"optional\":[],\"required\":[\"op\",\"param\",\"to\",\"causal_edge_ids\",\"rationale\"]}},\"rationale\":\"nonempty string\",\"root\":{\"patch\":\"list with exactly one operation\",\"required\":[\"patch\"]},\"rule\":{\"required\":[\"id\",\"when\",\"then\"],\"then\":{\"required\":[\"op\"],\"value_for\":[\"set_residual\",\"step_setpoint\"]},\"when_item\":{\"required\":[\"field\",\"op\",\"value\"]}}}\n",
      "role": "system"
    },
    {
      "content": "\n### CURRENT EXECUTABLE PROGRAM P_h\n```json\n{\"program_version\":0,\"params\":{\"precool_lead_steps\":4,\"precool_residual_c\":-5.0,\"pmv_band_lo\":0.3,\"pmv_band_hi\":0.45,\"pmv_step_c\":0.3},\"rules\":[{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}},{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}},{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}},{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}},{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}},{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}]}\n```\n\n### PARAMETER AND RULE LIMITS\n```json\n{\"precool_lead_steps\":{\"bounds\":[0,4],\"bounds_come_from\":\"visible forecast horizon\"},\"precool_residual_c\":{\"bounds\":[-5.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"pmv_band_lo\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_band_hi\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_step_c\":{\"bounds\":[0.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"a_rule_you_add\":{\"conditions_may_test\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"compared_against\":\"a number, or the name of a parameter above\",\"actions\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"most_rules_at_once\":8},\"weather_condition_values\":{\"must_be\":\"finite numeric literals\",\"parameter_references\":\"not allowed\"}}\n```\n\n### CAUSAL EVIDENCE\n| id | source | relation | target | tags | undirected |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Weak Impact\\\"]\" | false |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n\n### CONTROL DOMAIN\n```json\n{\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n```\n\n### WHAT SOME OF THE FIELD NAMES MEAN\nallowance_left_to_you_c -- the remaining cooling-budget amount for this hour's accepted patches, in the supplied budget units. It covers worst-case additional cooling only, not current residual, current setpoint or physical power\ncomfort_headroom_c -- how far zone temperature would have to rise, or fall, to reach the band edge. Room in zone temperature, not in the setpoint; the edge of the score, not of what people feel\nneg_param -- the name of a numeric parameter whose value is used with the opposite sign; it does not establish which action to take\noutdoor_temp_change_next_1h_c -- outdoor dry-bulb temperature at the fourth future 15-minute step minus the current value, in degrees Celsius; it describes the forecast change and does not prescribe an action\nprogram_version -- the program-version label recorded with a result; it does not establish result quality or control suitability\nsolar_irr_max_next_1h_w_m2 -- the maximum forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\nsolar_irr_mean_next_1h_w_m2 -- the mean forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":1.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":3}}\n```\n\n### CAOL WORKING MEMORY\n| hour | zone | context.regime_step_coverage.steady_state_occupancy | context.initial_observation.zone_temperature_c | context.initial_observation.current_occupancy | context.initial_observation.last_occupancy | context.initial_observation.occupancy_next_steps | context.initial_observation.last_pmv | context.initial_observation.last_setpoint_c | action.proposal.op | action.proposal.rationale | action.admission.status | action.admission.completed_validation_stages | action.program_version_before | action.program_version_after | action.actual_setpoints_c | action.matched_rules | action.shield | outcome.zone_temperatures_c | outcome.pmv | outcome.effective_occupancy | outcome.site_cost | outcome.site_energy_kwh | outcome.discomfort_zone_hours | outcome.discomfort_pmv_hours | outcome.occupied_peak_absolute_pmv | outcome.setpoint_total_variation_c | outcome.setpoint_direction_reversals | lesson |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 41 | \"wes\" | \"[164,165,166,167]\" | 24.36 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.36 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.36,24.36,24.36,24.36]\" | \"[0.36,0.36,0.36,0.36]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.36 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n\n### ACTIVE LONG-TERM EXPERIENCES\n| regime | revision | experience |\n| --- | --- | --- |\n| \"steady_state_occupancy\" | 1 | \"West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"occupancy_next_steps\":[1.0,1.0,1.0,1.0],\"zone_temp_c\":24.36,\"last_pmv\":0.36,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"comfort_headroom_c\":{\"warmer_c\":0.57,\"cooler_c\":2.5},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5,\"weather_next_steps\":[{\"step_ahead\":1,\"outdoor_temp_c\":31.6,\"solar_irr\":628.0},{\"step_ahead\":2,\"outdoor_temp_c\":31.8,\"solar_irr\":646.0},{\"step_ahead\":3,\"outdoor_temp_c\":32.0,\"solar_irr\":668.0},{\"step_ahead\":4,\"outdoor_temp_c\":32.2,\"solar_irr\":628.0}]}\n```\n",
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
      "content": "角色\n解释刚刚结束小时的确定性结果。\n\n证据\n使用给定的已完成小时确定性 Context、Action 与 Outcome。为每个区域生成一条 Lesson。不得复述或重新计算确定性字段，也不得推断反事实。 然后将各区域 Lesson 与该区域的三个状态槽比较，并为该区域最多选择一个操作。\n\n硬边界\n只使用给定的已完成小时证据。不得读取离线日志、未来数据、oracle 信号或控制指令。每个区域返回一条简洁的单行 Lesson。不得给出动作命令、目标或没有证据支持的因果结论。无效 Lesson 由确定性代码省略，且不得阻塞控制。 存储经验必须概括该区域在指定状态下贯穿整个运行的热响应、控制偏好或已观察权衡。不得提及具体小时、未来信息、其他区域、oracle、固定动作命令或隐藏控制规则。只能操作本小时实际出现的状态；replace 或 delete 必须使用给定 revision。\n\n输出\n返回一个裸 JSON 对象：{\"hourly_lessons\":[{\"zone\":...,\"lesson\":...}],\"memory_operations\":[...]}。两个列表中每个给定区域必须恰好出现一次。每个操作必须精确属于以下之一：{\"zone\":...,\"op\":\"no_change\"}；{\"zone\":...,\"op\":\"add\",\"regime\":...,\"experience\":...}；{\"zone\":...,\"op\":\"replace\",\"regime\":...,\"expected_revision\":...,\"experience\":...}；{\"zone\":...,\"op\":\"delete\",\"regime\":...,\"expected_revision\":...}。不返回解释文字、Markdown 围栏或未知字段。\n",
      "role": "system"
    },
    {
      "content": "\n### CURRENT HOUR DETERMINISTIC CAO\n| hour | zone | context.regime_step_coverage.steady_state_occupancy | context.initial_observation.zone_temperature_c | context.initial_observation.current_occupancy | context.initial_observation.last_occupancy | context.initial_observation.occupancy_next_steps | context.initial_observation.last_pmv | context.initial_observation.last_setpoint_c | action.proposal.op | action.proposal.rationale | action.admission.status | action.admission.completed_validation_stages | action.program_version_before | action.program_version_after | action.actual_setpoints_c | action.matched_rules | action.shield | outcome.zone_temperatures_c | outcome.pmv | outcome.effective_occupancy | outcome.site_cost | outcome.site_energy_kwh | outcome.discomfort_zone_hours | outcome.discomfort_pmv_hours | outcome.occupied_peak_absolute_pmv | outcome.setpoint_total_variation_c | outcome.setpoint_direction_reversals | action.proposal.param | action.proposal.to | action.proposal.causal_edge_ids | action.proposal.expected_effects | action.proposal.consistent_program_direction_proof.mode | action.proposal.consistent_program_direction_proof.program_direction | action.proposal.consistent_program_direction_proof.expected_effects | action.proposal.consistent_program_direction_proof.witness_count | action.proposal.consistent_program_direction_proof.cited_edge_ids |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 42 | \"cor\" | \"[168,169,170,171]\" | 24.31 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.34 | 25.0 | \"no_change\" | \"当前程序保持了占用舒适余量，且没有证据支持有益修改。\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.3,24.32,24.34,24.35]\" | \"[0.34,0.35,0.35,0.36]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.36 | 0.0 | 0 |  |  |  |  |  |  |  |  |  |\n| 42 | \"eas\" | \"[168,169,170,171]\" | 24.58 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.43 | 25.0 | \"set_param\" | \"East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 1 | \"[24.7,24.7,24.7,25.0]\" | \"[\\\"pmv_lower\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"pmv_raise\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.4,24.25,24.18,24.24]\" | \"[0.36,0.3,0.28,0.31]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.36 | 0.3 | 0 | \"pmv_band_hi\" | 0.4 | \"[\\\"ce_ebd13728\\\",\\\"ce_660795c7\\\"]\" | \"[{\\\"node\\\":\\\"power_meters\\\",\\\"direction\\\":\\\"up\\\"},{\\\"node\\\":\\\"zone_temp\\\",\\\"direction\\\":\\\"down\\\"}]\" | \"global\" | \"down\" | \"[{\\\"node\\\":\\\"power_meters\\\",\\\"direction\\\":\\\"up\\\"},{\\\"node\\\":\\\"zone_temp\\\",\\\"direction\\\":\\\"down\\\"}]\" | 180 | \"[\\\"ce_ebd13728\\\",\\\"ce_660795c7\\\"]\" |\n| 42 | \"nor\" | \"[168,169,170,171]\" | 24.22 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.31 | 25.0 | \"no_change\" | \"当前程序与已观察到的稳定占用状态相匹配。\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.23,24.24,24.25,24.27]\" | \"[0.31,0.32,0.32,0.33]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.33 | 0.0 | 0 |  |  |  |  |  |  |  |  |  |\n| 42 | \"sou\" | \"[168,169,170,171]\" | 24.47 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.39 | 25.0 | \"no_change\" | \"已观察舒适余量与当前程序不支持其他原子修改。\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.47,24.49,24.5,24.52]\" | \"[0.39,0.4,0.4,0.41]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.41 | 0.0 | 0 |  |  |  |  |  |  |  |  |  |\n| 42 | \"wes\" | \"[168,169,170,171]\" | 24.36 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.36 | 25.0 | \"no_change\" | \"给定证据不支持在本小时修改可执行规格。\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.37,24.38,24.4,24.41]\" | \"[0.36,0.37,0.37,0.38]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.38 | 0.0 | 0 |  |  |  |  |  |  |  |  |  |\n\n### CURRENT THREE-REGIME EXPERIENCE SLOTS\n```json\n{\"cor\":[{\"regime\":\"unoccupied\",\"state\":\"empty\"},{\"regime\":\"occupancy_transition\",\"state\":\"empty\"},{\"regime\":\"steady_state_occupancy\",\"revision\":2,\"experience\":\"Core temperature has remained slow-changing under occupied holding actions while warm-side comfort headroom stayed positive.\"}],\"eas\":[{\"regime\":\"unoccupied\",\"state\":\"empty\"},{\"regime\":\"occupancy_transition\",\"state\":\"empty\"},{\"regime\":\"steady_state_occupancy\",\"revision\":1,\"experience\":\"East has shown the smallest occupied warm-side comfort headroom and a faster temperature response than the other periods observed for this zone.\"}],\"nor\":[{\"regime\":\"unoccupied\",\"state\":\"empty\"},{\"regime\":\"occupancy_transition\",\"state\":\"empty\"},{\"regime\":\"steady_state_occupancy\",\"state\":\"empty\"}],\"sou\":[{\"regime\":\"unoccupied\",\"state\":\"empty\"},{\"regime\":\"occupancy_transition\",\"state\":\"empty\"},{\"regime\":\"steady_state_occupancy\",\"revision\":2,\"experience\":\"South has retained moderate occupied comfort headroom during stable setpoint periods despite elevated solar conditions.\"}],\"wes\":[{\"regime\":\"unoccupied\",\"state\":\"empty\"},{\"regime\":\"occupancy_transition\",\"state\":\"empty\"},{\"regime\":\"steady_state_occupancy\",\"revision\":1,\"experience\":\"West has shown moderate occupied thermal response with positive warm-side comfort headroom during stable actions.\"}]}\n```\n",
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
## 7. 完整CAOL与下一小时Working Memory

### Completed CAOL

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
### Next-hour Orchestrator CAOL working memory

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
### Next-hour East Executor CAOL working memory

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
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、已完成结果、舒适余量、给定的因果证据、额度与 CAOL WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n只使用给定的结构化对象。通过 causal_edge_ids 引用 ID。确定性验证器将派生作用并补齐必要的站点聚合边。不得复制或编造边文本。\n\n硬边界\n只使用当前区域输入以及按 k 提供的已完成 CAOL 历史。额度是以给定单位表示的高耗能动作额度，只覆盖本小时已接受补丁带来的最坏新增高耗能设定点移动，不是当前残差、当前设定点或物理功率。不得读取未提供的离线日志、未来数据、反事实、oracle 信号或给定 CAOL Lesson 之外的 Reflector 散文。可执行控制规格、操作名称、参数边界、动作词汇、预算收费、可达性、shield 和确定性解释器拥有最终权威。不得编写 Python、完整控制器、直接设定点或可执行规格之外的动作。缺失输入块整体省略。 启用的长期经验是本区域的观察，不是命令；它们不能覆盖可执行程序、验证、Budget 或 Safety。\n\n输出\n只返回一个精确的 root JSON 对象：{\"patch\":[{...}],\"memory_refs\":[{\"regime\":...,\"revision\":...}]}。patch 列表必须恰好包含一个操作。只引用实际使用的 active experience；空 memory_refs 列表合法。no_change 是一个可用操作，并与其他操作一样需要非空理由。不要返回解释文字、Markdown 围栏或未知字段。patch_contract：{\"causal_edge_ids\":\"stable IDs from the supplied structured edge objects\",\"operations\":{\"add_rule\":{\"optional\":[\"index\"],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"move_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"to_index\",\"causal_edge_ids\",\"rationale\"]},\"no_change\":{\"optional\":[],\"required\":[\"op\",\"rationale\"]},\"remove_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"causal_edge_ids\",\"rationale\"]},\"replace_rule\":{\"optional\":[],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"set_param\":{\"optional\":[],\"required\":[\"op\",\"param\",\"to\",\"causal_edge_ids\",\"rationale\"]}},\"rationale\":\"nonempty string\",\"root\":{\"patch\":\"list with exactly one operation\",\"required\":[\"patch\"]},\"rule\":{\"required\":[\"id\",\"when\",\"then\"],\"then\":{\"required\":[\"op\"],\"value_for\":[\"set_residual\",\"step_setpoint\"]},\"when_item\":{\"required\":[\"field\",\"op\",\"value\"]}}}\n",
      "role": "system"
    },
    {
      "content": "\n### CURRENT EXECUTABLE PROGRAM P_h\n```json\n{\"program_version\":1,\"params\":{\"precool_lead_steps\":4,\"precool_residual_c\":-5.0,\"pmv_band_lo\":0.3,\"pmv_band_hi\":0.4,\"pmv_step_c\":0.3},\"rules\":[{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}},{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}},{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}},{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}},{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}},{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}]}\n```\n\n### PARAMETER AND RULE LIMITS\n```json\n{\"precool_lead_steps\":{\"bounds\":[0,4],\"bounds_come_from\":\"visible forecast horizon\"},\"precool_residual_c\":{\"bounds\":[-5.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"pmv_band_lo\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_band_hi\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_step_c\":{\"bounds\":[0.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"a_rule_you_add\":{\"conditions_may_test\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"compared_against\":\"a number, or the name of a parameter above\",\"actions\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"most_rules_at_once\":8},\"weather_condition_values\":{\"must_be\":\"finite numeric literals\",\"parameter_references\":\"not allowed\"}}\n```\n\n### CAUSAL EVIDENCE\n| id | source | relation | target | tags | undirected |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Weak Impact\\\"]\" | false |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n\n### CONTROL DOMAIN\n```json\n{\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n```\n\n### WHAT SOME OF THE FIELD NAMES MEAN\nallowance_left_to_you_c -- the remaining cooling-budget amount for this hour's accepted patches, in the supplied budget units. It covers worst-case additional cooling only, not current residual, current setpoint or physical power\ncomfort_headroom_c -- how far zone temperature would have to rise, or fall, to reach the band edge. Room in zone temperature, not in the setpoint; the edge of the score, not of what people feel\nneg_param -- the name of a numeric parameter whose value is used with the opposite sign; it does not establish which action to take\noutdoor_temp_change_next_1h_c -- outdoor dry-bulb temperature at the fourth future 15-minute step minus the current value, in degrees Celsius; it describes the forecast change and does not prescribe an action\nprogram_version -- the program-version label recorded with a result; it does not establish result quality or control suitability\nsolar_irr_max_next_1h_w_m2 -- the maximum forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\nsolar_irr_mean_next_1h_w_m2 -- the mean forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":1.7,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":1}}\n```\n\n### CAOL WORKING MEMORY\n| hour | zone | context.regime_step_coverage.steady_state_occupancy | context.initial_observation.zone_temperature_c | context.initial_observation.current_occupancy | context.initial_observation.last_occupancy | context.initial_observation.occupancy_next_steps | context.initial_observation.last_pmv | context.initial_observation.last_setpoint_c | action.proposal.op | action.proposal.rationale | action.proposal.param | action.proposal.to | action.proposal.causal_edge_ids | action.proposal.expected_effects | action.proposal.consistent_program_direction_proof.mode | action.proposal.consistent_program_direction_proof.program_direction | action.proposal.consistent_program_direction_proof.expected_effects | action.proposal.consistent_program_direction_proof.witness_count | action.proposal.consistent_program_direction_proof.cited_edge_ids | action.admission.status | action.admission.completed_validation_stages | action.program_version_before | action.program_version_after | action.actual_setpoints_c | action.matched_rules | action.shield | outcome.zone_temperatures_c | outcome.pmv | outcome.effective_occupancy | outcome.site_cost | outcome.site_energy_kwh | outcome.discomfort_zone_hours | outcome.discomfort_pmv_hours | outcome.occupied_peak_absolute_pmv | outcome.setpoint_total_variation_c | outcome.setpoint_direction_reversals | lesson |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 42 | \"eas\" | \"[168,169,170,171]\" | 24.58 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.43 | 25.0 | \"set_param\" | \"East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。\" | \"pmv_band_hi\" | 0.4 | \"[\\\"ce_ebd13728\\\",\\\"ce_660795c7\\\"]\" | \"[{\\\"node\\\":\\\"power_meters\\\",\\\"direction\\\":\\\"up\\\"},{\\\"node\\\":\\\"zone_temp\\\",\\\"direction\\\":\\\"down\\\"}]\" | \"global\" | \"down\" | \"[{\\\"node\\\":\\\"power_meters\\\",\\\"direction\\\":\\\"up\\\"},{\\\"node\\\":\\\"zone_temp\\\",\\\"direction\\\":\\\"down\\\"}]\" | 180 | \"[\\\"ce_ebd13728\\\",\\\"ce_660795c7\\\"]\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 1 | \"[24.7,24.7,24.7,25.0]\" | \"[\\\"pmv_lower\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"pmv_raise\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.4,24.25,24.18,24.24]\" | \"[0.36,0.3,0.28,0.31]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.36 | 0.3 | 0 | \"更紧的上侧阈值之后出现了有界制冷响应，同时占用 PMV 保持在舒适带内。\" |\n\n### ACTIVE LONG-TERM EXPERIENCES\n| regime | revision | experience |\n| --- | --- | --- |\n| \"steady_state_occupancy\" | 2 | \"East 在占用状态下反复表现出有限的暖侧舒适余量，并在更紧上侧阈值获准后呈现有界制冷响应。\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"occupancy_next_steps\":[1.0,1.0,1.0,1.0],\"zone_temp_c\":24.24,\"last_pmv\":0.31,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"comfort_headroom_c\":{\"warmer_c\":0.34,\"cooler_c\":2.72},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5,\"weather_next_steps\":[{\"step_ahead\":1,\"outdoor_temp_c\":31.6,\"solar_irr\":628.0},{\"step_ahead\":2,\"outdoor_temp_c\":31.8,\"solar_irr\":646.0},{\"step_ahead\":3,\"outdoor_temp_c\":32.0,\"solar_irr\":668.0},{\"step_ahead\":4,\"outdoor_temp_c\":32.2,\"solar_irr\":628.0}]}\n```\n",
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
  "caol_working_memory_retained": true,
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
    "CURRENT THREE-REGIME EXPERIENCE SLOTS"
  ],
  "runtime_output_removed": [
    "long-term CRUD rows",
    "Executor memory-reference audit"
  ]
}
```
### Memory-off East Executor complete request

```json
{
  "messages": [
    {
      "content": "角色\n维护一个区域的可执行控制规格。\n\n决策\n使用当前观测、已完成结果、舒适余量、给定的因果证据、额度与 CAOL WORKING MEMORY，提出一个原子操作。在保持 |PMV| ≤ 0.5 的前提下，探索节能机会。不要计算解释器结果。\n\n因果证据\n只使用给定的结构化对象。通过 causal_edge_ids 引用 ID。确定性验证器将派生作用并补齐必要的站点聚合边。不得复制或编造边文本。\n\n硬边界\n只使用当前区域输入以及按 k 提供的已完成 CAOL 历史。额度是以给定单位表示的高耗能动作额度，只覆盖本小时已接受补丁带来的最坏新增高耗能设定点移动，不是当前残差、当前设定点或物理功率。不得读取未提供的离线日志、未来数据、反事实、oracle 信号或给定 CAOL Lesson 之外的 Reflector 散文。可执行控制规格、操作名称、参数边界、动作词汇、预算收费、可达性、shield 和确定性解释器拥有最终权威。不得编写 Python、完整控制器、直接设定点或可执行规格之外的动作。缺失输入块整体省略。\n\n输出\n只返回一个精确的 root JSON 对象：{\"patch\":[{...}]}。列表必须恰好包含一个操作。no_change 是一个可用操作，并与其他操作一样需要非空理由。不要返回解释文字、Markdown 围栏或未知执行字段。patch_contract：{\"causal_edge_ids\":\"stable IDs from the supplied structured edge objects\",\"operations\":{\"add_rule\":{\"optional\":[\"index\"],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"move_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"to_index\",\"causal_edge_ids\",\"rationale\"]},\"no_change\":{\"optional\":[],\"required\":[\"op\",\"rationale\"]},\"remove_rule\":{\"optional\":[],\"required\":[\"op\",\"id\",\"causal_edge_ids\",\"rationale\"]},\"replace_rule\":{\"optional\":[],\"required\":[\"op\",\"rule\",\"causal_edge_ids\",\"rationale\"]},\"set_param\":{\"optional\":[],\"required\":[\"op\",\"param\",\"to\",\"causal_edge_ids\",\"rationale\"]}},\"rationale\":\"nonempty string\",\"root\":{\"patch\":\"list with exactly one operation\",\"required\":[\"patch\"]},\"rule\":{\"required\":[\"id\",\"when\",\"then\"],\"then\":{\"required\":[\"op\"],\"value_for\":[\"set_residual\",\"step_setpoint\"]},\"when_item\":{\"required\":[\"field\",\"op\",\"value\"]}}}\n",
      "role": "system"
    },
    {
      "content": "\n### CURRENT EXECUTABLE PROGRAM P_h\n```json\n{\"program_version\":0,\"params\":{\"precool_lead_steps\":4,\"precool_residual_c\":-5.0,\"pmv_band_lo\":0.3,\"pmv_band_hi\":0.45,\"pmv_step_c\":0.3},\"rules\":[{\"id\":\"precool\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0},{\"field\":\"precool_due\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"set_residual\",\"value\":{\"param\":\"precool_residual_c\"}}},{\"id\":\"pmv_raise\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\"<\",\"value\":{\"param\":\"pmv_band_lo\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"param\":\"pmv_step_c\"}}},{\"id\":\"pmv_lower\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"last_pmv\",\"op\":\">\",\"value\":{\"param\":\"pmv_band_hi\"}}],\"then\":{\"op\":\"step_setpoint\",\"value\":{\"neg_param\":\"pmv_step_c\"}}},{\"id\":\"anchor\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1},{\"field\":\"occupied_last\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}},{\"id\":\"occupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":1}],\"then\":{\"op\":\"hold_setpoint\"}},{\"id\":\"unoccupied_hold\",\"when\":[{\"field\":\"occupied_now\",\"op\":\"==\",\"value\":0}],\"then\":{\"op\":\"set_residual\",\"value\":0.0}}]}\n```\n\n### PARAMETER AND RULE LIMITS\n```json\n{\"precool_lead_steps\":{\"bounds\":[0,4],\"bounds_come_from\":\"visible forecast horizon\"},\"precool_residual_c\":{\"bounds\":[-5.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"pmv_band_lo\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_band_hi\":{\"bounds\":[-0.5,0.5],\"bounds_come_from\":\"PMV evaluation range\"},\"pmv_step_c\":{\"bounds\":[0.0,5.0],\"bounds_come_from\":\"residual safety bound\"},\"a_rule_you_add\":{\"conditions_may_test\":[\"last_pmv\",\"occupied_last\",\"occupied_now\",\"outdoor_temp_change_next_1h_c\",\"precool_due\",\"solar_irr_max_next_1h_w_m2\",\"solar_irr_mean_next_1h_w_m2\"],\"comparisons\":[\"<\",\"<=\",\">\",\">=\",\"==\",\"!=\"],\"compared_against\":\"a number, or the name of a parameter above\",\"actions\":[\"set_residual\",\"step_setpoint\",\"hold_setpoint\"],\"most_rules_at_once\":8},\"weather_condition_values\":{\"must_be\":\"finite numeric literals\",\"parameter_references\":\"not allowed\"}}\n```\n\n### CAUSAL EVIDENCE\n| id | source | relation | target | tags | undirected |\n| --- | --- | --- | --- | --- | --- |\n| \"ce_aa18e859\" | \"outdoor_temp\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_fc68b8f7\" | \"solar_irr\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_ebd13728\" | \"cooling_setpoint\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_d8c6ee57\" | \"occupancy\" | \"Positive Corr\" | \"zone_temp\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_e8f5f362\" | \"outdoor_temp\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_5a968228\" | \"solar_irr\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Weak Impact\\\"]\" | false |\n| \"ce_00f91137\" | \"occupancy\" | \"Positive Corr\" | \"power_meters\" | \"[\\\"Delayed\\\",\\\"Strong Impact\\\"]\" | false |\n| \"ce_660795c7\" | \"cooling_setpoint\" | \"Negative Corr\" | \"power_meters\" | \"[\\\"Immediate\\\",\\\"Strong Impact\\\"]\" | false |\n\n### CONTROL DOMAIN\n```json\n{\"domain_id\":\"cooling\",\"controlled_setpoint\":\"zone cooling setpoint\",\"unit\":\"degC\",\"hard_bounds_c\":[20.0,30.0],\"occupied_base_c\":25.0,\"unoccupied_base_c\":30.0,\"pmv_comfort_band\":[0.3,0.45],\"preconditioning\":{\"label\":\"precool\",\"lead_steps\":4,\"target_c\":25.0},\"energy_intensive_setpoint_direction\":\"decrease\"}\n```\n\n### WHAT SOME OF THE FIELD NAMES MEAN\nallowance_left_to_you_c -- the remaining cooling-budget amount for this hour's accepted patches, in the supplied budget units. It covers worst-case additional cooling only, not current residual, current setpoint or physical power\ncomfort_headroom_c -- how far zone temperature would have to rise, or fall, to reach the band edge. Room in zone temperature, not in the setpoint; the edge of the score, not of what people feel\nneg_param -- the name of a numeric parameter whose value is used with the opposite sign; it does not establish which action to take\noutdoor_temp_change_next_1h_c -- outdoor dry-bulb temperature at the fourth future 15-minute step minus the current value, in degrees Celsius; it describes the forecast change and does not prescribe an action\nprogram_version -- the program-version label recorded with a result; it does not establish result quality or control suitability\nsolar_irr_max_next_1h_w_m2 -- the maximum forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\nsolar_irr_mean_next_1h_w_m2 -- the mean forecast solar irradiance over the next four 15-minute steps, in watts per square metre; it describes the forecast magnitude and does not prescribe an action\n\n### ALLOCATION\n```json\n{\"allocation\":{\"allowance_left_to_you_c\":2.0,\"group_allowance_not_yet_handed_out_c\":4.0,\"your_place_in_the_queue_for_the_remainder\":1}}\n```\n\n### CAOL WORKING MEMORY\n| hour | zone | context.regime_step_coverage.steady_state_occupancy | context.initial_observation.zone_temperature_c | context.initial_observation.current_occupancy | context.initial_observation.last_occupancy | context.initial_observation.occupancy_next_steps | context.initial_observation.last_pmv | context.initial_observation.last_setpoint_c | action.proposal.op | action.proposal.rationale | action.admission.status | action.admission.completed_validation_stages | action.program_version_before | action.program_version_after | action.actual_setpoints_c | action.matched_rules | action.shield | outcome.zone_temperatures_c | outcome.pmv | outcome.effective_occupancy | outcome.site_cost | outcome.site_energy_kwh | outcome.discomfort_zone_hours | outcome.discomfort_pmv_hours | outcome.occupied_peak_absolute_pmv | outcome.setpoint_total_variation_c | outcome.setpoint_direction_reversals | lesson |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 41 | \"eas\" | \"[164,165,166,167]\" | 24.58 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.43 | 25.0 | \"no_change\" | \"completed-hour fixture\" | \"accepted\" | \"[\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\",\\\"program_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":164,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":165,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":166,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":167,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.58,24.58,24.58,24.58]\" | \"[0.43,0.43,0.43,0.43]\" | \"[1.0,1.0,1.0,1.0]\" | 3.02 | 21.1 | 0.0 | 0.0 | 0.43 | 0.0 | 0 | \"稳定占用状态与正向暖侧舒适余量同时出现。\" |\n\n### ZONE OBSERVATION\n```json\n{\"current_occupancy\":1.0,\"last_occupancy\":1.0,\"occupancy_next_steps\":[1.0,1.0,1.0,1.0],\"zone_temp_c\":24.58,\"last_pmv\":0.43,\"last_setpoint_c\":25.0,\"outdoor_temp_c\":31.4,\"solar_irr\":612.0,\"price_now\":0.14231,\"comfort_headroom_c\":{\"warmer_c\":0.34,\"cooler_c\":2.72},\"outdoor_temp_change_next_1h_c\":0.8,\"solar_irr_max_next_1h_w_m2\":668.0,\"solar_irr_mean_next_1h_w_m2\":642.5,\"weather_next_steps\":[{\"step_ahead\":1,\"outdoor_temp_c\":31.6,\"solar_irr\":628.0},{\"step_ahead\":2,\"outdoor_temp_c\":31.8,\"solar_irr\":646.0},{\"step_ahead\":3,\"outdoor_temp_c\":32.0,\"solar_irr\":668.0},{\"step_ahead\":4,\"outdoor_temp_c\":32.2,\"solar_irr\":628.0}]}\n```\n",
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
      "content": "角色\n解释刚刚结束小时的确定性结果。\n\n证据\n使用给定的已完成小时确定性 Context、Action 与 Outcome。为每个区域生成一条 Lesson。不得复述或重新计算确定性字段，也不得推断反事实。\n\n硬边界\n只使用给定的已完成小时证据。不得读取离线日志、未来数据、oracle 信号或控制指令。每个区域返回一条简洁的单行 Lesson。不得给出动作命令、目标或没有证据支持的因果结论。无效 Lesson 由确定性代码省略，且不得阻塞控制。\n\n输出\n返回形如 {\"hourly_lessons\":[{\"zone\":...,\"lesson\":...}]} 的裸 JSON 对象。每个给定区域必须恰好出现一次。不返回解释文字、Markdown 围栏或未知字段。\n",
      "role": "system"
    },
    {
      "content": "\n### CURRENT HOUR DETERMINISTIC CAO\n| hour | zone | context.regime_step_coverage.steady_state_occupancy | context.initial_observation.zone_temperature_c | context.initial_observation.current_occupancy | context.initial_observation.last_occupancy | context.initial_observation.occupancy_next_steps | context.initial_observation.last_pmv | context.initial_observation.last_setpoint_c | action.proposal.op | action.proposal.rationale | action.admission.status | action.admission.completed_validation_stages | action.program_version_before | action.program_version_after | action.actual_setpoints_c | action.matched_rules | action.shield | outcome.zone_temperatures_c | outcome.pmv | outcome.effective_occupancy | outcome.site_cost | outcome.site_energy_kwh | outcome.discomfort_zone_hours | outcome.discomfort_pmv_hours | outcome.occupied_peak_absolute_pmv | outcome.setpoint_total_variation_c | outcome.setpoint_direction_reversals | action.proposal.param | action.proposal.to | action.proposal.causal_edge_ids | action.proposal.expected_effects | action.proposal.consistent_program_direction_proof.mode | action.proposal.consistent_program_direction_proof.program_direction | action.proposal.consistent_program_direction_proof.expected_effects | action.proposal.consistent_program_direction_proof.witness_count | action.proposal.consistent_program_direction_proof.cited_edge_ids |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 42 | \"cor\" | \"[168,169,170,171]\" | 24.31 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.34 | 25.0 | \"no_change\" | \"当前程序保持了占用舒适余量，且没有证据支持有益修改。\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.3,24.32,24.34,24.35]\" | \"[0.34,0.35,0.35,0.36]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.36 | 0.0 | 0 |  |  |  |  |  |  |  |  |  |\n| 42 | \"eas\" | \"[168,169,170,171]\" | 24.58 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.43 | 25.0 | \"set_param\" | \"East 的暖侧余量最小，因此收紧当前上侧 PMV 阈值。\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 1 | \"[24.7,24.7,24.7,25.0]\" | \"[\\\"pmv_lower\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"pmv_raise\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.4,24.25,24.18,24.24]\" | \"[0.36,0.3,0.28,0.31]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.36 | 0.3 | 0 | \"pmv_band_hi\" | 0.4 | \"[\\\"ce_ebd13728\\\",\\\"ce_660795c7\\\"]\" | \"[{\\\"node\\\":\\\"power_meters\\\",\\\"direction\\\":\\\"up\\\"},{\\\"node\\\":\\\"zone_temp\\\",\\\"direction\\\":\\\"down\\\"}]\" | \"global\" | \"down\" | \"[{\\\"node\\\":\\\"power_meters\\\",\\\"direction\\\":\\\"up\\\"},{\\\"node\\\":\\\"zone_temp\\\",\\\"direction\\\":\\\"down\\\"}]\" | 180 | \"[\\\"ce_ebd13728\\\",\\\"ce_660795c7\\\"]\" |\n| 42 | \"nor\" | \"[168,169,170,171]\" | 24.22 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.31 | 25.0 | \"no_change\" | \"当前程序与已观察到的稳定占用状态相匹配。\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.23,24.24,24.25,24.27]\" | \"[0.31,0.32,0.32,0.33]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.33 | 0.0 | 0 |  |  |  |  |  |  |  |  |  |\n| 42 | \"sou\" | \"[168,169,170,171]\" | 24.47 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.39 | 25.0 | \"no_change\" | \"已观察舒适余量与当前程序不支持其他原子修改。\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.47,24.49,24.5,24.52]\" | \"[0.39,0.4,0.4,0.41]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.41 | 0.0 | 0 |  |  |  |  |  |  |  |  |  |\n| 42 | \"wes\" | \"[168,169,170,171]\" | 24.36 | 1.0 | 1.0 | \"[1.0,1.0,1.0,1.0]\" | 0.36 | 25.0 | \"no_change\" | \"给定证据不支持在本小时修改可执行规格。\" | \"accepted\" | \"[\\\"program_validation\\\",\\\"causal_admissibility\\\",\\\"consistent_program_direction_proof\\\",\\\"energy_budget_validation\\\"]\" | 0 | 0 | \"[25.0,25.0,25.0,25.0]\" | \"[\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\",\\\"occupied_hold\\\"]\" | \"[{\\\"step\\\":168,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":169,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":170,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false},{\\\"step\\\":171,\\\"actuator_bounds\\\":false,\\\"setpoint_rate_limit\\\":false,\\\"comfort_recovery\\\":false}]\" | \"[24.37,24.38,24.4,24.41]\" | \"[0.36,0.37,0.37,0.38]\" | \"[1.0,1.0,1.0,1.0]\" | 3.1214 | 21.9425 | 0.0 | 0.0 | 0.38 | 0.0 | 0 |  |  |  |  |  |  |  |  |  |\n",
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
