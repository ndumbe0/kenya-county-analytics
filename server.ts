import express, { Request, Response, NextFunction } from "express";
import path from "path";
import fs from "fs";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(express.json());

const PORT = 3000;

// Lazy initialize Gemini AI client
let aiClient: GoogleGenAI | null = null;
function getGeminiClient(): GoogleGenAI | null {
  if (!aiClient) {
    const key = process.env.GEMINI_API_KEY;
    if (key && key !== "MY_GEMINI_API_KEY") {
      aiClient = new GoogleGenAI({
        apiKey: key,
        httpOptions: {
          headers: {
            "User-Agent": "aistudio-build",
          },
        },
      });
      console.log("Initialized server-side Gemini AI client successfully.");
    } else {
      console.warn("GEMINI_API_KEY environment variable is not configured. Falling back to offline botanical rule-based chat.");
    }
  }
  return aiClient;
}

// Global cached data to avoid redundant IO
const dataPaths = {
  metrics: path.join(process.cwd(), "src/data/processed/county_metrics.json"),
  forecast: path.join(process.cwd(), "src/data/processed/ml/population_forecast.json"),
  clusters: path.join(process.cwd(), "src/data/processed/ml/economic_clusters.json"),
  education: path.join(process.cwd(), "src/data/processed/ml/education_employment.json"),
  anomalies: path.join(process.cwd(), "src/data/processed/ml/health_anomalies.json"),
  geospatial: path.join(process.cwd(), "src/data/geospatial/kenya-counties.geojson"),
  downloadLog: path.join(process.cwd(), "src/data/processed/download_log.json")
};

function readJSONFile<T>(filePath: string, fallback: T): T {
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, "utf-8");
      return JSON.parse(content) as T;
    }
  } catch (error) {
    console.error(`Error reading or parsing JSON file at ${filePath}:`, error);
  }
  return fallback;
}

// -------------------------------------------------------------
// AI Chatbots Rules & Offline Fallbacks
// -------------------------------------------------------------
const COUNTIES = [
  "Mombasa", "Kwale", "Kilifi", "Tana River", "Lamu", "Taita-Taveta",
  "Garissa", "Wajir", "Mandera", "Marsabit", "Isiolo", "Meru",
  "Tharaka-Nithi", "Embu", "Kitui", "Machakos", "Makueni", "Nyandarua",
  "Nyeri", "Kirinyaga", "Murang'a", "Kiambu", "Turkana", "West Pokot",
  "Samburu", "Trans Nzoia", "Uasin Gishu", "Elgeyo-Marakwet", "Nandi",
  "Baringo", "Laikipia", "Nakuru", "Narok", "Kajiado", "Kericho",
  "Bomet", "Kakamega", "Vihiga", "Bungoma", "Busia", "Siaya",
  "Kisumu", "Homa Bay", "Migori", "Kisii", "Nyamira", "Nairobi",
];

const COUNTY_ALIASES: Record<string, string> = {};
for (const c of COUNTIES) {
  COUNTY_ALIASES[c.toLowerCase()] = c;
}
COUNTY_ALIASES["muranga"] = "Murang'a";
COUNTY_ALIASES["tharaka nithi"] = "Tharaka-Nithi";
COUNTY_ALIASES["taita taveta"] = "Taita-Taveta";
COUNTY_ALIASES["elgeyo marakwet"] = "Elgeyo-Marakwet";
COUNTY_ALIASES["trans nzoia"] = "Trans Nzoia";
COUNTY_ALIASES["uasin gishu"] = "Uasin Gishu";
COUNTY_ALIASES["homa bay"] = "Homa Bay";
COUNTY_ALIASES["tana river"] = "Tana River";
COUNTY_ALIASES["west pokot"] = "West Pokot";

