import gurobipy as gp
from gurobipy import GRB

# Sets
S = range(4)  # Shelters (0 is hub)
V = range(1)  # Trucks
T = range(2)  # Trips

# Parameters
distance = {
    (0, 1): 10, (1, 0): 10,
    (0, 2): 15, (2, 0): 15,
    (0, 3): 20, (3, 0): 20,
    (1, 2): 5,  (2, 1): 5,
    (1, 3): 10, (3, 1): 10,
    (2, 3): 7,  (3, 2): 7
}
speed = 60  # km/h
unload_time_per_ton = 10  # minutes
demand = {1: 2, 2: 3, 3: 1}  # tons
capacity = 5  # tons
Tmax = 1440  # minutes per trip

# Model
model = gp.Model("VehicleRoutingConnected")

x = model.addVars(S, S, V, T, vtype=GRB.BINARY, name="x")
q = model.addVars(S, V, T, vtype=GRB.CONTINUOUS, lb=0, name="q")
u = model.addVars(S, V, T, vtype=GRB.CONTINUOUS, lb=0, ub=len(S), name="u")

# Objective: minimize total travel time
model.setObjective(gp.quicksum((distance[i, j]/speed)*60 * x[i, j, v, t]
                                for i in S for j in S if i != j for v in V for t in T), GRB.MINIMIZE)

# Constraints
# Truck starts and ends at hub (node 0)
for v in V:
    for t in T:
        model.addConstr(gp.quicksum(x[0, j, v, t] for j in S if j != 0) == 1)  # Start at hub
        model.addConstr(gp.quicksum(x[j, 0, v, t] for j in S if j != 0) == 1)  # End at hub

# Flow conservation
for v in V:
    for t in T:
        for k in S:
            if k != 0:
                model.addConstr(gp.quicksum(x[i, k, v, t] for i in S if i != k) ==
                                gp.quicksum(x[k, j, v, t] for j in S if j != k))

# Capacity per trip
for v in V:
    for t in T:
        model.addConstr(gp.quicksum(q[i, v, t] for i in S if i != 0) <= capacity)

# Deliver only if visited
for v in V:
    for t in T:
        for i in S:
            if i != 0:
                model.addConstr(q[i, v, t] <= capacity * gp.quicksum(x[j, i, v, t] for j in S if j != i))

# Demand fulfillment
for i in S:
    if i != 0:
        model.addConstr(gp.quicksum(q[i, v, t] for v in V for t in T) == demand[i])

# Time per trip
for v in V:
    for t in T:
        drive_time = gp.quicksum((distance[i, j]/speed)*60 * x[i, j, v, t] for i in S for j in S if i != j)
        unload_time = gp.quicksum(unload_time_per_ton * q[i, v, t] for i in S if i != 0)
        model.addConstr(drive_time + unload_time <= Tmax)

# Subtour elimination (MTZ)
for v in V:
    for t in T:
        for i in S:
            for j in S:
                if i != j and i != 0 and j != 0:
                    model.addConstr(u[i, v, t] - u[j, v, t] + len(S) * x[i, j, v, t] <= len(S) - 1)

model.setParam('OutputFlag', 0)
model.optimize()

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