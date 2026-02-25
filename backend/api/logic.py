from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from new_predictions.datasets.engines.climate_engine import (  # noqa: E402
    calculate_climate_credit_score,
    calculate_engine_scores,
)


DEFAULT_PROJECTION_START_YEAR = 2026
DEFAULT_PROJECTION_HORIZON = 50
TENURE_PENALTY_PER_YEAR = 0.3

INDIA_STATE_COORDS: Dict[str, Tuple[float, float]] = {
    "Andhra Pradesh": (16.5062, 80.6480),
    "Arunachal Pradesh": (27.0844, 93.6053),
    "Assam": (26.1445, 91.7362),
    "Bihar": (25.5941, 85.1376),
    "Chhattisgarh": (21.2514, 81.6296),
    "Goa": (15.4909, 73.8278),
    "Gujarat": (23.2156, 72.6369),
    "Haryana": (30.7333, 76.7794),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jharkhand": (23.3441, 85.3096),
    "Karnataka": (12.9716, 77.5946),
    "Kerala": (8.5241, 76.9366),
    "Madhya Pradesh": (23.2599, 77.4126),
    "Maharashtra": (19.0760, 72.8777),
    "Manipur": (24.8170, 93.9368),
    "Meghalaya": (25.5788, 91.8933),
    "Mizoram": (23.7271, 92.7176),
    "Nagaland": (25.6751, 94.1086),
    "Odisha": (20.2961, 85.8245),
    "Punjab": (30.7333, 76.7794),
    "Rajasthan": (26.9124, 75.7873),
    "Sikkim": (27.3389, 88.6065),
    "Tamil Nadu": (13.0827, 80.2707),
    "Telangana": (17.3850, 78.4867),
    "Tripura": (23.8315, 91.2868),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Uttarakhand": (30.3165, 78.0322),
    "West Bengal": (22.5726, 88.3639),
}

REQUIRED_PORTFOLIO_COLUMNS = [
    "property_id",
    "latitude",
    "longitude",
    "tenure_years",
]


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(value)))


def _normalize_tenure_years(tenure_years: int) -> int:
    return int(_clamp(int(tenure_years), 1, 50))


def _engine_total_risk(engine_scores: Dict[str, float]) -> float:
    return round(_clamp(sum(float(v) for v in engine_scores.values()), 0.0, 100.0), 2)


def _apply_linear_tenure_adjustment(climate_credit_score: float, tenure_years: int) -> float:
    penalty = float(_normalize_tenure_years(tenure_years)) * TENURE_PENALTY_PER_YEAR
    adjusted = float(climate_credit_score) - penalty
    return round(_clamp(adjusted, 0.0, 100.0), 2)


def _annual_points_from_engine_scores(engine_scores: Dict[str, float]) -> Dict[str, float]:
    cyclone = float(engine_scores.get("Cyclone", 0.0))
    flood = float(engine_scores.get("Flood", 0.0))
    heat = float(engine_scores.get("Heat", 0.0))
    sea = float(engine_scores.get("Sea Level", 0.0))
    return {
        "Cyclone": round(cyclone, 2),
        "Heat": round(heat, 2),
        "Flood": round(flood, 2),
        "Sea Level": round(sea, 2),
    }


def _projection_series_50(total_risk: float, start_year: int) -> List[Dict[str, float]]:
    base = _clamp(total_risk / 100.0, 0.0, 1.0)
    drift = 0.0008 + (base * 0.0032)
    out: List[Dict[str, float]] = []
    for offset in range(DEFAULT_PROJECTION_HORIZON):
        year = int(start_year + offset)
        seasonal = 0.01 * math.sin(offset / 3.0)
        risk = _clamp(base + (drift * offset) + seasonal, 0.0, 1.0)
        out.append({"year": year, "predicted_climate_risk": round(float(risk), 4)})
    return out