function findCountiesInText(text: string): string[] {
  const lower = text.toLowerCase();
  const found: string[] = [];
  const seen = new Set<string>();

  // Check aliases first
  for (const [alias, canonical] of Object.entries(COUNTY_ALIASES)) {
    const rx = new RegExp(`\\b${alias}\\b`, 'i');
    if (rx.test(lower) && !seen.has(canonical)) {
      found.push(canonical);
      seen.add(canonical);
    }
  }

  // General check
  if (found.length === 0) {
    for (const c of COUNTIES) {
      if (lower.includes(c.toLowerCase()) && !seen.has(c)) {
        found.push(c);
        seen.add(c);
      }
    }
  }
  return found;
}

// Offline fallback bot logic mirroring Python codebase
function respondOffline(agent: string, query: string, metrics: any[], downloadLog: any): any {
  const q = query.toLowerCase().trim();
  const counties = findCountiesInText(query);
  let answer = "";
  let citations: string[] = [];

  if (agent === "data") {
    citations = ["src/data/processed/county_metrics.json", "src/data/processed/download_log.json"];
    
    if (q.includes("how many counties") || q.includes("total counties") || q.includes("number of counties")) {
      const available = downloadLog ? Object.values(downloadLog).filter((e: any) => e.file_status === "AVAILABLE" || e.status === "AVAILABLE").length : 16;
      answer = `Kenya has **47 counties**. KNBS County Statistical Abstract PDFs are currently available for **${available}** of them on this platform; the remaining ${47 - available} counties fall back to 2019 Census baseline estimates.`;
    } else if (q.includes("available") || q.includes("uploaded") || q.includes("have data")) {
      if (counties.length === 0) {
        const available = downloadLog ? Object.values(downloadLog).filter((e: any) => e.file_status === "AVAILABLE" || e.status === "AVAILABLE").length : 16;
        answer = `${available} of 47 counties have ingested KNBS abstracts. Ask me about a specific county to check.`;
      } else {
        const lines = counties.map(c => {
          const entry = downloadLog ? (downloadLog[c] || {}) : {};
          const isAvail = entry.file_status === "AVAILABLE" || entry.status === "AVAILABLE";
          if (isAvail) {
            return `Yes, **${c}** has data (year: ${entry.abstract_year || "2025"}).`;
          } else {
            return `**${c}** is currently marked DATA_UNAVAILABLE - using 2019 Census baseline estimates.`;
          }
        });
        answer = lines.join("\n\n");
      }
    } else if (q.includes("compare") && counties.length >= 2) {
      const [c1, c2] = counties;
      const m1 = metrics.find(m => m.county_name === c1);
      const m2 = metrics.find(m => m.county_name === c2);
      if (m1 && m2) {
        answer = `**Comparing ${c1} and ${c2}:**\n\n` + 
                 `- **Population**: ${c1} (~${m1.population?.toLocaleString()}) vs ${c2} (~${m2.population?.toLocaleString()})\n` +
                 `- **GDP Contribution**: ${m1.gdp_contribution_pct ?? "N/A"}% vs ${m2.gdp_contribution_pct ?? "N/A"}%\n` +
                 `- **Health Score**: ${m1.health_score ?? "N/A"} vs ${m2.health_score ?? "N/A"}\n` +
                 `- **Development Tier**: Tier ${m1.development_tier ?? "N/A"} vs Tier ${m2.development_tier ?? "N/A"}\n` +
                 `- **Employment Rate**: ${m1.employment_rate ?? "N/A"}% vs ${m2.employment_rate ?? "N/A"}%`;
      } else {
        answer = `I couldn't find stats to compare **${c1}** and **${c2}**.`;
      }
    } else if (counties.length > 0) {
      const c = counties[0];
      const m = metrics.find(mt => mt.county_name === c);
      if (m) {
        const status = (downloadLog?.[c]?.file_status === "AVAILABLE" || downloadLog?.[c]?.status === "AVAILABLE") ? "✅ Available" : "📭 Pending (baseline)";
        answer = `**${c} County Stats Overview (${status}):**\n` +
                 `- **Population (est)**: ${m.population?.toLocaleString()}\n` +
                 `- **Growth %**: ${m.population_growth_pct}%\n` +
                 `- **gdp Contribution %**: ${m.gdp_contribution_pct}%\n` +
                 `- **Health Score**: ${m.health_score}\n` +
                 `- **Education Rating**: ${m.education_rating} / 5\n` +
                 `- **Employment Rate**: ${m.employment_rate}%\n` +
                 `- **Development Tier**: Tier ${m.development_tier} / 5`;
      } else {
        answer = `Detailed stats for **${c}** are not currently pre-loaded.`;
      }
    } else if (q.includes("population") || q.includes("people")) {
      const topPop = [...metrics].sort((a, b) => (b.population || 0) - (a.population || 0)).slice(0, 5);
      const lines = topPop.map(m => `**${m.county_name}**: ${m.population?.toLocaleString()}`);
      answer = `**Top 5 most populous counties:**\n` + lines.join("\n");
    } else {
      answer = "I can answer questions about county populations, GDP contribution, health, employment, development tiers, and data ingestion logs. Try asking 'Population of Nairobi' or 'Does Makueni have data?'";
    }
  } else if (agent === "prediction") {
    citations = ["src/ml/population_forecaster.py", "src/ml/economic_clustering.py"];
    if (q.includes("tier") || q.includes("development") || q.includes("cluster")) {
      answer = "Counties are clustered into 5 development tiers (1 = highest, 5 = lowest) using K-Means clustering over geographic population density, GDP contribution %, and health index score. Tier 1 economic centers include Nairobi, Nakuru, and Kisumu. Ask about development tiers or a county comparison to see groupings.";
    } else if (q.includes("fastest") || q.includes("grow")) {
      answer = "The fastest-growing counties are primarily urban-adjacent clusters such as **Kiambu, Machakos, Kajiado, Nakuru, Kisumu**. Arid regions display slower growth in absolute figures. Models utilize compound growth rates adjusted for local developments.";
    } else if (counties.length > 0 && (q.includes("population") || q.includes("forecast") || q.includes("predict") || q.includes("2030") || q.includes("future"))) {
      const county = counties[0];
      const m = metrics.find(mt => mt.county_name === county);
      const basePop = m ? m.population : 800000;
      const rate = 0.023; // national Growth Rate
      const targetYear = q.match(/\b(20\d{2})\b/)?.[1] ? parseInt(q.match(/\b(20\d{2})\b/)?.[1]!) : 2030;
      const yearsDiff = Math.max(0, targetYear - 2025);
      const projected = Math.round(basePop * Math.pow(1 + rate, yearsDiff));
      const pctIncrease = ((projected / basePop - 1) * 100).toFixed(1);
      answer = `**${county} Population Projection:**\n` +
               `- 2025 Baseline: ~${basePop?.toLocaleString()}\n` +
               `- ${targetYear} Forecast: ~${projected?.toLocaleString()} (+${pctIncrease}% over ${yearsDiff} years)\n` +
               `- Mathematical Model: Compound growth at the national benchmark rate of 2.3% per annum. For advanced metrics, view the **Analytics** page or retrain our models under \`src/ml/population_forecaster.py\`.`;
    } else {
      answer = "I can forecast county populations, explain development clusters, and details on ML models. Try asking: 'What will Kiambu population be in 2030?' or 'How does economic clustering work?'";
    }
  } else {
    citations = ["README.md"];
    if (q.includes("download") || q.includes("export")) {
      answer = "**Data Export Methods on Kenya County Analytics:**\n\n" +
               "1. **Dashboard Interface**: Toggle the **📥 Data** explorer tab and click the CSV / JSON buttons.\n" +
               "2. **Standard API Endpoint**: Perform a GET request on `/api/v1/data/download/csv` or `/api/v1/data/download/json`.\n" +
               "3. **Raw Filesystem**: Processed and refined county-specific files are located under `src/data/processed/{county_slug}/`.";
    } else if (q.includes("map")) {
      answer = "The interactive **Kenya County Map** is featured right on our **🏠 Home** dashboard page. You can hover over any county to display live tooltips with GDP and population, or click on counties to trigger deep statistical analysis on the **📊 County Detail** page.";
    } else if (q.includes("chatbot") || q.includes("agent") || q.includes("assist")) {
      answer = "Three intelligent AI Assist Bots are featured on our **🤖 AI Assistant** page:\n\n" +
               "- 🔍 **Data Explorer**: Answers inquiries on current metrics, file coverage, and comparisons.\n" +
               "- 🔮 **Prediction**: Discusses ML forecasts, Isolation Forest anomalies, and developmental tiers.\n" +
               "- 🧭 **Guide**: Offers general assistance, download guides, and pipeline details.";
    } else if (q.includes("power bi") || q.includes("tableau") || q.includes("bi")) {
      answer = "Power BI and Tableau exports are facilitated by CSV extracts pre-staged in our workspace:\n" +
               "- Power BI: `src/data/processed/county_metrics.csv` for development indexes.\n" +
               "- Tableau: `src/data/processed/county_metrics.csv` for general overviews.\n" +
               "Plus we have compiled a web-equivalent, interactive plotting experience right on the **📊 Analytics** dashboard page.";
    } else if (q.includes("n8n") || q.includes("workflow") || q.includes("pipeline")) {
      answer = "Our automated KNBS ingestion pipeline is exported as an n8n JSON file at `n8n_workflows/data_pipeline.json`. To run it, import this file into your n8n workspace. It is scheduled to trigger weekly on Sundays at 02:00 UTC to ingest, scrape, and re-index county PDFs.";
    } else {
      answer = "I can assist in navigating this platform, explain mapping features, how to ingest raw PDFs, or detail dashboard pages. Try asking 'How do I download data?' or 'Tell me about the interactive map'.";
    }
  }

  return {
    agent,
    query,
    answer,
    citations
  };
}


