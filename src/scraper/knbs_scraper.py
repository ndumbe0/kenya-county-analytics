import os, json, time, random, requests, re, urllib3
from datetime import datetime
from pathlib import Path

urllib3.disable_warnings()

COUNTIES = [
    "Mombasa","Kwale","Kilifi","Tana River","Lamu","Taita-Taveta",
    "Garissa","Wajir","Mandera","Marsabit","Isiolo","Meru",
    "Tharaka-Nithi","Embu","Kitui","Machakos","Makueni","Nyandarua",
    "Nyeri","Kirinyaga","Murang'a","Kiambu","Turkana","West Pokot",
    "Samburu","Trans Nzoia","Uasin Gishu","Elgeyo-Marakwet","Nandi",
    "Baringo","Laikipia","Nakuru","Narok","Kajiado","Kericho",
    "Bomet","Kakamega","Vihiga","Bungoma","Busia","Siaya",
    "Kisumu","Homa Bay","Migori","Kisii","Nyamira","Nairobi"
]

COUNTY_CODES = {c:i+1 for i,c in enumerate(COUNTIES)}

BASE_URL = "https://www.knbs.or.ke/county-statistical-abstracts/"
PROJECT_DATA_DIR = Path("D:/personal projects/Project data")
LOG_PATH = Path("data/download_log.json")
PROJECT_ROOT = Path("D:/personal projects/kenya-county-analytics")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept": "text/html,*/*", "Accept-Language": "en-US,en;q=0.5"}


def fetch(url):
    try:
        return requests.get(url, headers=HEADERS, verify=False, timeout=30).text
    except Exception as e:
        print(f"  Fetch error {url}: {e}")
        return ""


def find_pdfs_in_html(html):
    found = {}
    pdf_urls = set(re.findall(r'https://www\.knbs\.or\.ke/wp-content/uploads/\d{4}/\d{2}/[^"\'<> ]+\.pdf', html))
    for url in pdf_urls:
        url_lower = url.lower()
        for county in COUNTIES:
            slug = county.lower().replace("'", "").replace(" ", "-")
            if slug in url_lower:
                if county not in found:
                    found[county] = url
                break
    return found


def get_year_from_url(url):
    m = re.search(r'/(20\d{2})/', url)
    return int(m.group(1)) if m else None


def download_pdf(url, filepath):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, verify=False, timeout=120, stream=True)
            if resp.status_code == 200:
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                sz = os.path.getsize(filepath)
                if sz > 5000:
                    return sz
                os.remove(filepath)
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None


def build_log():
    log = {}
    if LOG_PATH.exists():
        with open(LOG_PATH) as f:
            log = json.load(f)
    for county in COUNTIES:
        if county not in log:
            d = PROJECT_DATA_DIR / county
            files = list(d.glob("*.pdf")) if d.exists() else []
            if files:
                f = files[0]
                log[county] = {
                    "county_name": county, "county_code": COUNTY_CODES[county],
                    "status": "AVAILABLE", "file_path": str(f),
                    "size": os.path.getsize(f),
                    "year": get_year_from_url(str(f)),
                    "timestamp": datetime.fromtimestamp(os.path.getmtime(f)).isoformat()
                }
            else:
                log[county] = {
                    "county_name": county, "county_code": COUNTY_CODES[county],
                    "status": "DATA_UNAVAILABLE", "file_path": "", "size": 0,
                    "year": None, "timestamp": datetime.now().isoformat()
                }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)
    return log


def main():
    print("=" * 60)
    print("KNBS County Statistical Abstracts Scraper v2")
    print("=" * 60)

    log = build_log()
    available = sum(1 for v in log.values() if v["status"] == "AVAILABLE")
    print(f"Already have data for: {available}/47 counties\n")

    print("Scraping KNBS county-statistical-abstracts pages...")
    all_county_pdfs = {}

    for page_num in range(1, 20):
        url = f"{BASE_URL}page/{page_num}/" if page_num > 1 else BASE_URL
        html = fetch(url)
        if not html or "County Statistical Abstract" not in html:
            if page_num > 1:
                break
            continue
        pdfs = find_pdfs_in_html(html)
        for county, pdf_url in pdfs.items():
            if county not in all_county_pdfs:
                all_county_pdfs[county] = pdf_url
        print(f"  Page {page_num}: Found {len(pdfs)} county PDFs (total: {len(all_county_pdfs)})")
        time.sleep(1.5)

    print(f"\nTotal unique county PDFs found: {len(all_county_pdfs)}")

    downloaded = 0
    for county in sorted(COUNTIES):
        if log.get(county, {}).get("status") == "AVAILABLE":
            continue
        pdf_url = all_county_pdfs.get(county)
        if not pdf_url:
            log[county]["status"] = "DATA_UNAVAILABLE"
            with open(LOG_PATH, "w") as f:
                json.dump(log, f, indent=2)
            continue

        county_dir = PROJECT_DATA_DIR / county
        filename = pdf_url.split("/")[-1]
        filepath = county_dir / filename

        print(f"Downloading {county}... ", end="", flush=True)
        size = download_pdf(pdf_url, filepath)
        if size:
            log[county] = {
                "county_name": county, "county_code": COUNTY_CODES[county],
                "status": "AVAILABLE", "file_path": str(filepath),
                "size": size, "year": get_year_from_url(pdf_url),
                "timestamp": datetime.now().isoformat()
            }
            downloaded += 1
            print(f"OK ({size/1024:.0f} KB)")
        else:
            log[county]["status"] = "DATA_UNAVAILABLE"
            print("FAILED")

        with open(LOG_PATH, "w") as f:
            json.dump(log, f, indent=2)
        time.sleep(2 + random.random())

    final_available = sum(1 for v in log.values() if v["status"] == "AVAILABLE")
    print(f"\n{'='*60}")
    print(f"Download complete! Downloaded {downloaded} new PDFs this session.")
    print(f"Total counties with data: {final_available}/47")
    print(f"{'='*60}")
    return log


if __name__ == "__main__":
    main()
