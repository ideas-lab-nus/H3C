# Reflector Lesson evidence support

This audit-only map binds each documentation Lesson to canonical completed-interval fields. The pointers are not sent to the model and do not change the Reflector wire.

Result: `EVIDENCE-CLOSED` for the frozen documentation fixture.

| zone | English Lesson | canonical evidence pointers |
| --- | --- | --- |
| cor | Stable setpoints coincided with steady occupied PMV and positive warm-side headroom. | `/action/actual_setpoints_c`<br>`/outcome/pmv`<br>`/context/observed_context_history/temp_rise_to_warm_pmv_edge_c` |
| eas | A tighter upper threshold preceded a bounded cooling response while occupied PMV stayed within the comfort band. | `/action/proposal/to`<br>`/outcome/pmv`<br>`/context/abs_pmv_score_limit` |
| nor | The occupied hold branch coincided with small temperature and PMV changes. | `/action/matched_rules`<br>`/outcome/zone_temperatures_c`<br>`/outcome/pmv` |
| sou | The occupied hold branch retained positive warm-side headroom under elevated solar input. | `/action/matched_rules`<br>`/context/observed_context_history/solar_irradiance_w_m2`<br>`/context/observed_context_history/temp_rise_to_warm_pmv_edge_c` |
| wes | Stable actions coincided with a gradual occupied temperature response and bounded PMV. | `/action/actual_setpoints_c`<br>`/outcome/zone_temperatures_c`<br>`/outcome/pmv` |

Acceptance requires every pointer to resolve in the production-generated canonical record for that zone. Long-term experience slots are excluded from this support map because they are CRUD comparison material rather than completed-interval facts.
