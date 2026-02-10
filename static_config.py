from config import FIXED_HEATING_SETPOINT_VAL, MAPPING_DIR, ENABLE_CAUSAL_INJECTION

# 转换为 Kelvin
T_HEAT_K = FIXED_HEATING_SETPOINT_VAL + 273.15


"""
静态控制配置 (Static Control Configuration)
包含：固定控制动作、物理参数、奖励权重配置。
"""
START_DAY_CONFIG = {
    "bestest_air": 196,
    "multizone_office_simple_hydronic": 213,
    "multizone_office_simple_air": 192
}

MAX_OCCUPANCY_CONFIG = {
    "bestest_air": 2.0,
    "multizone_office_simple_air": 50.0,
    "multizone_office_simple_hydronic": 200.0
}

# --- [NEW] Phase 3.5: 实验阶段配置 ---
PHASE_CONFIG = {
    "warmup_days": 1,      # Day 0-3: 强制 RBC，填充 Memory
    "exploration_days": 6, # Day 3-7: LLM 高温探索 (Temp=0.7)
    "evaluation_days": 7   # Day 7-14: LLM 低温利用 (Temp=0.1)
}

NORMALIZATION_CONFIG = {
    "temp": (-10.0, 40.0),   # 室外温度范围
    "price": (0.0, 0.2),     # 电价范围
    "pmv": (-3.0, 3.0),      # PMV 范围
    "temp_trend": (-5.0, 5.0), # 1小时温差范围
    "price_trend": (-0.2, 0.2), # 1小时电价差范围
    'clo': (0.5, 1.0)
}

TEMPERATURE_SCHEDULE = {
    "warmup": 0.0,      # 不调用 LLM
    "exploration": 0.7, # 尝试新策略
    "evaluation": 0.1   # 稳定复现最佳实践
}

# --- 1. 固定控制动作 ---
STATIC_CONTROLS = {
    "bestest_air": {
        "con_oveTSetHea_u": T_HEAT_K, "con_oveTSetHea_activate": 1,
        "fcu_oveTSup_u": 290.15, "fcu_oveTSup_activate": 1,
        "con_oveTSetCoo_activate": 1,
    },
    "multizone_office_simple_air": {
        "hvac_oveAhu_TSupSet_u": 290.15, "hvac_oveAhu_TSupSet_activate": 1,
        "zone_patterns": {
            "heating_setpoint": "hvac_oveZonSup{Zone}_TZonHeaSet_u",
            "heating_activate": "hvac_oveZonSup{Zone}_TZonHeaSet_activate",
            "cooling_activate": "hvac_oveZonSup{Zone}_TZonCooSet_activate",
            "heating_value": T_HEAT_K
        }
    },
    "multizone_office_simple_hydronic": {
        "bms_oveTZonSetMinNz_u": T_HEAT_K, "bms_oveTZonSetMinNz_activate": 1,
        "bms_oveTZonSetMinSz_u": T_HEAT_K, "bms_oveTZonSetMinSz_activate": 1,
        "bms_oveTZonSetMaxNz_activate": 1, "bms_oveTZonSetMaxSz_activate": 1,
    }
}

# --- 2. 物理环境参数 (PMV计算用) ---
PHYSICAL_CONFIG = {
    'metabolic_rate': 1.1,
    'relative_humidity': 50.0,
    'air_velocity': 0.1,
    'clo_dynamic_params': {
        'winter_clo': 1.0,
        'summer_clo': 0.5,
        'temp_low': 10.0,
        'temp_high': 26.0
    }
}

# --- 2. 战略上下文 (Strategic Context for LLM) ---
# [UPDATED] Reflector Guide
COMMON_REFLECTOR_GUIDE = """
**TEMPERATURE CONTEXT GUIDE (Outdoor)**:
< 10°C: Very Cold | 10-18°C: Cold | 18-24°C: Mild/Moderate | 24-29°C: Warm | > 29°C: Hot / High Heat.
*Use this scale to describe the environment.*

### PHYSICS & LOGIC SELF-CHECK RULES
1. **Inverse Energy Law (Cooling Mode)**: In cooling mode, energy consumption is INVERSELY proportional to the setpoint.
   - ✅ CORRECT LOGIC: "To save energy, I should raise the setpoint."
2. **Thermal Comfort Boundaries**:
   - PMV < 0.35: OVERCOOLED.
   - PMV > 0.5: OVERHEATING.
3. **UNOCCUPIED EXCEPTION**:
   - If Occupancy = 0, PMV > 0.5 is **"Energy Saving Success"**. Evaluation: **POSITIVE**.
4. **RECOGNIZING SUCCESS (The Sweet Spot)**:
   - If Occupancy > 0 and PMV is in **[+0.35, +0.45]**, the strategy is **OPTIMAL**.
   - Evaluation MUST be **POSITIVE**.
   - **DO NOT** suggest raising the setpoint further.
5. **PASSIVE COOLING CHECK (Deadband)**:
   - If Zone Temp < Setpoint, cooling is likely OFF.
   - In this state, "Overcooling" is due to lack of heating or low outdoor temp, NOT because the cooling setpoint is active. 
   - Advice: "Keep Setpoint High to maintain passive saving.
6. **Step Size Constraint**: 
   - If PMV is low (e.g., < 0.35) but Outdoor Temp is High: **DO NOT** suggest large setpoint increases (e.g., +0.5°C or +1.0°C).
   - **ADVICE**: Explicitly recommend **"Micro-Adjustments"** (e.g., +0.1°C or +0.2°C maximum).
   - **Rationale**: "Due to high outdoor heat load, aggressive setpoint increases will break the thermal safety buffer. Use cautious, small steps to find the efficiency edge without crashing into overheating.
"""

