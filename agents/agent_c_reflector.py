import json
from openai import AsyncOpenAI
from configs.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from agents.prompts import REFLECTOR_SYSTEM_PROMPT


class AgentReflector:
    def __init__(self, memory_manager):
        self.client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        self.memory = memory_manager

    async def close(self):
        await self.client.close()

    async def reflect_and_store(self, zone_id, time_info, context_data, action_summary, result_metrics, reflection_guide="", evaluation_label="UNKNOWN"):
        """
        [Async] 分析 -> 生成 Insight -> 存入 Memory
        Args:
            evaluation_label: 由 Python 逻辑计算出的硬性评价 (POSITIVE/NEGATIVE)
        """

        avg_pmv = result_metrics.get('avg_pmv', 0.0)
        pmv_std = result_metrics.get('pmv_std', 0.0)
        pmv_max = result_metrics.get('pmv_max', 0.0)
        pmv_range = f"[{result_metrics.get('pmv_min', 0.0):.2f}, {pmv_max:.2f}]"

        # [NEW] Peak Warning
        peak_warning = ""
        if pmv_max > 0.5:
            peak_warning = f"⚠️ WARNING: PEAK OVERHEATING DETECTED (Max PMV {pmv_max:.2f}). Even if average is OK, this is a failure."

        user_input = f"""
        ### Context
        Time: {time_info}
        Environment: {context_data}

        ### Action
        Strategy Executed: {action_summary}
        
        ### ANALYSIS GUIDELINES (CRITICAL PHYSICS RULES)
        {reflection_guide}

        ### Result
        Reward: {result_metrics['reward']:.2f}
        Energy Cost: {result_metrics['cost']:.2f}
        Comfort Penalty: {result_metrics['penalty']:.2f}
        Avg Temp: {result_metrics['avg_temp']:.2f}
        
        ### PMV Analysis (Comfort Dynamics)
        - Average: {avg_pmv:.2f} 
        - Stability (Std Dev): {pmv_std:.2f}
        - Range (Min/Max): {pmv_range}
        {peak_warning}
        
        ### SYSTEM VERDICT (GROUND TRUTH)
        **Evaluation**: {evaluation_label}
        *(You must align your analysis with this verdict. Explain WHY it is {evaluation_label} based on the physics rules below.)*
        """

        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": REFLECTOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            insight = json.loads(response.choices[0].message.content)

            # [FIX] 提取并存储所有 7D 特征
            weather = context_data.get('weather', {})
            context_state = {
                "outdoor_temp": weather.get('outdoor_temp', 0.0),
                "occupancy": context_data.get('occupancy', 0),
                "price": weather.get('price', 0.0),
                "avg_pmv": avg_pmv,
                "max_pmv": pmv_max,  # [CRITICAL ADDITION]
                # Trend Features
                "temp_trend": weather.get('temp_trend', 0.0),
                "price_trend": weather.get('price_trend', 0.0),
                "occ_trend": context_data.get('occ_trend', 0.0)
            }

            metadata = {
                "zone_id": zone_id,
                "reward": result_metrics['reward'],
                "timestamp": context_data.get('timestamp', 0),
                "scope": "local",
                "strategy": insight.get("strategy_type", "unknown"),
                "verdict": evaluation_label
            }

            final_text = f"Evaluation: {evaluation_label}. {insight['insight_text']}"
            self.memory.add_memory(final_text, metadata, context_state)

            return f"Reflected {zone_id} ({evaluation_label})", user_input, response.choices[0].message.content

        except Exception as e:
            print(f"❌ [Reflector] Error: {e}")
            return f"Error {zone_id}", user_input, str(e)