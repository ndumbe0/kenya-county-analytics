import { useState, useEffect } from "react";
import Sidebar, { TabKey } from "./components/Sidebar";
import Map from "./components/Map";
import CountyDetail from "./components/CountyDetail";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import ComparisonMatrix from "./components/ComparisonMatrix";
import AssistantsChat from "./components/AssistantsChat";
import DataExport from "./components/DataExport";
import ManualTabs from "./components/ManualTabs";
import { CountyMetric } from "./types";
import { Loader2, AlertCircle, Database, HelpCircle, FileText, Info } from "lucide-react";

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('home');
  const [metrics, setMetrics] = useState<CountyMetric[]>([]);
  const [selectedCountyCode, setSelectedCountyCode] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load general county metrics database once on App Mount
  useEffect(() => {
    async function loadCountyMetrics() {
      try {
        setLoading(true);
        setError(null);
        const res = await fetch("/api/v1/counties");
        if (!res.ok) {
          throw new Error("Unable to retrieve county analytics from Express API backend.");
        }
        const data = await res.json();
        setMetrics(data);
        
        // Default select Nairobi on load to ensure smooth initial detail look-up
        const defaultCounty = data.find((x: any) => x.county_name === "Nairobi") || data[0];
        if (defaultCounty) {
          setSelectedCountyCode(defaultCounty.county_code);
        }
      } catch (err: any) {
        console.error("Error loading metrics:", err);
        setError(err.message || "Failed to establish a connection with the server.");
      } finally {
        setLoading(false);
      }
    }
    loadCountyMetrics();
  }, []);

  const handleSelectCounty = (code: string) => {
    setSelectedCountyCode(code);
    setActiveTab('detail'); // auto focus to details sheet when user clicks map
  };

  const selectedCountyName = metrics.find(x => x.county_code === selectedCountyCode)?.county_name;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950 font-sans">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-600 mb-2" />
        <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">Synchronizing Kenya County Analytics ledger...</p>
        <p className="text-xs text-gray-400 font-mono mt-1">Bootstrapping Express server APIs</p>
      </div>
    );
  }

  // Render proper subpage inside responsive layouts
  const renderTabContent = () => {
    switch (activeTab) {
      case 'home':
        return (
          <div className="flex flex-col gap-6">
            
            {/* Top Stat Banners */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none">
              <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 p-5 rounded-2xl flex flex-col justify-between hover:shadow-xs transition shadow-[0_2px_8px_-3px_rgba(0,0,0,0.05)]">
                <span className="text-[9px] font-mono font-bold text-gray-400 uppercase tracking-wide">Nationwide GDP Coverage</span>
                <div className="text-lg font-bold font-sans text-slate-800 dark:text-slate-100 mt-2">100% Core Indexing</div>
                <div className="text-[9px] text-emerald-600 dark:text-emerald-405 font-bold font-mono mt-1">47 Counties Tracked</div>
              </div>

              <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 p-5 rounded-2xl flex flex-col justify-between hover:shadow-xs transition shadow-[0_2px_8px_-3px_rgba(0,0,0,0.05)]">
                <span className="text-[9px] font-mono font-bold text-gray-400 uppercase tracking-wide">Total Estimated Population</span>
                <div className="text-lg font-bold font-sans text-slate-800 dark:text-slate-100 mt-2">
                  {(metrics.reduce((acc, cr) => acc + (cr.population || 0), 0) / 1000000).toFixed(2)}M
                </div>
                <div className="text-[9px] text-gray-500 font-semibold font-mono mt-1">Compound projection models</div>
              </div>

              <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 p-5 rounded-2xl flex flex-col justify-between hover:shadow-xs transition shadow-[0_2px_8px_-3px_rgba(0,0,0,0.05)]">
                <span className="text-[9px] font-mono font-bold text-gray-400 uppercase tracking-wide">Decoded PDF Statistical Abstracts</span>
                <div className="text-lg font-bold font-sans text-slate-800 dark:text-slate-100 mt-2">16 Ingested</div>
                <div className="text-[9px] text-amber-500 font-bold font-mono mt-1">31 Reverting to 2019 Census</div>
              </div>

              <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 p-5 rounded-2xl flex flex-col justify-between hover:shadow-xs transition shadow-[0_2px_8px_-3px_rgba(0,0,0,0.05)]">
                <span className="text-[9px] font-mono font-bold text-gray-400 uppercase tracking-wide">Unsupervised Development Tiers</span>
                <div className="text-lg font-bold font-sans text-slate-800 dark:text-slate-100 mt-2">5 Tier Groupings</div>
                <div className="text-[9px] text-emerald-600 font-bold font-mono mt-1">K-Means Algorythm Loaded</div>
              </div>
            </div>

            {/* Core Interactive Map Panel */}
            <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 rounded-3xl p-6 shadow-sm">
              <div className="border-b border-slate-50 dark:border-slate-900 pb-4 mb-6 select-none">
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">Interactive Geographic Heat Map</h3>
                <p className="text-[10px] text-gray-500 font-mono mt-0.5">Left-click and drag to move map, use buttons or mouse scroll to zoom. Select any county to drill-down.</p>
              </div>

              <Map metrics={metrics} onSelectCounty={handleSelectCounty} selectedCountyCode={selectedCountyCode} />
            </div>

          </div>
        );
      case 'detail':
        return (
          <CountyDetail countyCode={selectedCountyCode} metricsList={metrics} onSelectCounty={setSelectedCountyCode} />
        );
      case 'analytics':
        return (
          <AnalyticsDashboard metrics={metrics} onSelectCounty={handleSelectCounty} onNavigateTab={setActiveTab} />
        );
      case 'compare':
        return (
          <ComparisonMatrix metrics={metrics} selectedCountyCode={selectedCountyCode} />
        );
      case 'chat':
        return (
          <AssistantsChat selectedCountyName={selectedCountyName} onNavigateTab={setActiveTab} onSelectCounty={handleSelectCounty} />
        );
      case 'data':
        return (
          <DataExport />
        );
      case 'guideline':
        return (
          <ManualTabs />
        );
    }
  };

  return (
    <div className="flex flex-col lg:flex-row min-h-screen bg-[#F5F8F7] dark:bg-gray-950 text-slate-700 dark:text-gray-300 font-sans">
      
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} selectedCountyName={selectedCountyName} />

      {/* Main Indicators Dashboard viewport */}
      <main className="flex-1 px-6 py-8 md:px-8 max-w-7xl mx-auto w-full overflow-y-auto">
        
        {/* Header Section */}
        <header className="flex items-center justify-between gap-4 pb-6 border-b border-slate-205 dark:border-gray-900 mb-8 select-none">
          <div>
            <h1 className="text-lg font-bold font-sans tracking-tight text-slate-850 dark:text-slate-100">Kenya County Analytics</h1>
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-0.5">KNBS Micro-indicators Portal</p>
          </div>

          <div className="flex items-center gap-2.5">
            <span className="hidden sm:inline-block text-[11px] font-bold text-slate-500 dark:text-gray-400 font-mono bg-white dark:bg-gray-900 border border-slate-100 dark:border-slate-850 px-4 py-2 rounded-xl shadow-xs">
              System Live: 2026 UTC
            </span>
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse ml-1" />
          </div>
        </header>

        {error ? (
          <div className="p-6 bg-red-50 text-red-600 rounded-3xl border border-red-100 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0 animate-bounce" />
            <div>
              <div className="text-sm font-bold">API Connection Timeout</div>
              <div className="text-xs mt-1 text-red-500/85 font-mono">{error}</div>
            </div>
          </div>
        ) : (
          renderTabContent()
        )}
      </main>
    </div>
  );
}
