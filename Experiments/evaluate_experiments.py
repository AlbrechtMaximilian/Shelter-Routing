import pandas as pd
import matplotlib
matplotlib.use('TkAgg')  # for PyCharm GUI
import matplotlib.pyplot as plt
import seaborn as sns

def evaluate_results(results_excel_path):
    """
    Visualizes objective values as violin plots, computation time as bar chart (log scale),
    and relative optimality gap as a separate bar chart.
    """
    df = pd.read_excel(results_excel_path)

    # Melt for violin plot (objective values)
    df_long_obj = df.melt(
        id_vars=['scenarioID', 'scenario_description'],
        value_vars=['obj heuristic', 'obj naive', 'obj optimal'],
        var_name='method',
        value_name='objective'
    )
    df_long_obj['method'] = df_long_obj['method'].str.replace('obj ', '').str.title()

    # Objective value violin plot
    plt.figure(figsize=(14, 6))
    sns.violinplot(
        data=df_long_obj,
        x='scenario_description',
        y='objective',
        hue='method',
        split=False,
        inner="quartile"
    )
    plt.title('Distribution of Objective Values per Scenario and Method')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Objective Value")
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.legend(title='Method')
    plt.show()

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
    sns.barplot(
        data=time_summary,
        x='scenario_description',
        y='time',
        hue='method'
    )
    plt.yscale('log')
    plt.title('Average Computation Time per Scenario and Method (Log Scale)')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Computation Time (s, log scale)")
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.legend(title='Method')
    plt.show()

    # --- Optimality Gap Plot ---
    df['gap_heuristic'] = (df['obj heuristic'] - df['obj optimal']) / df['obj optimal']
    df['gap_naive'] = (df['obj naive'] - df['obj optimal']) / df['obj optimal']

    df_gap = df.melt(
        id_vars=['scenario_description'],
        value_vars=['gap_heuristic', 'gap_naive'],
        var_name='method',
        value_name='relative_gap'
    )
    df_gap['method'] = df_gap['method'].map({
        'gap_heuristic': 'Heuristic',
        'gap_naive': 'Naive'
    })

    gap_summary = df_gap.groupby(['scenario_description', 'method'])['relative_gap'].mean().reset_index()

    plt.figure(figsize=(14, 6))
    sns.barplot(
        data=gap_summary,
        x='scenario_description',
        y='relative_gap',
        hue='method',
        palette='Set2'
    )
    plt.title('Average Relative Optimality Gap per Scenario')
    plt.ylabel("Relative Gap to Optimal")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.legend(title='Method')
    plt.show()


if __name__ == "__main__":
    evaluate_results("Experiments/instances_20250528_135356/experiment_results.xlsx")