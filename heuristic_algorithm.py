import math
import time
import pandas as pd
import matplotlib.pyplot as plt  # For bar chart


def nearest_neighbor_heuristic(S, V_count, distance_matrix, demand_dict, capacity, speed, unload_t_per_unit):
    t0 = time.time()
    """
    Implements a Nearest Neighbor heuristic for the Vehicle Routing Problem.
    V_count is the number of available physical vehicles, which are assumed to be reusable
    for subsequent trips. The heuristic builds trips sequentially.

    Args:
        S (range or list): Set of all nodes, including the depot (assumed to be 0).
        V_count (int or range): Number of available physical vehicles (must be > 0). 
                                 In current usage, this is passed as range(V_size).
        distance_matrix (dict): Dictionary where keys are (from_node, to_node) tuples
                                and values are distances.
        demand_dict (dict): Dictionary where keys are customer nodes and values are their demands.
                            Node 0 (depot) should not be in demand_dict or have 0 demand.
        capacity (float): Capacity of each vehicle.
        speed (float): Speed of vehicles (distance unit per hour).
        unload_t_per_unit (float): Time in minutes to unload one unit of demand.

    Returns:
        tuple: (total_objective_value, comp_time)
               - total_objective_value: Sum of travel and unload time.
               - comp_time: Computation time for the heuristic.
    """

    # --- Helper function to calculate travel time ---
    def get_travel_time(node1, node2):
        dist = distance_matrix.get((node1, node2), float('inf'))
        if dist == float('inf'):
            # This warning can be noisy if called many times during chart generation
            # For chart generation, we might assume valid routes from heuristic output
            # print(f"Warning: No direct distance found in distance_matrix for ({node1}, {node2}). Assuming unreachable.")
            pass  # Suppress warning during chart's recalculation, rely on heuristic's earlier warnings
        return (dist / speed) * 60  # Time in minutes

    # --- Initialization ---
    customers = [node for node in S if node != 0 and node in demand_dict and demand_dict[node] > 1e-6]
    unvisited_customers = set(customers)
    remaining_demand = demand_dict.copy()

    routes = []
    total_travel_time = 0  # This is the grand total travel time for the objective
    total_unload_time = 0

    trips_made_count = 0

    # --- Main loop: Continue until all customers are visited ---
    while unvisited_customers:
        trips_made_count += 1

        current_route = [0]
        current_load = 0
        current_location = 0

        route_travel_time = 0  # Travel time for the current trip being built
        route_unload_time = 0

        num_physical_vehicles_for_print = 0
        if isinstance(V_count, range):
            num_physical_vehicles_for_print = len(V_count)
        elif isinstance(V_count, int):
            num_physical_vehicles_for_print = V_count
        else:
            try:
                num_physical_vehicles_for_print = len(V_count)
            except:
                num_physical_vehicles_for_print = V_count

        print(
            f"\nStarting Trip {trips_made_count} from depot (using one of {num_physical_vehicles_for_print} reusable vehicles).")

        while True:
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
                # Use a local variable for this segment's travel time to add to route_travel_time
                segment_travel_time = get_travel_time(current_location, best_next_customer)
                route_travel_time += segment_travel_time
                # total_travel_time is the grand total, accumulated here
                # total_travel_time += segment_travel_time # This was in original, keep it for objective function

                current_location = best_next_customer
                current_route.append(current_location)

                can_unload = capacity - current_load
                demand_at_customer = remaining_demand[current_location]
                unloaded_amount = min(can_unload, demand_at_customer)

                current_load += unloaded_amount
                remaining_demand[current_location] -= unloaded_amount

                unload_for_customer_time = unload_t_per_unit * unloaded_amount
                route_unload_time += unload_for_customer_time
                # total_unload_time += unload_for_customer_time # This was in original, keep it

                print(f"  Visited {current_location}. Delivered: {unloaded_amount:.2f}. "
                      f"Current load: {current_load:.2f}/{capacity}. "
                      f"Remaining demand for {current_location}: {remaining_demand[current_location]:.2f}")

                if remaining_demand[current_location] <= 1e-6:
                    unvisited_customers.remove(current_location)
                    print(f"  Customer {current_location} fully served.")

                if current_load >= capacity - 1e-6 or not unvisited_customers:
                    print(f"  Vehicle capacity reached or all customers globally served for this trip leg.")
                    break
            else:
                print(
                    f"  No suitable next customer for this trip from {current_location} (check capacity/reachability/unvisited status).")
                break

        if current_location != 0:
            segment_travel_time_to_depot = get_travel_time(current_location, 0)
            route_travel_time += segment_travel_time_to_depot
            # total_travel_time += segment_travel_time_to_depot # Original accumulation
            current_route.append(0)

        # Accumulate total travel and unload times for the objective function from completed trips
        if len(current_route) > 2:
            routes.append(current_route)
            total_travel_time += route_travel_time  # Accumulate this trip's travel time to grand total
            total_unload_time += route_unload_time  # Accumulate this trip's unload time to grand total
            print(f"Trip {trips_made_count} completed: {current_route}")
            print(f"  Trip travel time: {route_travel_time:.2f} min, Trip unload time: {route_unload_time:.2f} min")
        elif len(current_route) <= 2 and current_location == 0:
            print(f"Trip {trips_made_count}: No customers served (stayed at depot or empty trip).")

        if not unvisited_customers:
            print("\nAll customers have been served.")
            break

            # --- After the main loop ---
    if unvisited_customers:
        print(f"\nHeuristic finished. Some customers may remain unvisited due to reachability/logic issues.")
        print(f"Unvisited customers with remaining demand:")
        for customer_node in sorted(list(unvisited_customers)):
            if remaining_demand.get(customer_node, 0) > 1e-6:
                print(f"  Customer {customer_node}: Remaining Demand {remaining_demand[customer_node]:.2f}")

    # total_objective_value is calculated based on the grand total_travel_time and total_unload_time
    total_objective_value = total_travel_time + total_unload_time
    comp_time = time.time() - t0

    print("\n--- Heuristic Results ---")
    actual_num_vehicles = V_count
    if isinstance(V_count, range):
        actual_num_vehicles = len(V_count)
    print(f"Fleet Size (V_count interpreted as): {actual_num_vehicles} reusable vehicles.")
    print(f"Routes (all trips): {routes}")
    print(f"Total Trips Made: {trips_made_count}")
    print(f"Total Travel Time (Overall): {total_travel_time:.2f} minutes")
    print(f"Total Unload Time (Overall): {total_unload_time:.2f} minutes")
    print(f"Total Objective Value (Travel + Unload): {total_objective_value:.2f}")
    print(f"Computation Time: {comp_time:.4f} seconds")

    # --- Code for dictionary output for vehicle 1 to 5 ---
    num_physical_vehicles = 0
    if isinstance(V_count, range):
        num_physical_vehicles = len(V_count)
    elif isinstance(V_count, int):
        num_physical_vehicles = V_count
    else:
        try:
            num_physical_vehicles = len(V_count)
        except TypeError:
            print(
                "Warning: V_count is of an unexpected type. Could not determine number of physical vehicles for route assignment dictionary.")
            num_physical_vehicles = 0

    vehicle_trip_assignments = {}
    if num_physical_vehicles > 0:
        for i in range(1, num_physical_vehicles + 1):
            vehicle_trip_assignments[f"vehicle_{i}"] = []

        if routes:
            for trip_idx, trip_route_nodes in enumerate(routes):  # trip_route_nodes is list of nodes
                assigned_vehicle_num = (trip_idx % num_physical_vehicles) + 1
                vehicle_key = f"vehicle_{assigned_vehicle_num}"
                vehicle_trip_assignments[vehicle_key].append(trip_route_nodes)

    output_vehicle_routes_for_1_to_5 = {}  # Stores node sequences for each vehicle
    for i in range(1, 6):
        target_vehicle_key = f"vehicle_{i}"
        output_vehicle_routes_for_1_to_5[target_vehicle_key] = vehicle_trip_assignments.get(target_vehicle_key, [])

    print("\n--- Route Assignments for Vehicles 1-5 (Node Sequences) ---")
    for i in range(1, 6):
        key = f"vehicle_{i}"
        print(f"{key}: {output_vehicle_routes_for_1_to_5[key]}")
    # --- End code for dictionary output ---

    try:
        vehicle_ids_for_chart = list(output_vehicle_routes_for_1_to_5.keys())

        # Data preparation for individual trip times and total times per vehicle
        vehicle_individual_trip_times = {}
        vehicle_total_times_for_ylim_and_text = {}

        for vehicle_id in vehicle_ids_for_chart:
            vehicle_routes_nodes = output_vehicle_routes_for_1_to_5[vehicle_id]
            list_of_single_trip_times = []
            current_vehicle_total_for_this_vehicle = 0.0
            for trip_node_sequence in vehicle_routes_nodes:
                single_trip_travel_time = 0.0
                if len(trip_node_sequence) > 1:
                    for i_segment in range(len(trip_node_sequence) - 1):
                        node_from = trip_node_sequence[i_segment]
                        node_to = trip_node_sequence[i_segment + 1]
                        single_trip_travel_time += get_travel_time(node_from, node_to)
                list_of_single_trip_times.append(single_trip_travel_time)
                current_vehicle_total_for_this_vehicle += single_trip_travel_time
            vehicle_individual_trip_times[vehicle_id] = list_of_single_trip_times
            vehicle_total_times_for_ylim_and_text[vehicle_id] = current_vehicle_total_for_this_vehicle

        # Check if there's anything to plot
        all_plottable_trip_times = [
            time for v_id in vehicle_ids_for_chart
            for time in vehicle_individual_trip_times.get(v_id, []) if time > 1e-6
        ]
        if not all_plottable_trip_times:
            print("\nNo significant travel time for any trips of vehicles 1-5, skipping stacked bar chart generation.")
        else:
            plt.figure(figsize=(15, 8))

            # Select a color palette. 'tab20' provides 20 reasonably distinct colors.
            # Colors will cycle if total unique trips exceed palette size.
            color_palette = list(plt.cm.get_cmap('tab20').colors)
            if not color_palette:  # Fallback if colormap loading fails or is empty
                color_palette = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black']

            global_segment_idx = 0  # Global counter for uniquely coloring each trip segment

            max_overall_total_time_for_ylim = 0
            if vehicle_total_times_for_ylim_and_text:
                max_overall_total_time_for_ylim = max(
                    vehicle_total_times_for_ylim_and_text.values()) if vehicle_total_times_for_ylim_and_text else 0

            for i, vehicle_id in enumerate(vehicle_ids_for_chart):
                trip_times = vehicle_individual_trip_times.get(vehicle_id, [])
                current_bottom = 0

                for trip_idx, trip_time in enumerate(trip_times):
                    if trip_time > 1e-6:
                        # Assign a color to this segment from the global sequence
                        current_segment_color = color_palette[global_segment_idx % len(color_palette)]

                        plt.bar(vehicle_id, trip_time, bottom=current_bottom,
                                color=current_segment_color,
                                edgecolor='black',
                                linewidth=0.7,
                                zorder=2)
                        global_segment_idx += 1  # Increment for the next unique segment across all vehicles
                    current_bottom += trip_time

                # Add text for the total time on top of this vehicle's stacked bar
                vehicle_total_trip_time_for_text = vehicle_total_times_for_ylim_and_text.get(vehicle_id, 0.0)
                if vehicle_total_trip_time_for_text > 1e-6:
                    text_offset = max_overall_total_time_for_ylim * 0.015 if max_overall_total_time_for_ylim > 0 else 0.2
                    plt.text(vehicle_id, vehicle_total_trip_time_for_text + text_offset,
                             f'{vehicle_total_trip_time_for_text:.2f}',
                             ha='center', va='bottom', fontsize=9, fontweight='bold', zorder=3)

            plt.xlabel("Vehicle ID", fontsize=12)
            plt.ylabel("Travel Time (minutes) - Stacked per Trip", fontsize=12)
            plt.title("Individual Trip Travel Times (Globally Colored Segments) per Vehicle", fontsize=14, pad=20)
            plt.xticks(rotation=0)
            plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=1)

            # A legend for individual (globally unique) trip segment colors is impractical
            # if there are many trips. The coloring itself provides the distinction.

            if max_overall_total_time_for_ylim > 0:
                plt.ylim(0, max_overall_total_time_for_ylim * 1.20)

            print("\nDisplaying stacked bar chart with globally distinct colored segments for travel time per trip...")
            plt.tight_layout()
            plt.show()

    except ImportError:
        print(
            "\nMatplotlib library not found. Skipping stacked bar chart generation. Please install it (e.g., `pip install matplotlib`).")
    except Exception as e:
        print(f"\nAn error occurred during stacked bar chart generation: {e}. Skipping chart.")
        # --- END MODIFIED CODE ---

    return total_objective_value, comp_time
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
    dist_df = pd.read_excel(path, sheet_name="Distance", index_col=0)

    # parse params
    p = params_df.set_index("param")["value"].to_dict()
    S_size = int(p["S_size"])
    V_size = int(p["V_size"])
    capacity = float(p["capacity"])
    speed = float(p["speed"])
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
    try:
        S_nodes, V_vehicles_range, distances, demands, cap, spd, unload_time_per_unit = load_instance("real_data.xlsx")
        nearest_neighbor_heuristic(S_nodes, V_vehicles_range, distances, demands, cap, spd, unload_time_per_unit)
    except FileNotFoundError:
        print("Error: 'real_data.xlsx' not found. Please ensure the file exists in the correct location.")
    except ImportError:
        print("Error: A required library (like pandas or matplotlib) might be missing. Please check your environment.")
    except Exception as e:
        print(f"An error occurred during execution: {e}")