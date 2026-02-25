# =====================================================
# COMPLETE STANDALONE FLOOD ENGINE
# High Score = Low Flood Risk
# =====================================================

import math
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import os

# =====================================================
# LOAD DATASETS
# =====================================================

# Get project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Build dataset directory path
DATA_DIR = os.path.join(BASE_DIR, "processed")

rain_df = pd.read_csv(os.path.join(DATA_DIR, "india_annual_rainfall.csv"))

flood_hist_df = pd.read_csv(os.path.join(DATA_DIR, "flood_points_clean.csv"))

river_df = pd.read_csv(os.path.join(DATA_DIR, "india_flood_master_scored.csv"))

coast_df = pd.read_csv(os.path.join(DATA_DIR, "coastline_points.csv"))



# =====================================================
# BUILD KDTREES (FAST LOOKUP)
# =====================================================

rain_tree = cKDTree(rain_df[["Latitude", "Longitude"]].values)
coast_tree = cKDTree(np.radians(coast_df[["latitude", "longitude"]].values))
river_tree = cKDTree(river_df[["latitude", "longitude"]].values)
hist_tree = cKDTree(flood_hist_df[["latitude", "longitude"]].values)

EARTH_RADIUS = 6371  # km


# =====================================================
# HAVERSINE FUNCTION
# =====================================================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(a))


# =====================================================
# RAINFALL SCORE
# =====================================================

def rainfall_score(lat, lon):
    _, idx = rain_tree.query([lat, lon])
    rainfall = float(rain_df.iloc[idx]["Rainfall_mm"])

    # Normalize roughly to 0–100
    return min(100, rainfall / 10)


# =====================================================
# COAST DISTANCE
# =====================================================

def coastline_distance(lat, lon):
    point = np.radians([[lat, lon]])
    distance, _ = coast_tree.query(point)
    return float(distance[0] * EARTH_RADIUS)


# =====================================================
# HISTORICAL FLOOD PROXIMITY
# =====================================================

def historical_score(lat, lon):
    _, idx = hist_tree.query([lat, lon])
    nearest = flood_hist_df.iloc[idx]

    dist = haversine(lat, lon, nearest["latitude"], nearest["longitude"])
    beta = 12  # decay constant

    return 100 * math.exp(-dist / beta)


# =====================================================
# RIVER FLOOD RASTER
# =====================================================

def river_score(lat, lon):
    _, idx = river_tree.query([lat, lon])
    return float(river_df.iloc[idx]["flood_risk_score"]) * 100


# =====================================================
# SYNTHETIC ELEVATION (Simple Stable Proxy)
# =====================================================

def elevation_proxy(lat):
    # Smooth proxy — avoids srtm instability
    return max(0, 2000 * abs(math.sin(math.radians(lat))))


# =====================================================
# FINAL FLOOD ENGINE
# =====================================================

# =====================================================
# FINAL FLOOD RISK ENGINE (Hazard Only)
# Returns ONLY flood risk score (0 = Safe, 100 = Extreme Risk)
# =====================================================

def flood_score(lat, lon):

    rain = rainfall_score(lat, lon)
    hist = historical_score(lat, lon)
    elev = elevation_proxy(lat)
    coast_dist = coastline_distance(lat, lon)
    river = river_score(lat, lon)

    # --- Core hazard ---
    rain_prob = (rain / 100) ** 1.2
    hist_prob = hist / 100
    core = 0.75 * rain_prob + 0.25 * hist_prob

    # --- Elevation vulnerability ---
    alpha = 10
    elev_mod = 0.3 + 0.7 * math.exp(-elev / alpha)

    # --- Coastal vulnerability ---
    lam = 20
    coast_mod = 0.4 + 0.6 * math.exp(-coast_dist / lam)

    vulnerability = 0.6 * elev_mod + 0.4 * coast_mod

    raw = core * vulnerability
    amplified = raw ** 0.45

    composite_risk = 100 * amplified

    # --- Combine river raster ---
    risk_score = 0.7 * composite_risk + 0.3 * river
    risk_score = max(0, min(100, round(risk_score, 2)))
    flood_score_scaled = (risk_score / 100) * 30

    return round(flood_score_scaled, 2)
