import pandas as pd
import numpy as np
from pathlib import Path

# -----------------------------
# 1️⃣ Haversine Distance Function
# -----------------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


# -----------------------------
# 2️⃣ Cyclone Risk Function
# -----------------------------
def calculate_cyclone_risk(property_lat, property_lon, target_year=2050):

    # Load dataset
    csv_path = Path(__file__).resolve().parents[1] / "processed" / "india_cyclones_with_projection_till_2050.csv"
    df = pd.read_csv(csv_path)
    # Filter till selected horizon
    df = df[df["year"] <= target_year]

    # Convert numeric
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["wind_kts"] = pd.to_numeric(df["wind_kts"], errors="coerce")

    df = df.dropna()

    # -----------------------------
    # 3️⃣ Calculate distance
    # -----------------------------
    df["distance_km"] = haversine(
        property_lat,
        property_lon,
        df["latitude"],
        df["longitude"]
    )

    # -----------------------------
    # 4️⃣ Filter exposures (100 km radius)
    # -----------------------------
    exposure_radius = 100
    exposures = df[df["distance_km"] <= exposure_radius]

    total_years = target_year - df["year"].min() + 1

    if len(exposures) == 0:
        return 0.0

    # -----------------------------
    # 5️⃣ Frequency Score
    # -----------------------------
    exposure_count = len(exposures)
    frequency = exposure_count / total_years
    freq_score = min(frequency / 0.5, 1)  # normalize assuming 0.5 high freq cap

    # -----------------------------
    # 6️⃣ Intensity Score
    # -----------------------------
    avg_wind = exposures["wind_kts"].mean()
    intensity_score = min(avg_wind / 150, 1)

    # -----------------------------
    # 7️⃣ Proximity Score
    # -----------------------------
    avg_distance = exposures["distance_km"].mean()
    proximity_score = max((100 - avg_distance) / 100, 0)

    # Final Weighted Risk (0–1)
    cyclone_risk = (
        0.5 * freq_score +
        0.4 * intensity_score +
        0.1 * proximity_score
    )

    cyclone_risk = min(cyclone_risk, 1)

    # Convert to 30-point scale
    cyclone_score = cyclone_risk * 30

    return round(cyclone_score, 2)

# lat=float(input("Enter property latitude: "))
# lon=float(input("Enter property longitude: "))

# risk = calculate_cyclone_risk(lat, lon, 2050)
# print("Cyclone Score:", risk)
