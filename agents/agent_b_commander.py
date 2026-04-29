import json
from openai import AsyncOpenAI
from configs.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from agents.prompts import COMMANDER_SYSTEM_PROMPT


class AgentCommander:
    def __init__(self, memory_manager):
        self.client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        self.memory = memory_manager
    async def close(self):
        await self.client.close()

    async def generate_directives(self, time_info, global_forecast, zone_states, strategy_context,
                                  history_context=None, max_occupancy=10.0, future_outlook=None,
                                  temperature=0.3, phase_note="", enable_rag=True):
        """
        [Async] 生成指令 (支持趋势向量与探索率控制)
        """
        # 1. 检索 RAG
        rag_text_block = ""

        if enable_rag:
            rag_context = {}
            for z_id, state in zone_states.items():
                query = f"Zone: {z_id}, Weather: {global_forecast}, Occupancy: {state.get('occupancy_forecast', 'unknown')}"

                last_pmv = state.get('last_hour_pmv', 0.0)
                if isinstance(last_pmv, str): last_pmv = 0.0

                # [NEW] 构造 7D 上下文传给 Memory Manager
                current_phys_context = {
                    "outdoor_temp": global_forecast.get('outdoor_temp', 20.0),
                    "occupancy": state.get('occupancy_forecast', 0),
                    "price": global_forecast.get('price', 0.0),
                    "avg_pmv": last_pmv,
                    # Trend Features
                    "temp_trend": global_forecast.get('temp_trend', 0.0),
                    "price_trend": global_forecast.get('price_trend', 0.0),
                    "occ_trend": state.get('occ_trend', 0.0),
                    "clo": state.get('clo', 0.5)
                }

                retrieval = self.memory.retrieve_contrastive(
                    query,
                    zone_id=z_id,
                    current_context=current_phys_context,
                    max_occupancy=max_occupancy,
                    distance_threshold=1.5
                )
                rag_context[z_id] = retrieval

            # 2. 构造 RAG 文本块
            rag_text_block = ""
            for z_id, res in rag_context.items():
                if not res['positive'] and not res['negative']:
                    rag_text_block += f"Zone {z_id}: No historically matched context found.\n\n"
                else:
                    pos = "\n".join([f"  + Good: {d}" for d in res['positive']])
                    neg = "\n".join([f"  - Bad: {d}" for d in res['negative']])
                    rag_text_block += f"Zone {z_id}:\n{pos}\n{neg}\n\n"
        else:
            # [ABLATION MODE]
            rag_text_block = "NO HISTORICAL MEMORY AVAILABLE (ABLATION MODE). Rely on generic strategy logic."

        # 3. 构造 Feedback 文本块 (宏观闭环)
        # [MODIFIED] 2. 构造历史趋势表 (History Table)
        # 将原本简单的 last_reflections 替换为结构化表格
        history_text_block = ""
        if history_context:
            for z_id, buffer in history_context.items():
                if not buffer:
                    history_text_block += f"Zone {z_id}: No history yet.\n"
                    continue

                history_text_block += f"\n**Zone {z_id} Recent Trends (Last {len(buffer)} Hours):**\n"
                history_text_block += "| Hour | Avg SP | Avg PMV | Reward | Verdict | Insight (Truncated) |\n"
                history_text_block += "|------|--------|---------|--------|---------|---------------------|\n"

                # 遍历 buffer (deque)
                for frame in buffer:
                    # 截断 Insight 以防止 Prompt 过长
                    insight_full = frame.get('insight', 'No info')
                    insight_short = (insight_full[:100] + '..') if len(insight_full) > 100 else insight_full

                    history_text_block += (
                        f"| {frame['hour']} | {frame['avg_setpoint']:.1f}C | "
                        f"{frame['avg_pmv']:.2f} | {frame['reward']:.1f} | "
                        f"{frame['verdict']} | {insight_short} |\n"
                    )
                history_text_block += "\n"
        else:
            history_text_block = "No recent history available (First Hour)."

        # 4. Outlook Text
        outlook_text_block = ""
        if future_outlook:
            outlook_text_block += "Offset | Price | OutTemp | Zone Max Occupancy\n"
            outlook_text_block += "-------|-------|---------|-------------------\n"
            for item in future_outlook:
                occ_summary = ", ".join([f"{z}:{v:.0f}" for z, v in item['zone_max_occupancy'].items() if v > 0])
                if not occ_summary: occ_summary = "All 0"
                outlook_text_block += f" +{item['offset_hour']}h  | {item['avg_price']:.3f} | {item['avg_outdoor_temp']:.1f}C   | {occ_summary}\n"

        # 5. Prompt
        zone_status_str = json.dumps(zone_states, indent=2)

        user_input = f"""
                ### PHASE: {phase_note}
                
                ### 1. SYSTEM CONSTRAINTS & AUTHORITY
                - **Actuators**: {strategy_context.get('actuator_info')}
                - **Fixed Settings**: {strategy_context.get('fixed_info')}

                ### 2. EXPERT STRATEGY GUIDELINES
                {strategy_context.get('strategy_guide')}

                ### 3. RECENT HISTORY & TRENDS (CRITICAL: SLIDING WINDOW)
                {history_text_block}
                *INSTRUCTION: Analyze the TREND (Change over time).*
                - If PMV is oscillating (e.g., 0.6 -> -0.4 -> 0.5), your actions are too aggressive. Stabilize the setpoint.

                ### 4. CURRENT STATUS & FUTURE OUTLOOK
                - **Time**: {time_info}
                - **Global Forecast**: {global_forecast}

                **FUTURE HORIZON (Plan Ahead!)**:
                {outlook_text_block}
                *Check occupancy_profile FIRST! If ANY value in the list is > 0, the room is OCCUPIED. Do NOT assume occupancy is 0 just because the previous hour was 0.*
                *(Tip: If Occupancy > 0 in +1h, start PRE-COOLING now!)*
                *PHYSICS TRUTH: Pre-cooling MUST involve LOWERING the setpoint. Never propose raising the setpoint as a pre-cooling action.*

                - **Zone Statuses**: 
                {zone_status_str}
                *(CRITICAL: Pay attention to "semantic_status". If it says "People arriving", you MUST pre-cool immediately, even if current_occupancy is 0.)*
                """

        # 4. 异步调用
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": COMMANDER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                response_format={"type": "json_object"},
                temperature=temperature  # [NEW] Dynamic Temp
            )
            directives = json.loads(response.choices[0].message.content)
            return directives, user_input, response.choices[0].message.content
        except Exception as e:
            print(f"❌ [Commander] Error: {e}")
            fallback = {z: {"strategy": "fallback", "reasoning": "error", "reference_context": "maintain 25C"} for z in
                        zone_states}
            return fallback, user_input, str(e)