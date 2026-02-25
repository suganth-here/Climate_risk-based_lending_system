# climate_engine.py

try:
    from .cyclone_engine import calculate_cyclone_risk
    from .flood_engine import flood_score
    from .heat_risk_score import calculate_heat_risk
    from .sealevel_engine import calculate_sea_risk
except ImportError:
    from cyclone_engine import calculate_cyclone_risk
    from flood_engine import flood_score
    from heat_risk_score import calculate_heat_risk
    from sealevel_engine import calculate_sea_risk


def calculate_climate_credit_score(lat, lon):
    engine_scores = calculate_engine_scores(lat, lon)
    total_risk = sum(float(v) for v in engine_scores.values())
    total_risk = min(total_risk, 100)
    return round(100 - total_risk, 2)


def calculate_engine_scores(lat, lon):
    return {
        "Cyclone": round(float(calculate_cyclone_risk(lat, lon)), 2),
        "Flood": round(float(flood_score(lat, lon)), 2),
        "Heat": round(float(calculate_heat_risk(lat, lon)), 2),
        "Sea Level": round(float(calculate_sea_risk(lat, lon)), 2),
    }


if __name__ == "__main__":
    lat = float(input("Enter property latitude: "))
    lon = float(input("Enter property longitude: "))

    credit_score = calculate_climate_credit_score(lat, lon)

    print("\n🌍 Final Climate Credit Score:", credit_score)
