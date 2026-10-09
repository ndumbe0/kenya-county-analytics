import { Check, BookOpen, Layers, Terminal, AlertCircle, Sparkles, Database } from "lucide-react";

export default function ManualTabs() {
  return (
    <div className="flex flex-col gap-6 font-sans">
      
      {/* 1. Header Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 select-none">
        
        {/* Power BI Card */}
        <div className="bg-gradient-to-br from-[#f2c811]/15 to-amber-500/5 dark:from-[#f2c811]/5 dark:to-transparent border border-amber-500/10 dark:border-amber-950 px-6 py-5 rounded-3xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-[#f2c811]" />
              <span className="text-[10px] font-mono font-bold text-amber-500 uppercase tracking-widest">Business Intelligence</span>
            </div>
            <h3 className="text-base font-bold text-slate-800 dark:text-slate-100 mt-2">Power BI Integration Extract</h3>
            <p className="text-xs text-gray-500 mt-2 leading-relaxed">
              We provide pre-formated tabular summaries suitable for direct Power BI model ingestion.
            </p>
          </div>

          <div className="flex flex-col gap-2 mt-4 text-xs font-mono">
            <span className="text-[9px] uppercase tracking-wider text-gray-400 font-bold">Steps to configure:</span>
            <div className="flex items-start gap-2.5 bg-white dark:bg-gray-900 border border-slate-100 p-2.5 rounded-xl">
              <span className="text-[10px] bg-[#f2c811]/20 font-bold px-1.5 py-0.2 rounded text-amber-700">1</span>
              <p className="text-[11px] leading-snug">Choose **Get Data &gt; Web** inside Power BI Desktop.</p>
            </div>
            <div className="flex items-start gap-2.5 bg-white dark:bg-gray-900 border border-slate-100 p-2.5 rounded-xl">
              <span className="text-[10px] bg-[#f2c811]/20 font-bold px-1.5 py-0.2 rounded text-amber-700">2</span>
              <p className="text-[11px] leading-snug">Supply endpoint URI: **`http://localhost:3000/api/v1/data/download/csv`**</p>
            </div>
          </div>
        </div>

        {/* Tableau Card */}
        <div className="bg-gradient-to-br from-[#30628e]/15 to-blue-500/5 dark:from-[#30628e]/5 dark:to-transparent border border-blue-500/10 dark:border-blue-950 px-6 py-5 rounded-3xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-[#30628e]" />
              <span className="text-[10px] font-mono font-bold text-blue-500 uppercase tracking-widest">visualization</span>
            </div>
            <h3 className="text-base font-bold text-slate-800 dark:text-slate-100 mt-2">Tableau Template Configuration</h3>
            <p className="text-xs text-gray-500 mt-2 leading-relaxed">
              Ingest structured JSON or CSV extracts straight into Tableau worksheets.
            </p>
          </div>

          <div className="flex flex-col gap-2 mt-4 text-xs font-mono">
            <span className="text-[9px] uppercase tracking-wider text-gray-400 font-bold">Steps to configure:</span>
            <div className="flex items-start gap-2.5 bg-white dark:bg-gray-900 border border-slate-100 p-2.5 rounded-xl">
              <span className="text-[10px] bg-[#30628e]/20 font-bold px-1.5 py-0.2 rounded text-blue-700">1</span>
              <p className="text-[11px] leading-snug">Drag downloaded CSV or load directly via custom web connectors.</p>
            </div>
            <div className="flex items-start gap-2.5 bg-white dark:bg-gray-900 border border-slate-100 p-2.5 rounded-xl">
              <span className="text-[10px] bg-[#30628e]/20 font-bold px-1.5 py-0.2 rounded text-blue-700">2</span>
              <p className="text-[11px] leading-snug">Set dimensions: **`County`** matching geolocation fields.</p>
            </div>
          </div>
        </div>

      </div>

      {/* 2. n8n Pipelines Interactive Workflow */}
      <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 rounded-3xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-600 animate-pulse" />
              Automated n8n Ingestion Scraper
            </h3>
            <p className="text-[10px] text-gray-400 font-mono mt-0.5 uppercase tracking-wider">Scraping workflow Sunday 02:00 UTC</p>
          </div>

          <div className="text-[10px] font-mono bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400 px-3 py-1.5 border border-emerald-500/15 rounded-xl text-right font-semibold">
            pipeline script: `n8n_workflows/data_pipeline.json`
          </div>
        </div>

        {/* Interactive SVG Nodes flowchart graph */}
        <div className="mt-8 border border-slate-100 dark:border-gray-900 bg-slate-50/50 dark:bg-slate-900/10 rounded-2xl p-6 flex flex-col md:flex-row justify-between items-center gap-6 relative select-none">
          
          {[
            { id: 1, label: "Sunday 02:00 Scheduler", desc: "n8n cron trigger", color: "border-blue-500/20 bg-blue-500/5 text-blue-500" },
            { id: 2, label: "Crawling KNBS", desc: "HTTP request pdf lists", color: "border-cyan-500/20 bg-cyan-500/5 text-cyan-500" },
            { id: 3, label: "Parser Machine", desc: "Extracting tables nodes", color: "border-indigo-500/20 bg-indigo-500/5 text-indigo-500" },
            { id: 4, label: "Express Indexer API", desc: "Writes to metrics db", color: "border-emerald-500/20 bg-emerald-500/5 text-emerald-500" }
          ].map((node, i, arr) => (
            <div key={node.id} className="flex flex-col md:flex-row items-center gap-4 w-full md:w-auto">
              
              {/* Node Card */}
              <div className={`px-5 py-4 border rounded-xl flex items-center gap-3 w-52 md:w-auto shadow-sm backdrop-blur-sm ${node.color}`}>
                <div className="w-2.5 h-2.5 rounded-full bg-current animate-ping shrink-0" />
                <div className="leading-tight text-left">
                  <div className="text-xs font-bold font-sans text-slate-800 dark:text-slate-100">{node.label}</div>
                  <div className="text-[9px] text-gray-500 font-mono mt-0.5 uppercase tracking-wider">{node.desc}</div>
                </div>
              </div>

              {/* Connecting arrow if not final node */}
              {i < arr.length - 1 && (
                <div className="text-slate-300 dark:text-slate-800 font-bold font-mono rotate-90 md:rotate-0 select-none">
                  ➜
                </div>
              )}
            </div>
          ))}
          
        </div>

        {/* Technical Explainer card */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 leading-normal text-xs text-gray-500 bg-slate-50 dark:bg-slate-900/60 p-4 border border-slate-100 dark:border-gray-900 rounded-2xl select-none">
          <div className="flex gap-2">
            <Check className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <p>
              To run the extraction pipeline, simply import **`n8n_workflows/data_pipeline.json`** inside your local n8n workflow dashboard and run.
            </p>
          </div>
          <div className="flex gap-2">
            <Check className="w-5 h-5 text-[#06b6d4] shrink-0 mt-0.5" />
            <p>
              The scheduler triggers requests to search KNBS servers for the newest County Statistical Abstract PDF releases dynamically.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
