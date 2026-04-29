import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os
import warnings

# ================= CONFIGURATION =================
CSV_PATH = os.path.join("Analysis_Result", "comprehensive_log_analysis.csv")
OUTPUT_DIR = "Analysis_Plots"

# J-Curve Settings (Section 3-2 Right)
J_CURVE_BIN_SIZE = 200  # Token bin size
J_CURVE_IS_GROUP = False  # True: Merge all cases; False: Separate line for each case

# Plot Styling
sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
# Custom palette: Baseline (Grey/Blue) vs Causal (Orange/Red) or Case distinctions
PALETTE_COND = {"Baseline": "#95a5a6", "Causal": "#e74c3c"}
PALETTE_CASES = "viridis"  # For separating cases (MZ_Air, SZ_Air, etc.)


# ================= HELPERS =================

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def load_and_prep_data(csv_path):
    print(f"📂 Loading data from {csv_path}...")

    # Try reading with different encodings to handle UnicodeDecodeError
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        print("⚠️ UTF-8 decoding failed. Trying 'gbk' (Common on Windows)...")
        try:
            df = pd.read_csv(csv_path, encoding='gbk')
        except UnicodeDecodeError:
            print("⚠️ GBK decoding failed. Trying 'latin1'...")
            df = pd.read_csv(csv_path, encoding='latin1')

    # 1. Generate 'Condition' column for CausalAblation
    # Logic: Look for 'unCausal' in source_file -> Baseline, else -> Causal
    def get_condition(filename):
        if pd.isna(filename): return 'Unknown'
        if 'unCausal' in str(filename):
            return 'Baseline'
        return 'Causal'

    df['Condition'] = df['source_file'].apply(get_condition)

    # 2. Ensure Booleans are Integers for aggregation
    def robust_bool_convert(x):
        if pd.isna(x): return 0
        if isinstance(x, bool): return int(x)
        if isinstance(x, (int, float)): return int(x)
        if isinstance(x, str):
            return 1 if x.lower() == 'true' else 0
        return 0

    df['hallucination_flag'] = df['hallucination_flag'].apply(robust_bool_convert)
    df['Act_Diff'] = df['Act_Diff'].apply(robust_bool_convert)

    # 3. Calculate RISK Metric (Union of Hallucination OR Safety Net Trigger)
    df['Risk_Flag'] = ((df['hallucination_flag'] == 1) | (df['Act_Diff'] == 1)).astype(int)

    print(f"✅ Data Loaded. Shape: {df.shape}")
    return df


# ================= SECTION 2: MECHANISM =================

def plot_section_2(df):
    """
    Focus: CausalAblation Group
    2-1: Control Behavior Density (KDE)
    2-2: Cognitive Quality (Bar Charts)
    """
    print("🎨 Plotting Section 2 (Causal Mechanism)...")
    ensure_dir(OUTPUT_DIR)

    # Filter Data
    df_causal = df[df['group'] == 'CausalAblation'].copy()
    if df_causal.empty:
        print("⚠️ No data found for CausalAblation group. Skipping Section 2 plots.")
        return

    # --- Chart 2-1: Control Behavior Density (Action Granularity) ---
    plt.figure(figsize=(8, 5))
    try:
        sns.kdeplot(
            data=df_causal,
            x="action_delta",
            hue="Condition",
            palette=PALETTE_COND,
            fill=True,
            common_norm=False,
            alpha=0.4,
            linewidth=2
        )
        plt.title("Chart 2-1: Control Action Granularity Distribution")
        plt.xlabel("Setpoint Delta (|ΔSP| in °C)")
        plt.ylabel("Density")
        plt.xlim(0, 3.0)  # Limit x-axis to relevant range
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "2-1_Action_Granularity_KDE.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"⚠️ Error plotting 2-1: {e}")

    # --- Chart 2-2: Cognitive Quality Audit (Twin Bar Plots) ---
    # Aggregate data
    try:
        agg_metrics = df_causal.groupby(['case_name', 'Condition'])[
            ['hallucination_flag', 'Act_Diff']].mean().reset_index()

        fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

        # Subplot A: Inverse Physics Hallucination Rate
        sns.barplot(
            data=agg_metrics, x='case_name', y='hallucination_flag', hue='Condition',
            palette=PALETTE_COND, ax=axes[0], edgecolor="black"
        )
        axes[0].set_title("A. Inverse Physics Hallucination Rate")
        axes[0].set_ylabel("Rate (0-1)")
        axes[0].set_xlabel("Case")

        # Subplot B: Safety Net Reliance (Act_Diff)
        sns.barplot(
            data=agg_metrics, x='case_name', y='Act_Diff', hue='Condition',
            palette=PALETTE_COND, ax=axes[1], edgecolor="black"
        )
        axes[1].set_title("B. Safety Net Reliance (Intervention Rate)")
        axes[1].set_ylabel("")  # Share Y
        axes[1].set_xlabel("Case")

        plt.suptitle("Chart 2-2: Cognitive Quality Audit", fontsize=16)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "2-2_Cognitive_Quality.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"⚠️ Error plotting 2-2: {e}")


