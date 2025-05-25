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
    m.params.OutputFlag = 0
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


if __name__ == "__main__":
    S = range(6)
    V = range(40)

    demand = {1: 45.0, 2: 19.0, 3: 16.0, 4: 43.0, 5: 17.0}
    distance = {(0, 0): 0.0, (0, 1): 83.68322037874805, (0, 2): 75.6804227596865, (0, 3): 36.75445674204973,
                (0, 4): 65.70919649721311, (0, 5): 47.3354231251481, (1, 0): 83.68322037874805, (1, 1): 0.0,
                (1, 2): 13.29820762717557, (1, 3): 52.70381750142401, (1, 4): 96.11225482556968,
                (1, 5): 37.17957676193532, (2, 0): 75.6804227596865, (2, 1): 13.29820762717557, (2, 2): 0.0,
                (2, 3): 42.04372859580731, (2, 4): 82.9324530928631, (2, 5): 28.35037060897747,
                (3, 0): 36.75445674204973, (3, 1): 52.70381750142401, (3, 2): 42.04372859580731, (3, 3): 0.0,
                (3, 4): 53.25868896740302, (3, 5): 16.71966131615739, (4, 0): 65.70919649721311,
                (4, 1): 96.11225482556968, (4, 2): 82.9324530928631, (4, 3): 53.25868896740302, (4, 4): 0.0,
                (4, 5): 68.05640482087416, (5, 0): 47.3354231251481, (5, 1): 37.17957676193532,
                (5, 2): 28.35037060897747, (5, 3): 16.71966131615739, (5, 4): 68.05640482087416, (5, 5): 0.0}

    capacity = 30
    speed    = 60
    unload_t = 10

    obj, elapsed = solve_routing(
        S, V, distance, demand,
        capacity, speed, unload_t
    )
    print(f"Objective = {obj:.1f} min, solved in {elapsed:.2f} s")