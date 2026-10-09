import time
print('Testing K-Means...', flush=True)
t = time.time()
from src.ml.population_forecaster import get_development_tiers
tiers = get_development_tiers()
elapsed = time.time() - t
n = len(tiers["clusters"])
print(f'K-Means took {elapsed:.2f}s, {n} counties', flush=True)
print('  Nairobi tier:', tiers['clusters']['Nairobi']['tier'], flush=True)
print('  Tier counts:', tiers['tier_counts'], flush=True)

print('Testing isolation forest...', flush=True)
t = time.time()
from src.ml.population_forecaster import detect_health_anomalies
nairobi = detect_health_anomalies('Nairobi')
elapsed = time.time() - t
print(f'IF took {elapsed:.2f}s', flush=True)
print('  Nairobi anomaly:', nairobi['is_anomaly'], nairobi['alert'], flush=True)

print('Testing employment prediction...', flush=True)
t = time.time()
from src.ml.population_forecaster import predict_employment
emp = predict_employment('Nairobi')
elapsed = time.time() - t
print(f'Employment took {elapsed:.2f}s', flush=True)
print('  Predicted:', emp.get('predicted_employment_rate'), flush=True)
print('  Method:', emp.get('feature_importance_method'), flush=True)

print('All good.', flush=True)
