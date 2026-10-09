import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from src.ml.population_forecaster import (
    COUNTY_POPULATION_2019,
    forecast_population,
    get_development_tiers,
    detect_health_anomalies,
    predict_employment,
)


def test_population_forecast_nairobi():
    result = forecast_population("Nairobi")
    assert result["county"] == "Nairobi"
    assert result["historical"][2019] == 4396087
    assert "forecast" in result
    assert len(result["forecast"]) == 5
    assert result["growth_rate"] > 0


def test_population_forecast_all_counties():
    assert len(COUNTY_POPULATION_2019) == 47


def test_population_growth():
    result = forecast_population("Kiambu", years=3)
    forecast = result["forecast"]
    values = list(forecast.values())
    for i in range(1, len(values)):
        assert values[i] > values[i-1], "Population should grow"


def test_economic_clustering():
    result = get_development_tiers()
    assert "clusters" in result
    assert "Nairobi" in result["clusters"]
    assert len(result["clusters"]) == 47


def test_economic_clustering_tiers():
    result = get_development_tiers()
    clusters = result["clusters"]
    tiers = set(d["tier"] for d in clusters.values())
    assert tiers == {1, 2, 3, 4, 5}


def test_nairobi_top_tier():
    result = get_development_tiers()
    nairobi = result["clusters"]["Nairobi"]
    assert nairobi["tier"] == 1


def test_health_anomalies():
    result = detect_health_anomalies("Nairobi")
    assert "county" in result
    assert "is_anomaly" in result
    assert result["county"] == "Nairobi"


def test_education_model():
    result = predict_employment("Nairobi")
    assert "model" in result
    assert "predicted_employment_rate" in result
    assert "actual_employment_rate" in result
    assert "feature_contributions" in result


def test_education_feature_importance():
    result = predict_employment("Kiambu")
    feats = result.get("feature_contributions", {})
    assert len(feats) > 0
    for f in ["gdp_pc", "health_score", "education_rating", "urbanization"]:
        assert f in feats
