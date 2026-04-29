import asyncio
import json
import time
import sys
import csv
import os
import numpy as np
import traceback
from pathlib import Path
from datetime import datetime
from collections import deque

# Imports
from core.boptest_client import BoptestClient
from core.observation_builder import ObservationBuilder
from core.reward_calculator import RewardCalculator
from core.memory_manager import MemoryManager

from agents.agent_b_commander import AgentCommander
from agents.agent_b_coder import AgentZoneCoder
from agents.agent_c_reflector import AgentReflector

from configs.config import MAPPING_DIR, CONTROL_STEP_SIZE, FORECAST_HORIZON_STEPS, COMMANDER_LOOKAHEAD_HOURS, ROOT_DIR, DEFAULT_ENABLE_RAG
from configs import static_config

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

MAX_CONCURRENCY = 50
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
# [MODIFIED] 2. 定义滑动窗口大小 (3小时最适宜观察趋势)
HISTORY_WINDOW_SIZE = 1

def unsafe_exec_code(code_str, local_obs, zone_id="unknown", default_sp=25.0):
    local_scope = {}
    try:
        exec(code_str, {}, local_scope)
        if 'run_control' not in local_scope:
            return {"cooling_setpoint": 25.0}
        result = local_scope['run_control'](local_obs)
        if not isinstance(result, dict) or 'cooling_setpoint' not in result:
            return {"cooling_setpoint": 25.0}
        return result
    except Exception as e:
        # [关键] 这里利用 zone_id 打印具体的报错信息，方便您排查是哪个房间的代码写错了
        print(f"❌ [Coder Error] Zone {zone_id} Execution Failed. Error: {e}")
        # traceback.print_exc() # 如果想看详细堆栈可以取消注释
        return {"cooling_setpoint": default_sp}


# Logger classes omitted for brevity (same as before)
class InteractionLogger:
    def __init__(self, case_name, phase, enable_rag=True):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "_WITH_RAG" if enable_rag else "_NO_RAG"
        self.file_path = LOG_DIR / f"agent_trace_{case_name}_{phase}{suffix}_{timestamp}.jsonl"
        self.file = open(self.file_path, 'w', encoding='utf-8')

    def log(self, step_info, agent_name, input_prompt, output_response):
        record = {"timestamp": time.time(), "step_info": step_info, "agent": agent_name, "input": input_prompt,
                  "output": output_response}
        self.file.write(json.dumps(record) + "\n")
        self.file.flush()

    def close(self): self.file.close()


