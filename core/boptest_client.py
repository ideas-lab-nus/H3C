import requests
import time


class BoptestClient:
    """
    BOPTEST API Client
    Features: Robust retry logic, automatic testid management.
    """

    def __init__(self, url="http://127.0.0.1:80", rank=0):
        self.base_url = url
        self.rank = rank  # 用于并行时的标识
        self.testid = None
        self.case_name = None

    def _make_request_with_retry(self, method, url, context_msg, max_retries=5, **kwargs):
        """带指数退避和错误过滤的健壮请求 (User Provided)"""
        for attempt in range(max_retries):
            try:
                kwargs.setdefault('timeout', 600)
                response = requests.request(method, url, **kwargs)

                if response.status_code == 200:
                    return response.json() if response.content else {'status': 'success'}

                # 忽略重复停止导致的 400 错误
                if response.status_code == 400 and "stop" in url:
                    return {'status': 'ignored_error'}

                # 其他非200状态码，抛出异常以触发重试
                response.raise_for_status()

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    # print(f"[Rank {self.rank}] Retry {attempt+1} for {context_msg} after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"[Rank {self.rank}] ❌ {context_msg} 最终失败: {e}")
                    raise e
        return None

    def initialize(self, case_name, start_time, warmup_period=0):
        self.case_name = case_name

        # 1. Select
        res = self._make_request_with_retry(
            'post',
            f"{self.base_url}/testcases/{case_name}/select",
            f"Select {case_name}"
        )
        self.testid = res['testid']
        print(f"✅ [Client] Selected {case_name} (ID: {self.testid})")

        # 2. Set Price (Dynamic)
        self._make_request_with_retry(
            'put',
            f"{self.base_url}/scenario/{self.testid}",
            "Set Scenario",
            json={'electricity_price': 'dynamic'}
        )

        # 3. Set Step (900s)
        self._make_request_with_retry(
            'put',
            f"{self.base_url}/step/{self.testid}",
            "Set Step",
            json={'step': 900}
        )

        # 4. Initialize
        payload = {'start_time': start_time, 'warmup_period': warmup_period}
        res_init = self._make_request_with_retry(
            'put',
            f"{self.base_url}/initialize/{self.testid}",
            "Initialize",
            json=payload
        )
        return res_init['payload']

    def advance(self, u_dict):
        if not self.testid: return {}
        res = self._make_request_with_retry(
            'post',
            f"{self.base_url}/advance/{self.testid}",
            "Advance",
            json=u_dict
        )
        return res['payload']

    def get_forecast(self, point_names, horizon, interval):
        if not self.testid: return {}
        # 注意: horizon 应为 4*step, interval 应为 step
        # 返回结果长度为 (horizon/interval) + 1 = 5 个点 (t0, t+1, t+2, t+3, t+4)
        payload = {
            'point_names': point_names,
            'horizon': horizon,
            'interval': interval
        }
        res = self._make_request_with_retry(
            'put',
            f"{self.base_url}/forecast/{self.testid}",
            "Get Forecast",
            json=payload
        )
        return res['payload']

    def stop(self):
        if self.testid:
            self._make_request_with_retry(
                'put',
                f"{self.base_url}/stop/{self.testid}",
                "Stop Simulation"
            )
            print(f"🛑 [Client] Stopped {self.case_name}")
            self.testid = None