export interface CountyMetric {
  county_code: string;
  county_name: string;
  slug: string;
  availability_status: string;
  latest_year: number;
  population: number;
  population_growth_pct: number;
  gdp_contribution_pct: number;
  health_score: number;
  education_rating: number;
  employment_rate: number;
  unemployment_rate: number;
  development_score: number;
  development_tier: number;
  source: string;
}

export interface PopulationForecast {
  county: string;
  historical: Record<string, number>;
  forecast: Record<string, number>;
  confidence: Record<string, { lower: number; upper: number }>;
  model: string;
  growth_rate: number;
}

export interface EconomicClusters {
  clusters: Record<string, {
    tier: number;
    label: string;
    count: number;
    counties: string[];
  }>;
  total_counties: number;
}

export interface EducationEmploymentItem {
  county: string;
  model: string;
  feature_importance_method: string;
  actual_employment_rate: number;
  predicted_employment_rate: number;
  residuals: number;
  feature_contributions: {
    gdp_pc: number;
    health_score: number;
    education_rating: number;
    urbanization: number;
  };
}

export interface EducationEmployment {
  county_results: Record<string, EducationEmploymentItem>;
}

export interface HealthAnomalyItem {
  county: string;
  is_anomaly: boolean;
  anomaly_score: number;
  health_score: number;
  alert: string;
}

export interface HealthAnomaly {
  county_results: Record<string, HealthAnomalyItem>;
}

export interface AgentInfo {
  key: string;
  name: string;
  icon: string;
  description: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  agentKey?: string;
  citations?: string[];
}