def _tenure_payload(
    latitude: float,
    longitude: float,
    tenure_years: int,
    start_year: int,
    series_50: List[Dict[str, float]],
) -> Dict[str, float]:
    tenure_window = series_50[:tenure_years]
    avg = sum(float(row["predicted_climate_risk"]) for row in tenure_window) / max(1, len(tenure_window))
    return {
        "lat_bin": round(float(latitude), 2),
        "lon_bin": round(float(longitude), 2),
        "start_year": int(start_year),
        "end_year": int(start_year + tenure_years - 1),
        "tenure_risk_score": round(float(avg), 4),
        "tenure_risk_percent": round(float(avg) * 100.0, 2),
    }


def _elevation_proxy(latitude: float) -> float:
    # Lightweight proxy so this API no longer depends on old elevation datasets.
    return round(max(0.0, 1800.0 * abs(math.sin(math.radians(float(latitude))))), 2)


def _top_hazards(points: Dict[str, float], top_n: int = 2) -> List[str]:
    return [k for k, _ in sorted(points.items(), key=lambda x: float(x[1]), reverse=True)[:top_n]]


def build_interest_adjustment_short_text(score: float, tenure_years: int) -> str:
    tenor_ratio = float(_normalize_tenure_years(tenure_years)) / 50.0
    delta = ((100.0 - float(score)) * 0.03) + (0.35 * tenor_ratio)
    delta = _clamp(delta, 0.0, 5.0)
    if delta <= 0.0:
        return "Unchanged interest rate."
    return f"Interest rate increased by {delta:.2f}%."


def build_pricing_adjustment_text(score: float, tenure_years: int, engine_scores: Dict[str, float]) -> str:
    delta_text = build_interest_adjustment_short_text(score, tenure_years)
    if delta_text == "Unchanged interest rate.":
        return "Loan Pricing Adjustment: Interest rate unchanged due to low projected climate exposure."
    top2 = _top_hazards(engine_scores, top_n=2)
    if len(top2) >= 2:
        drivers = f"{top2[0].lower()} and {top2[1].lower()} exposure"
    elif len(top2) == 1:
        drivers = f"{top2[0].lower()} exposure"
    else:
        drivers = "multi-hazard exposure"
    return f"Loan Pricing Adjustment: {delta_text} due to {drivers}."


def build_property_score_text(property_id: str, score: float, engine_scores: Dict[str, float]) -> str:
    top2 = _top_hazards(engine_scores, top_n=2)
    if len(top2) >= 2:
        hazard_text = f"{top2[0].lower()} and {top2[1].lower()} risk"
    elif len(top2) == 1:
        hazard_text = f"{top2[0].lower()} risk"
    else:
        hazard_text = "multi-hazard climate risk"
    return f"Property-ID {property_id} assigned Climate Credit Score: {float(score):.2f}/100 driven by {hazard_text}."


def build_explainability_log_text(
    engine_scores: Dict[str, float],
    total_risk: float,
    tenure_years: int,
    tenure_risk_percent: float,
) -> str:
    cyclone = float(engine_scores.get("Cyclone", 0.0))
    flood = float(engine_scores.get("Flood", 0.0))
    heat = float(engine_scores.get("Heat", 0.0))
    sea = float(engine_scores.get("Sea Level", 0.0))
    return (
        "Explainability Log: Credit score is computed only from engine outputs in processed datasets. "
        f"Risk sum={total_risk:.2f} (Cyclone={cyclone:.2f}, Flood={flood:.2f}, Heat={heat:.2f}, Sea Level={sea:.2f}), "
        f"tenure window={int(tenure_years)} years, tenure climate stress={float(tenure_risk_percent):.2f}%."
    )


def build_portfolio_alert_text(concentration_pct: int, flood_mean: float, cyclone_mean: float, years: int = 10) -> str:
    joint = (float(flood_mean) + float(cyclone_mean)) / 2.0
    low_exp = max(4, int(round(joint * 0.2)))
    high_exp = max(low_exp + 2, int(round(joint * 0.3)))
    return (
        "Portfolio Risk Alert: "
        f"{int(concentration_pct)}% of loans are concentrated in high flood/cyclone zones. "
        f"Estimated climate-linked default exposure may rise by {low_exp}-{high_exp}% over {int(years)} years."
    )