# [已修正] ExperimentLogger 现在支持 enable_rag 参数，并将其反映在文件名中
class ExperimentLogger:
    def __init__(self, case_name, phase, enable_rag=True):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "_WITH_RAG" if enable_rag else "_NO_RAG"

        # 文件名加入 suffix，方便后续区分消融实验数据
        self.step_file = LOG_DIR / f"performance_{case_name}_{phase}{suffix}_{timestamp}.csv"
        self.hour_file = LOG_DIR / f"evolution_{case_name}_{phase}{suffix}_{timestamp}.csv"

        with open(self.step_file, 'w', newline='') as f:
            csv.writer(f).writerow(
                ['Time', 'Hour', 'Step', 'Total_Power', 'Total_Cost', 'Global_Reward', 'Zone_Temps', 'Zone_Setpoints',
                 'Zone_PMVs', 'Zone_Occs'])
        with open(self.hour_file, 'w', newline='') as f:
            csv.writer(f).writerow(['Hour', 'Global_Reward', 'Cost', 'Avg_Temp', 'Directives', 'Reflections'])

    def log_step(self, time_now, hour, step, p_total, cost, reward, temps, setpoints, pmvs, occs):
        with open(self.step_file, 'a', newline='') as f:
            csv.writer(f).writerow([time_now, hour, step, f"{p_total:.2f}", f"{cost:.4f}", f"{reward:.4f}",
                                    str([round(x, 2) for x in temps]), str([round(x, 2) for x in setpoints]),
                                    str([round(x, 2) for x in pmvs]), str([int(x) for x in occs])])

    def log_hour(self, hour, reward, cost, avg_temp, directives, reflections):
        with open(self.hour_file, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([hour, f"{reward:.2f}", f"{cost:.2f}", f"{avg_temp:.2f}", json.dumps(directives),
                                    json.dumps(reflections)])


def determine_evaluation_label(avg_pmv, is_occupied, max_pmv=0.0):
    if is_occupied:
        # [NEW] Peak Overheating Check
        if max_pmv > 0.5: return "NEGATIVE (Peak Overheating - Failed)"
        if avg_pmv > 0.5:
            return "NEGATIVE (Overheating)"
        elif 0.35 <= avg_pmv <= 0.5:
            return "POSITIVE (Optimal)"
        elif -0.5 <= avg_pmv < 0.35:
            return "NEUTRAL (Comfortable but Low Efficiency)"
        else:
            return "NEGATIVE (Overcooling)"
    else:
        if avg_pmv > 0.5:
            return "POSITIVE (Energy Saving)"
        elif 0.0 <= avg_pmv <= 0.5:
            return "NEUTRAL (Inefficient Comfort)"
        else:
            return "NEGATIVE (Wasteful Cooling)"


async def run_experiment_phase(phase_name, case_name, start_day, duration_days, memory, temperature, enable_rag=True):
    print(f"\n⚡ [Phase: {phase_name}] Starting {duration_days} days. LLM Temp: {temperature}. RAG: {enable_rag}")

    with open(MAPPING_DIR / f"{case_name}_mapping.json", 'r') as f:
        mapping = json.load(f)

    client = BoptestClient()
    obs_builder = ObservationBuilder(mapping)
    reward_calc = RewardCalculator(case_name)
    # [MODIFIED] Pass enable_rag to loggers
    exp_logger = ExperimentLogger(case_name, phase_name, enable_rag)
    int_logger = InteractionLogger(case_name, phase_name, enable_rag)

    commander = AgentCommander(memory)
    coder = AgentZoneCoder()
    reflector = AgentReflector(memory)
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    static_ctrl = static_config.get_static_controls(case_name)
    strat_context = static_config.get_strategic_context(case_name)
    max_occ = static_config.get_max_occupancy(case_name)
    zone_ids = list(mapping['zones'].keys())

    # Init
    start_sec = start_day * 24 * 3600
    y_curr = client.initialize(case_name, start_sec, 7 * 24 * 3600)
    obs_builder.initialize_buffer(y_curr, 298.15)

    # Forecast
    total_hours = duration_days * 24
    total_steps = total_hours * 4
    lookahead = COMMANDER_LOOKAHEAD_HOURS * 4
    total_horizon = (total_steps + lookahead + FORECAST_HORIZON_STEPS) * CONTROL_STEP_SIZE
    fc_points = obs_builder.forecast_points
    all_fc = client.get_forecast(fc_points, total_horizon, CONTROL_STEP_SIZE)
    # Clean Data
    all_fc = {k: [v if v is not None else 0.0 for v in v_list] for k, v_list in all_fc.items()}

    # State
    zone_last_pmv = {z: 0.0 for z in zone_ids}
    zone_realtime_pmv = {z: 0.0 for z in zone_ids}

    # [MODIFIED] 3. 初始化滑动窗口 Buffer
    # 结构: {zone_id: deque([frame_t-3, frame_t-2, frame_t-1], maxlen=3)}
    zone_history_buffers = {z: deque(maxlen=HISTORY_WINDOW_SIZE) for z in zone_ids}

    prev_setpoints_c = {z: 25.0 for z in zone_ids}
    prev_setpoints = [298.15] * len(zone_ids)
    # [NEW] Track real previous occupancy for edge detection (Cold Start)
    # 状态记忆增强：初始化上一时刻的真实占用
    zone_last_real_occupancy = {z: 0.0 for z in zone_ids}
    fc_len = len(next(iter(all_fc.values())))

    for hour_idx in range(total_hours):
        hour_start = hour_idx * 4
        print(f"\r   ⏳ Hour {hour_idx + 1}/{total_hours}...", end="")

        # --- 1. Calculate Trend Features ---
        curr_out_temp = all_fc[mapping['global_forecasts']['outdoor_temp']][hour_start] - 273.15
        next_out_temp = all_fc[mapping['global_forecasts']['outdoor_temp']][min(hour_start + 4, fc_len - 1)] - 273.15
        temp_trend = next_out_temp - curr_out_temp

        curr_price = all_fc[mapping['global_forecasts']['electricity_price']][hour_start]
        next_price = all_fc[mapping['global_forecasts']['electricity_price']][min(hour_start + 4, fc_len - 1)]
        price_trend = next_price - curr_price

        global_fc = {
            "outdoor_temp": curr_out_temp, "price": curr_price,
            "next_hour_price": next_price,
            "temp_trend": temp_trend, "price_trend": price_trend
        }
        current_clo_val = reward_calc.get_current_clo()

        zone_states = {}
        for z in zone_ids:
            occ_key = mapping['zones'][z]['forecasts']['occupancy']

            # Profile & Scalar Logic Update
            hourly_occ_profile = all_fc[occ_key][hour_start: hour_start + 4]
            occ_profile_list = [float(x) for x in hourly_occ_profile]

            # --- [新增] 特征工程：帮 LLM 总结 Profile 的含义 ---
            occ_status_text = "Steady Unoccupied"
            if all(x > 0 for x in occ_profile_list):
                occ_status_text = "Steady Occupied"
            elif any(x > 0 for x in occ_profile_list):
                # 检查是不是从无到有
                if occ_profile_list[0] == 0:
                    first_arrival_step = next((i for i, x in enumerate(occ_profile_list) if x > 0), -1)
                    occ_status_text = f"WARNING: People arriving in {first_arrival_step * 15} minutes! Pre-cooling Needed."
                else:
                    occ_status_text = "Mixed (People leaving soon)"
            # ------------------------------------------------

            # 确保只要这1小时内任何时候有人，Commander都知道是“有人状态”
            curr_occ_scalar = float(max(occ_profile_list)) if occ_profile_list else 0.0

            next_occ_slice = all_fc[occ_key][hour_start + 4: hour_start + 8]
            if len(next_occ_slice) > 0:
                next_max_occ = float(np.max(next_occ_slice))
            else:
                next_max_occ = 0.0

            occ_trend = 0
            if curr_occ_scalar == 0 and next_max_occ > 0:
                occ_trend = 1
            elif curr_occ_scalar > 0 and next_max_occ == 0:
                occ_trend = -1

            zone_states[z] = {
                # [关键修复] 显式添加 current_occupancy 字段，消除 LLM 歧义
                "current_occupancy": curr_occ_scalar,

                # 保留这个字段也没关系，但上面那个才是给 Commander 确权的
                "occupancy_forecast": curr_occ_scalar,
                "semantic_status": occ_status_text,

                "occupancy_profile": occ_profile_list,
                "next_hour_occupancy": float(next_max_occ),
                "last_hour_pmv": float(zone_last_pmv.get(z, 0.0)),
                "occ_trend": int(occ_trend),
                "clo": current_clo_val
            }
        # Future Outlook
        future_outlook = []
        for i in range(1, COMMANDER_LOOKAHEAD_HOURS + 1):
            s_idx = hour_start + i * 4
            e_idx = s_idx + 4
            if s_idx >= fc_len: break
            p_slice = all_fc[mapping['global_forecasts']['electricity_price']][s_idx:e_idx]
            t_slice = all_fc[mapping['global_forecasts']['outdoor_temp']][s_idx:e_idx]

            h_data = {
                "offset_hour": int(i),  # 转 int
                "avg_price": float(np.mean(p_slice)) if len(p_slice) else 0.0,  # 转 float
                "avg_outdoor_temp": float(np.mean(t_slice) - 273.15) if len(t_slice) else 0.0,  # 转 float
                "zone_max_occupancy": {}
            }
            for z in zone_ids:
                o_slice = all_fc[mapping['zones'][z]['forecasts']['occupancy']][s_idx:e_idx]
                # [FIX] 转 float
                h_data["zone_max_occupancy"][z] = float(np.max(o_slice)) if len(o_slice) else 0.0
            future_outlook.append(h_data)

        # --- 2. Strategy & Coding ---
        code_map = {}
        directives = {}

        # [WARMUP LOGIC] Force RBC
        if phase_name == "warmup":
            # Directives for log only
            directives = {z: {"strategy": "RBC Baseline", "reasoning": "Warmup Phase"} for z in zone_ids}
            # Hardcode RBC Logic
            for z in zone_ids:
                is_occ = zone_states[z]['occupancy_forecast'] > 0
                sp = 25.0 if is_occ else 30.0
                # Generate a dummy code string that reflects this (for consistency)
                code_map[z] = f"def run_control(obs): return {{'cooling_setpoint': {sp}}}"
        else:
            # [LLM LOGIC]
            phase_note = "EXPLORATION: Try new strategies." if phase_name == "exploration" else "EVALUATION: Stick to proven strategies."


            # [MODIFIED] 4. 将 zone_history_buffers 传给 Commander
            # 注意参数名变更：last_reflections -> history_context
            directives, p, r = await commander.generate_directives(
                f"Hour {hour_idx}", global_fc, zone_states, strat_context,
                history_context=zone_history_buffers,  # <-- 传入完整历史 Buffer
                max_occupancy=max_occ,
                future_outlook=future_outlook, temperature=temperature, phase_note=phase_note,
                enable_rag=enable_rag
            )
            int_logger.log(f"Hour {hour_idx}", "Commander", p, r)

            async def generate_code_task(z_id):
                async with semaphore:
                    c, p, r = await coder.generate_code(
                        z_id,
                        directives.get(z_id, {}),
                        mapping['zones'][z_id],
                        actuator_info=strat_context.get('actuator_info', ''),
                        fixed_info=strat_context.get('fixed_info', ''),
                        occupancy_profile=zone_states[z].get('occupancy_profile')  # <--- 必须加上这一行
                    )
                    int_logger.log(f"Hour {hour_idx} - {z_id}", "Coder", p, r)
                    return c

            codes = await asyncio.gather(*[generate_code_task(z) for z in zone_ids])
            code_map = {z: c for z, c in zip(zone_ids, codes)}

        # --- 3. Execution ---
        hour_stats = {"reward": 0, "cost": 0, "penalty": 0, "avg_temp": 0}
        zone_reward_acc = {z: 0.0 for z in zone_ids}
        zone_pmv_history = {z: [] for z in zone_ids}
        zone_temp_history = {z: [] for z in zone_ids}
        action_summary = {z: [] for z in zone_ids}
        zone_status_snapshot = {z: "Unknown" for z in zone_ids}

        for sub in range(4):
            g_step = hour_start + sub
            fc_sub = {k: v[g_step: g_step + FORECAST_HORIZON_STEPS + 1] for k, v in all_fc.items()}
            obs = obs_builder.build_observation(y_curr['time'], y_curr, fc_sub)

            u_dict = {}
            current_sps_k = []

            for k, v in static_ctrl.items():
                if k != "zone_patterns": u_dict[k] = v

            for z in zone_ids:
                if phase_name == "warmup":
                    # Hardcoded RBC Execution
                    is_occ = zone_states[z]['occupancy_forecast'] > 0
                    sp_c = 25.0 if is_occ else 30.0
                else:
                    # Agent Execution
                    local_obs = obs.copy()
                    local_obs['zone_temp'] = obs[f'temp_{z}']
                    local_obs['occupancy'] = obs[f'obs_Occ_{z}_0']
                    local_obs['last_pmv'] = zone_realtime_pmv[z]
                    local_obs['last_setpoint'] = prev_setpoints_c[z]
                    local_obs['next_hour_occupancy'] = zone_states[z]['next_hour_occupancy']
                    local_obs['next_hour_price'] = global_fc['next_hour_price']
                    local_obs['current_price'] = global_fc['price']
                    local_obs['current_occupancy'] = local_obs['occupancy']
                    local_obs['last_occupancy'] = float(zone_last_real_occupancy[z])

                    fallback_sp = 25.0 if local_obs['occupancy'] > 0 else 30.0
                    res = unsafe_exec_code(
                        code_map[z],
                        local_obs,
                        zone_id=z,  # 传入 Zone ID 用于报错定位
                        default_sp=fallback_sp  # 传入 动态兜底值
                    )
                    sp_c = max(20.0, min(30.0, res.get('cooling_setpoint', 25.0)))
                    zone_last_real_occupancy[z] = float(local_obs['occupancy'])

                sp_k = sp_c + 273.15
                current_sps_k.append(sp_k)
                action_summary[z].append(sp_c)
                prev_setpoints_c[z] = sp_c
                u_dict[mapping['zones'][z]['actuators']['cooling_setpoint']] = sp_k


                pat = static_ctrl.get('zone_patterns')
                if pat:
                    z_c = z.capitalize()
                    try:
                        u_dict[pat['heating_setpoint'].format(Zone=z_c)] = pat['heating_value']
                        u_dict[pat['heating_activate'].format(Zone=z_c)] = 1
                        u_dict[pat['cooling_activate'].format(Zone=z_c)] = 1
                    except:
                        pass

            y_next = client.advance(u_dict)

            t_out_c = fc_sub[mapping['global_forecasts']['outdoor_temp']][0] - 273.15
            reward_calc.update_clo(y_curr['time'], t_out_c)
            p_total = obs_builder.get_current_total_power(y_next)
            cost = (p_total * CONTROL_STEP_SIZE / 3.6e6) * global_fc['price']
            z_temps = [y_next[mapping['zones'][z]['sensors']['zone_temp']] - 273.15 for z in zone_ids]
            z_occs = [fc_sub[mapping['zones'][z]['forecasts']['occupancy']][0] > 0 for z in zone_ids]

            rew_res = reward_calc.calculate_reward(cost, z_temps, z_occs, current_sps_k, prev_setpoints)

            for idx, z in enumerate(zone_ids):
                current_pmv = rew_res['pmv_values'][idx]
                zone_realtime_pmv[z] = current_pmv
                zone_pmv_history[z].append(current_pmv)
                zone_temp_history[z].append(z_temps[idx])
                zone_reward_acc[z] += rew_res['zone_rewards'][idx]
                zone_status_snapshot[z] = rew_res['zone_status_list'][idx]

            exp_logger.log_step(y_curr['time'], hour_idx, g_step, p_total, cost, rew_res['total_reward'], z_temps,
                                [k - 273.15 for k in current_sps_k], rew_res['pmv_values'], z_occs)

            hour_stats['reward'] += rew_res['total_reward']
            hour_stats['cost'] += cost
            hour_stats['penalty'] += rew_res['raw']['penalty']
            hour_stats['avg_temp'] += sum(z_temps) / len(z_temps)

            act_dict = {z: sp for z, sp in zip(zone_ids, current_sps_k)}
            obs_builder.update_buffer(y_next, act_dict, reward_calc.cfg['max_power'])
            y_curr = y_next
            prev_setpoints = current_sps_k[:]

        # --- 4. Reflection ---
        hour_stats['avg_temp'] /= 4
        for z in zone_ids: zone_last_pmv[z] = sum(zone_pmv_history[z]) / 4

        async def reflect_task(z_id):
            avg_act = sum(action_summary[z_id]) / 4
            min_act = min(action_summary[z_id])
            max_act = max(action_summary[z_id])
            context = {"weather": global_fc, "occupancy": zone_states[z_id]['occupancy_forecast'], "hour_idx": hour_idx,
                       "timestamp": time.time(),
                       "temp_trend": global_fc['temp_trend'], "price_trend": global_fc['price_trend'],
                       "occ_trend": zone_states[z_id]['occ_trend']}

            local_metrics = {
                'reward': zone_reward_acc[z_id], 'cost': hour_stats['cost'] / len(zone_ids),
                'penalty': 0.0, 'avg_temp': sum(zone_temp_history[z_id]) / 4,
                'comfort_status': zone_status_snapshot[z_id]
            }
            pmvs = zone_pmv_history[z_id]
            local_metrics.update(
                {'avg_pmv': np.mean(pmvs), 'pmv_std': np.std(pmvs), 'pmv_min': np.min(pmvs), 'pmv_max': np.max(pmvs)})

            eval_label = determine_evaluation_label(local_metrics['avg_pmv'],
                                                    zone_states[z_id]['occupancy_forecast'] > 0,
                                                    local_metrics['pmv_max'])

            async with semaphore:
                res, p, r = await reflector.reflect_and_store(z_id, f"Hour {hour_idx}", context,
                                                              f"Avg Setpoint: {avg_act:.2f} (Range: {min_act:.1f}-{max_act:.1f})",
                                                              local_metrics,
                                                              strat_context.get('reflector_guide', ''), eval_label)
                int_logger.log(f"Hour {hour_idx} - {z_id}", "Reflector", p, r)
                # [MODIFIED] 5. 解析并构建结构化 Frame
                try:
                    insight_json = json.loads(r)
                    insight_text = insight_json.get('insight_text', 'No insight')
                except:
                    insight_text = "Analysis Failed"

                # 构建数据帧 (Frame)
                history_frame = {
                    "hour": hour_idx,
                    "avg_setpoint": avg_act,
                    "avg_pmv": local_metrics['avg_pmv'],
                    "reward": local_metrics['reward'],
                    "verdict": eval_label,
                    "insight": insight_text
                }

                return z_id, history_frame

        reflection_results = await asyncio.gather(*[reflect_task(z) for z in zone_ids])
        # [MODIFIED] 6. 更新 Buffer 并兼容 Logger
        log_reflections = []
        for z_id, frame in reflection_results:
            zone_history_buffers[z_id].append(frame)
            log_reflections.append(frame['insight'])

        # 这里的日志记录保持兼容性 (因为 step file 才是分析重点)
        exp_logger.log_hour(hour_idx, hour_stats['reward'], hour_stats['cost'], hour_stats['avg_temp'], directives,
                            log_reflections)

    client.stop()
    int_logger.close()
    print(f"\n✅ [Phase: {phase_name}] Completed.")


async def run_full_experiment(case_name):
    print(f"🚀 [Experiment] Starting 3-Phase Evolution for {case_name}")

    mem = MemoryManager(case_name=case_name, collection_name="memories")
    start = static_config.get_start_day(case_name)
    phases = static_config.get_phase_config()
    temps = static_config.get_temperature_schedule()

    if DEFAULT_ENABLE_RAG:
        print(f"🚀 [Experiment] Starting Full 3-Phase Evolution for {case_name} (RAG: ON)")

        # 1. Warmup (RBC) - RAG usually off/irrelevant here anyway, but keep standard flow
        await run_experiment_phase("warmup", case_name, start, phases['warmup_days'], mem, temps['warmup'],
                                   enable_rag=True)
        time.sleep(3)

        # 2. Exploration
        s2 = start + phases['warmup_days']
        await run_experiment_phase("exploration", case_name, s2, phases['exploration_days'], mem, temps['exploration'],
                                   enable_rag=True)
        time.sleep(3)

        # 3. Evaluation
        s3 = s2 + phases['exploration_days']
        await run_experiment_phase("evaluation", case_name, s3, phases['evaluation_days'], mem, temps['evaluation'],
                                   enable_rag=True)

    else:
        print(f"🔥 [Ablation Experiment] Starting ZERO-SHOT Evaluation for {case_name} (RAG: OFF)")
        print("   Skipping Warmup & Exploration phases...")

        # Calculate Start Day for Evaluation Phase to match the Full Experiment timeline
        # Start = StartDay + WarmupDays + ExplorationDays
        s_eval = start + phases['warmup_days'] + phases['exploration_days']

        # Run only Evaluation, RAG=False
        await run_experiment_phase("evaluation", case_name, s_eval, phases['evaluation_days'], mem, temps['evaluation'],
                                   enable_rag=False)

    print(f"\n🏆 Experiment Finished.")


if __name__ == "__main__":
    target_case = "bestest_air"
    #target_case = "multizone_office_simple_air"
    asyncio.run(run_full_experiment(target_case))