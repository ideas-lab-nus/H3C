import json
import os
import sys
from pathlib import Path
from openai import OpenAI
from configs.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, MAPPING_DIR


# -------------------------------------------------------------------------
# Agent D: Causal Discovery Agent
# -------------------------------------------------------------------------
class CausalDiscoveryAgent:
    def __init__(self):
        self.client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    def propose_causal_graph(self, case_name, variable_list, user_feedback=None):
        """
        基于标准化变量列表，构建通用的因果叙事链。
        """
        # 将变量列表转换为易读的字符串，强调 Standard Name
        variables_desc = ""
        for v in variable_list:
            variables_desc += f"- {v['name']} ({v['type']}): {v['desc']}\n"

        system_prompt = """
        You are a Building Physics & Thermodynamics Expert.
        Your task is to construct a "Causal Narrative Chain" for a building control system.

        ### CRITICAL RULE: USE STANDARDIZED NAMES
        - You MUST use the **Standard Variable Names** provided in the list (e.g., `zone_temp`, `cooling_setpoint`, `power_meters`).
        - **NEVER** invent new names or use BMS IDs (like `zon_reaTRooAir_y`).
        - Treat variables as generic physical concepts that apply to all zones.

        ### OUTPUT FORMAT (Strict)
        Output a list of causal arrows. Each line must follow this format:
        `{Cause Variable} --[Relationship/Trend]--> {Effect Variable} [Attributes]`

        - **Relationship/Trend**: Positive Corr (Same direction), Negative Corr (Inverse direction), Threshold.
        - **Attributes**: [Immediate], [Delayed], [High Inertia], [Strong Impact], [Weak Impact].
        """

        user_prompt = f"""
        ### BUILDING CASE: {case_name}

        ### AVAILABLE STANDARDIZED VARIABLES (Nodes)
        {variables_desc}

        ### INSTRUCTION
        Generate the Causal Narrative Chain using the names above.
        Analyze:
        1. How **Setpoints** affect **Temp** and **Power**.
        2. How **Occupancy** and **Weather** affect the system.
        3. Explicitly mark **[Delayed]** effects (especially for Temp changes).
        """

        if user_feedback:
            user_prompt += f"\n\n### USER FEEDBACK (CRITIC)\nThe user reviewed your previous proposal and said:\n'{user_feedback}'\n\nPlease revise the causal chain strictly adhering to this feedback."

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"


# -------------------------------------------------------------------------
# Helper: Standardized Variable Extractor
# -------------------------------------------------------------------------
def extract_standardized_variables(mapping_data):
    """
    提取标准化变量名（Mapping Keys），去重并分类。
    不提取具体的 BMS ID。
    """
    variables = []
    seen_names = set()

    def add_var(name, v_type, desc=""):
        if name not in seen_names:
            variables.append({"name": name, "type": v_type, "desc": desc})
            seen_names.add(name)

    # 1. Global Forecasts (e.g., outdoor_temp, electricity_price)
    # 直接提取 Key
    for key in mapping_data.get('global_forecasts', {}).keys():
        add_var(key, "Disturbance/Forecast", "External environmental factor")

    # 2. Global Sensors (e.g., power_meters)
    # 直接提取 Key
    for key in mapping_data.get('global_sensors', {}).keys():
        add_var(key, "Global Sensor", "Whole building measurement")

    # 3. Zone Variables (e.g., zone_temp, cooling_setpoint)
    # 遍历所有 Zone，提取通用的 Key
    for zone_id, zone_data in mapping_data.get('zones', {}).items():
        # Sensors
        for key in zone_data.get('sensors', {}).keys():
            add_var(key, "Zone Sensor", f"Measured inside zone (applies to {zone_id} etc.)")

        # Actuators
        for key in zone_data.get('actuators', {}).keys():
            add_var(key, "Zone Actuator", f"Controllable setpoint (applies to {zone_id} etc.)")

        # Forecasts
        for key in zone_data.get('forecasts', {}).keys():
            add_var(key, "Zone Forecast", f"Local prediction (applies to {zone_id} etc.)")

    return variables


# --------------------------------------------------------------outdoor_temp --[Positive Corr]--> zone_temp (Perimeter Zones) [Delayed, Strong Impact]
# solar_irr --[Positive Corr]--> zone_temp (Perimeter Zones) [Immediate to Delayed, Strong Impact]
# occupancy --[Positive Corr]--> zone_temp (All Zones) [Immediate, Moderate Impact]
# cooling_setpoint --[Positive Corr]--> zone_temp [Delayed, High Inertia, Strong Impact]
# occupancy --[Threshold]--> cooling_setpoint [Immediate, Strategic Control]
# electricity_price --[Negative Corr]--> cooling_setpoint [Delayed, Weak to Moderate]
# cooling_setpoint --[Negative Corr]--> power_meters (Chiller & Fan) [Immediate, Strong Impact]
# outdoor_temp --[Negative Corr]--> power_meters [Immediate, Moderate Impact]
# zone_temp --[Positive Corr]--> power_meters [Immediate, Strong Impact]-----------
# Main Execution Loop (Interactive)
# -------------------------------------------------------------------------
def main():
    print("🚀 [Phase 0] Causal Discovery Module Initialized (Standardized Mode)")

    # 硬编码 Case Name 用于测试，实际使用可改为 input
    case_name = "multizone_office_simple_hydronic"
    # case_name = "bestest_air" # Uncomment to test other case

    mapping_path = MAPPING_DIR / f"{case_name}_mapping.json"
    if not mapping_path.exists():
        print(f"❌ Mapping file not found: {mapping_path}")
        return

    with open(mapping_path, 'r') as f:
        mapping_data = json.load(f)

    # 2. Extract Standardized Variables
    variables = extract_standardized_variables(mapping_data)
    print(f"📊 Extracted {len(variables)} Standardized Variables:")
    for v in variables:
        print(f"   - {v['name']} ({v['type']})")

    agent_d = CausalDiscoveryAgent()
    current_proposal = ""
    feedback = None

    # 3. Interaction Loop
    iteration = 1
    while True:
        print(f"\n--- Iteration {iteration}: Agent D generating causal narrative... ---")
        current_proposal = agent_d.propose_causal_graph(case_name, variables, feedback)

        print("\n📝 [Agent D Proposed Causal Narrative]:")
        print("=" * 60)
        print(current_proposal)
        print("=" * 60)

        # Agent E (User Proxy) Logic
        print("\n👤 [User Proxy / Critic]")
        print("Review the graph above. Check for:")
        print("1. Are names standardized? (e.g., 'zone_temp' NOT 'zon_reaTRooAir_y')")
        print("2. Is the physics logic correct?")
        user_input = input(">> Type 'Approve' to save, or enter critique to refine: ")

        if user_input.lower().strip() in ["approve", "yes", "ok"]:
            # Save
            out_path = MAPPING_DIR / f"{case_name}_causal_rules.txt"
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(current_proposal)
            print(f"\n✅ Standardized Causal Narrative Saved to: {out_path}")
            print("Configuration is ready. Ensure 'ENABLE_CAUSAL_INJECTION = True' in config.py.")
            break
        else:
            feedback = user_input
            iteration += 1
            print("🔄 Feedback received. Regenerating...")


if __name__ == "__main__":
    main()