import pandas as pd
import math
from optimal_algorithm import solve_routing
import os

def load_instance(path):
    """
    Reads an Excel file at `path` with sheets:
      • Params   (cols: param, value)
      • Demand   (index=node_id, col=demand)
      • Distance (square matrix of size S×S)
    Returns:
      S, V, distance_dict, demand_dict, capacity, speed, unload_t
    """
    # read sheets
    params_df = pd.read_excel(path, sheet_name="Params")
    demand_df = pd.read_excel(path, sheet_name="Demand", index_col=0)
    dist_df   = pd.read_excel(path, sheet_name="Distance", index_col=0)

    # parse params
    p = params_df.set_index("param")["value"].to_dict()
    S_size   = int(p["S_size"])
    V_size   = int(p["V_size"])
    capacity = float(p["capacity"])
    speed    = float(p["speed"])
    unload_t = float(p["unload_t"])

    # build sets
    S = range(S_size)
    V = range(V_size)

    # build demand dict
    demand = {int(i): float(demand_df.loc[i, "demand"])
              for i in demand_df.index}

    # build distance dict
    distance = {
        (int(i), int(j)): float(dist_df.loc[i, j])
        for i in dist_df.index for j in dist_df.columns
    }

    return S, V, distance, demand, capacity, speed, unload_t


def batch_solve_all(base_folder, results_path="results.xlsx"):
    """
    Walks through all scenario folders under base_folder,
    loads each instance, calls solve_routing, and records results.
    """
    rows = []

    for scen_dir in sorted(os.listdir(base_folder)):
        scen_path = os.path.join(base_folder, scen_dir)
        if not os.path.isdir(scen_path) or not scen_dir.startswith("scenario_"):
            continue
        scenario_id = int(scen_dir.split("_")[1])

        for fname in sorted(os.listdir(scen_path)):
            if not fname.endswith(".xlsx"):
                continue
            instance_id = int(fname.rstrip(".xlsx").split("_")[-1])
            path = os.path.join(scen_path, fname)

            # load params and solve
            S, V, distance, demand, capacity, speed, unload_t = load_instance(path)
            obj_val, comp_time = solve_routing(
                S, V,
                distance, demand,
                capacity, speed,
                unload_t
            )

            # record result
            rows.append({
                "scenario_id": scenario_id,
                "instance_id": instance_id,
                "obj_value": obj_val,
                "computation_time": comp_time
            })

            # print per-instance status
            print(f"Scenario {scenario_id}, Instance {instance_id}: "
                  f"Obj = {obj_val:.2f}, Time = {comp_time:.3f}s")

        print(f"Completed scenario {scenario_id}")

    # save summary
    df = pd.DataFrame(rows, columns=[
        "scenario_id", "instance_id", "obj_value", "computation_time"
    ])
    df.to_excel(results_path, index=False)
    print(f"Results written to {results_path}")


# Example usage:
# At bottom of run_experiments.py:
if __name__ == "__main__":
    base_folder = "instances_20250525_132700"  # or point to your actual folder
    batch_solve_all(base_folder, "cvrp_results.xlsx")