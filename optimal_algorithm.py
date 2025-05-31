import gurobipy as gp
from gurobipy import GRB
import time
import math
import pandas as pd

def solve_routing(S, V,
                  distance, demand,
                  capacity, speed,
                  unload_t):
    """
    S: iterable of nodes (0 = depot)
    V: iterable of vehicles
    distance: dict[(i,j)] → km
    demand: dict[i] → tons (i≠0)
    capacity: max tons/trip
    speed: km/h
    unload_t: minutes to unload 1 ton
    """

    # 1) Compute worst‐case number of trips
    D = sum(demand[i] for i in S if i != 0)
    T_max = math.ceil(D / (capacity * len(V)))
    T = range(T_max)
    print(f"maximum number of trips needed: {T_max}")

    # 2) Build model
    m = gp.Model()
    x = m.addVars(S, S, V, T, vtype=GRB.BINARY, name="x")
    q = m.addVars(S, V, T, vtype=GRB.CONTINUOUS, lb=0, name="q")
    u = m.addVars(S, V, T, vtype=GRB.CONTINUOUS, lb=0, ub=len(S)-1, name="u")

    # 3) Objective: drive time + unload time
    drive_time = gp.quicksum((distance[i,j]/speed)*60 * x[i,j,v,t]
                             for i in S for j in S if i != j
                             for v in V for t in T)
    unload_time = gp.quicksum(unload_t * q[i,v,t]
                              for i in S if i != 0
                              for v in V for t in T)

    m.setObjective(drive_time + unload_time, GRB.MINIMIZE)

    # 4) Ensure any trip that leaves returns
    for v in V:
        for t in T:
            m.addConstr(
                gp.quicksum(x[0,j,v,t] for j in S if j != 0)
                ==
                gp.quicksum(x[j,0,v,t] for j in S if j != 0)
            )

    # 5) Flow conservation at customer nodes
    for v in V:
        for t in T:
            for k in S:
                if k != 0:
                    m.addConstr(
                        gp.quicksum(x[i,k,v,t] for i in S if i != k)
                        ==
                        gp.quicksum(x[k,j,v,t] for j in S if j != k)
                    )

    # 6) Capacity & demand
    for v in V:
        for t in T:
            # total load on trip ≤ capacity
            m.addConstr(
                gp.quicksum(q[i,v,t] for i in S if i != 0)
                <= capacity
            )
            for i in S:
                if i != 0:
                    # can unload only if arc arrives
                    m.addConstr(
                        q[i,v,t]
                        <= capacity * gp.quicksum(x[j,i,v,t] for j in S if j != i)
                    )
                    m.addConstr(q[i,v,t] <= demand[i])

    # each demand must be exactly met
    for i in S:
        if i != 0:
            m.addConstr(
                gp.quicksum(q[i,v,t] for v in V for t in T)
                == demand[i]
            )

    # 7) MTZ subtour elimination
    n = len(S)
    for v in V:
        for t in T:
            m.addConstr(u[0,v,t] == 0)
            for i in S:
                for j in S:
                    if i != j and i != 0 and j != 0:
                        m.addConstr(
                            u[i,v,t] - u[j,v,t] + n * x[i,j,v,t]
                            <= n - 1
                        )

    # 8) Solve
    m.params.TimeLimit = 120
    m.params.OutputFlag = 1
    t0 = time.time()
    m.optimize()
    runtime = time.time() - t0

    # 9) Extract and print routes
    for v in V:
        for t in T:
            arcs = [(i,j) for i in S for j in S if i!=j and x[i,j,v,t].X > 0.5]
            if arcs:
                tour = [0]
                while True:
                    i = tour[-1]
                    legs = [j for (ii,j) in arcs if ii == i]
                    if not legs or legs[0] == 0:
                        tour.append(0)
                        break
                    tour.append(legs[0])
                print(f"Vehicle {v}, Trip {t}: {tour}")
                for i in tour:
                    if i != 0 and q[i,v,t].X > 1e-6:
                        print(f"  Delivered to {i}: {q[i,v,t].X:.2f} tons")

    return m.ObjVal, runtime


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


if __name__ == "__main__":
    S, V, distance, demand, capacity, speed, unload_t = load_instance("Experiments/instances_20250528_135356/scenario_1/scenario_1_instance_1.xlsx")
    obj_val, dict = solve_routing(S, V, distance, demand, capacity, speed, unload_t)
    print(obj_val)
    print(dict)