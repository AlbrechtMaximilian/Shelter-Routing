import math
import time
import pandas as pd

def nearest_neighbor_heuristic(S, V_count, distance_matrix, demand_dict, capacity, speed, unload_t_per_unit):
    t0 = time.time()
    """
    Implements a Nearest Neighbor heuristic for the Vehicle Routing Problem.
    V_count is the number of available physical vehicles, which are assumed to be reusable
    for subsequent trips. The heuristic builds trips sequentially.

    Args:
        S (range or list): Set of all nodes, including the depot (assumed to be 0).
        V_count (int): Number of available physical vehicles (must be > 0).
        distance_matrix (dict): Dictionary where keys are (from_node, to_node) tuples
                                and values are distances.
        demand_dict (dict): Dictionary where keys are customer nodes and values are their demands.
                            Node 0 (depot) should not be in demand_dict or have 0 demand.
        capacity (float): Capacity of each vehicle.
        speed (float): Speed of vehicles (distance unit per hour).
        unload_t_per_unit (float): Time in minutes to unload one unit of demand.

    Returns:
        tuple: (list_of_routes, total_travel_time, total_unload_time, total_objective_value)
               - list_of_routes: A list of lists, where each inner list represents a route (trip).
               - total_travel_time: Total time spent traveling for all routes in minutes.
               - total_unload_time: Total time spent unloading for all routes in minutes.
               - total_objective_value: Sum of travel and unload time.
    """

    """if V_count <= 0:
        print("Error: V_count (number of physical vehicles) must be positive for the heuristic to run.")
        return [], 0, 0, 0"""

    # --- Helper function to calculate travel time ---
    def get_travel_time(node1, node2):
        dist = distance_matrix.get((node1, node2), float('inf'))
        if dist == float('inf'):
            print(f"Warning: No direct distance found in distance_matrix for ({node1}, {node2}). Assuming unreachable.")
        return (dist / speed) * 60  # Time in minutes

    # --- Initialization ---
    customers = [node for node in S if node != 0 and node in demand_dict and demand_dict[node] > 1e-6]
    unvisited_customers = set(customers)
    remaining_demand = demand_dict.copy()

    routes = []
    total_travel_time = 0
    total_unload_time = 0

    trips_made_count = 0 # Counter for total trips made

    # --- Main loop: Continue until all customers are visited ---
    # Assumes the V_count vehicles are reused for these sequential trips.
    while unvisited_customers:
        trips_made_count += 1

        current_route = [0]
        current_load = 0
        current_location = 0

        route_travel_time = 0
        route_unload_time = 0

        print(f"\nStarting Trip {trips_made_count} from depot (using one of {V_count} reusable vehicles).")

        while True: # Loop for building a single trip
            best_next_customer = None
            min_distance_to_next = float('inf')

            for customer_node in unvisited_customers:
                if remaining_demand.get(customer_node, 0) > 1e-6:
                    dist = distance_matrix.get((current_location, customer_node), float('inf'))

                    if dist < min_distance_to_next:
                        if current_load < capacity - 1e-6:
                            min_distance_to_next = dist
                            best_next_customer = customer_node

            if best_next_customer is not None:
                travel_to_next_time = get_travel_time(current_location, best_next_customer)
                route_travel_time += travel_to_next_time
                total_travel_time += travel_to_next_time

                current_location = best_next_customer
                current_route.append(current_location)

                can_unload = capacity - current_load
                demand_at_customer = remaining_demand[current_location]
                unloaded_amount = min(can_unload, demand_at_customer)

                current_load += unloaded_amount
                remaining_demand[current_location] -= unloaded_amount

                unload_for_customer_time = unload_t_per_unit * unloaded_amount
                route_unload_time += unload_for_customer_time
                total_unload_time += unload_for_customer_time

                print(f"  Visited {current_location}. Delivered: {unloaded_amount:.2f}. "
                      f"Current load: {current_load:.2f}/{capacity}. "
                      f"Remaining demand for {current_location}: {remaining_demand[current_location]:.2f}")

                if remaining_demand[current_location] <= 1e-6:
                    unvisited_customers.remove(current_location)
                    print(f"  Customer {current_location} fully served.")

                if current_load >= capacity - 1e-6 or not unvisited_customers:
                    print(f"  Vehicle full or all customers (globally) served.")
                    break
            else:
                print(f"  No suitable next customer for this trip from {current_location} (check capacity/reachability).")
                break

        if current_location != 0:
            travel_to_depot_time = get_travel_time(current_location, 0)
            route_travel_time += travel_to_depot_time
            total_travel_time += travel_to_depot_time
            current_route.append(0)

        if len(current_route) > 2:
            routes.append(current_route)
            print(f"Trip {trips_made_count} completed: {current_route}")
            print(f"  Trip travel time: {route_travel_time:.2f} min, Trip unload time: {route_unload_time:.2f} min")
        elif len(current_route) <= 2 and current_location == 0 :
            print(f"Trip {trips_made_count}: No customers served (stayed at depot or empty trip).")

        if not unvisited_customers:
            print("\nAll customers have been served.")
            break

    # --- After the main loop ---
    if unvisited_customers: # Should ideally not happen if all customers are reachable and have demand
        print(f"\nHeuristic finished. Some customers may remain unvisited due to reachability/logic issues.")
        print(f"Unvisited customers with remaining demand:")
        for customer_node in sorted(list(unvisited_customers)):
            if remaining_demand.get(customer_node, 0) > 1e-6:
                print(f"  Customer {customer_node}: Remaining Demand {remaining_demand[customer_node]:.2f}")

    total_objective_value = total_travel_time + total_unload_time
    print("\n--- Heuristic Results ---")
    print(f"Fleet Size (V_count): {V_count} reusable vehicles.")
    print(f"Routes: {routes}")
    print(f"Total Trips Made: {trips_made_count}")
    print(f"Total Travel Time: {total_travel_time:.2f} minutes")
    print(f"Total Unload Time: {total_unload_time:.2f} minutes")
    print(f"Total Objective Value (Travel + Unload): {total_objective_value:.2f}")
    print(time.time() - t0)
    return routes, total_travel_time, total_unload_time, total_objective_value


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
    S, V, distance, demand, capacity, speed, unload_t = load_instance("instances_20250526_113426/scenario_3/scenario_3_instance_1.xlsx")
    nearest_neighbor_heuristic(S, V, distance, demand, capacity, speed, unload_t)