def _decision_and_reason(score: float, tenure_risk_percent: float, engine_scores: Dict[str, float]) -> Tuple[bool, str]:
    top2 = _top_hazards(engine_scores, top_n=2)
    h1 = top2[0] if len(top2) > 0 else "Flood"
    h2 = top2[1] if len(top2) > 1 else "Cyclone"
    safe = float(score) >= 50.0 and float(tenure_risk_percent) < 60.0
    reason = (
        f"Primary drivers: {h1.lower()} and {h2.lower()}. "
        f"Credit score={float(score):.2f}/100, tenure climate stress={float(tenure_risk_percent):.2f}%."
    )
    return safe, reason


def _compute_engine_based_result(
    latitude: float,
    longitude: float,
    tenure_years: int,
    projection_start_year: int,
    property_id: str,
) -> Dict[str, object]:
    years = _normalize_tenure_years(tenure_years)
    start_year = int(projection_start_year)

    engine_scores = {k: float(v) for k, v in calculate_engine_scores(float(latitude), float(longitude)).items()}
    total_risk = _engine_total_risk(engine_scores)
    base_climate_credit_score = float(calculate_climate_credit_score(float(latitude), float(longitude)))
    climate_credit_score = _apply_linear_tenure_adjustment(base_climate_credit_score, years)
    annual_points = _annual_points_from_engine_scores(engine_scores)
    series_50 = _projection_series_50(total_risk=total_risk, start_year=start_year)
    tenure = _tenure_payload(
        latitude=float(latitude),
        longitude=float(longitude),
        tenure_years=years,
        start_year=start_year,
        series_50=series_50,
    )
    safe, reason = _decision_and_reason(
        score=climate_credit_score,
        tenure_risk_percent=float(tenure["tenure_risk_percent"]),
        engine_scores=engine_scores,
    )

    return {
        "reason": reason,
        "safe": bool(safe),
        "safety_status": "SAFE" if safe else "NOT SAFE",
        "tenure": tenure,
        "annual_points": annual_points,
        "engine_scores": engine_scores,
        "engine_total_risk": float(total_risk),
        "base_climate_credit_score": float(round(base_climate_credit_score, 2)),
        "tenure_adjustment_penalty": float(round(years * TENURE_PENALTY_PER_YEAR, 2)),
        "climate_credit_score": float(climate_credit_score),
        "output_statements": {
            "property_climate_credit_score": build_property_score_text(
                str(property_id),
                float(climate_credit_score),
                engine_scores,
            ),
            "loan_pricing_adjustment": build_pricing_adjustment_text(
                score=float(climate_credit_score),
                tenure_years=years,
                engine_scores=engine_scores,
            ),
            "portfolio_risk_alert": build_portfolio_alert_text(
                concentration_pct=int(round(float(engine_scores.get("Sea Level", 0.0)))),
                flood_mean=float(engine_scores.get("Flood", 0.0)),
                cyclone_mean=float(engine_scores.get("Cyclone", 0.0)),
                years=10,
            ),
            "explainability_log": build_explainability_log_text(
                engine_scores=engine_scores,
                total_risk=float(total_risk),
                tenure_years=years,
                tenure_risk_percent=float(tenure["tenure_risk_percent"]),
            ),
        },
        "elevation_m": _elevation_proxy(float(latitude)),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "series_50": series_50,
    }


def evaluate_single_application(
    latitude: float,
    longitude: float,
    tenure_years: int,
    loan_amount: float,
    projection_start_year: int = DEFAULT_PROJECTION_START_YEAR,
    property_id: str = "98122",
) -> Dict[str, object]:
    _ = float(loan_amount)
    return _compute_engine_based_result(
        latitude=float(latitude),
        longitude=float(longitude),
        tenure_years=int(tenure_years),
        projection_start_year=int(projection_start_year),
        property_id=str(property_id),
    )


