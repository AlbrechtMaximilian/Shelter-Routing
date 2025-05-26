import pandas as pd
import matplotlib
matplotlib.use('TkAgg')  # fix for PyCharm
import matplotlib.pyplot as plt
import numpy as np

def evaluate_results(results_excel_path):
    """
    Visualizes average objective value and runtime per scenario in comparative barplots.
    Includes: NN Heuristic, Naive Heuristic, Optimal.
    """
    df = pd.read_excel(results_excel_path)

    # Group by scenarioID + description
    grouped = df.groupby(['scenarioID', 'scenario_description']).agg({
        'obj heuristic': 'mean',
        'obj naive': 'mean',
        'obj optimal': 'mean',
        'time heuristic': 'mean',
        'time naive': 'mean',
        'time optimal': 'mean'
    }).reset_index()

    # Bar positions
    x = np.arange(len(grouped))
    width = 0.25

    # Plot Objective Value Comparison
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    ax1.bar(x - width,      grouped['obj heuristic'], width, label='NN Heuristic', color='skyblue')
    ax1.bar(x,              grouped['obj naive'],     width, label='Naive Heuristic', color='lightgreen')
    ax1.bar(x + width,      grouped['obj optimal'],   width, label='Optimal', color='salmon')
    ax1.set_ylabel('Objective Value')
    ax1.set_title('Average Objective Value per Scenario')
    ax1.set_xticks(x)
    ax1.set_xticklabels(grouped['scenario_description'], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, axis='y', linestyle='--', alpha=0.5)
    fig1.tight_layout()
    plt.show()

    # Plot Computation Time Comparison
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    ax2.bar(x - width,      grouped['time heuristic'], width, label='NN Heuristic', color='skyblue')
    ax2.bar(x,              grouped['time naive'],     width, label='Naive Heuristic', color='lightgreen')
    ax2.bar(x + width,      grouped['time optimal'],   width, label='Optimal', color='salmon')
    ax2.set_ylabel('Computation Time (s)')
    ax2.set_title('Average Computation Time per Scenario')
    ax2.set_xticks(x)
    ax2.set_xticklabels(grouped['scenario_description'], rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, axis='y', linestyle='--', alpha=0.5)
    fig2.tight_layout()
    plt.show()


if __name__ == "__main__":
    evaluate_results("instances_20250526_162716/experiment_results.xlsx")