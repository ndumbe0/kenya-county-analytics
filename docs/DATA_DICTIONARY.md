# Data Dictionary - Kenya County Analytics

## County Master Table

| Field | Type | Description | Example |
|-------|------|-------------|----------|
| code | string | County code (ISO 3166-2) | KE-30 |
| name | string | County name | Nairobi |
| region | string | Geographic region | Central |
| population_2019 | integer | 2019 Census population | 4397073 |
| area_km2 | float | Geographic area in km² | 696.1 |
| capital | string | County capital city | Nairobi |

## Population Forecast Table

| Field | Type | Description | Example |
|-------|------|-------------|----------|
| county | string | County name | Nairobi |
| year | integer | Forecast year | 2025 |
| population | integer | Projected population | 4725000 |
| lower_bound | integer | 95% CI lower | 4650000 |
| upper_bound | integer | 95% CI upper | 4800000 |
| confidence | float | Model confidence (0-1) | 0.92 |

## Economic Indicators Table

| Field | Type | Description | Example |
|-------|------|-------------|----------|
| county | string | County name | Nairobi |
| year | integer | Year | 2023 |
| gdp_billion_kes | float | Gross Domestic Product | 3200 |
| poverty_rate | float | Poverty rate (%) | 16.8 |
| unemployment | float | Unemployment rate (%) | 7.5 |
| gini_coefficient | float | Income inequality (0-1) | 0.42 |
| urbanization | float | Urban population (%) | 98 |

## Health Metrics Table

| Field | Type | Description | Example |
|-------|------|-------------|----------|
| county | string | County name | Nairobi |
| year | integer | Year | 2023 |
| maternal_mortality | float | Per 100,000 live births | 114 |
| infant_mortality | float | Per 1,000 live births | 32 |
| life_expectancy | float | Years | 73 |
| hospital_beds_per_1000 | float | Hospital bed density | 2.5 |
| doctors_per_100k | float | Doctor density | 85 |
| malaria_cases | integer | Annual cases | 5000 |

## Education Metrics Table

| Field | Type | Description | Example |
|-------|------|-------------|----------|
| county | string | County name | Nairobi |
| year | integer | Year | 2023 |
| literacy_rate | float | Literacy (%) | 88 |
| primary_enrollment | float | Net enrollment (%) | 95 |
| secondary_enrollment | float | Net enrollment (%) | 85 |
| university_enrollment | float | Tertiary enrollment (%) | 12 |
| teacher_student_ratio | float | Ratio | 1:45 |