# [UPDATED] Strategy Guide 增加优先级
COMMON_STRATEGY_GUIDE = """
**1. ECONOMIC RULE (PRE-COOLING) - STRICTLY FOLLOW**:
   - Pre-cooling (Unoccupied Only): If current occupancy == 0 BUT next hour > 0, you MUST lower the setpoint (e.g., 22-23°C) to store cold air. This is your ONLY chance for aggressive cooling.
   - Occupied Maintenance (Current > 0): If people are ALREADY present, do NOT use "Aggressive Pre-cooling". Instead, use "Steady Comfort". Target PMV [+0.35, +0.45] to balance cost and comfort.
   - If price is rising but people are present: Target the "Upper Comfort Limit" (PMV ≈ +0.45). This saves money without triggering penalties.

**2. OCCUPANCY RULE**:
   - **Occupied (>0)**: Comfort is Priority #1. Keep PMV < 0.45.
   - **Unoccupied (==0)**: Energy is Priority #1. Set 30°C. Ignore PMV (High PMV is GOOD here).

**3. OPTIMIZATION TARGET (When Occupied)**:
   - Target PMV range: **[+0.35, +0.45]**.
   - +0.45 is the "Sweet Spot" (Maximum efficient comfort).
   - > +0.5 is Failure (Penalty).
"""

STRATEGIC_CONTEXT = {
    "bestest_air": {
        "actuator_info": "You can ONLY control: Cooling Temperature Setpoint (Range: 20.0-30.0°C).",
        "fixed_info": "Heating Setpoint is FIXED at 15°C. Supply Fan is ALWAYS ON.",
        "strategy_guide": "Single Zone logic. " + COMMON_STRATEGY_GUIDE,
        "reflector_guide": COMMON_REFLECTOR_GUIDE + "\n*Specific Note: Low thermal mass, reacts quickly.*"
    },
    "multizone_office_simple_air": {
        "actuator_info": "You can ONLY control: Cooling Temperature Setpoint (Range: 20.0-30.0°C) for each zone.",
        "fixed_info": "Heating Setpoints are FIXED at 15°C. AHU Supply Temp is FIXED at 17°C.",
        "strategy_guide": "5-Zone VAV system. " + COMMON_STRATEGY_GUIDE,
        "reflector_guide": COMMON_REFLECTOR_GUIDE + "\n*Specific Note: VAV system. If temp < setpoint, airflow is min.*"
    },
    "multizone_office_simple_hydronic": {
        "actuator_info": "You can ONLY control: Cooling Temperature Setpoint (Range: 20.0-30.0°C) for North/South zones.",
        "fixed_info": "Heating Setpoints are FIXED at 15°C. Pump speeds are automated.",
        "strategy_guide": "Hydronic system with high inertia. Pre-cooling is effective. " + COMMON_STRATEGY_GUIDE,
        "reflector_guide": COMMON_REFLECTOR_GUIDE + "\n*Specific Note: Inertia delays effects.*"
    }
}

# --- 3. 奖励权重与归一化参数 ---
# 数据来源：用户提供的 RBC 代码
REWARD_CONFIG = {
    "bestest_air": {
        "n_zones": 1.0,
        "max_power": 1500.0,
        "weights": {'w_energy': 1.0, 'w_comfort': 20.0, 'w_smooth': 0.1},
        "scalers": {'energy': 120.351459, 'comfort': 10.0, 'smooth': 0.179875}
    },
    "multizone_office_simple_air": {
        "n_zones": 5.0,
        "max_power": 40000.0,
        "weights": {'w_energy': 1.0, 'w_comfort': 20.0, 'w_smooth': 0.2},
        "scalers": {'energy': 18.532822, 'comfort': 10.0, 'smooth': 0.193466}
    },
    "multizone_office_simple_hydronic": {
        "n_zones": 2.0,
        "max_power": 35000.0,
        "weights": {'w_energy': 1.0, 'w_comfort': 20.0, 'w_smooth': 0.1},
        "scalers": {'energy': 3, 'comfort': 0.75, 'smooth': 0.1755995}
    }
}

def get_static_controls(case_name: str) -> dict:
    return STATIC_CONTROLS.get(case_name, {})

def get_reward_config(case_name: str) -> dict:
    return REWARD_CONFIG.get(case_name, {})