# ================= SECTION 3: WORKING MEMORY =================

def plot_section_3(df):
    """
    Focus: SWAblation Group
    3-1: Decision Stability (Boxplots)
    3-2 Left: Token Consumption (Bar)
    3-2 Right: Hallucination J-Curve (Line)
    """
    print("🎨 Plotting Section 3 (Working Memory)...")
    ensure_dir(OUTPUT_DIR)

    # Filter Data
    df_sw = df[df['group'] == 'SWAblation'].copy()
    if df_sw.empty:
        print("⚠️ No data found for SWAblation group. Skipping Section 3 plots.")
        return

    # --- Chart 3-1: Decision Stability in Steady States ---
    # Filter for Steady Regimes only
    target_regimes = ['Unoccupied_Steady', 'Occupied_Steady']
    df_steady = df_sw[df_sw['regime'].isin(target_regimes)].copy()

    if not df_steady.empty:
        try:
            g = sns.catplot(
                data=df_steady,
                kind="box",
                x="sw_window",
                y="semantic_jitter",
                hue="case_name",  # 3 cases per window
                col="regime",  # Facet by Regime
                palette=PALETTE_CASES,
                height=5, aspect=1.2,
                showfliers=False  # Optional: Hide outliers for cleaner view
            )
            g.set_axis_labels("Sliding Window Size", "Semantic Jitter (1 - Cosine Sim)")
            g.fig.subplots_adjust(top=0.85)
            g.fig.suptitle("Chart 3-1: Decision Stability in Steady States")
            plt.savefig(os.path.join(OUTPUT_DIR, "3-1_Decision_Stability.png"), dpi=300)
            plt.close()
        except Exception as e:
            print(f"⚠️ Error plotting 3-1: {e}")
    else:
        print("⚠️ No steady state data found for Chart 3-1.")

    # --- Chart 3-2: The Cost of Context (Combined Figure) ---
    try:
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # Left: Token Consumption
        # Aggregate mean tokens per case/window
        token_agg = df_sw.groupby(['sw_window', 'case_name'])['commander_input_tokens'].mean().reset_index()

        sns.barplot(
            data=token_agg,
            x='sw_window',
            y='commander_input_tokens',
            hue='case_name',
            palette=PALETTE_CASES,
            ax=axes[0],
            edgecolor="black"
        )
        axes[0].set_title("A. Context Cost (Token Consumption)")
        axes[0].set_ylabel("Avg Input Tokens")
        axes[0].set_xlabel("Sliding Window Size")
        axes[0].legend(title="Case")

        # Right: The Hallucination J-Curve (Risk Probability)
        # 1. Binning Tokens
        # Create bins range
        max_tokens = df_sw['commander_input_tokens'].max()
        # Handle case where max_tokens is smaller than BIN_SIZE or NaN
        if pd.isna(max_tokens) or max_tokens == 0:
            max_tokens = 1000

        bins = np.arange(0, max_tokens + J_CURVE_BIN_SIZE, J_CURVE_BIN_SIZE)
        labels = bins[:-1] + J_CURVE_BIN_SIZE / 2  # Use bin center for plotting

        df_sw['Token_Bin'] = pd.cut(df_sw['commander_input_tokens'], bins=bins, labels=labels)

        # 2. Aggregation Logic
        if J_CURVE_IS_GROUP:
            # Group only by Token Bin (Merge Cases)
            risk_agg = df_sw.groupby('Token_Bin', observed=True)['Risk_Flag'].mean().reset_index()
            # Plot single line
            sns.lineplot(
                data=risk_agg, x='Token_Bin', y='Risk_Flag',
                marker='o', linewidth=2.5, color='darkred', ax=axes[1]
            )
            plot_title_suffix = "(Aggregated)"
        else:
            # Group by Token Bin AND Case
            risk_agg = df_sw.groupby(['Token_Bin', 'case_name'], observed=True)['Risk_Flag'].mean().reset_index()
            # Plot multiple lines
            sns.lineplot(
                data=risk_agg, x='Token_Bin', y='Risk_Flag', hue='case_name',
                palette=PALETTE_CASES, marker='o', linewidth=2.5, ax=axes[1]
            )
            plot_title_suffix = "(Per Case)"

        # Improve J-Curve layout
        axes[1].set_title(f"B. The 'Context Risk' J-Curve {plot_title_suffix}")
        axes[1].set_xlabel("Input Token Count")
        axes[1].set_ylabel("Risk Probability (Hallucination | Safety Trigger)")
        axes[1].grid(True, which='both', linestyle='--', alpha=0.7)

        plt.suptitle("Chart 3-2: The Cost & Risk of Context", fontsize=16)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "3-2_Cost_Risk_Curve.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"⚠️ Error plotting 3-2: {e}")


# ================= MAIN =================

def main():
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: CSV file not found at {CSV_PATH}")
        return

    # 1. Load Data
    df = load_and_prep_data(CSV_PATH)

    # 2. Generate Plots
    plot_section_2(df)
    plot_section_3(df)

    print(f"🎉 All plots generated in '{OUTPUT_DIR}' folder!")


if __name__ == "__main__":
    main()