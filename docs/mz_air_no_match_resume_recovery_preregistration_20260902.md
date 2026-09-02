# MZ Air no-rule-match context recovery preregistration

## Observed terminal fact

The immutable run `20260902T053717223407Z-57f043e175f9` completed atomic hour 119
(steps 0--479) and then advanced physical steps 480--483. Before the hour-120
Reflector call, context compilation raised
`ValueError: working-memory history row is incomplete`.

The terminal rows show one legitimate interpreter result at step 481 for zone
`cor`: no rule matched, so the unoccupied regime-base setpoint of 30 C was
applied. The interpreter explicitly supports this result. Physical execution,
the program and the applied action were not corrupted. The defect was that the
Agent-view compiler treated an absent matched-rule ID as an incomplete row.

## Frozen correction and recovery boundary

The correction is limited to:

1. accepting `matched_rule=None` as the interpreter's legitimate no-match result
   while retaining strict non-null checks for every other required history field;
2. rendering that result as the deterministic fact
   `no_rule_matched; interpreter_residual=0` without changing the canonical
   evidence or executable controller; and
3. adding an evidence-bound CLI attestation for only this audited control-neutral
   `terminal_runtime_error`. The attestation binds the failed run, source, plan,
   test, checkpoint, program versions, prefix, terminal artifacts, post-checkpoint
   suffix, supervision stderr and clean repair commit. Unknown or mismatched runtime
   errors remain ineligible.

No Prompt policy, model setting, P0 program, patch semantics, causal/Budget/Safety
gate, reward, KPI or acceptance criterion changes. The failed directory and test
remain immutable. After offline tests and a clean commit, recovery must use a
fresh run directory and fresh BOPTEST test, physically replay and verify the
480-step atomic prefix, issue no completed-prefix Agent calls, and continue from
hour 120. The four post-checkpoint source steps are incomplete-hour evidence and
are not imported.

## 中文说明

原运行在完整提交第119小时（step 0--479）后，又物理执行了step 480--483，
但在调用该小时Reflector之前构造工作记忆失败。step 481的`cor`并非证据损坏：
它是解释器允许的“没有规则命中，因此采用未占用状态30 C基准设定点”。错误来自
上下文编译器把合法的空规则ID误判为整行缺失。

本次只修复这一表示错误，并为该经过外部审计确认的控制中性runtime错误增加
证据绑定的恢复证明；证明必须逐项匹配失败run、source、plan、test、checkpoint、
program version、prefix、终态文件、未提交后缀、监督stderr和修复commit。默认仍不
放行普通runtime错误。恢复必须使用fresh run/test，完整物理回放并核验已提交的
480步，不重发这些完整小时的Agent调用，然后从第120小时继续。
