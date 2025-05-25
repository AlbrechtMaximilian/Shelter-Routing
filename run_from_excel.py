import pandas as pd
import math
from optimal_algorithm import solve_routing

def load_instance(path):
    """Load CVRP instance from Excel at `path`."""
    params_df = pd.read_excel(path, sheet_name="Params")
    demand_df = pd.read_excel(path, sheet_name="Demand", index_col=0)
    dist_df   = pd.read_excel(path, sheet_name="Distance", index_col=0)

    p = params_df.set_index("param")["value"].to_dict()
    S     = range(int(p["S_size"]))
    V     = range(int(p["V_size"]))
    capacity = float(p["capacity"])
    speed    = float(p["speed"])
    unload_t = float(p["unload_t"])

    demand = {int(i): float(demand_df.loc[i, "demand"])
              for i in demand_df.index}
    distance = {
        (int(i), int(j)): float(dist_df.loc[i, j])
        for i in dist_df.index for j in dist_df.columns
    }

    return S, V, distance, demand, capacity, speed, unload_t

if __name__ == "__main__":
    # hard-coded instance path
    instance_path = "scenario_2_instance_1.xlsx"

    # 1) load parameters
    S, V, distance, demand, capacity, speed, unload_t = load_instance(instance_path)

    print(demand)
    print(distance)

    # 2) solve (make sure solve_routing is silent except return values)
    """obj_value, solve_time = solve_routing(
        S, V,
        distance, demand,
        capacity, speed,
        unload_t
    )"""

    # 3) report
    #print(f"Obj value = {obj_value:.3f} min")
    #print(f"Solve time = {solve_time:.3f} s")