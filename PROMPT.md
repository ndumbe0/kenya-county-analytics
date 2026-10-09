# MISSION
Take three existing project folders from scaffold to finished, production-quality, showcase-ready full-stack data apps with machine learning, real documentation, screenshots, and free deployment. Work fully autonomously: nobody is available to answer questions or approve anything for ~8+ hours. NEVER ask the user a question or for confirmation. When ambiguous, choose the most reasonable option, log it in DECISIONS.md, and continue. If something fails, diagnose and fix it; after 3 failed attempts log it in PROGRESS.md, skip it, and move on. Do not stop until every phase is done or logged as blocked.

# PROJECTS (run in this order; you may work on a later project while a long job such as the PubMed ingest runs in the background)
1. D:\personal projects\pubmed-explorer     repo: https://github.com/ndumbe0/pubmed-explorer.git      data: data\key_pubmed.csv (~3.4GB, ~4.84M rows; columns title, doi, abstract, journal, date, authors, year, keyword)
2. D:\personal projects\saas-intel-hub      repo: https://github.com/ndumbe0/saas-intel-hub.git       data: data\Micro-SaaS Ideas Database [Starter Story].xlsx (~181 rows; Idea, Monthly Revenue, Monthly Traffic, Revenue per Visitor, Starting Costs, Solopreneur Score, ICP, Growth Tactics)
3. D:\personal projects\mortality-explorer  repo: https://github.com/ndumbe0/mortality-explorer.git    data: data\IHME_GBD_2010_MORTALITY_AGE_SPECIFIC_BY_COUNTRY_1970_2010.csv (~58,906 rows; Country Code, Country Name, Year, Age Group, Sex, Number of Deaths, Death Rate Per 100,000)
Folders may already contain code from earlier work or from the remote repo. Inspect first, then improve and extend rather than blindly overwriting; keep anything that works.

# ENVIRONMENT AND RULES
- Windows, PowerShell. Python 3.11+ (one venv per project), Node 18+. Stay inside D:\personal projects\. Never delete or alter the source datasets.
- Projects are isolated: own DB, own ingestion, own deps, own repo. No shared runtime code.
- Use only FREE tools and services. No paid APIs, no credit card services. Prefer SQLite, local models (scikit-learn, statsmodels/Prophet, sentence-transformers if size allows), Recharts, Tailwind.
- Keep PROGRESS.md (update after every phase) and DECISIONS.md at D:\personal projects\.

# GIT: PUSHING IS PRE-AUTHORIZED
The user has explicitly authorized you to commit and push to each project's GitHub repo (origin, branch main) with no confirmation, at any time, for the whole run. The GitHub CLI is already authenticated and git is configured for non-interactive pushes. Never ask permission to push.
- Verify with git remote -v; fix origin if wrong.
- Commit after every meaningful step with conventional messages (feat:, fix:, docs:, test:, chore:). Push immediately after every commit that completes a feature, and at the end of every phase: git push origin main. Push often so work is never lost.
- Never force push. If a push is rejected, run git pull --rebase origin main, resolve conflicts, and push again. If auth fails, log it in PROGRESS.md, keep committing locally, and retry the push at the end of each phase.
- NEVER commit raw datasets, SQLite DBs, uploads, venvs, or node_modules. Check git status before each commit. GitHub rejects files over 100MB. Commit only small sample data (under 5MB) in data\samples\ so the repo and demo work out of the box.

# ENGINEERING STANDARD (every project)
Backend: FastAPI + SQLAlchemy, typed, structured logging, config via env/.env.example, health endpoint, paginated endpoints, CORS, OpenAPI docs. Frontend: React + Vite + TypeScript + Tailwind + Recharts, responsive, polished, with loading/empty/error states and dark/light mode. Tests: pytest (parsers, ingest, dedup, ML, API), plus Vitest or Playwright smoke tests. GitHub Actions CI (lint, tests, build). Dockerfile and docker-compose.yml (valid, optional to run).

# DATA INGESTION (every project)
- Ingest same-schema CSV/XLSX through both a CLI (scripts\ingest_*.py) and an Add Data page/endpoint. Case-insensitive column mapping, preview, dry-run, then commit. Report rows_read, rows_valid, rows_added, rows_skipped, rows_failed, errors_sample. Append-only, deduplicated by natural key, with source_file and ingested_at provenance. Bad rows never crash a file.
- SOURCES READY FOR LATER: create sources.yaml plus a pluggable connector layer (scripts\fetch_sources.py) so the user can later add URLs/APIs/file paths of the same data type, and the project downloads, validates, and ingests them. Include a disabled-by-default scheduled GitHub Action (cron) for it. Document how to add a source.
- Bring your own data: after a user uploads similar data, the app must analyze it and produce its own output (new dashboard, ML predictions/insights), not just store it. Provide a dataset selector/workspace so uploaded data can be explored separately from the base dataset.

