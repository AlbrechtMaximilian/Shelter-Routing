def greedy_nn_capacity(S, distance, demand, capacity, speed, unload_t, launch_cost):
    rem = demand.copy()
    routes = []

    while any(rem[i] > 0 for i in S if i != 0):
        load = 0
        pos  = 0
        route = [0]

        while True:
            # 找最近且裝得下的點
            cand = [j for j in S if j != 0 and rem[j] > 0 and rem[j] <= capacity - load]
            if not cand:
                break
            j = min(cand, key=lambda n: distance[(pos, n)])
            route.append(j)
            load += rem[j]
            rem[j] = 0
            pos = j

        route.append(0)
        routes.append(route)

    # --- 計算成本 ---
    drive = sum(distance[(route[k], route[k+1])]/speed*60
                for route in routes
                for k in range(len(route)-1))

    unload = unload_t * sum(demand[i] for i in demand)
    obj = drive + unload + launch_cost * len(routes)
    return routes, obj
