# Kenya County Analytics Architecture

The platform has five layers:

1. KNBS ingestion downloads County Statistical Abstract PDFs into `D:\personal projects\Project data\{county_name}\`.
2. PDF extraction stores normalized CSV and JSON tables under `data/processed/{county}/{domain}/`.
3. Geospatial bootstrap stores county boundaries at `data/geospatial/kenya-counties.geojson`.
4. ML modules produce population forecasts, economic tiers, health anomaly alerts, and employment explanations.
5. FastAPI and Streamlit expose the data through an API and interactive dashboard.

The system is designed to continue when individual PDFs, parsers, model libraries, Docker, or visualization tools fail. Each step emits structured logs and falls back to baseline data where possible.
