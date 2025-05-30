import pandas as pd
import matplotlib
matplotlib.use('TkAgg')  # for PyCharm GUI
import matplotlib.pyplot as plt
import seaborn as sns
import os

def evaluate_results(results_excel_path):
    df = pd.read_excel(results_excel_path)
    plots_dir = "Experiments/Plots"
    os.makedirs(plots_dir, exist_ok=True)

    # --- Objective Value Violin Plot ---
    df_long_obj = df.melt(
        id_vars=['scenarioID', 'scenario_description'],
        value_vars=['obj heuristic', 'obj naive', 'obj optimal'],
        var_name='method',
        value_name='objective'
    )
    df_long_obj['method'] = df_long_obj['method'].str.replace('obj ', '').str.title()

    plt.figure(figsize=(14, 6))
    ax = sns.violinplot(
        data=df_long_obj,
        x='scenario_description',
        y='objective',
        hue='method',
        split=False,
        inner="quartile"
    )
    plt.xlabel("")  # Remove x-axis label
    plt.ylabel("Objective Value")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend_.set_title("")  # Remove legend title
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "objective_violin.png"))
    plt.close()

    # --- Computation Time Bar Chart ---
    time_cols = ['time heuristic', 'time naive', 'time optimal']
    df_time = df.melt(
        id_vars=['scenarioID', 'scenario_description'],
        value_vars=time_cols,
        var_name='method',
        value_name='time'
    )
    df_time['method'] = df_time['method'].str.replace('time ', '').str.title()
    time_summary = df_time.groupby(['scenario_description', 'method'])['time'].mean().reset_index()

    plt.figure(figsize=(14, 6))
    ax = sns.barplot(
        data=time_summary,
        x='scenario_description',
        y='time',
        hue='method'
    )
    plt.xlabel("")  # Remove x-axis label
    plt.ylabel("Computation Time (log scale)")
    plt.yscale('log')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend_.set_title("")  # Remove legend title
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "computation_time_bar.png"))
    plt.close()

    # --- Optimality Gap Bar Chart ---
    df['gap_heuristic'] = (df['obj heuristic'] - df['obj optimal']) / df['obj optimal']
    df['gap_naive'] = (df['obj naive'] - df['obj optimal']) / df['obj optimal']

    df_gap = df.melt(
        id_vars=['scenarioID', 'scenario_description'],
        value_vars=['gap_heuristic', 'gap_naive'],
        var_name='method',
        value_name='relative_gap'
    )
    df_gap['method'] = df_gap['method'].map({
        'gap_heuristic': 'Heuristic',
        'gap_naive': 'Naive'
    })

    # Define and enforce scenario order based on scenarioID
    scenario_order = df.sort_values("scenarioID")["scenario_description"].unique()
    df_gap["scenario_description"] = pd.Categorical(
        df_gap["scenario_description"],
        categories=scenario_order,
        ordered=True
    )

    gap_summary = df_gap.groupby(['scenario_description', 'method'])['relative_gap'].mean().reset_index()

    plt.figure(figsize=(14, 6))
    ax = sns.barplot(
        data=gap_summary,
        x='scenario_description',
        y='relative_gap',
        hue='method',
        palette='Set2'
    )
    plt.xlabel("")  # Remove x-axis label
    plt.ylabel("Relative Gap")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend_.set_title("")  # Remove legend title
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "relative_gap_bar.png"))
    plt.close()

if __name__ == "__main__":
    evaluate_results("Experiments/instances_20250528_135356/experiment_results.xlsx")