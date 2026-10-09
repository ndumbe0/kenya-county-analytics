import { useState, useEffect } from "react";
import { CountyMetric } from "../types";
import { GitCompare, Award, AlertCircle, ArrowLeftRight } from "lucide-react";

interface ComparisonMatrixProps {
  metrics: CountyMetric[];
  selectedCountyCode?: string;
}

export default function ComparisonMatrix({ metrics, selectedCountyCode }: ComparisonMatrixProps) {
  const [codeA, setCodeA] = useState("");
  const [codeB, setCodeB] = useState("");

  useEffect(() => {
    if (metrics.length > 1) {
      // Initialize dropdowns with standard representative pairs
      const firstCode = selectedCountyCode || metrics[0].county_code;
      setCodeA(firstCode);
      
      const secondCounty = metrics.find(item => item.county_code !== firstCode) || metrics[1];
      setCodeB(secondCounty.county_code);
    }
  }, [metrics, selectedCountyCode]);

  const mA = metrics.find(m => m.county_code === codeA);
  const mB = metrics.find(m => m.county_code === codeB);

  const getLeader = (key: keyof CountyMetric, higherIsBetter = true) => {
    if (!mA || !mB) return null;
    const valA = mA[key] as number;
    const valB = mB[key] as number;
    if (valA === valB) return "draw";
    if (higherIsBetter) {
      return valA > valB ? "A" : "B";
    } else {
      return valA < valB ? "A" : "B";
    }
  };

  // Helper for visual comparison gauge percent fill
  const getGaugePercent = (val: number, max: number) => {
    if (max <= 0) return 0;
    return Math.min(100, Math.max(0, (val / max) * 100));
  };

  return (
    <div className="flex flex-col gap-6">
      
      {/* Selector Dual Panel */}
      <div className="grid grid-cols-1 md:grid-cols-12 items-center gap-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 px-6 py-4 rounded-3xl select-none">
        
        {/* County A Dropdown */}
        <div className="col-span-1 md:col-span-5 flex flex-col gap-1.5">
          <label htmlFor="compare-a" className="text-[10px] font-mono font-bold text-gray-400 uppercase tracking-widest leading-none">County A (Left Panel)</label>
          <select
            id="compare-a"
            value={codeA}
            onChange={e => setCodeA(e.target.value)}
            className="bg-white dark:bg-gray-800 border border-slate-200 dark:border-slate-800 px-4 py-2.5 rounded-2xl text-sm font-bold focus:outline-none focus:ring-2 focus:ring-emerald-500 w-full"
          >
            {metrics.map(item => (
              <option key={item.county_code} value={item.county_code} disabled={item.county_code === codeB}>
                {item.county_code} - {item.county_name}
              </option>
            ))}
          </select>
        </div>

        {/* Visual Swap Indicator */}
        <div className="col-span-1 md:col-span-2 flex justify-center text-slate-300 dark:text-slate-700 py-2">
          <div className="p-3 bg-white dark:bg-gray-800 border border-slate-100 dark:border-slate-850 rounded-2xl shadow-sm">
            <ArrowLeftRight className="w-5 h-5 text-emerald-600 animate-pulse" />
          </div>
        </div>

        {/* County B Dropdown */}
        <div className="col-span-1 md:col-span-5 flex flex-col gap-1.5">
          <label htmlFor="compare-b" className="text-[10px] font-mono font-bold text-gray-400 uppercase tracking-widest leading-none">County B (Right Panel)</label>
          <select
            id="compare-b"
            value={codeB}
            onChange={e => setCodeB(e.target.value)}
            className="bg-white dark:bg-gray-800 border border-slate-200 dark:border-slate-800 px-4 py-2.5 rounded-2xl text-sm font-bold focus:outline-none focus:ring-2 focus:ring-emerald-500 w-full"
          >
            {metrics.map(item => (
              <option key={item.county_code} value={item.county_code} disabled={item.county_code === codeA}>
                {item.county_code} - {item.county_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {mA && mB ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Key Leaderboard Banner */}
          <div className="col-span-1 lg:col-span-12 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 p-5 rounded-3xl flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/10 text-amber-500 rounded-xl">
                <Award className="w-5 h-5 animate-bounce" />
              </div>
              <div className="text-xs">
                <span className="font-bold text-slate-800 dark:text-slate-100">Economic Leadership Matrix:</span>
                <p className="text-gray-500 mt-0.5">Summary comparisons of developmental indices</p>
              </div>
            </div>
            
            <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
              <div className="px-3 py-1 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-gray-900 rounded-lg">
                🏆 Population Head: <span className="font-bold text-slate-800 dark:text-slate-200">{getLeader("population") === "A" ? mA.county_name : mB.county_name}</span>
              </div>
              <div className="px-3 py-1 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-gray-900 rounded-lg">
                📈 GDP Leader: <span className="font-bold text-slate-800 dark:text-slate-200">{getLeader("gdp_contribution_pct") === "A" ? mA.county_name : mB.county_name}</span>
              </div>
              <div className="px-3 py-1 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-gray-900 rounded-lg">
                🌟 Higher Dev Tier: <span className="font-bold text-slate-800 dark:text-slate-200">{getLeader("development_tier", false) === "A" ? mA.county_name : mB.county_name}</span>
              </div>
            </div>
          </div>

          {/* Core Gauge Fields side-by-side comparisons */}
          <div className="col-span-1 lg:col-span-12 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 rounded-3xl p-6 shadow-sm flex flex-col gap-6">
            
            {/* Header Column Labels */}
            <div className="grid grid-cols-12 gap-4 pb-3 border-b border-slate-50 dark:border-slate-900 select-none items-center">
              <div className="col-span-5 text-left"><span className="text-xs font-bold text-slate-800 dark:text-slate-100">{mA.county_name}</span> <span className="text-[10px] font-mono text-gray-400 bg-slate-50 dark:bg-slate-900 px-1.5 py-0.5 rounded ml-1">Code {mA.county_code}</span></div>
              <div className="col-span-2 text-center text-[10px] font-mono font-bold text-slate-400 uppercase tracking-widest">Indicators</div>
              <div className="col-span-5 text-right"><span className="text-[10px] font-mono text-gray-400 bg-slate-50 dark:bg-slate-900 px-1.5 py-0.5 rounded mr-1">Code {mB.county_code}</span> <span className="text-xs font-bold text-slate-800 dark:text-slate-100">{mB.county_name}</span></div>
            </div>

            {/* Gauge Sections */}
            {[
              { label: "Population", key: "population", format: (v: number) => v.toLocaleString(), max: 5000000, desc: "Total population from pre-computed metrics" },
              { label: "GDP Contribution Share", key: "gdp_contribution_pct", format: (v: number) => `${v}%`, max: 30, desc: "County share of total nationwide GDP value" },
              { label: "Health Index Score", key: "health_score", format: (v: number) => `${v} / 100`, max: 100, desc: "Composite health services and residual benchmark" },
              { label: "Education Quality", key: "education_rating", format: (v: number) => `${v} / 5`, max: 5, desc: "KNBS and local abstract literacy rating score" },
              { label: "Employment Rate", key: "employment_rate", format: (v: number) => `${v}%`, max: 100, desc: "County labor force outcome indicator" },
              { label: "Composite Development Score", key: "development_score", format: (v: number) => `${v} pts`, max: 100, desc: "Aggregated physical & digital development score" }
            ].map((metric, i) => {
              const valA = mA[metric.key as keyof CountyMetric] as number || 0;
              const valB = mB[metric.key as keyof CountyMetric] as number || 0;
              const pctA = getGaugePercent(valA, metric.max);
              const pctB = getGaugePercent(valB, metric.max);
              const leader = getLeader(metric.key as keyof CountyMetric, metric.key !== "development_tier");

              return (
                <div key={i} className="flex flex-col gap-2">
                  <div className="grid grid-cols-12 items-center gap-4 text-xs font-mono">
                    
                    {/* Val Left A */}
                    <div className="col-span-4 text-left leading-none flex items-center gap-2">
                      <span className={`font-bold font-sans text-sm ${leader === "A" ? "text-emerald-600 dark:text-emerald-400" : "text-gray-500"}`}>
                        {metric.format(valA)}
                      </span>
                      {leader === "A" && <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1 py-0.2 rounded font-bold font-sans">WIN</span>}
                    </div>

                    {/* Central Title */}
                    <div className="col-span-4 text-center">
                      <div className="font-semibold text-slate-700 dark:text-slate-300 font-sans tracking-tight">{metric.label}</div>
                      <div className="text-[8px] text-gray-400 font-sans mt-0.5">{metric.desc}</div>
                    </div>

                    {/* Val Right B */}
                    <div className="col-span-4 text-right leading-none flex items-center justify-end gap-2">
                      {leader === "B" && <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1 py-0.2 rounded font-bold font-sans">WIN</span>}
                      <span className={`font-bold font-sans text-sm ${leader === "B" ? "text-emerald-600 dark:text-emerald-400" : "text-gray-500"}`}>
                        {metric.format(valB)}
                      </span>
                    </div>

                  </div>

                  {/* Dual Bar Gauge sliders */}
                  <div className="grid grid-cols-12 gap-8 items-center">
                    
                    {/* Left bar filled to the right */}
                    <div className="col-span-6 h-2 bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden flex justify-end">
                      <div 
                        style={{ width: `${pctA}%` }} 
                        className={`h-full rounded-full transition-all duration-300 ${leader === "A" ? "bg-[#10b981]" : "bg-slate-400"}`} 
                      />
                    </div>

                    {/* Right bar filled to the left */}
                    <div className="col-span-6 h-2 bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                      <div 
                        style={{ width: `${pctB}%` }} 
                        className={`h-full rounded-full transition-all duration-300 ${leader === "B" ? "bg-[#10b981]" : "bg-slate-400"}`} 
                      />
                    </div>

                  </div>
                </div>
              );
            })}

            {/* Custom Notes */}
            <div className="flex gap-2 items-start text-[10px] leading-relaxed text-gray-500 bg-slate-50 dark:bg-slate-900 px-4 py-3 border border-slate-100 dark:border-gray-900 rounded-2xl font-sans mt-2 select-none">
              <AlertCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              This duel audit matrix is pre-computed directly from KNBS abstracts. For counties running on baselines, comparisons revert back to standard 2019 census figures automatically for alignment.
            </div>

          </div>
        </div>
      ) : (
        <div className="p-12 text-center border border-dashed border-gray-200 rounded-3xl">
          <GitCompare className="w-8 h-8 text-slate-300 mx-auto animate-spin" />
          <p className="text-xs text-gray-500 font-mono mt-2">Loading Dual-Comparison Matrix indicators...</p>
        </div>
      )}
    </div>
  );
}
