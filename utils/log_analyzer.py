import os
import json
import re
import glob
import pandas as pd
import numpy as np
import tiktoken
import asyncio
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from tqdm import tqdm

# ================= CONFIGURATION =================
# 【调试开关】
# True: 每个文件只处理前 DEBUG_LIMIT_STEPS 个小时的数据，但会进行真实的 API 调用。
# False: 处理所有数据。
DEBUG_MODE = False
DEBUG_LIMIT_STEPS = 5

# API Configuration
# OpenAI 用于 Embedding (text-embedding-3-small)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# DeepSeek 用于 Judge (deepseek-chat)
# 请确保您的 .env 中有 DEEPSEEK_API_KEY 和 DEEPSEEK_API_BASE
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")

EMBEDDING_MODEL = "text-embedding-3-small"
JUDGE_MODEL = "deepseek-chat"

OUT_DIR = "Analysis_Result"
OUT_FILE = "comprehensive_log_analysis6.csv"


# ================= HELPERS =================

class LogAnalyzer:
    def __init__(self, logs_dir="logs6"):
        self.logs_dir = logs_dir
        if not OPENAI_API_KEY or not DEEPSEEK_API_KEY:
            raise ValueError("❌ API Keys not found in environment variables.")

        # 初始化两个客户端：OpenAI用于向量，DeepSeek用于判断
        self.client_openai = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        self.client_deepseek = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Regex Patterns
        self.re_step = re.compile(r"Hour\s+(\d+)")
        self.re_zone = re.compile(r"Hour\s+\d+\s+-\s+(.+)")

        # Reflector Regex Parsers
        self.re_sp_avg = re.compile(r"Avg Setpoint:\s*([\d\.]+)")
        self.re_pmv_avg = re.compile(r"PMV Analysis.*?Average:\s*([\-\d\.]+)", re.DOTALL)
        self.re_reward = re.compile(r"Reward:\s*([\-\d\.]+)")

        # Context Regex for Regime Tagging
        self.re_occ = re.compile(r"'occupancy':\s*([\d\.]+)")
        self.re_next_occ = re.compile(r"'next_hour_occupancy':\s*([\d\.]+)")
        self.re_price_trend = re.compile(r"'price_trend':\s*([\-\d\.]+)")

        # 使用正则匹配多种“冷启动”变体
        self.re_cold_start = re.compile(
            r"(No historical RAG data available \(cold start\)\.?|Cold start: No historical RAG data available\.?)",
            re.IGNORECASE
        )

        # In-memory storage
        self.raw_data = []
        self.processed_cache = {}  # 用于断点续传的缓存

    def load_checkpoint(self):
        """从现有 CSV 加载已处理过的数据以实现断点续传"""
        path = os.path.join(OUT_DIR, OUT_FILE)
        if os.path.exists(path):
            print(f"🔄 Found existing checkpoint at {path}. Loading processed results...")
            try:
                df = pd.read_csv(path)
                # 只有标记了 hallucination_flag 的行才认为已完成 AI 分析
                df_valid = df.dropna(subset=['hallucination_flag'])
                for _, row in df_valid.iterrows():
                    key = (row['source_file'], row['zone_id'], int(row['step']))
                    self.processed_cache[key] = {
                        'semantic_jitter': row.get('semantic_jitter', np.nan),
                        'hallucination_flag': row.get('hallucination_flag'),
                        'confidence': row.get('confidence', 1.0),
                        'reason': row.get('reason', ""),
                        'Act_Diff': row.get('Act_Diff', False)
                    }
                print(f"✅ Loaded {len(self.processed_cache)} processed steps from checkpoint.")
            except Exception as e:
                print(f"⚠️ Failed to load checkpoint: {e}. Starting fresh.")

    def save_to_csv(self):
        """将当前内存中的 raw_data 实时写入 CSV"""
        if not self.raw_data: return
        os.makedirs(OUT_DIR, exist_ok=True)
        path = os.path.join(OUT_DIR, OUT_FILE)

        df = pd.DataFrame(self.raw_data)
        df = df.sort_values(by=['source_file', 'zone_id', 'step'])

        # 计算 Action Delta
        if 'sp_avg' in df.columns:
            df['sp_prev'] = df.groupby(['source_file', 'zone_id'])['sp_avg'].shift(1)
            df['action_delta'] = (df['sp_avg'] - df['sp_prev']).abs()
            df = df.drop(columns=['sp_prev'])

        df.to_csv(path, index=False)

    def extract_metadata(self, filepath: str) -> dict:
        parts = filepath.replace("\\", "/").split("/")
        try:
            filename = parts[-1]
            case = parts[-2]
            group = parts[-3]
        except IndexError:
            group, case, filename = "Unknown", "Unknown", filepath

        sw_match = re.search(r"_SW(\d+)", filename)
        sw_window = int(sw_match.group(1)) if sw_match else 3
        return {"source_file": filename, "group": group, "case_name": case, "sw_window": sw_window}

    def get_regime_tag(self, occupancy: float, next_occ: float, price_trend: float) -> str:
        if occupancy == 0:
            return "Unoccupied_Steady" if next_occ == 0 else "Transition_PreCool"
        return "Occupied_PriceChange" if abs(price_trend) > 0.01 else "Occupied_Steady"

    def parse_jsonl(self, filepath: str):
        meta = self.extract_metadata(filepath)
        print(f"📂 Parsing: {meta['source_file']}")
        steps_data = {}

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except:
                    continue

                step_info = entry.get("step_info", "")
                agent = entry.get("agent")

                h_match = self.re_step.search(step_info)
                if not h_match: continue
                hour = int(h_match.group(1))

                if DEBUG_MODE and hour > DEBUG_LIMIT_STEPS:
                    continue

                z_match = self.re_zone.search(step_info)
                zone_id_ref = z_match.group(1) if z_match else "zone_0"

                if hour not in steps_data: steps_data[hour] = {}

                if agent == "Commander":
                    try:
                        output_json = json.loads(entry.get("output", "{}"))
                    except:
                        output_json = {}

                    for z_key, z_data in output_json.items():
                        if z_key not in steps_data[hour]: steps_data[hour][z_key] = {}

                        # 清洗推理逻辑中的无效冷启动语句
                        reasoning_raw = z_data.get('reasoning', "")
                        reasoning_clean = self.re_cold_start.sub("", reasoning_raw).strip()

                        steps_data[hour][z_key]['commander_input_tokens'] = len(
                            self.tokenizer.encode(entry.get("input", "")))
                        steps_data[hour][z_key]['commander_reasoning'] = reasoning_clean
                        steps_data[hour][z_key]['commander_strategy'] = z_data.get('strategy', "")

                elif agent == "Reflector":
                    if zone_id_ref not in steps_data[hour]: steps_data[hour][zone_id_ref] = {}
                    blob = steps_data[hour][zone_id_ref]
                    ref_input = entry.get("input", "")

                    occ_m = self.re_occ.search(ref_input)
                    next_occ_m = self.re_next_occ.search(ref_input)
                    pt_m = self.re_price_trend.search(ref_input)
                    occ = float(occ_m.group(1)) if occ_m else 0.0
                    next_occ = float(next_occ_m.group(1)) if next_occ_m else 0.0
                    pt = float(pt_m.group(1)) if pt_m else 0.0

                    blob['regime'] = self.get_regime_tag(occ, next_occ, pt)

                    rw_m = self.re_reward.search(ref_input)
                    blob['reward'] = float(rw_m.group(1)) if rw_m else np.nan

                    sp_avg_m = self.re_sp_avg.search(ref_input)
                    blob['sp_avg'] = float(sp_avg_m.group(1)) if sp_avg_m else np.nan
                    pmv_avg_m = self.re_pmv_avg.search(ref_input)
                    blob['pmv_avg'] = float(pmv_avg_m.group(1)) if pmv_avg_m else np.nan

        for h in sorted(steps_data.keys()):
            for z, data in steps_data[h].items():
                if data:
                    self.raw_data.append({**meta, "step": h, "zone_id": z, **data})

    def check_action_difference(self, strategy: str, action_sp: float, tolerance: float = 1.5) -> bool:
        if not strategy or pd.isna(action_sp):
            return False
        temps_in_strategy = re.findall(r"(\d+\.?\d*)\s*(?:°|deg|degrees)?\s*C", strategy, re.IGNORECASE)
        if not temps_in_strategy:
            return False
        for t_str in temps_in_strategy:
            try:
                t_val = float(t_str)
                if abs(t_val - action_sp) <= tolerance:
                    return False
            except ValueError:
                continue
        return True

    async def compute_ai_metrics_batch(self):
        print(f"🧠 Starting AI Audit (Serial + Checkpoint + DeepSeek)...")
        df = pd.DataFrame(self.raw_data)
        if df.empty: return

        grouped = df.groupby(['source_file', 'zone_id'])

        async def process_row(idx, row, prev_vector, prev_regime):
            reasoning = row.get('commander_reasoning', "")
            strategy = row.get('commander_strategy', "")
            regime = row.get('regime', "Other")
            sp_avg = row.get('sp_avg', np.nan)
            pmv_avg = row.get('pmv_avg', np.nan)

            key = (row['source_file'], row['zone_id'], int(row['step']))

            # --- 检查断点续传缓存 ---
            if key in self.processed_cache:
                cached = self.processed_cache[key]
                # Embedding 仍需计算以维持下一行的 Jitter 计算链
                curr_vec = None
                if reasoning and len(reasoning) > 5:
                    try:
                        resp = await self.client_openai.embeddings.create(input=reasoning, model=EMBEDDING_MODEL)
                        curr_vec = resp.data[0].embedding
                    except:
                        pass
                return idx, cached['semantic_jitter'], cached['hallucination_flag'], cached['confidence'], cached[
                    'reason'], cached['Act_Diff'], curr_vec

            # --- 正常分析逻辑 ---
            act_diff = self.check_action_difference(strategy, sp_avg)
            jitter, curr_vector = np.nan, None

            # 1. Semantic Jitter (OpenAI Embedding)
            if reasoning and isinstance(reasoning, str) and len(reasoning) > 5:
                try:
                    resp = await self.client_openai.embeddings.create(input=reasoning, model=EMBEDDING_MODEL)
                    curr_vector = resp.data[0].embedding
                    if prev_vector is not None and regime == prev_regime:
                        sim = np.dot(prev_vector, curr_vector)
                        jitter = 1.0 - sim
                except Exception as e:
                    print(f"⚠️ Embed Error (Step {key[2]}): {e}")

            # 2. Physical Hallucination Judge (DeepSeek Chat)
            is_hallucination = False
            confidence = 1.0
            reason = ""

            if reasoning and isinstance(reasoning, str) and len(reasoning) > 5:
                try:
                    prompt = f"""
                    Role: AI Logic Auditor for HVAC Control Agent.
                    Context: Building is currently in '{regime}' state. Current PMV is {pmv_avg}.

                    Agent's Reasoning: "{reasoning}"
                    Agent's Target Strategy: "{strategy}"

                    Task: Identify "Cognitive Hallucinations" (Fundamental logical failures).

                    STRICT AUDIT GUIDELINES:
                    1. IGNORE MINOR NUMERICAL DIFFERENCES: 
                       - Do NOT flag hallucinations for small gaps between Reasoning and Strategy temperatures (e.g., 29.6C vs 30C is acceptable rounding).
                       - Do NOT flag small discrepancies in sensor data (e.g., PMV 0.96 vs 0.88 is normal trend variation).
                       - Numerical precision is NOT your job (handled by external Python scripts).

                    2. FOCUS ON DIRECTIONAL & CATEGORICAL ERRORS:
                       - Context Mismatch: Claiming "Occupied comfort needed" when state is '{regime}' (Unoccupied).
                       - Internal Contradiction: Reasoning says "Heat up to save energy" but Strategy says "Maintain 21C" (Categorical reversal).
                       - Inverse Physics: Claiming that raising the setpoint increases cooling intensity.
                       - Fact Hallucination: Fabricating events that contradict the basic status (e.g., claiming high price when price trend is stable).
                       - Claiming mid Setpoint (e.g., 24°C) is an "Energy Saving" strategy for an Unoccupied zone is a Logical Hallucination. A higher setpoint (e.g., 30°C) is more energy-efficient, whereas a lower setpoint (e.g., 24°C) results in significantly higher energy consumption.

                    Goal: Only flag the agent if it is "thinking illogically" or fundamentally misunderstanding the environment. Minor descriptive variances are NOT hallucinations.

                    Return JSON:
                    {{
                      "is_hallucination": true/false,
                      "confidence": 0.0-1.0,
                      "reason": "Explain the specific LOGICAL contradiction or categorical error. If not a hallucination, explain why the minor numerical variation is acceptable."
                    }}
                    """

                    chat_resp = await self.client_deepseek.chat.completions.create(
                        model=JUDGE_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                        temperature=0.0
                    )
                    res = json.loads(chat_resp.choices[0].message.content)
                    is_hallucination = res.get('is_hallucination', False)
                    confidence = res.get('confidence', 1.0)
                    reason = res.get('reason', "")
                except Exception as e:
                    print(f"⚠️ DeepSeek Judge Error (Step {key[2]}): {e}")

            return idx, jitter, is_hallucination, confidence, reason, act_diff, curr_vector

        # 串行处理保证逻辑稳定，每处理完一个区域保存一次
        for name, group in tqdm(grouped, desc="Processing Zones"):
            prev_vec, prev_reg = None, None
            for idx, row in group.iterrows():
                pidx, jitter, is_hall, conf, res_text, act_diff, curr_vec = await process_row(idx, row, prev_vec,
                                                                                              prev_reg)

                self.raw_data[pidx].update({
                    'semantic_jitter': jitter,
                    'hallucination_flag': is_hall,
                    'confidence': conf,
                    'reason': res_text,
                    'Act_Diff': act_diff
                })
                prev_vec, prev_reg = curr_vec, row.get('regime', "Other")

            # 每个区域保存一次进度，实现断点续传
            self.save_to_csv()

    def run(self):
        files = glob.glob(os.path.join(self.logs_dir, "**", "*.jsonl"), recursive=True)
        print(f"🔍 Found {len(files)} log files in {self.logs_dir}")
        if not files:
            print("❌ No files found.");
            return

        # 1. 尝试加载断点
        self.load_checkpoint()

        # 2. 解析文件
        for f in files:
            self.parse_jsonl(f)

        # 3. 计算指标
        if self.raw_data:
            try:
                asyncio.run(self.compute_ai_metrics_batch())
            except KeyboardInterrupt:
                print("\n⚠️ Interrupted. Progress has been saved.")

        # 4. 最终保存
        self.save_to_csv()
        print(f"✅ Analysis saved to {os.path.join(OUT_DIR, OUT_FILE)}")


if __name__ == "__main__":
    analyzer = LogAnalyzer()
    analyzer.run()