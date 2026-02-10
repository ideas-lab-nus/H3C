from openai import AsyncOpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from agents.prompts import CODER_SYSTEM_PROMPT
import re


class AgentZoneCoder:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    async def close(self):
        await self.client.close()

    async def generate_code(self, zone_id, directive, mapping_schema, actuator_info, fixed_info,
                            occupancy_profile=None):
        """
        [Async] 生成代码
        Args:
            occupancy_profile: [Optional] List of floats, e.g., [1.0, 1.0, 0.0, 0.0].
                               Representing occupancy forecast for the 4 steps of the current hour.
        """
        # 提取可用变量
        available_vars = []
        if 'sensors' in mapping_schema:
            available_vars.extend([f"obs['{k}']" for k in mapping_schema['sensors'].keys()])
        if 'forecasts' in mapping_schema:
            available_vars.extend([f"obs['{k}']" for k in mapping_schema['forecasts'].keys()])
        available_vars.extend([
            "obs['obs_sin_time']",
            "obs['obs_outdoor_temp_0']",
            "obs['last_pmv']",
            "obs['last_setpoint']",
            "obs['last_occupancy']",  # Critical for edge detection
            # [UPDATED] Friendly Aliases
            "obs['current_price'] (Alias for obs_electricity_price_0)",
            "obs['current_occupancy'] (Alias for obs_Occ_0)",
            "obs['next_hour_occupancy']",
            "obs['next_hour_price']"
        ])

        # 构造 Profile 上下文
        profile_context = "Not Available"
        if occupancy_profile:
            profile_context = str(occupancy_profile)
            profile_note = f"The list {profile_context} shows the forecasted occupancy for the 4 steps (15-min intervals) of this hour."
            if sum(occupancy_profile) > 0 and 0 in occupancy_profile:
                profile_note += "\n   **ATTENTION**: This is a MIXED OCCUPANCY hour. Your code logic MUST handle the transition (Occupied <-> Unoccupied) in real-time!"
        else:
            profile_note = "Assume consistent occupancy based on `obs['occupancy']`."

        user_input = f"""
        ### ZONE ID: {zone_id}

        ### INPUT DATA
        - **Occupancy Profile (15-min)**: {occupancy_profile}
        - **Commander Strategy**: "{directive.get('strategy', 'Standard Control')}"
        *Your Goal: Translate this Strategy into Python code, strictly following the logic rules below.*

        ### CONTROL AUTHORITY
        {actuator_info}
        *Your return dictionary MUST ONLY contain keys related to this authority.*

        ### CRITICAL EXECUTION RULES (Strictly Follow)
        1. **SAFETY INTERLOCK**: 
           - IF (`current_occupancy > 0` AND `last_occupancy > 0` AND `abs(last_pmv) > 0.5`):
           - **ACTION**: FORCE Reset setpoint to **25.0°C** immediately. (Overrides all other logic).

        2. **ANCHORING (Prevent Runaway)**: 
           - Transition (Unoccupied -> Occupied): FORCE base setpoint = **25.0°C**. Discard `last_setpoint`.
           - Steady State: Use `obs['last_setpoint']` as your base.
           - ❌ NEVER use `zone_temp` as a base.

        3. **UNOCCUPIED BASELINE**:
           - IF `current_occupancy == 0` AND `next_hour_occupancy == 0`:
           - **ACTION**: Set **30.0°C**. (Energy Priority).

        4. **PRE-COOLING LOGIC (The "Inertia" Handler)**:
           - **Scenario A (Comfort Prep - HIGH PRIORITY)**: 
             - IF `current_occupancy == 0` BUT `next_hour_occupancy > 0`:
             - **ACTION**: You **MUST** Pre-cool. 
             - **OVERRIDE**: IGNORE electricity price. Comfort/Physics takes precedence here.
           - **Scenario B (Economic Only - LOW PRIORITY)**: 
             - IF `current_occupancy == 0` AND `next_hour_occupancy == 0`:
             - **ACTION**: Only pre-cool IF `current_price < next_hour_price`. Otherwise, stay at 30.0°C.


        ### PYTHON SYNTAX ENFORCEMENT (CRITICAL)
        1. **Empty Blocks**: Python does NOT allow empty blocks with only comments.
        2. If an `if/else` branch requires no action (e.g., "maintain current setpoint"), you **MUST** write `pass`.
        - ❌ **BAD**:
          ```python
          else:
              # Do nothing
          ```
        - ✅ **GOOD**:
          ```python
          else:
              # Do nothing
              pass
          ```

        ### USE FEEDBACK (CLOSED-LOOP CONTROL)
        - You have access to `obs['last_pmv']`.
        - **Target**: PMV [+0.3, +0.4].
        - **Action**: If PMV < 0.3, RAISE setpoint. If PMV > 0.4, LOWER setpoint.

        ### AVAILABLE VARIABLES (Use exact keys)
        {', '.join(available_vars)}
        """

        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": CODER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.2
            )
            raw_text = response.choices[0].message.content

            # 提取代码
            code_match = re.search(r"```python\n(.*?)```", raw_text, re.DOTALL)
            code = code_match.group(1) if code_match else raw_text

            return code, user_input, raw_text
        except Exception as e:
            print(f"❌ [Coder-{zone_id}] Error: {e}")
            return "def run_control(obs): return {'cooling_setpoint': 25.0}", user_input, str(e)