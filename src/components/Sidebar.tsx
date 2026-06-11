import { 
  Map, 
  LayoutDashboard, 
  GitCompare, 
  Bot, 
  Download, 
  BookOpen,
  Sliders,
  Sparkles
} from "lucide-react";

export type TabKey = 'home' | 'detail' | 'analytics' | 'compare' | 'chat' | 'data' | 'guideline';

interface SidebarProps {
  activeTab: TabKey;
  setActiveTab: (tab: TabKey) => void;
  selectedCountyName?: string;
}

export default function Sidebar({ activeTab, setActiveTab, selectedCountyName }: SidebarProps) {
  const navItems = [
    { key: 'home', label: 'Home Map', icon: Map, desc: 'Interactive county mapping' },
    { key: 'detail', label: 'County Detail', icon: Sliders, desc: selectedCountyName ? `Stats for ${selectedCountyName}` : 'Deep-dive indicators' },
    { key: 'analytics', label: 'ML Analytics', icon: LayoutDashboard, desc: 'Clustering & forecast models' },
    { key: 'compare', label: 'County Compare', icon: GitCompare, desc: 'Dual-county audit matrices' },
    { key: 'chat', label: 'AI Assistants', icon: Bot, desc: 'Rule-based & Gemini chat' },
    { key: 'data', label: 'Data Center', icon: Download, desc: 'Download CSV & JSON exports' },
    { key: 'guideline', label: 'BI & Pipelines', icon: BookOpen, desc: 'Power BI, Tableau & n8n' },
  ];

  return (
    <aside className="w-full lg:w-72 border-r border-slate-100 dark:border-gray-800 p-6 flex flex-col justify-between shrink-0 bg-white/60 dark:bg-gray-950/60 backdrop-blur-md h-full">
      <div className="flex flex-col gap-8">
        
        {/* Branding Title */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-11 h-11 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-sm shadow-emerald-500/20 text-white font-bold text-lg">
            K
            <Sparkles className="absolute -top-1 -right-1 w-4 h-4 text-amber-400 animate-pulse" />
          </div>
          <div>
            <h1 className="text-[15px] font-sans font-bold tracking-tight text-slate-800 dark:text-slate-100">Kenya County</h1>
            <p className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold tracking-wider uppercase">Analytics Hub</p>
          </div>
        </div>

        {/* Separator / Ingest Banner */}
        <div className="bg-emerald-50 dark:bg-emerald-950/20 px-4 py-3 rounded-2xl border border-emerald-100/30 dark:border-emerald-800/10">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-mono font-bold text-emerald-800 dark:text-emerald-400 uppercase tracking-wide">KNBS Ingestion Log</span>
          </div>
          <p className="text-[11px] text-emerald-700/85 dark:text-emerald-500/85 mt-1 leading-normal font-sans">
            Currently **16 / 47** counties contain uploaded PDF statistical digests.
          </p>
        </div>

        {/* Menu Items */}
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.key;
            return (
              <button
                key={item.key}
                onClick={() => setActiveTab(item.key as TabKey)}
                id={`sidebar-tab-${item.key}`}
                className={`flex items-center gap-4 px-4 py-3 border rounded-2xl transition-all text-left ${
                  isActive 
                    ? 'bg-slate-900 border-slate-900 text-white shadow-md dark:bg-slate-100 dark:border-slate-100 dark:text-slate-900' 
                    : 'bg-transparent border-transparent text-gray-500 dark:text-gray-400 hover:bg-slate-50 dark:hover:bg-slate-900 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
              >
                <Icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-white dark:text-slate-900' : 'text-slate-400'}`} />
                <div>
                  <div className="text-xs font-semibold leading-none">{item.label}</div>
                  <div className={`text-[9px] mt-0.5 leading-none font-sans ${isActive ? 'text-white/70 dark:text-slate-900/70' : 'text-gray-400'}`}>
                    {item.desc}
                  </div>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Branding */}
      <div className="text-[10px] font-mono text-gray-400 dark:text-gray-500 mt-8 pt-4 border-t border-slate-100 dark:border-gray-800 text-center">
        KNBS Data Pipeline 2026<br />
        <span className="text-emerald-600/80 font-bold uppercase tracking-wider">Production Environment</span>
      </div>
    </aside>
  );
}
