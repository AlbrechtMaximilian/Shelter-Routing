import numpy as np
import pandas as pd
import os
import math
from datetime import datetime

def instance_generator_comparison(num_instances=3):
    """
    Generates 4 scenarios (with increasing shelter counts) × num_instances Excel files.
    Includes: Params, Demand, Distance, Coordinates.
    Shelter counts: low, medium, medium-high, high.
    """
    base_speed = 60
    base_unload = 10

    shelters = {'low': 10, 'med': 50, 'med_high': 200, 'high': 500}
    vehicles = 3
    capacity = 20

    def d_med(n): return np.random.randint(10, 51, size=n)

    scenarios = [
        ('low',),
        ('med',),
        ('med_high',),
        ('high',),
    ]

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = f"heuristic_instances_{ts}"
    os.makedirs(base, exist_ok=True)
    print(f"Created base folder: {base}")

    for idx, (A,) in enumerate(scenarios, 1):
        scen_dir = os.path.join(base, f"scenario_{idx}")
        os.makedirs(scen_dir, exist_ok=True)

        nS = shelters[A]
        nV = vehicles
        cap = capacity

        for inst in range(1, num_instances + 1):
            # Coordinates with medium clustering
            k = max(3, nS // 4)
            centers = np.random.rand(k, 2) * 100
            coords = [np.random.normal(loc=centers[i % k], scale=5, size=2) for i in range(nS)]
            depot = np.array([[50.0, 50.0]])
            coords = np.vstack([depot, coords])

            dist = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)
            vals = d_med(nS)
            demand = {i + 1: float(vals[i]) for i in range(nS)}
            Dtot = sum(demand.values())
            T_max = math.ceil(Dtot / (cap * nV))

            params = pd.DataFrame({
                'param': ['S_size', 'V_size', 'capacity', 'speed', 'unload_t', 'T_max'],
                'value': [nS + 1, nV, cap, base_speed, base_unload, T_max]
            })
            dem_df = pd.DataFrame.from_dict(demand, orient='index', columns=['demand'])
            dem_df.index.name = 'node_id'
            dist_df = pd.DataFrame(dist, index=range(nS + 1), columns=range(nS + 1))
            coords_df = pd.DataFrame(coords, columns=['x', 'y'])
            coords_df.index.name = 'node_id'

            path = os.path.join(scen_dir, f"scenario_{idx}_instance_{inst}.xlsx")
            with pd.ExcelWriter(path) as w:
                params.to_excel(w, sheet_name='Params', index=False)
                dem_df.to_excel(w, sheet_name='Demand')
                dist_df.to_excel(w, sheet_name='Distance')
                coords_df.to_excel(w, sheet_name='Coordinates')

        print(f"  → Completed scenario {idx} with {nS} shelters")

    print("All comparison scenarios generated.")

if __name__ == "__main__":
    instance_generator_comparison(num_instances=10)