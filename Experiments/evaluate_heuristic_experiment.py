import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.ticker import PercentFormatter

def evaluate_heuristic_experiment(results_excel_path):
    df = pd.read_excel(results_excel_path)

    # Compute relative improvements
    df['rel_improvement_obj'] = (df['obj naive'] - df['obj heuristic']) / df['obj naive']
    df['rel_improvement_time'] = (df['time naive'] - df['time heuristic']) / df['time naive']

    # Manual mapping from scenarioID to number of shelters
    scenario_shelter_map = {
        1: 50,
        2: 100,
        3: 200,
        4: 500
    }

    df['num_shelters'] = df['scenarioID'].map(scenario_shelter_map)
    df = df.dropna(subset=['num_shelters', 'rel_improvement_obj', 'rel_improvement_time'])

    # Output directory
    plots_dir = "Experiments/Plots"
    os.makedirs(plots_dir, exist_ok=True)

    order = [50, 100, 200, 500]

    # Plot: Objective Improvement
    plt.figure(figsize=(10, 5))
    sns.boxplot(x='num_shelters', y='rel_improvement_obj', data=df, color='skyblue', order=order)
    plt.title("Relative Objective Improvement of Heuristic vs Naive")
    plt.xlabel("Number of Shelters")
    plt.ylabel("Relative Improvement (Objective)")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1.0))
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "relative_obj_improvement.png"))
    plt.close()

    # Plot: Computation Time Improvement
    plt.figure(figsize=(10, 5))
    sns.boxplot(x='num_shelters', y='rel_improvement_time', data=df, color='lightgreen', order=order)
    plt.title("Relative Computation Time Improvement of Heuristic vs Naive")
    plt.xlabel("Number of Shelters")
    plt.ylabel("Relative Improvement (Time)")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1.0))
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "relative_time_improvement.png"))
    plt.close()

if __name__ == "__main__":
    evaluate_heuristic_experiment("Experiments/heuristic_instances_20250528_134226/experiment_results.xlsx")