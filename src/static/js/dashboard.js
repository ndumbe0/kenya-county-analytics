const API_BASE = "/api/v1";
const svg = d3.select("#kenya-map");
const tooltip = d3.select("#tooltip");
const detailPanel = d3.select("#county-detail");
const detailHeader = d3.select("#detail-header");
const detailBody = d3.select("#detail-body");

const summaryCounties = document.getElementById("summary-counties");
const summaryAvailable = document.getElementById("summary-available");
const summaryTiers = document.getElementById("summary-tiers");
const summaryForecast = document.getElementById("summary-forecast");

async function fetchJson(path) {
    const res = await fetch(path);
    if (!res.ok) {
        throw new Error(`Request failed: ${res.status}`);
    }
    return res.json();
}

function formatNumber(value) {
    return Intl.NumberFormat("en-KE").format(value);
}

function showTooltip(event, content) {
    tooltip.html(content)
        .style("left", `${event.pageX + 12}px`)
        .style("top", `${event.pageY + 12}px`)
        .classed("hidden", false);
}

function hideTooltip() {
    tooltip.classed("hidden", true);
}

function buildCountySummary(counties) {
    const total = counties.length;
    const available = counties.filter(c => c.data_available).length;
    const avgTier = (counties.reduce((sum, c) => sum + (c.development_tier || 5), 0) / total).toFixed(2);
    const forecastReady = counties.filter(c => c.population_forecast && Object.keys(c.population_forecast || {}).length).length;

    summaryCounties.querySelector("strong").textContent = total;
    summaryAvailable.querySelector("strong").textContent = `${available} / ${total}`;
    summaryTiers.querySelector("strong").textContent = `${avgTier}`;
    summaryForecast.querySelector("strong").textContent = `${forecastReady}`;
}

async function loadDashboard() {
    const [geojson, countyDataResponse] = await Promise.all([
        fetchJson("/static/kenya-counties.geojson"),
        fetchJson(`${API_BASE}/counties/`),
    ]);

    const countyMap = {};
    countyDataResponse.counties.forEach(item => {
        countyMap[item.name] = item;
    });
    buildCountySummary(countyDataResponse.counties);

    const width = 1000;
    const height = 1000;
    const projection = d3.geoMercator()
        .center([37.8, 0.6])
        .scale(3600)
        .translate([width / 2, height / 2]);
    const path = d3.geoPath().projection(projection);

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    svg.selectAll("path").remove();
    svg.selectAll("path")
        .data(geojson.features)
        .enter()
        .append("path")
        .attr("d", path)
        .attr("class", "county-shape")
        .attr("fill", d => {
            const name = d.properties.county_name;
            const record = countyMap[name];
            if (!record || !record.data_available) return "#b0b0b0";
            const tier = record.development_tier || 5;
            return tier === 1 ? "#006600"
                : tier === 2 ? "#33cc33"
                : tier === 3 ? "#ffd700"
                : tier === 4 ? "#ff6600"
                : "#cc0000";
        })
        .attr("stroke", "#0d2f15")
        .attr("stroke-width", 0.6)
        .on("mouseover", function (event, d) {
            d3.select(this).attr("stroke-width", 1.8);
            const name = d.properties.county_name;
            const record = countyMap[name] || {};
            const status = record.data_available ? "Data available" : "No data";
            showTooltip(event, `<strong>${name}</strong><br>${status}<br>Tier: ${record.development_tier || "N/A"}<br>Latest year: ${record.latest_year || "—"}`);
        })
        .on("mousemove", function (event) {
            showTooltip(event, tooltip.html());
        })
        .on("mouseout", function () {
            d3.select(this).attr("stroke-width", 0.6);
            hideTooltip();
        })
        .on("click", function (event, d) {
            const name = d.properties.county_name;
            const record = countyMap[name];
            if (!record) return;
            openCountyDetail(record);
        });
}

function openCountyDetail(record) {
    detailPanel.classed("hidden", false);
    detailHeader.html(`
        <h2>${record.name}</h2>
        <p><strong>Status:</strong> ${record.data_available ? "Available" : "Data unavailable"}</p>
        <p><strong>Latest year:</strong> ${record.latest_year || "—"}</p>
    `);
    detailBody.html(`<div class="detail-loading">Loading county data...</div>`);

    fetch(`${API_BASE}/counties/${record.code}`)
        .then(res => res.json())
        .then(data => {
            renderCountyDetail(data);
        })
        .catch(() => {
            detailBody.html(`<p class="error-text">County details are not available right now.</p>`);
        });
}

function renderCountyDetail(data) {
    const hasForecast = data.population_forecast && Object.keys(data.population_forecast).length;
    detailBody.html(`
        <div class="detail-grid">
            <div><strong>County code</strong><p>${data.code}</p></div>
            <div><strong>Domains</strong><p>${Object.keys(data.domains || {}).length}</p></div>
            <div><strong>Population forecast</strong><p>${hasForecast ? "Ready" : "Pending"}</p></div>
            <div><strong>Development cluster</strong><p>${data.development_cluster?.tier_label || "N/A"}</p></div>
        </div>
        <div id="detail-chart" class="chart-panel"></div>
    `);

    if (hasForecast) {
        const series = data.population_forecast.forecast || {};
        const years = Object.keys(series).map(Number).sort((a, b) => a - b);
        const values = years.map(year => series[year]);
        Plotly.newPlot("detail-chart", [{ x: years, y: values, type: "scatter", mode: "lines+markers", marker: { color: "#1f7a1f" } }], {
            title: "Population Forecast",
            xaxis: { title: "Year" },
            yaxis: { title: "Population" },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(255,255,255,0.04)",
            font: { color: "#f5f7f6" },
        }, { responsive: true });
    } else {
        const chartTarget = document.getElementById("detail-chart");
        chartTarget.innerHTML = `<div class="error-text">Population forecast is not available for this county.</div>`;
    }
}

function setupPanel() {
    document.getElementById("close-panel").addEventListener("click", () => {
        detailPanel.classed("hidden", true);
    });
}

window.addEventListener("load", async () => {
    setupPanel();
    try {
        await loadDashboard();
    } catch (error) {
        console.error(error);
        document.getElementById("map-wrapper").innerHTML = `<div class="error-text">Unable to load dashboard data. Check API connectivity.</div>`;
    }
});
