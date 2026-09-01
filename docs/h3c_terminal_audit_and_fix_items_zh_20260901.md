# H3C 三案例终态审计与修改条目

## 范围

本审计覆盖 MZ Air、SZ Air 和 MZ Hydro 三条已完成的 Baseten、仅工作记忆
轨迹。原始 `failure.json` 和 `verification.json` 保持不可变；修复后只允许追加
零调用再认证证据。

## 物理运行中真实发生的事情

三条轨迹都完成了预登记的完整物理评估窗口。普通模型退化发生后，runtime
按照已登记的确定性 fallback 继续运行：

| 案例 | 真实模型契约事件 |
|---|---|
| MZ Air | 第 63 小时 WES 和第 162 小时 COR 的 Executor 因长度耗尽返回空输出；第 15 小时 Orchestrator 缺少因果 ID，第 116 小时分配超过已登记 cap，均使用 fallback |
| SZ Air | 第 136 小时 Executor 因长度耗尽返回空输出；第 44、126 小时 Reflector Lesson 无效；第 6 小时 Orchestrator cap 不匹配，第 87 小时缺少因果 ID，均使用 fallback |
| MZ Hydro | 第 13、80、108 小时 SZ Executor 因长度耗尽返回空输出；第 40、66、89 小时 Orchestrator 缺少因果 ID，均使用 fallback |

这些属于真实的模型契约退化，但不表示物理轨迹损坏：Executor 空输出确定性
映射为 `no_change`，Orchestrator 非法输出使用已登记且再次验证的分配
fallback，Reflector 非法输出只省略 Lesson。

## 旧终态为何被判 invalid

旧 verifier 同时存在以下执行层误判：

1. 跨午夜时直接比较时钟字符串，没有按 24 小时取模；
2. 没有从真实 Baseten strict `json_schema` wire schema 重建请求身份；
3. 把 runtime 确定性补齐“当前可见的站点功率因果边”误判为模型 patch 被篡改；
4. Budget 使用浮点严格相等；
5. SZ Air 某小时用默认 site cap 重算，而没有使用该运行分配契约中的动态 cap。

这些是 verifier 缺陷，不是放宽新的接受标准。修复使用原运行内嵌的 runtime
contract 重放同一证据，并把轨迹、模型契约和性能三个状态分开报告。

## 待修改条目

| 编号 | 修改 | 对控制行为的影响 |
|---|---|---|
| V1 | 工作记忆时钟按 24 小时取模验证 | 无 |
| V2 | 从 Provider 原生 wire schema 重建请求身份 | 无 |
| V3 | 把确定性站点功率边补齐验证为有界、只追加转换 | 无 |
| V4 | Budget 数值共享一个登记的绝对容差 | 无 |
| V5 | renderer、runtime 和 verifier 共用精确动态 cap owner | 无 |
| V6 | 分离 `trajectory_status`、`model_contract_status` 和 `performance_status` | 无 |
| V7 | 追加带源身份和原终态哈希的零调用再认证，绝不覆盖历史文件 | 无 |
| R1 | 把已完成 step 的精确 reward 分解加入下一小时工作记忆 | 只增加可观测反馈，不增加准入或 Safety |

## 发布纪律

旧轨迹继续作为历史证据。新的 MZ Hydro 候选是 fresh、预登记、单次正式运行，
唯一方法变化是 R1。只有它的 reward 严格优于冻结 eRBC 且占用峰值
`|PMV| <= 0.70`，才会用同一 commit 继续验证 SZ Air 和 MZ Air。
