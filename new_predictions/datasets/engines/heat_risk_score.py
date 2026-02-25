import pandas as pd
import numpy as np
from pathlib import Path

# -----------------------------
# Haversine Distance Function
# -----------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


# -----------------------------
# Heat Risk Function
# -----------------------------
def calculate_heat_risk(property_lat, property_lon):

    BASE_DIR = Path(__file__).resolve().parents[1]
    DATA_DIR = BASE_DIR / "processed"

    df = pd.read_csv(DATA_DIR / "india_heat_with_risk_score.csv")

    # Compute distance to all grid points
    df["distance_km"] = haversine(
        property_lat,
        property_lon,
        df["latitude"],
        df["longitude"]
    )

    # Find nearest grid point
    nearest = df.loc[df["distance_km"].idxmin()]

    return round(min(nearest["heat_score"] * 1.25, 25), 2)


# -----------------------------
# Manual Test Input
# -----------------------------
# lat = float(input("Enter Latitude: "))
# lon = float(input("Enter Longitude: "))

# risk = calculate_heat_risk(lat, lon)

# print("🔥 Heat Risk Score (0–25):", risk)
