import numpy as np
from static_config import get_reward_config, PHYSICAL_CONFIG

# 尝试导入 pythermalcomfort
try:
    from pythermalcomfort.models import pmv_ppd_iso

    HAS_PTC = True
except ImportError:
    HAS_PTC = False
    print("[WARN] pythermalcomfort not found. PMV will be 0.")


class RewardCalculator:
    """
    物理归一化奖励计算器 (Enhanced with Comfort Labels)
    """

    def __init__(self, case_name):
        self.case_name = case_name
        self.cfg = get_reward_config(case_name)
        if not self.cfg:
            raise ValueError(f"No reward config found for {case_name}")

        self.n_zones = self.cfg['n_zones']
        self.weights = self.cfg['weights']
        self.scalers = self.cfg['scalers']
        self.phys = PHYSICAL_CONFIG

        # 状态变量
        self.prev_day_idx = -1
        self.current_clo = 0.5

    def update_clo(self, time_now, outdoor_temp_daily_mean):
        day_idx = int(time_now // 86400)
        if day_idx != self.prev_day_idx:
            p = self.phys['clo_dynamic_params']
            t = outdoor_temp_daily_mean
            if t < p['temp_low']:
                self.current_clo = p['winter_clo']
            elif t > p['temp_high']:
                self.current_clo = p['summer_clo']
            else:
                ratio = (t - p['temp_low']) / (p['temp_high'] - p['temp_low'])
                self.current_clo = p['winter_clo'] + ratio * (p['summer_clo'] - p['winter_clo'])

            self.prev_day_idx = day_idx

    def calc_pmv(self, t_air_c):
        if not HAS_PTC: return 0.0
        try:
            res = pmv_ppd_iso(
                tdb=t_air_c, tr=t_air_c,
                vr=self.phys['air_velocity'],
                rh=self.phys['relative_humidity'],
                met=self.phys['metabolic_rate'],
                clo=self.current_clo
            )
            val = res['pmv'] if isinstance(res, dict) else res.pmv
            return max(-3.0, min(3.0, val))
        except:
            return 0.0

    def calculate_reward(self, step_cost, zone_temps_c, is_occupied_mask, current_setpoints, prev_setpoints):
        """
        计算奖励 (支持区域独立归因)

        Returns:
            dict: {
                'total_reward': float,
                'zone_rewards': [float, ...], # [NEW] 每个区域的独立得分
                'pmv_values': [float, ...],
                ...
            }
        """
        n_z = self.n_zones
        w = self.weights

        # --- 1. 公共项 (Shared Term) ---
        # 能耗是全局共享的，所有区域平摊
        # Energy Term per zone = (Total Cost / N_Zones) * Scaler * Weight
        shared_energy_term = (step_cost / n_z) * self.scalers['energy'] * w['w_energy']

        # --- 2. 局部项 (Local Terms) & 聚合 ---
        zone_rewards = []
        pmv_details = []
        zone_status_list = []

        status_list = []

        total_pmv_penalty = 0.0
        total_delta_u = 0.0

        for i in range(len(zone_temps_c)):
            # A. Comfort (Local)
            t_c = zone_temps_c[i]
            pmv = self.calc_pmv(t_c)
            pmv_details.append(pmv)

            local_pmv_penalty = 0.0

            # [NEW] Generate Physical Status Label
            if not is_occupied_mask[i]:
                # Unoccupied
                status = "Unoccupied (Energy Saving)"
            else:
                # Occupied
                deviation = max(0, abs(pmv) - 0.5)
                local_pmv_penalty = deviation ** 2

                if -0.5 <= pmv <= 0.5:
                    if 0.3 <= pmv <= 0.5:
                        status = "Optimal Comfort (Efficient)"
                    else:
                        status = "Comfortable (Standard)"
                elif pmv < -0.5:
                    status = f"Warning: TOO COLD (PMV {pmv:.2f})"
                else:
                    status = f"Warning: TOO HOT (PMV {pmv:.2f})"

            zone_status_list.append(status)

            # Weighted Comfort Term
            local_comfort_term = local_pmv_penalty * self.scalers['comfort'] * w['w_comfort']

            # B. Smoothness (Local)
            local_delta = abs(current_setpoints[i] - prev_setpoints[i])
            local_smooth_term = local_delta * self.scalers['smooth'] * w['w_smooth']

            # C. Local Reward Calculation
            # R_i = - (Shared_Energy + Local_Comfort + Local_Smooth)
            r_i = - (shared_energy_term + local_comfort_term + local_smooth_term)
            zone_rewards.append(r_i)

            # D. Accumulate for Global Stats (Verification)
            total_pmv_penalty += local_pmv_penalty
            total_delta_u += local_delta

        # --- 3. Global Stats ---
        # Comfort Status String
        if not status_list:
            comfort_status = "Unoccupied (Energy Saving Mode)"
        else:
            uncomfortable = [s for s in status_list if "Comfortable" not in s]
            if not uncomfortable:
                comfort_status = "All Zones Comfortable (Ideal)"
            else:
                comfort_status = f"Discomfort Detected: {', '.join(list(set(uncomfortable)))}"

        # Total Global Reward (应该等于所有 Local Reward 的平均值? 或者总和?)
        # 之前的逻辑是: Total R = - (W*E_avg + W*C_avg + W*S_avg)
        # 这里为了保持兼容性，Total Reward 依然是归一化后的标量

        # 验证: Sum(zone_rewards) = - (N * Shared_Energy + Sum(Local_Comfort) + Sum(Local_Smooth))
        # Total Reward (Global Definition) = Sum(zone_rewards) / N
        # 这样保持量纲一致
        total_reward = sum(zone_rewards) / n_z

        return {
            'total_reward': total_reward,
            'zone_rewards': zone_rewards,  # [NEW]
            'pmv_values': pmv_details,
            'zone_status_list': zone_status_list,  # [NEW] List of status strings per zone
            'comfort_status': comfort_status,
            'components': {
                'energy_term_shared': shared_energy_term,  # Debug usage
            },
            'raw': {
                'cost': step_cost,
                'penalty': total_pmv_penalty,
                'delta_u': total_delta_u
            }
        }

    def get_current_clo(self):
        return self.current_clo