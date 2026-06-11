import { useState, useEffect } from "react";
import { CountyMetric } from "../types";
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, Cell
} from "recharts";
import { Loader2, AlertCircle, TrendingUp, Cpu, Activity, UserCheck, Award, MapPin } from "lucide-react";

interface CountyDetailProps {
  countyCode?: string;
  metricsList: CountyMetric[];
  onSelectCounty: (code: string) => void;
}

export default function CountyDetail({ countyCode, metricsList, onSelectCounty }: CountyDetailProps) {
  const [activeCode, setActiveCode] = useState<string>("");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync active code from props
  useEffect(() => {
    if (countyCode) {
      setActiveCode(countyCode);
    } else if (metricsList.length > 0 && !activeCode) {
      // Default to first county in alphabetical list (Nairobi or Mombasa)
      const defaultCounty = metricsList.find(m => m.county_name === "Nairobi") || metricsList[0];
      setActiveCode(defaultCounty.county_code);
    }
  }, [countyCode, metricsList]);

  // Load detailed structured indicators from Express API
  useEffect(() => {
    async function fetchCountyDetails() {
      if (!activeCode) return;
      try {
        setLoading(true);
        setError(null);
        const res = await fetch(`/api/v1/counties/${activeCode}`);
        if (!res.ok) throw new Error("County stats not found.");
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Failed to fetch indicators.");
      } finally {
        setLoading(false);
      }
    }
    fetchCountyDetails();
  }, [activeCode]);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600 mb-2" />
        <p className="text-sm font-mono text-slate-500">Retrieving Detailed County Ledger...</p>
      </div>
    );
  }

  // Map counties dropdown
  const handleDropdownChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setActiveCode(val);
    onSelectCounty(val);
  };

  const m: CountyMetric | null = data;

  // Prepare population chart series
  let forecastSeries: any[] = [];
  if (data?.forecast) {
    const hist = data.forecast.historical || {};
    const fc = data.forecast.forecast || {};
    const conf = data.forecast.confidence || {};

    // Combine into timeline
    Object.keys(hist).forEach(yr => {
      forecastSeries.push({
        year: yr,
        historical: hist[yr],
        forecast: null,
        lower: null,
        upper: null
      });
    });

    Object.keys(fc).forEach(yr => {
      const confidenceRange = conf[yr] || {};
      forecastSeries.push({
        year: yr,
        historical: null,
        forecast: fc[yr],
        lower: confidenceRange.lower || null,
        upper: confidenceRange.upper || null
      });
    });
    
    // Sort chronologically by year flag
    forecastSeries.sort((a, b) => parseInt(a.year) - parseInt(b.year));
  }

  // Prepare linear regression contributions
  let contributionSeries: any[] = [];
  if (data?.education_employment?.feature_contributions) {
    const cont = data.education_employment.feature_contributions;
    contributionSeries = [
      { name: "GDP per Capita", value: cont.gdp_pc, desc: "Regional economic power" },
      { name: "Health Indicator", value: cont.health_score, desc: "Worker safety residuals" },
      { name: "Education Rating", value: cont.education_rating, desc: "Skilled literacy tiers" },
      { name: "Urban Density", value: cont.urbanization, desc: "Infrastructure access" }
    ];
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Top Selector Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 px-6 py-4 rounded-3xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-500 rounded-2xl text-white">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-800 dark:text-slate-100">County Deep-Dive Indicators</h2>
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-0.5">Statistical abstract audits</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label htmlFor="county-selector" className="text-xs font-mono font-bold text-slate-500 uppercase shrink-0">County Selection</label>
          <select
            id="county-selector"
            value={activeCode}
            onChange={handleDropdownChange}
            className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-800 px-4 py-2 rounded-xl text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {metricsList.map(item => (
              <option key={item.county_code} value={item.county_code}>
                {item.county_code} - {item.county_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="p-6 bg-red-50 text-red-600 rounded-3xl border border-red-100 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0" />
          <div className="text-xs font-medium">{error}</div>
        </div>
      )}

      {m && (
        <>
          {/* Key Indicators Bento Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { label: "Population", value: m.population?.toLocaleString(), sub: `Growth rate +${m.population_growth_pct}%`, icon: UserCheck, color: "bg-blue-500/10 text-blue-600" },
              { label: "GDP Share", value: `${m.gdp_contribution_pct}%`, sub: `National product`, icon: TrendingUp, color: "bg-emerald-500/10 text-emerald-600" },
              { label: "Health Score", value: `${m.health_score}`, sub: `Index rating`, icon: Activity, color: "bg-rose-500/10 text-rose-600" },
              { label: "Edu Rating", value: `${m.education_rating} / 5`, sub: `Literacy ranking`, icon: Award, color: "bg-indigo-500/10 text-indigo-600" },
              { label: "Employment", value: `${m.employment_rate}%`, sub: `Labor force`, icon: Cpu, color: "bg-amber-500/10 text-amber-600" },
              { label: "Dev Tier", value: `Tier ${m.development_tier}`, sub: `${m.development_score} overall index`, icon: MapPin, color: "bg-teal-500/10 text-teal-600" }
            ].map((stat, i) => {
              const Icon = stat.icon;
              return (
                <div key={i} className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 p-5 rounded-2xl flex flex-col justify-between hover:shadow-sm transition-all shadow-[0_2px_8px_-3px_rgba(0,0,0,0.05)]">
                  <div className="flex justify-between items-start gap-2">
                    <span className="text-[10px] font-mono font-bold text-gray-400 uppercase tracking-wide leading-none">{stat.label}</span>
                    <div className={`p-1.5 rounded-lg shrink-0 ${stat.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="text-lg font-bold font-sans text-slate-800 dark:text-slate-100 leading-tight">{stat.value}</div>
                    <div className="text-[9px] text-gray-500 dark:text-gray-400 font-medium font-mono mt-1 leading-none">{stat.sub}</div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* 1. Left - Population Projections Curve */}
            <div className="col-span-1 lg:col-span-7 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 px-6 py-5 rounded-3xl flex flex-col justify-between shadow-sm">
              <div>
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  Population Growth Curve (5-Year Forecast)
                </h3>
                <p className="text-[10px] text-gray-500 font-mono mt-0.5 uppercase tracking-wider">Compound growth at 2.3% per annum</p>
              </div>

              <div className="h-72 w-full mt-6">
                {forecastSeries.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={forecastSeries} margin={{ top: 10, right: 10, left: -5, bottom: 0 }}>
                      <defs>
                        <linearGradient id="popHistColor" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#2563eb" stopOpacity={0.25}/>
                          <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="popForeColor" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.25}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(148, 163, 184, 0.12)" />
                      <XAxis dataKey="year" fontSize={10} fontClassName="font-mono text-gray-400" tickLine={false} axisLine={false} />
                      <YAxis 
                        fontSize={10} 
                        fontClassName="font-mono text-gray-400" 
                        tickLine={false} 
                        axisLine={false} 
                        tickFormatter={(v) => v >= 1000000 ? `${(v/1000000).toFixed(1)}M` : v.toLocaleString()}
                      />
                      <Tooltip 
                        contentStyle={{ background: '#0f172a', border: 'none', borderRadius: '12px', fontSize: '11px', color: '#f8fafc' }}
                        formatter={(val: any, name: string) => [val?.toLocaleString(), name]}
                      />
                      <Legend verticalAlign="top" height={36} iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '10px', fontFamily: 'monospace' }} />
                      <Area name="Historical" type="monotone" dataKey="historical" stroke="#2563eb" fillOpacity={1} fill="url(#popHistColor)" strokeWidth={1.5} connectNulls />
                      <Area name="Forecast" type="monotone" dataKey="forecast" stroke="#10b981" fillOpacity={1} fill="url(#popForeColor)" strokeWidth={1.5} strokeDasharray="4 4" connectNulls />
                      <Area name="Confidence Upper" type="monotone" dataKey="upper" stroke="#10b981" strokeWidth={0.5} strokeOpacity={0.2} fill="transparent" connectNulls />
                      <Area name="Confidence Lower" type="monotone" dataKey="lower" stroke="#10b981" strokeWidth={0.5} strokeOpacity={0.2} fill="transparent" connectNulls />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-xs italic text-gray-500 font-mono">No pre-loaded timeline projections available.</p>
                  </div>
                )}
              </div>
            </div>

            <div className="col-span-1 lg:col-span-5 flex flex-col gap-6">
              
              {/* 2. OLS Feature Contributions bar chart on Labor */}
              <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 px-6 py-5 rounded-3xl flex-1 flex flex-col justify-between shadow-sm">
                <div>
                  <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-emerald-600" />
                    OLS Employment Drivers Permutations
                  </h3>
                  <p className="text-[10px] text-gray-500 font-mono mt-0.5 uppercase tracking-wider">Permutation weights driving labor indexes</p>
                </div>

                <div className="h-44 w-full mt-4">
                  {contributionSeries.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={contributionSeries} layout="vertical" margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(148, 163, 184, 0.1)" />
                        <XAxis type="number" fontSize={9} fontClassName="font-mono text-gray-400" tickLine={false} axisLine={false} />
                        <YAxis dataKey="name" type="category" width={90} fontSize={9} fontClassName="font-semibold" tickLine={false} axisLine={false} />
                        <Tooltip
                          contentStyle={{ background: '#0f172a', border: 'none', borderRadius: '12px', fontSize: '10px', color: '#f8fafc' }}
                        />
                        <Bar dataKey="value" name="Contribution" radius={[0, 4, 4, 0]}>
                          {contributionSeries.map((entry, idx) => (
                            <Cell key={idx} fill={idx % 2 === 0 ? "rgba(16, 185, 129, 0.85)" : "rgba(6, 182, 212, 0.85)"} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <p className="text-xs italic text-gray-500 font-mono">Statistical regressors uncalculated for baseline data.</p>
                    </div>
                  )}
                </div>

                <div className="text-[10px] leading-relaxed text-gray-500 bg-slate-50 dark:bg-slate-900/60 p-3 rounded-xl border border-slate-100 dark:border-gray-900 font-sans mt-3">
                  This OLS regression model uses health residuals, developmental tiers, composite GDP contributions, and education to forecast county employment rates with a permutation weight ratio.
                </div>
              </div>

              {/* 3. Isolation Forest Health Check status alert index */}
              <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 px-6 py-5 rounded-3xl shadow-sm flex flex-col justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-600" />
                    Isolation Forest Health Audit
                  </h3>
                  <p className="text-[10px] text-gray-500 font-mono mt-0.5 uppercase tracking-wider">Health index anomalies checks</p>
                </div>

                <div className="mt-4">
                  {data?.health_anomaly ? (
                    <div className="flex flex-col gap-3">
                      <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-xl shrink-0 ${data.health_anomaly.is_anomaly ? 'bg-rose-100 text-rose-600 dark:bg-rose-950/30 dark:text-rose-400' : 'bg-emerald-100 text-[#047857] dark:bg-emerald-950/30'}`}>
                          <AlertCircle className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="text-xs font-semibold uppercase font-mono tracking-wider">
                            Anomaly Flag: {data.health_anomaly.is_anomaly ? "🚨 Detected" : "✅ Normal"}
                          </div>
                          <div className="text-[10px] text-gray-400 font-mono mt-0.5">
                            Anomaly Score: <span className="font-bold text-gray-200">{data.health_anomaly.anomaly_score?.toFixed(3)}</span> (Deviation limit &gt; 0.6)
                          </div>
                        </div>
                      </div>

                      <p className="text-xs font-medium text-slate-700 bg-slate-50 dark:bg-slate-900 px-4 py-2.5 border border-slate-100 dark:border-gray-800 rounded-xl mt-1 leading-normal italic">
                        &ldquo;{data.health_anomaly.alert}&rdquo;
                      </p>
                    </div>
                  ) : (
                    <div className="p-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-gray-900 rounded-2xl text-center">
                      <p className="text-xs text-slate-400 font-mono italic">Anomaly checker currently inactive for baseline counties.</p>
                    </div>
                  )}
                </div>
              </div>

            </div>
          </div>
        </>
      )}
    </div>
  );
}