def get_start_day(case_name: str) -> int:
    return START_DAY_CONFIG.get(case_name, 1)


# [MODIFIED] 实现因果注入逻辑
def get_strategic_context(case_name: str) -> dict:
    """
    获取战略上下文。
    逻辑：
    1. 获取基础上下文。
    2. 检查 ENABLE_CAUSAL_INJECTION。如果不启用，**清除所有战略指南**，只返回基础设备约束 (Pure Ablation)。
    3. 如果启用，优先尝试读取 Phase 0b 生成的 'strategic_rules.txt' (蒸馏后的高级规则)。
    4. 如果没有蒸馏规则，尝试回退到 'causal_rules.txt' (原始因果图 + 硬编码规则)。
    """
    # 1. 获取基础配置 (包含 Actuators, Fixed Info, 和 默认的 Strategy Guide)
    base_context = STRATEGIC_CONTEXT.get(case_name, {}).copy()

    # 2. 纯净消融逻辑：如果未启用因果注入，清除默认的 Strategy Guide
    if not ENABLE_CAUSAL_INJECTION:
        print(f"🛑 [Strategic Context] Causal Injection DISABLED. Clearing strategy guide for pure ablation.")
        # [CRITICAL CHANGE] 强制清空策略指南，确保无因果注入时没有任何规则提示
        base_context['strategy_guide'] = "Rely on generic internal logic."
        return base_context

    # 3. 尝试读取蒸馏后的战略规则 (优先)
    distilled_path = MAPPING_DIR / f"{case_name}_strategic_rules.txt"
    if distilled_path.exists():
        try:
            with open(distilled_path, 'r', encoding='utf-8') as f:
                distilled_rules = f.read()

            # 使用 LLM 蒸馏生成的规则替换默认的 Strategy Guide
            base_context['strategy_guide'] = f"""
            ### STRATEGIC RULES

            {distilled_rules}
            """
            print(f"✅ [Strategic Context] Loaded DISTILLED rules from {distilled_path}")
            return base_context
        except Exception as e:
            print(f"⚠️ [Strategic Context] Error reading distilled rules: {e}")

    # 4. 回退逻辑：尝试读取原始因果图 (Legacy Mode)
    causal_file = MAPPING_DIR / f"{case_name}_causal_rules.txt"
    if causal_file.exists():
        try:
            with open(causal_file, 'r', encoding='utf-8') as f:
                causal_narrative = f.read()

            print(f"✨ [Injector] Fallback: Causal Narrative Injected for {case_name}")

            # 硬编码的规则作为回退
            base_context['strategy_guide'] = f"""
            ### 2. PHYSICS-BASED CAUSAL RULES
            The following rules describe the specific cause-and-effect dynamics of THIS building.
            Use these arrows to deduce the outcome of your actions.

            {causal_narrative}

            **DERIVED PRIORITY RULES (COMBINING PHYSICS & POLICY)**:

            1. **UNOCCUPIED BASELINE (The "30°C Rule")**:
               - Condition: `current_occupancy == 0` AND `next_hour_occupancy == 0`.
               - **ACTION**: Set Setpoint to **30.0°C**.
               - **REASON**: Energy is Priority #1. High PMV is GOOD/ACCEPTABLE here.

            2. **PRE-COOLING EXCEPTION (The "Inertia Rule")**:
               - Condition: `current_occupancy == 0` BUT `next_hour_occupancy > 0`.
               - **ACTION**: Check causal chain above. 
                 - If `cooling_setpoint -> zone_temp` has `[Delayed]` or `[High Inertia]`: **MUST Pre-cool (22-23°C)**.
                 - Reason: You need to overcome the physics delay identified in the causal graph.

            3. **OCCUPIED COMFORT**:
               - Condition: `current_occupancy > 0`.
               - **ACTION**: Target PMV **[+0.35, +0.45]**.
            """

            # # Reflector 使用真值逻辑 (可选，若要完全一致性可只改 Commander)
            # base_context['reflector_guide'] = f"""
            # ### PHYSICS & LOGIC GROUND TRUTH
            # Analyze the results based on these validated causal links:
            #
            # {causal_narrative}
            #
            # **VERDICT LOGIC**:
            # - If you see an action (e.g., Lower SP) but the effect (Temp Drop) is missing, check the causal chain for [Delayed]. If [Delayed] exists, this is NOT a failure, it is physics.
            # """

        except Exception as e:
            print(f"⚠️ [Injector] Failed to read causal file: {e}. Fallback to defaults.")
    else:
        print(f"⚠️ [Injector] No causal file found at {causal_file}. Run Phase 0 first. Fallback to defaults.")

    return base_context

def get_max_occupancy(case_name: str) -> float:
    return MAX_OCCUPANCY_CONFIG.get(case_name, 10.0)
def get_normalization_config() -> dict: return NORMALIZATION_CONFIG
def get_phase_config() -> dict: return PHASE_CONFIG
def get_temperature_schedule() -> dict: return TEMPERATURE_SCHEDULE