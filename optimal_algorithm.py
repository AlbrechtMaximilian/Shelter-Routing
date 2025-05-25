import gurobipy as gp
from gurobipy import GRB
import time
import math

def solve_routing(S, V,
                  distance, demand,
                  capacity, speed,
                  unload_t):
    """
    S: iterable of nodes (0 = depot)
    V: iterable of vehicles
    T: iterable of trips per vehicle
    distance: dict[(i,j)]→km
    demand: dict[i]→tons (i≠0)
    capacity: max tons/trip
    speed: km/h
    unload_t: min to unload 1 ton
    Tmax: max minutes/trip
    """
    # calculate T
    # calculate wors-case trip number
    D = sum(demand[i] for i in S if i != 0)  # total demand
    T_max = math.ceil(D / (capacity * len(V)))  # worst-case trips
    T = range(T_max)
    print("maximum number of trips needed: " + str(T_max))

    # start gurobi
    m = gp.Model()
    # Vars
    x = m.addVars(S, S, V, T, vtype=GRB.BINARY)
    q = m.addVars(S, V, T, vtype=GRB.CONTINUOUS, lb=0)
    u = m.addVars(S, V, T, vtype=GRB.CONTINUOUS, lb=0, ub=len(S)-1)
    # Obj
    drive_time = gp.quicksum((distance[i, j] / speed) * 60 * x[i, j, v, t]
                             for i in S for j in S if i != j
                             for v in V for t in T)

    unload_time = gp.quicksum(unload_t * q[i, v, t]
                              for i in S if i != 0
                              for v in V for t in T)

    launch_ind = gp.quicksum(x[0, j, v, t]  # arc 0→j exists ⇒ trip is dispatched
                             for j in S if j != 0
                             for v in V for t in T)

    m.setObjective(drive_time + unload_time + launch_cost * launch_ind,
                   GRB.MINIMIZE)
    # 1) start/end at 0
    for v in V:
        for t in T:
            m.addConstr(sum(x[0,j,v,t] for j in S if j!=0)<=1)
            m.addConstr(sum(x[j,0,v,t] for j in S if j!=0)<=1)
    # 2) flow conservation
    for v in V:
        for t in T:
            for k in S:
                if k!=0:
                    m.addConstr(
                        sum(x[i,k,v,t] for i in S if i!=k)
                        == sum(x[k,j,v,t] for j in S if j!=k)
                    )
    # 3) capacity & demand
    for v in V:
        for t in T:
            m.addConstr(sum(q[i,v,t] for i in S if i!=0) <= capacity)
            for i in S:
                if i!=0:
                    m.addConstr(q[i,v,t] <= capacity *
                                sum(x[j,i,v,t] for j in S if j!=i))
                    m.addConstr(q[i, v, t] <= demand[i])
    for i in S:
        if i!=0:
            m.addConstr(sum(q[i,v,t] for v in V for t in T)==demand[i])
    """# 4) time limit
    for v in V:
        for t in T:
            drive = sum((distance[i,j]/speed)*60 * x[i,j,v,t]
                        for i in S for j in S if i!=j)
            unload = sum(unload_t * q[i,v,t] for i in S if i!=0)
            m.addConstr(drive + unload <= Tmax)"""
    # 5) MTZ + root
    for v in V:
        for t in T:
            m.addConstr(u[0,v,t]==0)
            for i in S:
                for j in S:
                    if i!=j and i!=0 and j!=0:
                        m.addConstr(u[i,v,t] - u[j,v,t]
                                    + len(S)*x[i,j,v,t]
                                    <= len(S)-1)
    # solve & time
    start = time.time()
    m.params.OutputFlag = 0
    m.optimize()
    runtime = time.time() - start

    # Output
    for v in V:
        for t in T:
            route = []
            for i in S:
                for j in S:
                    if i != j and x[i, j, v, t].X > 0.5:
                        route.append((i, j))
            if route:
                print(f"Vehicle {v}, Trip {t}: Route: {route}")
                for i in S:
                    if i != 0 and q[i, v, t].X > 0:
                        print(f"  Deliver to {i}: {q[i, v, t].X:.2f} tons")

    return m.ObjVal, runtime


if __name__ == "__main__":
    # normal function call
    S = range(4)
    V = range(1)
    distance = {
        (0,1):10,(1,0):10,(0,2):15,(2,0):15,
        (0,3):20,(3,0):20,(1,2):5, (2,1):5,
        (1,3):10,(3,1):10,(2,3):7, (3,2):7
    }
    demand = {1:2, 2:3, 3:1}
    capacity = 1
    speed = 60
    unload_t = 10
    launch_cost = 100

    obj, runtime = solve_routing(
        S, V,
        distance, demand,
        capacity, speed,
        unload_t
    )
    print(f"Obj value = {obj:.1f} min, solve time = {runtime:.3f} s")