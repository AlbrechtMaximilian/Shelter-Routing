import gurobipy as gp
from gurobipy import GRB
import numpy as np

# ----- Parameters -----
n_shelters = 10
n_hubs = 2
n_trucks = 5
truck_capacity = 50
demand_per_shelter = 200
truck_speed = 50  # km/h

# Random coordinates for simplicity
np.random.seed(0)
coords = np.random.rand(n_shelters, 2) * 100  # 100x100 grid

def euclidean(i, j):
    return np.linalg.norm(coords[i] - coords[j])

# Distance and time matrix
c = np.array([[euclidean(i, j) for j in range(n_shelters)] for i in range(n_shelters)])
t = c / truck_speed

model = gp.Model("Hub_Location_and_Routing")

# ----- Variables -----
# y[i]: 1 if shelter i is a hub
y = model.addVars(n_shelters, vtype=GRB.BINARY, name="y")

# x[i,j,k,h]: 1 if truck k from hub h goes from i to j
x = model.addVars(n_shelters, n_shelters, n_trucks, n_shelters, vtype=GRB.BINARY, name="x")

# q[i,k,h]: quantity delivered by truck k from hub h to shelter i
q = model.addVars(n_shelters, n_trucks, n_shelters, vtype=GRB.CONTINUOUS, lb=0, name="q")

# ----- Objective: minimize total travel time -----
model.setObjective(gp.quicksum(t[i][j] * x[i, j, k, h]
                    for i in range(n_shelters) for j in range(n_shelters)
                    for k in range(n_trucks) for h in range(n_shelters)), GRB.MINIMIZE)

# ----- Constraints -----
# 1. Exactly 10 hubs
model.addConstr(y.sum() == n_hubs, "num_hubs")

# 2. Demand satisfaction for non-hubs
for i in range(n_shelters):
    model.addConstr(
        gp.quicksum(q[i, k, h] for k in range(n_trucks) for h in range(n_shelters)) == demand_per_shelter * (1 - y[i]),
        f"demand_{i}")

# 3. No delivery to hubs
for i in range(n_shelters):
    for k in range(n_trucks):
        for h in range(n_shelters):
            model.addConstr(q[i, k, h] <= demand_per_shelter * (1 - y[i]), f"no_delivery_to_hubs_{i}{k}{h}")

# 4. Truck capacity
for h in range(n_shelters):
    for k in range(n_trucks):
        model.addConstr(gp.quicksum(q[i, k, h] for i in range(n_shelters)) <= truck_capacity * y[h],
                        f"truck_capacity_{h}_{k}")

# 5. Start and end at hub
for h in range(n_shelters):
    for k in range(n_trucks):
        model.addConstr(gp.quicksum(x[h, j, k, h] for j in range(n_shelters) if j != h) == y[h], f"start_{h}_{k}")
        model.addConstr(gp.quicksum(x[i, h, k, h] for i in range(n_shelters) if i != h) == y[h], f"end_{h}_{k}")

# 6. Routing only if hub is selected
for i in range(n_shelters):
    for j in range(n_shelters):
        for k in range(n_trucks):
            for h in range(n_shelters):
                model.addConstr(x[i, j, k, h] <= y[h], f"route_hub_active_{i}{j}{k}_{h}")

# ----- Solve -----
model.setParam('OutputFlag', 1)
model.optimize()