// -------------------------------------------------------------
// REST API ENDPOINTS
// -------------------------------------------------------------

// 1. All counties metrics
app.get("/api/v1/counties", (req: Request, res: Response) => {
  const metrics = readJSONFile<any[]>(dataPaths.metrics, []);
  res.json(metrics);
});

// 2. Single county detail
app.get("/api/v1/counties/:code", (req: Request, res: Response) => {
  const { code } = req.params;
  const metrics = readJSONFile<any[]>(dataPaths.metrics, []);
  
  // Find county by code
  const county = metrics.find(m => m.county_code === code || m.slug === code || m.county_name.toLowerCase() === code.toLowerCase());
  
  if (!county) {
    return res.status(404).json({ error: `County with code/slug ${code} not found.` });
  }

  // Enrich with forecasts
  const forecastData = readJSONFile<any>(dataPaths.forecast, {});
  const countyForecast = forecastData[county.county_name] || null;

  // Enrich with education/employment models
  const eduEmpData = readJSONFile<any>(dataPaths.education, { county_results: {} });
  const countyEduEmp = eduEmpData.county_results?.[county.county_name] || null;

  // Enrich with health anomalies
  const anomalyData = readJSONFile<any>(dataPaths.anomalies, { county_results: {} });
  const countyAnomaly = anomalyData.county_results?.[county.county_name] || null;

  // Enrich with Ingestion logs
  const downloadLog = readJSONFile<any>(dataPaths.downloadLog, {});
  const countyLog = downloadLog[county.county_name] || null;

  res.json({
    ...county,
    forecast: countyForecast,
    education_employment: countyEduEmp,
    health_anomaly: countyAnomaly,
    ingestion_log: countyLog
  });
});