def _validate_portfolio_df(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_PORTFOLIO_COLUMNS if c not in portfolio_df.columns]
    if missing:
        raise ValueError(f"Missing required portfolio columns: {missing}")

    out = portfolio_df.copy()
    out["property_id"] = out["property_id"].astype(str)
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce")
    out["tenure_years"] = pd.to_numeric(out["tenure_years"], errors="coerce")
    out = out.dropna(subset=["property_id", "latitude", "longitude", "tenure_years"]).reset_index(drop=True)
    if out.empty:
        raise ValueError("Portfolio CSV has no valid rows after validation.")
    out["tenure_years"] = out["tenure_years"].astype(int)
    return out


def analyze_portfolio(portfolio_df: pd.DataFrame, projection_start_year: int) -> Dict[str, object]:
    clean_df = _validate_portfolio_df(portfolio_df)

    internal_rows = []
    output_rows = []
    approved_count = 0
    rejected_count = 0

    for row in clean_df.itertuples(index=False):
        result = _compute_engine_based_result(
            latitude=float(row.latitude),
            longitude=float(row.longitude),
            tenure_years=int(row.tenure_years),
            projection_start_year=int(projection_start_year),
            property_id=str(row.property_id),
        )
        score_val = float(result["climate_credit_score"])
        tenure = result["tenure"]
        engine_scores = result["engine_scores"]
        if bool(result["safe"]):
            approved_count += 1
        else:
            rejected_count += 1

        interest_adjustment_text = build_interest_adjustment_short_text(score=score_val, tenure_years=int(row.tenure_years))

        internal_rows.append(
            {
                "property_id": str(row.property_id),
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "tenure_years": int(row.tenure_years),
                "tenure_risk_percent": round(float(tenure["tenure_risk_percent"]), 2),
                "Cyclone": round(float(engine_scores["Cyclone"]), 2),
                "Heat": round(float(engine_scores["Heat"]), 2),
                "Flood": round(float(engine_scores["Flood"]), 2),
                "Sea Level": round(float(engine_scores["Sea Level"]), 2),
                "reason": str(result["reason"]),
                "score": score_val,
                "interest_adjustment": interest_adjustment_text,
            }
        )
        output_rows.append(
            {
                "Property id": str(row.property_id),
                "Latitude": float(row.latitude),
                "Longitude": float(row.longitude),
                "Tenure years": int(row.tenure_years),
                "Interest adjustment": interest_adjustment_text,
                "Reason": str(result["reason"]),
                "Score": f"{score_val:.2f}/100",
            }
        )

    results_df = pd.DataFrame(internal_rows)
    avg_tenure_risk = float(results_df["tenure_risk_percent"].mean()) if not results_df.empty else None
    portfolio_alert = "Portfolio Risk Alert: Not available."
    if not results_df.empty:
        coastal = results_df[results_df["Sea Level"] >= 8.0]
        base = coastal if not coastal.empty else results_df
        high = base[base["score"] < 50.0]
        pct = int(round((len(high) / max(len(base), 1)) * 100.0))
        flood_mean = float(base["Flood"].mean()) if "Flood" in base.columns else 0.0
        cyclone_mean = float(base["Cyclone"].mean()) if "Cyclone" in base.columns else 0.0
        portfolio_alert = build_portfolio_alert_text(
            concentration_pct=pct,
            flood_mean=flood_mean,
            cyclone_mean=cyclone_mean,
            years=10,
        )

    return {
        "total_records": int(len(clean_df)),
        "approved": int(approved_count),
        "not_approved": int(rejected_count),
        "average_tenure_risk": None if avg_tenure_risk is None else round(float(avg_tenure_risk), 2),
        "portfolio_risk_alert": portfolio_alert,
        "results": output_rows,
    }


def metadata_payload() -> Dict[str, object]:
    return {
        "default_projection_start_year": DEFAULT_PROJECTION_START_YEAR,
        "default_projection_horizon_years": DEFAULT_PROJECTION_HORIZON,
        "states": INDIA_STATE_COORDS,
        "required_portfolio_columns": REQUIRED_PORTFOLIO_COLUMNS,
    }
