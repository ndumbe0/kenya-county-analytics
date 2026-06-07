import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from src.ml.population_forecaster import forecast_population, COUNTY_POPULATION_2019
from src.ml.economic_clustering import cluster_counties
from src.ml.health_predictor import detect_anomalies, compute_health_score
from src.ml.education_employment import train_employment_model


def test_population_forecast_nairobi():
    result = forecast_population("Nairobi")
    assert result["county"] == "Nairobi"
    assert result["base_population"] == 4396086
    assert "forecast" in result
    assert len(result["forecast"]) == 5
    assert result["confidence_score"] > 0


def test_population_forecast_all_counties():
    assert len(COUNTY_POPULATION_2019) == 47


def test_population_growth():
    result = forecast_population("Kiambu", years=3)
    forecast = result["forecast"]
    values = list(forecast.values())
    for i in range(1, len(values)):
        assert values[i] > values[i-1], "Population should grow"


def test_economic_clustering():
    result = cluster_counties()
    assert "cluster_info" in result
    assert "county_clusters" in result
    assert result["cluster_info"]["n_counties"] == 47
    assert result["cluster_info"]["n_clusters"] == 5


def test_economic_clustering_tiers():
    result = cluster_counties()
    clusters = result["county_clusters"]
    tiers = set(d["development_tier"] for d in clusters.values())
    assert tiers == {1, 2, 3, 4, 5}


def test_nairobi_top_tier():
    result = cluster_counties()
    nairobi = result["county_clusters"]["Nairobi"]
    assert nairobi["development_tier"] == 1


def test_health_anomalies():
    result = detect_anomalies()
    assert "model" in result
    assert "county_results" in result
    assert result["total_counties"] == 47


def test_health_score_calculation():
    score = compute_health_score({
        "doc_per_10000": 20, "bed_per_10000": 30,
        "immunization": 90, "malaria_incidence": 50,
        "hiv_prevalence": 3, "life_expectancy": 70
    })
    assert 0 < score < 100


def test_education_model():
    result = train_employment_model()
    assert "model" in result
    assert "r2_score" in result
    assert "county_results" in result
    assert len(result["county_results"]) == 47


def test_education_feature_importance():
    result = train_employment_model()
    assert len(result["feature_importance"]) == 4
    for f in ["literacy", "secondary_enrollment", "tertiary_enrollment", "unemployment"]:
        assert f in result["feature_importance"]
