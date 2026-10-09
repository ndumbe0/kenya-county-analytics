import os
import json
import time
import asyncio
from playwright.async_api import async_playwright
import requests
from pathlib import Path

BASE_URL = "https://www.knbs.or.ke/county-statistical-abstracts/"
DATA_RAW = Path("D:/personal projects/kenya-county-analytics/data/raw")
LOG_FILE = DATA_RAW / "download_log.json"

COUNTIES = [
    "Mombasa","Kwale","Kilifi","Tana River","Lamu","Taita-Taveta","Garissa","Wajir",
    "Mandera","Marsabit","Isiolo","Meru","Tharaka-Nithi","Embu","Kitui","Machakos",
    "Makueni","Nyandarua","Nyeri","Kirinyaga","Murang'a","Kiambu","Turkana","West Pokot",
    "Samburu","Trans Nzoia","Uasin Gishu","Elgeyo-Marakwet","Nandi","Baringo","Laikipia",
    "Nakuru","Narok","Kajiado","Kericho","Bomet","Kakamega","Vihiga","Bungoma","Busia",
    "Siaya","Kisumu","Homa Bay","Migori","Kisii","Nyamira","Nairobi"
]

async def scrape():
    os.makedirs(DATA_RAW, exist_ok=True)
    log = {"downloads": []}
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            log = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(BASE_URL)
        await page.wait_for_load_state("networkidle")

        links = await page.query_selector_all("a")
        pdf_links = []
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if href and "County Statistical Abstract" in text and href.endswith(".pdf"):
                pdf_links.append(href)

        for link in pdf_links:
            for county in COUNTIES:
                if county.lower() in link.lower():
                    years = ["2025","2024","2023","2022","2021","2020"]
                    for year in years:
                        if year in link:
                            county_dir = DATA_RAW / county / year
                            county_dir.mkdir(parents=True, exist_ok=True)
                            filename = county_dir / f"{county}_{year}.pdf"
                            if filename.exists():
                                continue
                            try:
                                resp = requests.get(link, timeout=30)
                                resp.raise_for_status()
                                with open(filename, "wb") as f:
                                    f.write(resp.content)
                                log["downloads"].append({
                                    "county": county, "year": year, "status": "OK",
                                    "file_path": str(filename), "size": len(resp.content),
                                    "timestamp": time.time()
                                })
                                print(f"Downloaded {county} {year}")
                                time.sleep(2)
                            except Exception as e:
                                log["downloads"].append({"county": county, "year": year, "status": "FAIL", "error": str(e)})
        await browser.close()

    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

if __name__ == "__main__":
    asyncio.run(scrape())
