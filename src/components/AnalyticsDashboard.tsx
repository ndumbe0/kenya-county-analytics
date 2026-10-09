import { useState, useEffect } from "react";
import { CountyMetric } from "../types";
import { 
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip as ChartTooltip, LabelList, 
  ResponsiveContainer, CartesianGrid, Legend
} from "recharts";
import { Search, Loader2, Filter, AlertCircle, Info, RefreshCw, BarChart } from "lucide-react";

interface AnalyticsDashboardProps {
  metrics: CountyMetric[];
  onSelectCounty: (code: string) => void;
  onNavigateTab: (tab: any) => void;
}

export default function AnalyticsDashboard({ metrics, onSelectCounty, onNavigateTab }: AnalyticsDashboardProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeTierFilter, setActiveTierFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("gdp_contribution_pct");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [clusters, setClusters] = useState<any>(null);
  const [loadingClusters, setLoadingClusters] = useState(false);

  // Load K-Means Cluster information from Express backend
  useEffect(() => {
    async function loadClusters() {
      try {
        setLoadingClusters(true);
        const res = await fetch("/api/v1/analytics/clustering");
        if (res.ok) {
          const json = await res.json();
          setClusters(json);
        }
      } catch (err) {
        console.error("Error loading clustering statistics:", err);
      } finally {
        setLoadingClusters(false);
      }
    }
    loadClusters();
  }, []);

  // Filter and sort metrics lists
  const filteredMetrics = metrics.filter(m => {
    const matchesSearch = m.county_name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          m.county_code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTier = activeTierFilter === "all" || m.development_tier?.toString() === activeTierFilter;
    const matchesStatus = statusFilter === "all" || m.availability_status === statusFilter;
    return matchesSearch && matchesTier && matchesStatus;
  }).sort((a: any, b: any) => {
    const factor = sortOrder === "asc" ? 1 : -1;
    const valA = a[sortBy] ?? 0;
    const valB = b[sortBy] ?? 0;
    if (typeof valA === "string") {
      return valA.localeCompare(valB) * factor;
    }
    return (valA - valB) * factor;
  });

  const toggleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(o => o === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  };

  // Build scatter plot series
  const scatterSeries = metrics.map(m => ({
    name: m.county_name,
    code: m.county_code,
    gdp: m.gdp_contribution_pct,
    growth: m.population_growth_pct,
    population: m.population,
    tier: m.development_tier
  }));

  const getTierBadgeClass = (tier: number) => {
    switch (tier) {
      case 1: return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400";
      case 2: return "bg-cyan-100 text-cyan-800 dark:bg-cyan-950/40 dark:text-cyan-400";
      case 3: return "bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-400";
      case 4: return "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400";
      default: return "bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400";
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col lg:flex-row gap-6">
        
        {/* Plot - Left Side (Scatter Plot GDP vs Population Growth) */}
        <div className="flex-1 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 px-6 py-5 rounded-3xl shadow-sm">
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <BarChart className="w-4 h-4 text-emerald-600" />
              Economic Scatter Matrix
            </h3>
            <p className="text-[10px] text-gray-500 font-mono mt-0.5 uppercase tracking-wider">County gdp shares vs population growth pct</p>
          </div>

          <div className="h-80 w-full mt-6">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.08)" />
                <XAxis 
                  dataKey="growth" 
                  name="Population Growth Rate" 
                  unit="%" 
                  fontSize={10} 
                  fontClassName="font-mono text-gray-400" 
                  type="number" 
                  tickLine={false} 
                  axisLine={false}
                />
                <YAxis 
                  dataKey="gdp" 
                  name="GDP Contribution" 
                  unit="%" 
                  fontSize={10} 
                  fontClassName="font-mono text-gray-400" 
                  type="number" 
                  tickLine={false} 
                  axisLine={false}
                />
                <ZAxis dataKey="population" range={[40, 400]} name="Population" />
                <ChartTooltip 
                  cursor={{ strokeDasharray: '3 3' }} 
                  contentStyle={{ background: '#0f172a', border: 'none', borderRadius: '12px', fontSize: '10px', color: '#f8fafc' }}
                  formatter={(value: any, name: string, props: any) => {
                    if (name === "Population") return [value?.toLocaleString(), name];
                    return [`${value}%`, name];
                  }}
                  labelFormatter={() => ""}
                />
                <Scatter name="Counties" data={scatterSeries} fill="#10b981">
                  {scatterSeries.map((entry, idx) => {
                    const colors = ["#10b981", "#06b6d4", "#3b82f6", "#f59e0b", "#f43f5e"];
                    const fill = colors[(entry.tier || 1) - 1] || "#10b981";
                    return (
                      <rect
                        key={idx}
                        width={8}
                        height={8}
                        x={props => props.cx - 4}
                        y={props => props.cy - 4}
                        fill={fill}
                        className="cursor-pointer hover:stroke-white transition-colors"
                        onClick={() => onSelectCounty(entry.code)}
                      />
                    );
                  })}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* Color Legend */}
          <div className="flex flex-wrap justify-center gap-4 text-[10px] font-mono mt-4 pt-4 border-t border-slate-50 dark:border-slate-900/60 text-gray-500">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-[#10b981]" /> Tier 1 (High Engine)</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-[#06b6d4]" /> Tier 2 (Upper Engine)</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-[#3b82f6]" /> Tier 3 (Middle Engine)</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-[#f59e0b]" /> Tier 4 (Emerging Engine)</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-[#f43f5e]" /> Tier 5 (Baseline Engine)</span>
          </div>
        </div>

        {/* Dynamic K-Means Clusters List */}
        <div className="w-full lg:w-96 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 px-6 py-5 rounded-3xl shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <Info className="w-4 h-4 text-emerald-600" />
              Machine Learning Clustering (K-Means)
            </h3>
            <p className="text-[10px] text-gray-500 font-mono mt-0.5 uppercase tracking-wider">Unsupervised development clustering</p>
          </div>

          <div className="flex-1 overflow-y-auto max-h-72 mt-4 pr-1 flex flex-col gap-3">
            {loadingClusters ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
                <p className="text-[10px] font-mono text-gray-400 mt-2">Running clustering updates...</p>
              </div>
            ) : clusters?.clusters ? (
              Object.keys(clusters.clusters).map((key) => {
                const cluster = clusters.clusters[key];
                return (
                  <div key={key} className="p-3 border border-slate-100 dark:border-gray-900 bg-slate-50/50 dark:bg-slate-900/10 rounded-xl leading-normal flex flex-col gap-1.5">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-800 dark:text-slate-100">{cluster.label}</span>
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded-full ${getTierBadgeClass(cluster.tier)}`}>
                        Tier {cluster.tier} ({cluster.count} counties)
                      </span>
                    </div>
                    <p className="text-[10px] text-gray-500 font-mono leading-relaxed truncate">
                      {cluster.counties?.join(", ")}
                    </p>
                  </div>
                );
              })
            ) : (
              <div className="flex flex-col items-center justify-center p-6 text-center border border-dashed border-gray-200 rounded-xl">
                <AlertCircle className="w-5 h-5 text-gray-400 mb-1" />
                <p className="text-[10px] text-gray-400 font-mono">No cluster metrics loaded. Standard fallbacks deployed.</p>
              </div>
            )}
          </div>

          <div className="text-[9px] text-gray-500 leading-relaxed font-mono bg-slate-50 dark:bg-slate-900 p-3 rounded-xl border border-slate-100 dark:border-gray-900 mt-3">
            Algorithm: K-Means (K=5) mapped over population density, GDP % contribution, and health safety scores. Recalculated locally during system boots.
          </div>
        </div>

      </div>

      {/* Roster Table - Bottom Section */}
      <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 rounded-3xl p-6 shadow-sm flex flex-col gap-4">
        
        {/* Filter Roster Bar */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 font-sans">47 Counties Register</h3>
            <p className="text-[10px] text-gray-400 font-mono mt-0.5">Filter, search, and audit specific indicators</p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
            {/* Search Input */}
            <div className="relative flex-1 md:flex-initial min-w-[200px]">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
              <input
                id="roster-search"
                type="text"
                placeholder="Search by county..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-xs font-semibold rounded-xl pl-9 pr-4 py-2 w-full focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {/* Filter Dropdown */}
            <select
              id="tier-filter"
              value={activeTierFilter}
              onChange={e => setActiveTierFilter(e.target.value)}
              className="bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-xs font-semibold rounded-xl px-3 py-2 focus:outline-none"
            >
              <option value="all">All Tiers</option>
              <option value="1">Tier 1</option>
              <option value="2">Tier 2</option>
              <option value="3">Tier 3</option>
              <option value="4">Tier 4</option>
              <option value="5">Tier 5</option>
            </select>

            <select
              id="status-filter"
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-xs font-semibold rounded-xl px-3 py-2 focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="AVAILABLE">✅ KNBS Decoded</option>
              <option value="BASELINE_PENDING_KNBS">📭 Baseline Only</option>
            </select>
          </div>
        </div>

        {/* Actual Roster Grid Table */}
        <div className="w-full overflow-x-auto border border-slate-100 dark:border-gray-900 rounded-2xl max-h-96">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 dark:bg-slate-900/50 text-[10px] font-mono text-gray-500 border-b border-slate-100 dark:border-gray-900 select-none">
                <th className="px-5 py-3 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/50 font-semibold" onClick={() => toggleSort("county_code")}>Code</th>
                <th className="px-5 py-3 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/50 font-semibold" onClick={() => toggleSort("county_name")}>County</th>
                <th className="px-5 py-3 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/50 font-semibold text-right" onClick={() => toggleSort("population")}>Population (est)</th>
                <th className="px-5 py-3 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/50 font-semibold text-right" onClick={() => toggleSort("gdp_contribution_pct")}>GDP Share</th>
                <th className="px-5 py-3 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/50 font-semibold text-right" onClick={() => toggleSort("health_score")}>Health Score</th>
                <th className="px-5 py-3 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/50 font-semibold text-right" onClick={() => toggleSort("employment_rate")}>Employment %</th>
                <th className="px-5 py-3 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/50 font-semibold text-center" onClick={() => toggleSort("development_tier")}>Tier</th>
                <th className="px-5 py-3 font-semibold text-center">Data Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-gray-900 text-xs text-slate-700 dark:text-gray-300 font-sans">
              {filteredMetrics.map((row) => (
                <tr 
                  key={row.county_code} 
                  className="hover:bg-slate-50/30 dark:hover:bg-slate-900/20 transition-colors cursor-pointer"
                  onClick={() => {
                    onSelectCounty(row.county_code);
                    onNavigateTab("detail");
                  }}
                >
                  <td className="px-5 py-3.5 font-mono text-[11px] font-semibold text-slate-400">{row.county_code}</td>
                  <td className="px-5 py-3.5 font-semibold text-slate-800 dark:text-slate-100">{row.county_name}</td>
                  <td className="px-5 py-3.5 font-mono text-right">{row.population?.toLocaleString()}</td>
                  <td className="px-5 py-3.5 font-mono text-right text-emerald-600 dark:text-emerald-400 font-medium">{row.gdp_contribution_pct}%</td>
                  <td className="px-5 py-3.5 font-mono text-right">{row.health_score}</td>
                  <td className="px-5 py-3.5 font-mono text-right">{row.employment_rate}%</td>
                  <td className="px-5 py-3.5 text-center">
                    <span className={`text-[10px] font-mono leading-none font-bold px-2 py-0.5 rounded-full ${getTierBadgeClass(row.development_tier)}`}>
                      Tier {row.development_tier}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-center">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold font-mono ${row.availability_status === "AVAILABLE" ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400" : "bg-amber-500/10 text-amber-600"}`}>
                      {row.availability_status === "AVAILABLE" ? "✅ KNBS Abstract" : "📭 Census Baseline"}
                    </span>
                  </td>
                </tr>
              ))}
              {filteredMetrics.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-5 py-8 text-center text-gray-400 font-mono italic">
                    No matching counties found. Try updating search queries.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