# MACHINE LEARNING (every project): train well, test well, document honestly
Proper train/validation/test splits (time-aware where relevant), cross-validation, a baseline to beat, metrics in docs, saved artifacts under models\ (small committed, large gitignored), reproducible scripts\train.py, docs\MODEL_CARD.md, and an in-app ML page with metrics and live predictions. Retrain on newly ingested data via button or CLI.
- pubmed-explorer: (a) TF-IDF/semantic similar-paper recommendations; (b) topic modeling or clustering of abstracts with a topic explorer view; (c) classifier predicting topic/journal group from title+abstract; (d) publication-trend analysis per keyword. Train on a sampled subset sized for a normal laptop; document the sample size.
- saas-intel-hub: (a) regression predicting monthly revenue from traffic, costs, score, ICP, tactics, with cross-validation and honesty about the ~181-row limit; (b) clustering ideas into archetypes; (c) tactic-effectiveness analysis; (d) an idea-scorer form returning a predicted revenue range with confidence.
- mortality-explorer: (a) forecasting death rate/deaths per country-age-sex beyond 2010, baseline (naive/linear) vs better model (ETS/Prophet/gradient boosting), evaluated on held-out final years; (b) anomaly detection for spikes with annotations; (c) country clustering by mortality profile; (d) interactive forecast page.

# WEB APP AND FREE DEPLOYMENT
Each project must be a real web app that launches with one command (documented, plus a root run script). Make it deployable for free: frontend to GitHub Pages via Actions; backend/demo to a free tier such as Hugging Face Spaces (Docker) or Render free. Verify current free-tier limits by searching the web; do not assume. Full datasets are too big for free hosting, so deploy a clearly labeled demo mode on the committed sample data and keep full-data mode for local use. Use gh api to enable GitHub Pages if possible. If a live deployment needs the user's accounts or secrets, prepare everything (workflows, Dockerfile, config, step-by-step docs\DEPLOY.md) and log exactly what the user must click.

# DOCUMENTATION AND VISUALS
- Rewrite each README.md to showcase standard: title and tagline, badges (CI, license, tech), hero screenshot/GIF, features, Mermaid architecture diagram, tech stack, data description, ML section with real metrics tables and charts, 3-command quick start, full setup, ingesting and adding data, adding sources, API overview, project structure, testing, deployment, roadmap, MIT license, live demo link if available.
- Generate real images: Playwright screenshots of the running app (dashboard, search, ML page, add-data page) into docs\images\, matplotlib charts from real data/model results, embedded in the README. Add a demo GIF if feasible. Add docs\ARCHITECTURE.md, docs\MODEL_CARD.md, docs\DEPLOY.md, CONTRIBUTING.md.
- Write a root D:\personal projects\README.md covering all three projects.

# PROJECT SPECIFICS
pubmed-explorer: streaming ingestion only (never load the whole file), 5,000-row chunks, one transaction per batch, SQLite WAL, FTS5 built AFTER bulk load, resumable checkpoints, DOI dedup (fallback hash of normalized title+year+journal), raw date preserved with derived published_date/year. Boolean search, facets (year histogram, journals, keywords, authors), paging 50/100/250, sorting, detail view with DOI link, filtered CSV export, background ingest with progress endpoint and UI progress bar. Prove everything on a 10k-row slice (separate test DB) first, then launch the FULL ingest as a detached background process logging to data\ingest.log; monitor, resume if it dies, build FTS when done. Continue other work meanwhile.
saas-intel-hub: parsers for $24K, $1.67M, 30K, "—"; growth tactics split into arrays; search, filters, facets, dashboards, CSV export; validation: 181 rows ingest, re-ingest adds 0, 5 new rows give 186.
mortality-explorer: strip thousands separators; natural key (country_code, year, age_group, sex); time series, age distribution, sex breakdown, multi-country comparison; validation: 58,906 rows, Afghanistan/1970/Male/0-6 days sane, appended subset adds exactly the new rows; consider a choropleth map using free topojson.

# EXECUTION ORDER
Phase 0 setup and inspection. Phase 1 pubmed-explorer. Phase 2 saas-intel-hub. Phase 3 mortality-explorer. Phase 4 final quality pass on each: tests green, frontends build, apps launch from a clean clone using only the README, screenshots regenerated, README polished, everything committed AND pushed. Phase 5 root README and SUMMARY.md at D:\personal projects\ (what works, run commands, metrics, deployment status, push status per repo, anything skipped, exactly what the user must do manually).

# DEFINITION OF DONE
Each project: runs locally with one command, tests pass, ML trained and evaluated with documented metrics, ingestion and bring-your-own-data work, showcase-grade README with real screenshots, CI configured, deployment prepared (or live), all work committed and pushed to its GitHub repo, SUMMARY.md written. Do not finish until this is true.
