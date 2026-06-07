import pandas as pd
from prophet import Prophet
import pickle

def train_population_forecast():
    df = pd.DataFrame({
        'ds': pd.date_range('2015-01-01', periods=10, freq='Y'),
        'y': [1.2e6,1.25e6,1.3e6,1.35e6,1.4e6,1.45e6,1.5e6,1.55e6,1.6e6,1.65e6]
    })
    model = Prophet()
    model.fit(df)
    with open('population_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("Population model trained (demo).")

if __name__ == "__main__":
    train_population_forecast()