// 3. Analytics clusters
app.get("/api/v1/analytics/clustering", (req: Request, res: Response) => {
  const clusters = readJSONFile<any>(dataPaths.clusters, {});
  res.json(clusters);
});

// 4. Health anomalies
app.get("/api/v1/health/anomalies", (req: Request, res: Response) => {
  const anomalies = readJSONFile<any>(dataPaths.anomalies, {});
  res.json(anomalies);
});

// 5. Geospatial GeoJSON map boundary
app.get("/api/v1/geospatial/counties", (req: Request, res: Response) => {
  const geojson = readJSONFile<any>(dataPaths.geospatial, null);
  if (!geojson) {
    return res.status(404).json({ error: "Geospatial boundary GeoJSON is not available." });
  }
  res.json(geojson);
});

// 6. Bulk Data Exports
app.get("/api/v1/data/download/json", (req: Request, res: Response) => {
  const metrics = readJSONFile<any[]>(dataPaths.metrics, []);
  res.setHeader("Content-Disposition", "attachment; filename=kenya_county_metrics.json");
  res.setHeader("Content-Type", "application/json");
  res.json(metrics);
});

app.get("/api/v1/data/download/csv", (req: Request, res: Response) => {
  const metrics = readJSONFile<any[]>(dataPaths.metrics, []);
  if (!metrics || metrics.length === 0) {
    return res.status(404).text("No data available.");
  }

  // Convert array of objects to CSV
  const keys = Object.keys(metrics[0]);
  const csvRows = [];
  csvRows.push(keys.join(",")); // Header row

  for (const row of metrics) {
    const values = keys.map(k => {
      const val = row[k];
      if (typeof val === 'string') {
        return `"${val.replace(/"/g, '""')}"`;
      }
      return val === null ? "" : val;
    });
    csvRows.push(values.join(","));
  }

  const csvContent = csvRows.join("\n");
  res.setHeader("Content-Disposition", "attachment; filename=kenya_county_metrics.csv");
  res.setHeader("Content-Type", "text/csv");
  res.send(csvContent);
});

