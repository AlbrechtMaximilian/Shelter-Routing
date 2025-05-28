import os
import pandas as pd
import time
from heuristic_algorithm import nearest_neighbor_heuristic
from naive_algorithm import naive_single_delivery
from opitmal_algorithm_speed_up import solve_routing

def run_experiments(path_to_folder, include_heuristic=True, include_naive_heuristic=True, include_optimal=True):
    """
    Runs the selected algorithms on all Excel instance files in the given folder.

    Args:
        path_to_folder (str): Base folder containing scenario subfolders with Excel instances.
        include_heuristic (bool): Whether to run the nearest neighbor heuristic.
        include_naive_heuristic (bool): Whether to run the naive heuristic.
        include_optimal (bool): Whether to run the optimal solver.
    """
    description_map = {
        1: "baseline (med shelters, med vehicles, med cap, med clustering)",
        2: "few shelters",
        3: "many shelters",
        4: "few vehicles",
        5: "many vehicles",
        6: "low vehicle capacity",
        7: "high vehicle capacity",
        8: "low clustering (uniform)",
        9: "high clustering (tight groups)",
    }

    results = []

    for scenario_name in sorted(os.listdir(path_to_folder)):
        scenario_path = os.path.join(path_to_folder, scenario_name)
        if not os.path.isdir(scenario_path):
            continue

        scenario_id = int(scenario_name.split("_")[-1])
        scenario_description = description_map.get(scenario_id, "unknown")

        for file_name in sorted(os.listdir(scenario_path)):
            if not file_name.endswith(".xlsx"):
                continue

            instance_id = int(file_name.split("_")[-1].split(".")[0])
            excel_path = os.path.join(scenario_path, file_name)

            # Load data
            params_df = pd.read_excel(excel_path, sheet_name="Params")
            demand_df = pd.read_excel(excel_path, sheet_name="Demand", index_col=0)
            dist_df = pd.read_excel(excel_path, sheet_name="Distance", index_col=0)

            p = params_df.set_index("param")["value"].to_dict()
            S_size = int(p["S_size"])
            V_size = int(p["V_size"])
            capacity = float(p["capacity"])
            speed = float(p["speed"])
            unload_t = float(p["unload_t"])

            S = range(S_size)
            V = range(V_size)
            demand = {int(i): float(demand_df.loc[i, "demand"]) for i in demand_df.index}
            distance = {(int(i), int(j)): float(dist_df.loc[i, j]) for i in dist_df.index for j in dist_df.columns}

            # Initialize values
            obj_heuristic = time_heuristic = None
            obj_naive = time_naive = None
            obj_optimal = time_optimal = None

            # Nearest Neighbor Heuristic
            if include_heuristic:
                start = time.time()
                obj_heuristic, computation_time , _ = nearest_neighbor_heuristic(S, V_size, distance, demand, capacity, speed, unload_t)
                #time_heuristic = time.time() - start
                time_heuristic = computation_time
                print(f"[✓] NN Heuristic finished: Scenario {scenario_id}, Instance {instance_id}")

            # Naive Heuristic (returns only obj)
            if include_naive_heuristic:
                start = time.time()
                obj_naive, _ = naive_single_delivery(S, range(V_size), distance, demand, capacity, speed, unload_t)
                time_naive = time.time() - start
                print(f"[✓] Naive Heuristic finished: Scenario {scenario_id}, Instance {instance_id}")

            # Optimal Solver
            if include_optimal:
                start = time.time()
                obj_optimal, _ = solve_routing(S, V, distance, demand, capacity, speed, unload_t)
                time_optimal = time.time() - start
                print(f"[✓] Optimal Solver finished: Scenario {scenario_id}, Instance {instance_id}")

            # Store results
            results.append({
                "scenarioID": scenario_id,
                "scenario_description": scenario_description,
                "instanceID": instance_id,
                "obj heuristic": obj_heuristic,
                "time heuristic": time_heuristic,
                "obj naive": obj_naive,
                "time naive": time_naive,
                "obj optimal": obj_optimal,
                "time optimal": time_optimal,
            })

    results_df = pd.DataFrame(results)
    output_path = os.path.join(path_to_folder, "experiment_results.xlsx")
    results_df.to_excel(output_path, index=False)
    print(f"\nAll experiments completed. Results saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    run_experiments(
        path_to_folder="instances_20250528_101234",
        include_heuristic=True,
        include_naive_heuristic=True,
        include_optimal=True
    )
