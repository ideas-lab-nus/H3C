import asyncio
import os
from pathlib import Path
from openai import AsyncOpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, MAPPING_DIR

# [CRITICAL UPDATE] Sensitivity-Aware Distiller Prompt
# 这个 Prompt 经过了彻底重写，引入了控制论中的“增益(Gain)”和“滞后(Lag)”概念
DISTILLER_SYSTEM_PROMPT = """
You are a **Control Theory & Building Physics Expert**.
Your task is to translate a raw "Causal Graph" into a set of **Strategic Control Rules**.

### CRITICAL: PHYSICS SENSITIVITY INTERPRETATION
You must interpret the causal tags (`[Strong Impact]`, `[Delayed]`) using **Control Theory**, not just common sense.

**1. The "Strong Impact" Trap (High Gain System)**
- **Wrong Interpretation**: "It has strong impact, so I should use it aggressively."
- **CORRECT Interpretation**: "The system has **HIGH GAIN**. A small change in Setpoint causes a LARGE change in Temperature. Therefore, you must use **CAUTION** and **MICRO-ADJUSTMENTS**."
- **Rule**: If `cooling_setpoint -> zone_temp` is `[Strong Impact]`, the strategy MUST emphasize **"Precision"**, **"Small Steps"** (e.g., 0.5°C), and **"Avoid Overshoot"**.

**2. The "Delayed" Trap (Inertia)**
- **Wrong Interpretation**: "It is slow, so I must push it hard to make it move."
- **CORRECT Interpretation**: "The system has **LAG**. If you push hard now, you will overshoot later. You must start **EARLY**, but with **GENTLE INTENSITY**."
- **Rule**: If `[Delayed]` is present, mandate **"Early Pre-cooling"** but explicitly forbid "Deep Pre-cooling". Suggest **"Gentle Pre-cooling"** (e.g., lowering setpoint by only 0.5-1.0°C).

### YOUR OUTPUT GOAL
Generate a "Strategic Guide" (Markdown) containing 3 specific rules.

**1. ENERGY BASELINE (Unoccupied)**:
   - Define strategy for `occupancy == 0`.
   - If `cooling_setpoint -> power` is `[Strong Impact]`, emphasize that raising the setpoint yields MASSIVE savings.

**2. ADAPTIVE PRE-COOLING (The "Gentle" Handler)**:
   - Analyze `cooling_setpoint -> zone_temp`.
   - **MANDATORY**: If `[Strong Impact]` is found, you MUST write: "**CAUTION: High Authority System. Do NOT over-cool.** Use micro-adjustments."
   - Define pre-cooling based on Load:
     - High Load: Start earlier, but keep delta small (< 1.5°C).
     - Low Load: Minimal or no pre-cooling.

**3. COMFORT MAINTENANCE (Occupied)**:
   - If `occupancy -> zone_temp` is `[Immediate]`, recommend real-time feedback (PID).
   - Explicitly warn against "Oscillation" if the system is High Gain.

### OUTPUT FORMAT
(Return ONLY the markdown content.)

### STRATEGIC CONTROL RULES (Sensitivity-Aware)

**1. Energy Baseline (Unoccupied)**
[Your rule here...]

**2. Adaptive Pre-cooling (Anti-Overshoot)**
[Your rule here...]

**3. Comfort Maintenance (Occupied)**
[Your rule here...]
"""


class RuleDistiller:
    def __init__(self, case_name):
        self.case_name = case_name
        self.client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

        # 路径定义
        self.raw_rules_path = MAPPING_DIR / f"{case_name}_causal_rules.txt"
        self.distilled_path = MAPPING_DIR / f"{case_name}_strategic_rules.txt"

    async def distill(self):
        """
        执行知识蒸馏：Causal Graph (TXT) -> Strategic Rules (TXT)
        """
        print(f"⚗️ [Distiller] Starting SENSITIVITY-AWARE distillation for {self.case_name}...")

        # 1. 读取原始因果图
        if not self.raw_rules_path.exists():
            print(f"❌ [Distiller] Raw rules not found at {self.raw_rules_path}. Run Phase 0a first.")
            return False

        with open(self.raw_rules_path, 'r') as f:
            raw_graph = f.read()

        print(f"📖 [Distiller] Read raw causal graph ({len(raw_graph)} chars).")

        # 2. 调用 LLM 进行蒸馏
        try:
            user_input = f"### RAW CAUSAL GRAPH:\n{raw_graph}"

            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": DISTILLER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1  # 低温以保证逻辑严谨
            )

            strategic_rules = response.choices[0].message.content

            # 3. 保存蒸馏结果
            with open(self.distilled_path, 'w') as f:
                f.write(strategic_rules)

            print(f"✅ [Distiller] Strategic Rules generated and saved to: {self.distilled_path}")
            print(f"--- PREVIEW ---\n{strategic_rules}\n---")
            return True

        except Exception as e:
            print(f"❌ [Distiller] LLM Error: {e}")
            return False

    async def close(self):
        await self.client.close()


# 独立运行入口
if __name__ == "__main__":
    target_case = "multizone_office_simple_hydronic"
    distiller = RuleDistiller(target_case)
    asyncio.run(distiller.distill())