import pandas as pd
import matplotlib.pyplot as plt

def plot_shelter_coordinates(excel_path):
    """
    Plots the depot and shelter locations from an Excel instance file.

    Args:
        excel_path (str): Path to the Excel file containing the 'Coordinates' sheet.
    """
    # Lade die Koordinaten
    coords_df = pd.read_excel(excel_path, sheet_name='Coordinates', index_col=0)

    # Trenne Depot (node 0) und Shelter
    depot = coords_df.loc[0]
    shelters = coords_df.drop(index=0)

    # Erzeuge Plot
    plt.figure(figsize=(8, 6))
    plt.scatter(shelters['x'], shelters['y'], c='blue', label='Shelters', alpha=0.7)
    plt.scatter(depot['x'], depot['y'], c='red', label='Depot', marker='X', s=100)
    plt.title("Shelter and Depot Locations")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True)
    plt.legend()
    plt.axis("equal")

    # Versuche Anzeige, alternativ Speichern
    try:
        plt.switch_backend('TkAgg')  # Wechsel auf zuverlässiges Fenster-Backend
        plt.show()
    except Exception as e:
        print("Plot display failed (likely due to PyCharm backend).")
        fallback_path = "shelter_plot_fallback.png"
        plt.savefig(fallback_path, dpi=150)
        print(f"Plot saved as fallback image: {fallback_path}")

if __name__ == "__main__":
    plot_shelter_coordinates("instances_20250526_143435/scenario_9/scenario_9_instance_1.xlsx")