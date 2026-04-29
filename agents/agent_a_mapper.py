import json
import os
from typing import List, Optional, Dict
from openai import OpenAI
from configs.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DOCS_DIR, MAPPING_DIR


class SemanticMapper:
    """
    Agent A: 语义映射器 (Master Systems Integrator)

    角色设定：一个专业的智能建筑系统集成商。
    任务：阅读物理建筑的技术文档（BMS点位表/说明书），根据【控制需求】和【观测需求】，
          提取对应的物理点位名称（Point IDs）。

    特点：
    - 不依赖仿真术语，模拟真实世界的集成过程。
    - 采用“正向需求注入”：明确告诉 Agent 我们需要哪些数据。
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )

        # --- 1. 定义标准观测需求 (Standard Observation Requirements) ---
        # 这些是任何控制算法运行所必须的基础数据
        self.standard_observations = [
            "Zone Air Temperature",
            "Zone Occupancy Forecast/Schedule",
            "Outdoor Air Temperature Forecast",
            "Global Solar Irradiation Forecast",
            "Electricity Price Forecast",
            "Total Building Power Consumption"
        ]

        # --- 2. 定义默认控制目标 (Default Control Targets) ---
        # 这是我们当前算法想要控制的物理量。如果以后要控制风扇，加在这里即可。
        self.default_target_actuators = [
            "Cooling Temperature Setpoint"
        ]

    def _read_document(self, case_name: str) -> str:
        """读取建筑说明书/点位表"""
        file_path = DOCS_DIR / f"{case_name}.md"
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def generate_mapping(self, case_name: str,
                         custom_actuators: Optional[List[str]] = None,
                         custom_observations: Optional[List[str]] = None) -> dict:
        """
        核心方法：执行映射任务
        """
        print(f"🔄 [Agent A] Integrating Building System: {case_name}...")

        # 1. 准备上下文数据
        doc_content = self._read_document(case_name)

        # 2. 组装“需求清单” (Requirements List)
        # 这是正向提示的核心：告诉 LLM 我们“要什么”
        req_obs = custom_observations if custom_observations else self.standard_observations
        req_acts = custom_actuators if custom_actuators else self.default_target_actuators

        req_obs_str = "\n".join([f"   - {item}" for item in req_obs])
        req_acts_str = "\n".join([f"   - {item}" for item in req_acts])

        # 3. 定义通用的 Schema (意图驱动的结构)
        json_structure_hint = {
            "case_name": case_name,
            "zones": {
                "<Zone_ID_String>": {
                    "description": "Zone description (e.g., North Office)",
                    "sensors": {
                        "zone_temp": "Variable name for Zone Temperature"
                    },
                    "actuators": {
                        "cooling_setpoint": "Variable name for Cooling Setpoint"
                        # LLM should only fill this if 'Cooling Setpoint' is in requirements
                    },
                    "forecasts": {
                        "occupancy": "Variable name for Occupancy Forecast"
                    }
                }
            },
            "global_sensors": {
                "power_meters": ["List of ALL Power variables (Watts) to be summed up for Total Energy"]
            },
            "global_forecasts": {
                "outdoor_temp": "Variable name for Outdoor Temp",
                "solar_irr": "Variable name for Solar Irradiation",
                "electricity_price": "Variable name for Price"
            }
        }

        # 4. 构建 System Prompt (建立专家人设 - 现实世界语境)
        system_prompt = (
            "You are a Master Systems Integrator for Smart Buildings. "
            "Your goal is to configure a Unified Control Layer by mapping specific BMS (Building Management System) "
            "points from technical documentation to a standardized internal schema.\n"
            "You focus ONLY on extracting the data points requested by the user."
        )

        # 5. 构建 User Prompt (正向、物理导向)
        user_prompt = f"""
        ### SCENARIO
        We are deploying an advanced AI controller for a physical building. 
        We have received the technical documentation (Points List) below.
        We need you to identify the specific **Variable Names** (Point IDs) that correspond to our Control & Observation requirements.

        ### 1. OBSERVATION REQUIREMENTS (Sensors & Forecasts)
        Please find the variable names for:
        {req_obs_str}

        *Crucial Requirement for Total Power*: Find ALL sensors measuring electrical or thermal power (Watts). 
        (e.g., Chillers, Heat Pumps, Fans, Pumps). We will sum them up to calculate Total Energy.

        ### 2. CONTROL REQUIREMENTS (Actuators)
        Please find the variable names for:
        {req_acts_str}

        ### 3. NAMING CONVENTIONS (Heuristics)
        The documentation follows this naming standard:
        - **Inputs/Setpoints** (Actuators) typically end with `_u`.
        - **Measurements/Sensors** typically end with `_y`.
        - **Forecasts** are typically distinct strings (e.g., array accessors or specific keywords).

        ### 4. BUILDING DOCUMENTATION
        ```markdown
        {doc_content}
        ```

        ### 5. OUTPUT FORMAT
        Produce a JSON object that strictly matches this schema:
        {json.dumps(json_structure_hint, indent=2)}
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0  # 保持零温度以确保提取精确
            )

            mapping = json.loads(response.choices[0].message.content)

            # 确保 case_name 字段存在
            mapping["case_name"] = case_name

            # 保存映射文件
            out_path = MAPPING_DIR / f"{case_name}_mapping.json"
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, indent=2)

            print(f"✅ [Agent A] Configuration saved: {out_path}")
            return mapping

        except Exception as e:
            print(f"❌ [Agent A] Integration failed for {case_name}: {e}")
            raise e


if __name__ == "__main__":
    # 单元测试：模拟集成过程
    mapper = SemanticMapper()
    # mapper.generate_mapping("bestest_air")