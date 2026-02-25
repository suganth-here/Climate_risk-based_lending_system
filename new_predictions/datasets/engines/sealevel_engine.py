import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "processed"

# -----------------------------
# Haversine Distance Function
# -----------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)

    a = (np.sin(dlat/2) ** 2 +
         np.cos(np.radians(lat1)) *
         np.cos(np.radians(lat2)) *
         np.sin(dlon/2) ** 2)

    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


# -----------------------------
# Sea Level Risk Function
# -----------------------------
def calculate_sea_risk(property_lat, property_lon):

    # Load coastline dataset
    df = pd.read_csv(DATA_DIR / "coastline_points.csv")  # <-- change filename if needed

    # Compute distance from property to all coastline points
    df["distance_km"] = haversine(
        property_lat,
        property_lon,
        df["latitude"],
        df["longitude"]
    )

    # Find nearest coastline distance
    min_distance = df["distance_km"].min()

    # Linear sea risk calculation (0–10 scale)
    sea_score = 15 * (1 - (min_distance / 100))

    # Clamp between 0 and 10
    sea_score = max(0, min(sea_score, 15))

    return round(sea_score, 2)


# -----------------------------
# Manual Test
# -----------------------------
# lat = float(input("Enter Latitude: "))
# lon = float(input("Enter Longitude: "))

# risk = calculate_sea_risk(lat, lon)

# print("🌊 Sea Level Risk Score (0–15):", risk)
