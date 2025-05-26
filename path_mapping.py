import pandas as pd
import shapely.geometry as geom
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D


def plot_shelter_trips(excel_path, vehicle_routes):
    """
    Reads shelter coordinates from an Excel file (sheet 'Coordinates') and plots
    all shelters and the given vehicle routes without fetching external basemap tiles.

    Supported 'Coordinates' sheet formats:
      • Columns ['shelter_id' or 'node_id', 'Longitude' & 'Latitude']
      • Columns ['shelter_id' or 'node_id', 'x' & 'y']
      • Columns ['shelter_id' or 'node_id', 'coordinates'] where each entry is a
        string like "[lon, lat]".

    Args:
        excel_path (str): Path to the Excel file.
        vehicle_routes (dict): Mapping from vehicle_id to list of trips,
            each trip is a list of node indices starting and ending at the hub (0).

    Returns:
        gdf_trip_legs (GeoDataFrame): LineString geometries of each trip leg.
        gdf_shelters  (GeoDataFrame): Point geometries of all shelters.
    """
    # 1) load coordinates
    df = pd.read_excel(excel_path, sheet_name='Coordinates')
    cols = {c.lower(): c for c in df.columns}

    # identify ID column
    if 'shelter_id' in cols:
        id_col = cols['shelter_id']
    elif 'node_id' in cols:
        id_col = cols['node_id']
    else:
        raise KeyError(
            f"'Coordinates' sheet must have 'shelter_id' or 'node_id' column; found: {list(df.columns)}"
        )

    # detect coordinate columns
    if 'longitude' in cols and 'latitude' in cols:
        df['Longitude'] = df[cols['longitude']].astype(float)
        df['Latitude'] = df[cols['latitude']].astype(float)
    elif 'x' in cols and 'y' in cols:
        df['Longitude'] = df[cols['x']].astype(float)
        df['Latitude'] = df[cols['y']].astype(float)
    elif 'coordinates' in cols:
        df[['Longitude','Latitude']] = (
            df[cols['coordinates']]
              .astype(str)
              .str.strip('[]() ')
              .str.split(',', expand=True)
              .astype(float)
        )
    else:
        raise KeyError(
            f"'Coordinates' sheet must have either 'Longitude' & 'Latitude', 'x' & 'y', or 'coordinates'; found: {list(df.columns)}"
        )

    # set index to shelter_id
    df = df.rename(columns={id_col: 'shelter_id'}).set_index('shelter_id')

    # 2) build trip legs
    legs = []
    for vid, routes in vehicle_routes.items():
        for trip_idx, route in enumerate(routes):
            for i in range(len(route) - 1):
                o, d = route[i], route[i+1]
                if o not in df.index or d not in df.index:
                    continue
                olon, olat = df.loc[o, ['Longitude', 'Latitude']]
                dlon, dlat = df.loc[d, ['Longitude', 'Latitude']]
                legs.append({
                    'vehicle_id': vid,
                    'trip_id': f"{vid}_{trip_idx}",
                    'origin': o,
                    'destination': d,
                    'Origin Lon': olon,
                    'Origin Lat': olat,
                    'Destination Lon': dlon,
                    'Destination Lat': dlat,
                })
    df_legs = pd.DataFrame(legs)

    # 3) GeoDataFrame of lines
    df_legs['geometry'] = df_legs.apply(
        lambda r: geom.LineString([
            geom.Point(r['Origin Lon'], r['Origin Lat']),
            geom.Point(r['Destination Lon'], r['Destination Lat'])
        ]),
        axis=1
    )
    gdf_trip_legs = gpd.GeoDataFrame(df_legs, geometry='geometry', crs='EPSG:4326')

    # 4) GeoDataFrame of points
    gdf_shelters = gpd.GeoDataFrame(
        df.reset_index().rename(columns={'shelter_id': 'shelter_id'}),
        geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']),
        crs='EPSG:4326'
    )

    # 5) plotting on square canvas with padded x-axis
    fig, ax = plt.subplots(figsize=(8, 8))

    # plot all shelters in light grey
    gdf_shelters.plot(ax=ax, color='lightgrey', markersize=30, alpha=0.6)

    # highlight non-hub shelters in blue
    mask_hub = gdf_shelters['shelter_id'] == 0
    others = gdf_shelters[~mask_hub]
    others.plot(ax=ax, color='blue', markersize=60, alpha=0.8, label='Shelter')

    # highlight hub in green star
    if mask_hub.any():
        hub = gdf_shelters[mask_hub]
        hub.plot(ax=ax, color='green', marker='*', markersize=250, label='Shelter 0 (Hub)')

    # plot trip legs by vehicle color
    vehicles = sorted(gdf_trip_legs['vehicle_id'].unique())
    palette = plt.cm.get_cmap('tab20', len(vehicles))
    color_map = {v: palette(i) for i, v in enumerate(vehicles)}
    for vid in vehicles:
        subset = gdf_trip_legs[gdf_trip_legs['vehicle_id'] == vid]
        subset.plot(ax=ax, color=color_map[vid], linewidth=2, alpha=0.8,
                    label=f'Vehicle {vid}')

        # compute full data extents
    xs = [pt.x for pt in gdf_shelters.geometry]
    ys = [pt.y for pt in gdf_shelters.geometry]
    for line in gdf_trip_legs.geometry:
        xs.extend([coord[0] for coord in line.coords])
        ys.extend([coord[1] for coord in line.coords])
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    # ensure equal numeric spans on both axes
    lon_span = maxx - minx
    lat_span = maxy - miny
    span = max(lon_span, lat_span)
    lon_center = (minx + maxx) / 2
    lat_center = (miny + maxy) / 2
    half = span / 2
    ax.set_xlim(lon_center - half, lon_center + half)
    ax.set_ylim(lat_center - half, lat_center + half)
    # enforce equal aspect for square representation
    ax.set_aspect('equal', adjustable='box')

    # build legend
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='upper left', title='Legend')

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Shelter Locations & Vehicle Trip Paths')

    plt.tight_layout()
    plt.show()

    return gdf_trip_legs, gdf_shelters