// 7. Chat Agents list
app.get("/api/v1/chat/agents", (req: Request, res: Response) => {
  res.json({
    agents: [
      {
        key: "data",
        name: "Data Explorer Bot",
        icon: "🔍",
        description: "Answers questions about current county statistics, economic metrics, and data coverage."
      },
      {
        key: "prediction",
        name: "Prediction Bot",
        icon: "🔮",
        description: "Explains population forecasts, development tier clustering, and ML models confidence."
      },
      {
        key: "guide",
        name: "Guide Bot",
        icon: "🧭",
        description: "Helps you navigate the platform dashboard, download processed data extracts, and understand workflows."
      }
    ]
  });
});

// 8. AI Chatbot Programmatic POST query with Gemini implementation
app.post("/api/v1/chat/query", async (req: Request, res: Response) => {
  const { query, agent = "data" } = req.body;

  if (!query || !query.trim()) {
    return res.status(400).json({ error: "Query cannot be empty" });
  }
  if (query.length > 1000) {
    return res.status(400).json({ error: "Query too long (max 1000 chars)" });
  }

  const metrics = readJSONFile<any[]>(dataPaths.metrics, []);
  const downloadLog = readJSONFile<any>(dataPaths.downloadLog, {});

  // Determine active agent key automatically if not specified
  let activeAgent = agent;
  const qLower = query.toLowerCase();
  if (!req.body.agent) {
    if (qLower.includes("how do") || qLower.includes("how to") || qLower.includes("help") || qLower.includes("where") || qLower.includes("navigate") || qLower.includes("guide") || qLower.includes("download") || qLower.includes("export") || qLower.includes("n8n")) {
      activeAgent = "guide";
    } else if (qLower.includes("forecast") || qLower.includes("predict") || qLower.includes("2030") || qLower.includes("future") || qLower.includes("tier") || qLower.includes("cluster") || qLower.includes("anomaly") || qLower.includes("linear") || qLower.includes("ml")) {
      activeAgent = "prediction";
    } else {
      activeAgent = "data";
    }
  }

  const gemini = getGeminiClient();

  if (!gemini) {
    // Return offline rule-based fallback response
    const fallbackResponse = respondOffline(activeAgent, query, metrics, downloadLog);
    return res.json(fallbackResponse);
  }

  try {
    // Let's customize system instructions and supply relevant context depending on agent key
    let systemInstruction = "";
    let contextStr = "";

    if (activeAgent === "data") {
      // Create a clean summary string of metrics context
      const simplifiedMetrics = metrics.map(m => ({
        code: m.county_code,
        name: m.county_name,
        pop: m.population,
        gdp_pct: m.gdp_contribution_pct,
        health: m.health_score,
        edu: m.education_rating,
        emp: m.employment_rate,
        tier: m.development_tier,
        status: downloadLog?.[m.county_name]?.file_status || "BASELINE"
      }));
      contextStr = JSON.stringify(simplifiedMetrics);
      systemInstruction = `You are "Data Explorer", an intelligent analytical companion for the Kenya County Analytics platform.
Your purpose is to answer user queries with pristine numerical precision using the following county metrics dataset:
${contextStr}

GUIDELINES:
1. Always parse county names accurately and lookup their respective metrics.
2. If a county has a status of "BASELINE" or similar, explain that its data falls back to 2019 Census, but still state its baseline metrics!
3. Format output beautifully using Markdown. Use bold headers, bullet lists, and highlight numbers (e.g., **2,345,100** or **5.4%**).
4. Do NOT make up any numbers. If a county isn't in the dataset, say you don't have records for it.
5. If requested to compare two counties, do so in a clean compared summary format (such as comparing population, GDP, health, employment, and tier side-by-side).
6. State that you are using processed KNBS source data and the platform-cached download logs.`;
    } else if (activeAgent === "prediction") {
      const simplifiedForecasts = metrics.map(m => {
        const pop = m.population || 800000;
        return {
          name: m.county_name,
          base_2025: pop,
          forecast_2030: Math.round(pop * Math.pow(1.023, 5)), // 2.3% per year for 5 years
          tier: m.development_tier,
          health_score: m.health_score,
          emp_rate: m.employment_rate
        };
      });
      contextStr = `Forecast rate: 2.3% compound growth per annum.
County tiers (K-Means Clustering):
Tier 1 (High): Nakuru, Kisumu, Nairobi
Tier 2 (Upper-Middle): Marsabit, Kirinyaga, Murang'a, Baringo, Laikipia, Busia, Siaya, Homa Bay
Tier 3 (Middle): Isiolo, Meru, Tharaka-Nithi, Embu, Kitui, Machakos, Samburu, Trans Nzoia, Uasin Gishu, Elgeyo-Marakwet, Nandi, Narok, Kisii, Nyamira
Tier 4 (Lower-Middle): Kiambu, Turkana, West Pokot, Kajiado, Kericho, Bomet, Kakamega, Vihiga, Bungoma, Migori
Tier 5 (Low): Mombasa, Kwale, Kilifi, Tana River, Lamu, Taita-Taveta, Garissa, Wajir, Mandera, Makueni, Nyandarua, Nyeri

Models in use:
1. Population Forecaster - Prophet-inspired exponential growth at 2.3% baseline.
2. Economic Clustering - K-Means (k=5) based on population density, GDP contribution %, and health score.
3. Health Anomaly Detector - Isolation Forest trained on health score residual metrics; flags counties with severe deviation.
4. Employment Predictor - Ordinary Least Squares (OLS) regression over GDP, Health, and Education and urbanization.

County Tiers & Forecasts summary table for reference:
${JSON.stringify(simplifiedForecasts)}`;

      systemInstruction = `You are "Prediction Bot", the machine learning analyst on the Kenya County Analytics platform.
Your purpose is to explain statistical projections, population forecasts, development clustering, and machine learning models to the user.
Use the following context to respond:
${contextStr}

GUIDELINES:
1. Explain exponential forecasts, K-Means clustering, and Isolation Forest anomaly scores conceptually and with county-specific context.
2. Highlight figures, growth rates, and model parameters in **bold**.
3. Use a clear, academic but highly readable analytical tone. Highlight that confidence is high (75-85%) for counties with uploaded KNBS abstracts and moderate (50-60%) for baseline fallback counties.
4. If a user asks about future years like 2030, calculate and explain projections using compound growth equations based on their baseline stats.
5. Reference your citations as "src/ml/population_forecaster.py" and "src/ml/economic_clustering.py".`;
    } else {
      systemInstruction = `You are "Guide Bot", the navigator assistant for the Kenya County Analytics platform.
Your purpose is to help users find statistical reports, locate data download files, and leverage this platform.

PLATFORM MAP & NAVIGATION GUIDE:
- **🏠 Home Page**: Interactive SVG Map of Kenya's 47 counties. You can hover counties for live tooltips with GDP/population or click/select to launch deep dive analyses.
- **📊 County Detail Page**: Displays detailed population trajectories, historic and forecast graphs, economic contributions, OLS employment contributions, and active health checks.
- **📊 Analytics & ML Page**: Features countrywide sortable metrics tables, GDP vs growth scatters, K-Means cluster lists, and Isolation Forest anomaly checklists.
- **🔍 Compare Page**: Dynamic side-by-side comparison matrix with highlights indicating leadership in various categories.
- **🤖 AI Assistants Page**: That is right here! Access Data Explorer, Prediction, and Guide bots inside specialized chats.
- **📥 Data Center Page**: Allows table exploration and direct downloads of CSV or JSON database exports.
- **⚙️ Manual integrations / BI Dashboards**: Guides for importing analytics extracts inside Power BI desktop, configuring Tableau templates, and running the automated weeklySunday 02:00 UTC n8n scraper workflow (\`n8n_workflows/data_pipeline.json\`).

GUIDELINES:
1. Deliver structured, friendly, numbered guidelines in your answers.
2. Direct users to the exact UI elements or endpoints (e.g. \`/api/v1/data/download/csv\`) corresponding to their objectives.
3. Be supportive, concise, and professional. Use beautiful formatting.`;
    }

    const response = await gemini.models.generateContent({
      model: "gemini-3.5-flash",
      contents: query,
      config: {
        systemInstruction,
        temperature: 0.7,
      },
    });

    const answer = response.text || "Sorry, I am unable to generate a response right now.";
    const citations = activeAgent === "data" 
      ? ["src/data/processed/county_metrics.json", "src/data/processed/download_log.json"]
      : activeAgent === "prediction"
      ? ["src/ml/population_forecaster.py", "src/ml/economic_clustering.py"]
      : ["README.md"];

    res.json({
      agent: activeAgent,
      query,
      answer,
      citations
    });

  } catch (error: any) {
    console.error("Gemini AI API execution failed, returning offline fallback:", error);
    const fallbackResponse = respondOffline(activeAgent, query, metrics, downloadLog);
    res.json(fallbackResponse);
  }
});


// -------------------------------------------------------------
// VITE MIDDLEWARE & STATIC FILE SERVING
// -------------------------------------------------------------
async function bootstrap() {
  if (process.env.NODE_ENV !== "production") {
    console.log("Starting server in development mode with Vite middleware...");
    const { createServer: createViteServer } = await import("vite");
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa"
    });
    app.use(vite.middlewares);
  } else {
    console.log("Starting server in production mode serving static bundle...");
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req: Request, res: Response) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Kenya County Analytics Server booting successfully on http://0.0.0.0:${PORT}`);
  });
}

bootstrap().catch(err => {
  console.error("Server bootstrapping failed:", err);
});
