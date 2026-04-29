import numpy as np
from collections import deque
from configs.config import COOLING_SETPOINT_MAX


class ObservationBuilder:
    """
    观测空间构建器
    功能：
    1. 维护 Rolling Buffer (过去4步的状态)
    2. 获取 Forecast (未来4步)
    3. 聚合 Total Power
    4. 组装标准 Obs 字典
    """

    def __init__(self, mapping_config):
        self.mapping = mapping_config
        self.case_name = mapping_config['case_name']

        self.zone_ids = list(self.mapping['zones'].keys())

        # 历史缓冲区
        self.history_temp = {z: deque(maxlen=4) for z in self.zone_ids}
        self.history_action = {z: deque(maxlen=4) for z in self.zone_ids}
        self.history_power_norm = deque(maxlen=4)

        self.forecast_points = self._extract_forecast_points()
        self.power_meters = self.mapping['global_sensors']['power_meters']

    def _extract_forecast_points(self):
        pts = []
        gf = self.mapping['global_forecasts']
        pts.extend([gf['outdoor_temp'], gf['solar_irr'], gf['electricity_price']])

        for z in self.zone_ids:
            occ_key = self.mapping['zones'][z]['forecasts']['occupancy']
            if occ_key not in pts:
                pts.append(occ_key)
        return pts

    def initialize_buffer(self, y_current, initial_setpoint_k):
        p_total = sum([y_current.get(m, 0.0) for m in self.power_meters])
        p_norm = 0.0

        for _ in range(4):
            self.history_power_norm.append(p_norm)
            for z in self.zone_ids:
                t_sensor = self.mapping['zones'][z]['sensors']['zone_temp']
                t_val = y_current.get(t_sensor, 293.15)
                self.history_temp[z].append(t_val)
                self.history_action[z].append(initial_setpoint_k)

    def update_buffer(self, y_next, action_dict_k, max_system_power):
        p_total = sum([y_next.get(m, 0.0) for m in self.power_meters])
        p_norm = p_total / max_system_power if max_system_power > 0 else 0.0
        self.history_power_norm.append(p_norm)

        for z in self.zone_ids:
            t_sensor = self.mapping['zones'][z]['sensors']['zone_temp']
            self.history_temp[z].append(y_next.get(t_sensor, 293.15))
            act = action_dict_k.get(z, 298.15)
            self.history_action[z].append(act)

    def build_observation(self, time_now, y_current, forecast_data):
        """
        构建标准 Obs 字典
        [FIX]: 使用标准名称 (outdoor_temp) 作为 Key，与 Coder Prompt 保持一致。
        """
        obs = {}

        # 1. Time Encoding
        day_seconds = time_now % 86400
        obs['obs_sin_time'] = np.sin(2 * np.pi * day_seconds / 86400)
        obs['obs_cos_time'] = np.cos(2 * np.pi * day_seconds / 86400)

        # 2. Global Forecasts (Current + Future 4)
        gf = self.mapping['global_forecasts']

        # [CRITICAL FIX] Map keys to standard readable names
        key_map = {
            'outdoor_temp': gf['outdoor_temp'],  # Was 'TDryBul'
            'solar_irr': gf['solar_irr'],  # Was 'HGloHor'
            'electricity_price': gf['electricity_price']  # Was 'Price'
        }

        for name, key in key_map.items():
            data = forecast_data.get(key, [0] * 5)
            data = [d if d is not None else 0.0 for d in data]
            # Generates: obs_outdoor_temp_0, obs_electricity_price_0, etc.
            obs[f'obs_{name}_0'] = data[0]
            for i in range(1, 5):
                obs[f'obs_{name}_f{i}'] = data[i]

        # 3. Zone Data (History + Forecast)
        for z in self.zone_ids:
            # History Temp
            hist_t = list(self.history_temp[z])
            obs[f'obs_T_{z}_p1'] = hist_t[-1] - 273.15
            obs[f'obs_T_{z}_p2'] = hist_t[-2] - 273.15
            obs[f'obs_T_{z}_p3'] = hist_t[-3] - 273.15
            obs[f'obs_T_{z}_p4'] = hist_t[-4] - 273.15
            obs[f'temp_{z}'] = y_current.get(self.mapping['zones'][z]['sensors']['zone_temp'], 0) - 273.15

            # History Action
            hist_a = list(self.history_action[z])
            obs[f'obs_act_{z}_p1'] = hist_a[-1]

            # Forecast Occupancy
            occ_key = self.mapping['zones'][z]['forecasts']['occupancy']
            occ_data = forecast_data.get(occ_key, [0] * 5)
            occ_data = [d if d is not None else 0.0 for d in occ_data]

            obs[f'obs_Occ_{z}_0'] = occ_data[0]
            for i in range(1, 5):
                obs[f'obs_Occ_{z}_f{i}'] = occ_data[i]

        # 4. Global Power History
        hist_p = list(self.history_power_norm)
        for i in range(1, 5):
            obs[f'obs_power_norm_p{i}'] = hist_p[-i]

        return obs

    def get_current_total_power(self, y_curr):
        return sum([y_curr.get(m, 0.0) for m in self.power_meters])