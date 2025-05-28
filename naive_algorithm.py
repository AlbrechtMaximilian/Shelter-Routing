import pandas as pd

def naive_single_delivery(S, V, distance, demand, capacity, speed, unload_t):
    rem = demand.copy()
    routes_by_vehicle = {v: [] for v in V}
    vehicle_idx = 0
    total_unload = 0

    for i in S:
        if i == 0:
            continue
        while rem[i] > 0:
            load = min(rem[i], capacity)
            rem[i] -= load
            total_unload += load

            route = [0, i, 0]
            routes_by_vehicle[vehicle_idx].append(route)

            # Move to next vehicle (round-robin)
            vehicle_idx = (vehicle_idx + 1) % len(V)

    # --- Calculate objective ---
    drive = sum(distance[(route[k], route[k+1])] / speed * 60
                for trips in routes_by_vehicle.values()
                for route in trips
                for k in range(len(route) - 1))

    unload_time = total_unload * unload_t
    obj = drive + unload_time

    return obj, routes_by_vehicle


def load_instance(path):
    params_df = pd.read_excel(path, sheet_name="Params")
    demand_df = pd.read_excel(path, sheet_name="Demand", index_col=0)
    dist_df   = pd.read_excel(path, sheet_name="Distance", index_col=0)

    p = params_df.set_index("param")["value"].to_dict()
    S_size   = int(p["S_size"])
    V_size   = int(p["V_size"])
    capacity = float(p["capacity"])
    speed    = float(p["speed"])
    unload_t = float(p["unload_t"])

    S = range(S_size)
    V = range(V_size)

    demand = {int(i): float(demand_df.loc[i, "demand"])
              for i in demand_df.index}

    distance = {
        (int(i), int(j)): float(dist_df.loc[i, j])
        for i in dist_df.index for j in dist_df.columns
    }

    return S, V, distance, demand, capacity, speed, unload_t


if __name__ == "__main__":
    path = "instances_20250528_101234/scenario_1/scenario_1_instance_1.xlsx"
    S, V, distance, demand, capacity, speed, unload_t = load_instance(path)

    obj_val, routes = naive_single_delivery(S, V, distance, demand, capacity, speed, unload_t)

    print(f"Objective: {obj_val:.2f}")
    print("Routes:")
    for v, trips in routes.items():
        print(f"  Vehicle {v}: {trips}")