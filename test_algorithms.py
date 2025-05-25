from run_experiments import load_instance

# just load—no solve_routing call!
S, V, distance, demand, capacity, speed, unload_t = load_instance("scenario_1_instance_1.xlsx")

print("Nodes:", list(S))
print("Vehicles:", list(V))
print("Capacity:", capacity)
print("Speed:", speed)
print("Unload per ton:", unload_t)
print("First 5 demands:", {k:demand[k] for k in list(demand)[:5]})
print("Distance(0→1):", distance[(0,1)])

