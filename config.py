import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# --- 路径配置 (Path Configuration) ---
ROOT_DIR = Path(__file__).parent.resolve()
DOCS_DIR = ROOT_DIR / "docs"
MAPPING_DIR = ROOT_DIR / "configs"
MAPPING_DIR.mkdir(parents=True, exist_ok=True)

# --- LLM 配置 (LLM Configuration) ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # 用于 Embedding


# --- 物理约束与控制常量 (Physical Constraints) ---
# 制冷设定点范围 (Celsius) - 根据你的修正
COOLING_SETPOINT_MIN = 20.0
COOLING_SETPOINT_MAX = 30.0

# 固定的加热设定点 (安全值, Celsius)
# 注意：这只是一个数值常量，具体的点位名称在 static_config.py 中定义
FIXED_HEATING_SETPOINT_VAL = 15.0

# 预测视界
FORECAST_HORIZON_STEPS = 4
COMMANDER_LOOKAHEAD_HOURS = 3
CONTROL_STEP_SIZE = 900

DEFAULT_ENABLE_RAG = False
ENABLE_CAUSAL_INJECTION = True  # Phase 0 因果图注入开关
# 目标案例
TARGET_CASES = [
    "bestest_air",
    "multizone_office_simple_air",
    "multizone_office_simple_hydronic"
]