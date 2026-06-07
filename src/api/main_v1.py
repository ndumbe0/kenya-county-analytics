import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import pandas as pd
import json

app = FastAPI(title="Kenya County Analytics")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="src/static"), name="static")

COUNTIES = [ "Mombasa","Kwale","Kilifi","Tana River","Lamu","Taita-Taveta","Garissa","Wajir",
    "Mandera","Marsabit","Isiolo","Meru","Tharaka-Nithi","Embu","Kitui","Machakos",
    "Makueni","Nyandarua","Nyeri","Kirinyaga","Murang'a","Kiambu","Turkana","West Pokot",
    "Samburu","Trans Nzoia","Uasin Gishu","Elgeyo-Marakwet","Nandi","Baringo","Laikipia",
    "Nakuru","Narok","Kajiado","Kericho","Bomet","Kakamega","Vihiga","Bungoma","Busia",
    "Siaya","Kisumu","Homa Bay","Migori","Kisii","Nyamira","Nairobi"
]

@app.get("/")
def root():
    return {"message": "Kenya County Analytics API", "status": "live"}

@app.get("/api/v1/counties/")
def list_counties():
    return {"counties": COUNTIES}

@app.get("/api/v1/counties/{code}")
def county_details(code: str):
    if code not in COUNTIES:
        raise HTTPException(404, "County not found")
    return {"county": code, "population": "estimate", "gdp": "N/A"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("src/templates/dashboard.html", "r") as f:
        return f.read()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
    except OSError:
        print(f"Port {port} in use, trying {port+1}")
        uvicorn.run(app, host="0.0.0.0", port=port+1, reload=True)
