import gurobipy as gp
from gurobipy import GRB
import time, math
import pandas as pd

def solve_routing(S, V, distance, demand, capacity, speed, unload_t):
    # 1) total demand & trip bound
    D     = sum(demand[i] for i in S if i != 0)
    # worst-case trips if all single-customer loads
    K     = sum(math.ceil(demand[i]/capacity) for i in demand)
    V_eff = range(min(len(V), K))
    T_max = math.ceil(D / (capacity * len(V_eff)))
    T     = range(T_max)
    print(f"max trips needed: {T_max}, vehicles used: {len(V_eff)}")

    # 2) model & vars
    m = gp.Model()

    x = m.addVars(S, S, V_eff, T, vtype=GRB.BINARY,     name="x")
    q = m.addVars(S, V_eff, T,      vtype=GRB.CONTINUOUS, lb=0, name="q")
    u = m.addVars(S, V_eff, T,      vtype=GRB.CONTINUOUS, lb=0, ub=len(S)-1, name="u")
    y = m.addVars(V_eff, T,         vtype=GRB.BINARY,     name="y")

    # 3) objective
    drive = gp.quicksum((distance[i,j]/speed)*60 * x[i,j,v,t]
                        for i in S for j in S if i!=j
                        for v in V_eff for t in T)
    unload= gp.quicksum(unload_t * q[i,v,t]
                        for i in S if i!=0
                        for v in V_eff for t in T)
    m.setObjective(drive + unload, GRB.MINIMIZE)

    # 4) depot return & y‐link
    for v in V_eff:
        for t in T:
            dep = gp.quicksum(x[0,j,v,t] for j in S if j!=0)
            ret = gp.quicksum(x[j,0,v,t] for j in S if j!=0)
            m.addConstr(dep == ret)
            m.addConstr(dep <= (len(S)-1) * y[v,t])
            m.addConstr(dep >= y[v,t])
            if t < T_max-1:
                m.addConstr(y[v,t] >= y[v,t+1])

    # 5) flow at customers
    for v in V_eff:
        for t in T:
            for k in S:
                if k != 0:
                    m.addConstr(
                        gp.quicksum(x[i,k,v,t] for i in S if i!=k)
                        ==
                        gp.quicksum(x[k,j,v,t] for j in S if j!=k)
                    )

    # 6) capacity & multi-stop unload
    for v in V_eff:
        for t in T:
            m.addConstr(gp.quicksum(q[i,v,t] for i in S if i!=0) <= capacity)
            for i in S:
                if i != 0:
                    arr = gp.quicksum(x[j,i,v,t] for j in S if j!=i)
                    m.addConstr(q[i,v,t] <= capacity * arr)
                    m.addConstr(q[i,v,t] <= demand[i])

    # 7) satisfy all demand
    for i in S:
        if i != 0:
            m.addConstr(
                gp.quicksum(q[i,v,t] for v in V_eff for t in T)
                == demand[i]
            )

    # 8) MTZ + tighten with y
    n = len(S)
    for v in V_eff:
        for t in T:
            m.addConstr(u[0,v,t] == 0)
            for i in S:
                m.addConstr(u[i,v,t] <= (n-1) * y[v,t])
                for j in S:
                    if i!=j and i!=0 and j!=0:
                        m.addConstr(
                            u[i,v,t] - u[j,v,t] + n * x[i,j,v,t]
                            <= n - 1
                        )

    # 9) solve
    m.params.OutputFlag = 0
    t0 = time.time()

    # Stop when (UB – LB)/UB ≤ 1%
    #m.params.MIPGap = 0.01

    # Don’t run longer than 30 min (1,800 s)
    #m.params.TimeLimit = 10
    m.params.OutputFlag = 1
    m.optimize()
    status_str = {GRB.LOADED: "Loaded", GRB.OPTIMAL: "Optimal", GRB.INFEASIBLE: "Infeasible",
                  GRB.INTERRUPTED: "Interrupted", GRB.TIME_LIMIT: "Time limit", GRB.SOLUTION_LIMIT: "Solution limit"}.get(m.Status, str(m.Status))
    print(f"Model Status: {status_str} ({m.Status})")
    print(f"Reported MIPGap: {m.MIPGap:.6f}")
    print(f"Solved in {time.time()-t0:.2f}s, Obj={m.ObjVal:.1f}")

    # 10) extract routes
    for v in V_eff:
        for t in T:
            if y[v,t].X < 0.5: continue
            arcs = [(i,j) for i in S for j in S
                    if i!=j and x[i,j,v,t].X > 0.5]
            tour = [0]
            while True:
                cur = tour[-1]
                nxt = [j for (ii,j) in arcs if ii==cur]
                if not nxt or nxt[0]==0:
                    tour.append(0)
                    break
                tour.append(nxt[0])
            print(f"Vehicle {v}, Trip {t}: {tour}")
            for i in tour:
                if i!=0 and q[i,v,t].X > 1e-6:
                    print(f"  Delivered {q[i,v,t].X:.2f} t to node {i}")


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
    S, V, distance, demand, capacity, speed, unload_t = load_instance("instances_20250526_131056/scenario_1/scenario_1_instance_1.xlsx")
    solve_routing(S, V, distance, demand, capacity, speed, unload_t)