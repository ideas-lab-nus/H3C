import os
import sys
import pandas as pd
import chromadb
from dotenv import load_dotenv
from openai import OpenAI

# 尝试导入 AutoGen 扩展
try:
    from autogen_ext.memory.chromadb import ChromaDBVectorMemory

    AUTOGEN_EXT_AVAILABLE = True
except ImportError:
    AUTOGEN_EXT_AVAILABLE = False


# --- 配置打印颜色 ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_status(step, message, status):
    symbol = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
    color = Colors.OKGREEN if status == "success" else Colors.FAIL if status == "error" else Colors.WARNING
    print(f"{color}{symbol} [{step}] {message}{Colors.ENDC}")


def check_environment():
    print(f"{Colors.HEADER}{Colors.BOLD}🚀 开始 H-RAG-Control 环境自检程序...{Colors.ENDC}\n")

    # 1. 加载环境变量
    load_dotenv(override=True)
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if deepseek_key:
        print_status("Env", f"DEEPSEEK_API_KEY 已加载 (长度: {len(deepseek_key)})", "success")
    else:
        print_status("Env", "未找到 DEEPSEEK_API_KEY", "error")

    if openai_key:
        print_status("Env", f"OPENAI_API_KEY 已加载 (用于 Embedding) (长度: {len(openai_key)})", "success")
    else:
        print_status("Env", "未找到 OPENAI_API_KEY (可能导致无法使用在线 Embedding)", "warning")

    print("-" * 30)

    # 2. 验证基础库
    try:
        df = pd.DataFrame({"test": [1]})
        print_status("Pandas", f"Pandas 版本: {pd.__version__}", "success")
    except Exception as e:
        print_status("Pandas", f"Pandas 错误: {e}", "error")

    try:
        chroma_ver = chromadb.__version__
        client = chromadb.Client()  # 测试内存模式
        print_status("ChromaDB", f"ChromaDB 版本: {chroma_ver} (内存客户端初始化成功)", "success")
    except Exception as e:
        print_status("ChromaDB", f"ChromaDB 错误: {e}", "error")

    # 3. 验证 AutoGen 扩展
    if AUTOGEN_EXT_AVAILABLE:
        print_status("AutoGen", "autogen_ext.memory.chromadb 导入成功", "success")
    else:
        print_status("AutoGen", "无法导入 autogen_ext。请检查是否安装: pip install autogen-ext[chromadb]", "error")

    print("-" * 30)

    # 4. 实际连通性测试 (DeepSeek LLM)
    if deepseek_key:
        print(f"{Colors.OKCYAN}🔄 正在测试 DeepSeek API 连通性...{Colors.ENDC}")
        try:
            client_ds = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
            response = client_ds.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "Say 'DeepSeek works'"}],
                max_tokens=10
            )
            reply = response.choices[0].message.content
            print_status("DeepSeek API", f"调用成功! 回复: {reply}", "success")
        except Exception as e:
            print_status("DeepSeek API", f"调用失败: {e}", "error")
    else:
        print_status("DeepSeek API", "跳过测试 (无 Key)", "warning")

    # 5. 实际连通性测试 (OpenAI Embedding)
    if openai_key:
        print(f"{Colors.OKCYAN}🔄 正在测试 OpenAI Embedding API 连通性...{Colors.ENDC}")
        try:
            client_oa = OpenAI(api_key=openai_key)
            # 测试 embedding
            response = client_oa.embeddings.create(
                input="Test embedding",
                model="text-embedding-3-small"
            )
            vec_len = len(response.data[0].embedding)
            print_status("Embedding API", f"调用成功! 向量维度: {vec_len}", "success")
        except Exception as e:
            print_status("Embedding API", f"调用失败: {e}", "error")
    else:
        print_status("Embedding API", "跳过测试 (无 Key - 将使用本地 Embedding 或报错)", "warning")

    print(f"\n{Colors.HEADER}{Colors.BOLD}🎉 检查结束{Colors.ENDC}")


if __name__ == "__main__":
    check_environment()