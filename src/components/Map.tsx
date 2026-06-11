import { useState, useEffect, useRef } from "react";
import { geoMercator, geoPath } from "d3-geo";
import { CountyMetric } from "../types";
import { Loader2, Maximize2, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface MapProps {
  metrics: CountyMetric[];
  onSelectCounty: (code: string) => void;
  selectedCountyCode?: string;
}

type MetricKey = 'population' | 'gdp_contribution_pct' | 'health_score' | 'employment_rate' | 'development_score';

export default function Map({ metrics, onSelectCounty, selectedCountyCode }: MapProps) {
  const [geoData, setGeoData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeMetric, setActiveMetric] = useState<MetricKey>('gdp_contribution_pct');
  const [hoveredCounty, setHoveredCounty] = useState<any>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  
  // Transform map states for panning/zooming
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  
  const mapContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadGeoJson() {
      try {
        setLoading(true);
        const res = await fetch("/api/v1/geospatial/counties");
        if (!res.ok) throw new Error("Failed to load map geojson boundaries.");
        const data = await res.json();
        setGeoData(data);
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Unable to display geospatial map.");
      } finally {
        setLoading(false);
      }
    }
    loadGeoJson();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] border border-gray-100 dark:border-gray-800 rounded-2xl bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600 mb-2" />
        <p className="text-sm text-gray-500 font-mono">Loading Geospatial Boundaries...</p>
      </div>
    );
  }

  if (error || !geoData) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] border border-red-100 rounded-2xl bg-red-50/50 p-6 text-center">
        <p className="text-sm font-medium text-red-600">Map Rendering Offline</p>
        <p className="text-xs text-red-500 max-w-sm mt-1">{error || "No boundary data loaded."}</p>
      </div>
    );
  }

  // Set up D3 projection
  const mapWidth = 650;
  const mapHeight = 550;
  
  const projection = geoMercator().fitSize([mapWidth, mapHeight], geoData);
  const pathGen = geoPath().projection(projection);

  // Helper to color counties based on active metric
  const getCountyColor = (feature: any) => {
    const cCode = feature.properties?.county_code;
    const m = metrics.find(item => item.county_code === cCode);
    
    if (!m) return "#e5e7eb"; // fallback gray
    
    const isSelected = m.county_code === selectedCountyCode;
    
    // Normalize values to 0-1 scale for gradients
    let val = 0;
    let min = 0;
    let max = 1;

    if (activeMetric === 'population') {
      val = m.population || 0;
      min = Math.min(...metrics.map(x => x.population || 0));
      max = Math.max(...metrics.map(x => x.population || 0));
    } else if (activeMetric === 'gdp_contribution_pct') {
      val = m.gdp_contribution_pct || 0;
      min = Math.min(...metrics.map(x => x.gdp_contribution_pct || 0));
      max = Math.max(...metrics.map(x => x.gdp_contribution_pct || 0));
    } else if (activeMetric === 'health_score') {
      val = m.health_score || 0;
      min = Math.min(...metrics.map(x => x.health_score || 0));
      max = Math.max(...metrics.map(x => x.health_score || 0));
    } else if (activeMetric === 'employment_rate') {
      val = m.employment_rate || 0;
      min = Math.min(...metrics.map(x => x.employment_rate || 0));
      max = Math.max(...metrics.map(x => x.employment_rate || 0));
    } else if (activeMetric === 'development_score') {
      val = m.development_score || 0;
      min = Math.min(...metrics.map(x => x.development_score || 0));
      max = Math.max(...metrics.map(x => x.development_score || 0));
    }

    const norm = max > min ? (val - min) / (max - min) : 0.5;

    // Return gorgeous Tailwind-like emerald gradients
    if (isSelected) {
      return "url(#selectedGlow)";
    }

    // Emerald gradient interpolations
    if (norm < 0.2) return "rgba(16, 185, 129, 0.15)";
    if (norm < 0.4) return "rgba(16, 185, 129, 0.35)";
    if (norm < 0.6) return "rgba(16, 185, 129, 0.55)";
    if (norm < 0.8) return "rgba(16, 185, 129, 0.75)";
    return "rgba(5, 150, 105, 0.95)"; // Deep forest emerald
  };

  const getMetricDisplayValue = (m: CountyMetric) => {
    const val = m[activeMetric];
    if (activeMetric === 'population') {
      return val?.toLocaleString();
    }
    if (activeMetric === 'gdp_contribution_pct' || activeMetric === 'employment_rate') {
      return `${val}%`;
    }
    if (activeMetric === 'health_score') {
      return `${val} / 100`;
    }
    if (activeMetric === 'development_score') {
      return `${val} pts`;
    }
    return String(val);
  };

  // Mouse handlers for custom responsive hover tooltips
  const handleMouseMove = (e: React.MouseEvent, feature: any) => {
    if (!mapContainerRef.current) return;
    const rect = mapContainerRef.current.getBoundingClientRect();
    setTooltipPos({
      x: e.clientX - rect.left + 15,
      y: e.clientY - rect.top + 15
    });

    const cCode = feature.properties?.county_code;
    const m = metrics.find(item => item.county_code === cCode);
    setHoveredCounty({
      properties: feature.properties,
      metric: m
    });
  };

  const handlePointerDown = (e: React.PointerEvent) => {
    // Left click only
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    setOffset({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    setIsDragging(false);
    e.currentTarget.releasePointerCapture(e.pointerId);
  };

  const resetZoomPan = () => {
    setZoom(1);
    setOffset({ x: 0, y: 0 });
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      {/* Map Control Sidebar */}
      <div className="w-full lg:w-64 shrink-0 flex flex-col gap-4">
        <div className="bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 p-4 rounded-2xl">
          <label className="text-xs font-mono font-medium text-slate-500 uppercase tracking-widest block mb-3">Map Metric</label>
          <div className="flex flex-col gap-2">
            {[
              { key: 'gdp_contribution_pct', label: 'GDP Contribution', desc: 'County share of national GDP %' },
              { key: 'population', label: 'Population', desc: 'Estimated county population' },
              { key: 'health_score', label: 'Health Score', desc: 'Residual safety benchmark' },
              { key: 'employment_rate', label: 'Employment Rate', desc: 'Labor outcomes %' },
              { key: 'development_score', label: 'Development Index', desc: 'Composite development index' },
            ].map(m => (
              <button
                key={m.key}
                onClick={() => setActiveMetric(m.key as MetricKey)}
                id={`btn-metric-${m.key}`}
                className={`text-left p-3 rounded-xl transition-all border ${
                  activeMetric === m.key 
                    ? 'bg-white dark:bg-gray-800 border-emerald-500/30 text-emerald-700 dark:text-emerald-400 font-medium shadow-sm' 
                    : 'bg-transparent border-transparent text-gray-600 dark:text-gray-400 hover:bg-white/50 dark:hover:bg-slate-800/50'
                }`}
              >
                <div className="text-sm leading-tight">{m.label}</div>
                <div className="text-[10px] text-gray-500 dark:text-gray-500 mt-0.5">{m.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 p-4 rounded-2xl flex flex-col gap-3">
          <span className="text-xs font-mono font-medium text-slate-500 uppercase tracking-widest block">Heat Gradient</span>
          <div className="flex items-center gap-1">
            <div className="h-3 w-full rounded-md bg-gradient-to-r from-emerald-500/15 via-emerald-500/55 to-emerald-600" />
          </div>
          <div className="flex justify-between text-[10px] text-gray-500 font-mono mt-0.5">
            <span>LOW</span>
            <span>HIGH</span>
          </div>
        </div>
      </div>

      {/* Actual Map Screen */}
      <div className="flex-1 relative border border-gray-100 dark:border-gray-800 rounded-3xl bg-white dark:bg-gray-950 overflow-hidden shadow-sm" ref={mapContainerRef}>
        
        {/* Navigation / Zoom Controls */}
        <div className="absolute top-4 left-4 z-10 flex flex-col gap-1.5 bg-white/95 dark:bg-gray-900/95 border border-gray-100 dark:border-gray-800 p-1.5 rounded-xl shadow-sm backdrop-blur-sm">
          <button onClick={() => setZoom(z => Math.min(6, z + 0.3))} className="p-2 hover:bg-slate-50 dark:hover:bg-gray-800 rounded-lg text-gray-600 dark:text-gray-400 transition" title="Zoom In">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button onClick={() => setZoom(z => Math.max(0.6, z - 0.3))} className="p-2 hover:bg-slate-50 dark:hover:bg-gray-800 rounded-lg text-gray-600 dark:text-gray-400 transition" title="Zoom Out">
            <ZoomOut className="w-4 h-4" />
          </button>
          <button onClick={resetZoomPan} className="p-2 hover:bg-slate-50 dark:hover:bg-gray-800 rounded-lg text-gray-600 dark:text-gray-400 transition" title="Reset View">
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        <div className="absolute top-4 right-4 z-10 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-100/30 dark:border-emerald-800/10 px-3 py-1.5 rounded-xl text-[11px] text-emerald-800 dark:text-emerald-400 font-mono shadow-sm flex items-center gap-1.5">
          <Maximize2 className="w-3.5 h-3.5 animate-pulse text-emerald-600" />
          Drag to Pan, Scroll / Click to Zoom
        </div>

        {/* SVG Wrapper */}
        <div 
          className={`w-full flex justify-center cursor-move p-2 select-none ${isDragging ? 'grabbing' : 'grab'}`}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onWheel={(e) => {
            const zFactor = e.deltaY < 0 ? 1.05 : 0.95;
            setZoom(z => Math.max(0.5, Math.min(8, z * zFactor)));
          }}
        >
          <svg 
            width={mapWidth} 
            height={mapHeight} 
            viewBox={`0 0 ${mapWidth} ${mapHeight}`}
            className="w-full h-auto max-h-[500px]"
          >
            <defs>
              {/* Selected County Stripe Pattern Glow */}
              <pattern id="selectedGlowPattern" width="6" height="6" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                <line x1="0" y1="0" x2="0" y2="6" stroke="rgba(245, 158, 11, 0.2)" strokeWidth="3" />
              </pattern>
              <linearGradient id="selectedGlow" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#d97706" stopOpacity="0.95" />
              </linearGradient>
            </defs>

            {/* Render Paths */}
            <g transform={`translate(${offset.x}, ${offset.y}) scale(${zoom})`} className="transition-transform duration-100 ease-out">
              {geoData.features.map((feature: any, idx: number) => {
                const cCode = feature.properties?.county_code;
                const m = metrics.find(item => item.county_code === cCode);
                const isSelected = cCode === selectedCountyCode;

                return (
                  <path
                    key={idx}
                    d={pathGen(feature) || ""}
                    fill={getCountyColor(feature)}
                    stroke={isSelected ? "#b45309" : "#ffffff"}
                    strokeWidth={isSelected ? 1.8 / zoom : 0.4 / zoom}
                    strokeLinejoin="round"
                    className="transition-colors duration-200 cursor-pointer hover:stroke-amber-400 hover:opacity-[0.88]"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (cCode) onSelectCounty(cCode);
                    }}
                    onMouseMove={(e) => handleMouseMove(e, feature)}
                    onMouseLeave={() => setHoveredCounty(null)}
                  />
                );
              })}
            </g>
          </svg>
        </div>

        {/* Hover Hover Custom Tooltip */}
        {hoveredCounty && (
          <div 
            style={{ 
              position: 'absolute', 
              left: tooltipPos.x, 
              top: tooltipPos.y,
              pointerEvents: 'none'
            }}
            className="z-50 bg-slate-900/95 dark:bg-black/95 text-slate-100 p-4 rounded-xl border border-slate-800 shadow-xl max-w-xs text-xs backdrop-blur-md"
          >
            <div className="font-semibold text-sm border-b border-white/10 pb-1 flex justify-between items-center gap-4">
              <span>{hoveredCounty.properties?.county_name || hoveredCounty.properties?.name}</span>
              <span className="font-mono text-[10px] text-gray-400 bg-white/10 px-1.5 py-0.5 rounded">
                Code {hoveredCounty.properties?.county_code || hoveredCounty.metric?.county_code}
              </span>
            </div>

            {hoveredCounty.metric ? (
              <div className="flex flex-col gap-1.5 mt-2">
                <div className="flex justify-between gap-4 font-mono">
                  <span className="text-gray-400 uppercase text-[9px] tracking-wider font-semibold">Active Stat:</span>
                  <span className="text-amber-400 font-bold">{getMetricDisplayValue(hoveredCounty.metric)}</span>
                </div>
                <div className="flex justify-between gap-4 font-mono">
                  <span className="text-gray-400 uppercase text-[9px] tracking-wider">Dev Index:</span>
                  <span>{hoveredCounty.metric.development_score} pts</span>
                </div>
                <div className="flex justify-between gap-4 font-mono">
                  <span className="text-gray-400 uppercase text-[9px] tracking-wider">Eco Status:</span>
                  <span className={hoveredCounty.metric.availability_status === "AVAILABLE" ? "text-emerald-400 font-medium" : "text-amber-400"}>
                    {hoveredCounty.metric.availability_status === "AVAILABLE" ? "✅ KNBS Decoded" : "📭 Baseline Only"}
                  </span>
                </div>
                <div className="flex justify-between gap-4 font-mono pt-1 border-t border-white/5">
                  <span className="text-gray-400 uppercase text-[9px] tracking-wider">GDP Contribution:</span>
                  <span>{hoveredCounty.metric.gdp_contribution_pct ?? "N/A"}%</span>
                </div>
                <div className="flex justify-between gap-4 font-mono">
                  <span className="text-gray-400 uppercase text-[9px] tracking-wider font-semibold">Development Tier:</span>
                  <span className="text-slate-100 font-semibold bg-emerald-700/60 leading-none px-1 py-0.5 rounded">
                    Tier {hoveredCounty.metric.development_tier} / 5
                  </span>
                </div>
                <p className="text-[9px] text-slate-400 font-medium italic mt-2 text-center border-t border-slate-800 pt-1">
                  Click county for forecast & models deep dive
                </p>
              </div>
            ) : (
              <p className="text-slate-400 italic mt-2">No indicators pre-loaded for this region.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
