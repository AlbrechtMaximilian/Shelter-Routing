import os
import math
import numpy as np
import pandas as pd
from datetime import datetime

def instance_generator(num_instances=30):
    """
    Generates 9 OFAT scenarios × num_instances Excel files with sheets:
      • Params: S_size, V_size, capacity, speed, unload_t, T_max
      • Demand: node_id → demand
      • Distance: full S×S matrix
    """
    # hard-coded params
    base_speed = 60       # km/h
    base_unload = 10      # min per ton

    # --- level definitions ---
    shelters = {'low':4, 'med':6, 'high':10}
    vehicles = {'low':1,  'med':3,  'high':4}
    capacity = {'low':5, 'med':20, 'high':30}
    def d_low(n):        return np.random.randint(1,11, size=n)
    def d_med(n):        return np.random.randint(10,51, size=n)
    def d_high(n, cap):  return np.random.randint(math.floor(0.8*cap), cap+1, size=n)

    # 9 OFAT scenarios: (A,B,C,D)
    scenarios = [
      ('med','med','med','med'),
      ('low','med','med','med'),
      ('high','med','med','med'),
      ('med','low','med','med'),
      ('med','high','med','med'),
      ('med','med','low','med'),
      ('med','med','high','med'),
      ('med','med','med','low'),
      ('med','med','med','high'),
    ]

    # make base folder
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = f"instances_{ts}"
    os.makedirs(base, exist_ok=True)
    print(f"Created base folder: {base}")

    for idx, (A,B,C,D) in enumerate(scenarios, 1):
        scen_dir = os.path.join(base, f"scenario_{idx}")
        os.makedirs(scen_dir, exist_ok=True)

        nS = shelters[A]
        nV = vehicles[B]
        cap = capacity[C]

        for inst in range(1, num_instances+1):
            # coords + dist matrix
            coords = np.random.rand(nS+1,2)*100
            dist = np.linalg.norm(coords[:,None,:] - coords[None,:,:], axis=2)

            # demands
            if D=='low':
                vals = d_low(nS)
            elif D=='med':
                vals = d_med(nS)
            else:
                vals = d_high(nS, cap)
            demand = {i+1: float(vals[i]) for i in range(nS)}

            # compute T_max
            Dtot = sum(demand.values())
            T_max = math.ceil(Dtot / (cap * nV))

            # build DataFrames
            params = pd.DataFrame({
              'param': ['S_size','V_size','capacity','speed','unload_t','T_max'],
              'value': [nS+1, nV, cap, base_speed, base_unload, T_max]
            })
            dem_df = pd.DataFrame.from_dict(demand, orient='index', columns=['demand'])
            dem_df.index.name = 'node_id'
            dist_df = pd.DataFrame(dist, index=range(nS+1), columns=range(nS+1))

            # write Excel
            path = os.path.join(scen_dir, f"scenario_{idx}_instance_{inst}.xlsx")
            with pd.ExcelWriter(path) as w:
                params.to_excel(w, sheet_name='Params', index=False)
                dem_df.to_excel(w, sheet_name='Demand')
                dist_df.to_excel(w, sheet_name='Distance')

        print(f"  → Completed scenario {idx} ({A},{B},{C},{D})")

    print("All scenarios generated.")

# call the generator
if __name__ == "__main__":
    instance_generator(num_instances=30)