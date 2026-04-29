import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === Paths ===
ROOT_DIR = Path(__file__).parent.parent.resolve()
DOCS_DIR = ROOT_DIR / "docs"
MAPPING_DIR = Path(__file__).parent.resolve()

# === LLM API ===
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === Physical constraints ===
COOLING_SETPOINT_MIN = 20.0
COOLING_SETPOINT_MAX = 30.0
FIXED_HEATING_SETPOINT_VAL = 15.0

# === Control parameters ===
FORECAST_HORIZON_STEPS = 4
COMMANDER_LOOKAHEAD_HOURS = 3
CONTROL_STEP_SIZE = 900

DEFAULT_ENABLE_RAG = False
ENABLE_CAUSAL_INJECTION = True

TARGET_CASES = [
    "bestest_air",
    "multizone_office_simple_air",
    "multizone_office_simple_hydronic"
]
