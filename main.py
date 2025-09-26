from fastapi import FastAPI, Query, Request
from fastapi import HTTPException
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Serve all required middlewares and static files.
app = FastAPI(title="Philippine Address API (PSGC)", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/src/img", StaticFiles(directory="src/img"), name="img")

# Load JSON data into memory
DATA_DIR = Path(__file__).parent / "pgsc_data"

with open(DATA_DIR / "pgsc_region.json", "r", encoding="utf-8") as f:
    REGIONS = json.load(f)["data"]

with open(DATA_DIR / "pgsc_province.json", "r", encoding="utf-8") as f:
    PROVINCES = json.load(f)["data"]

with open(DATA_DIR / "pgsc_citymunicipality.json", "r", encoding="utf-8") as f:
    CITIES = json.load(f)["data"]

with open(DATA_DIR / "pgsc_submunicipality.json", "r", encoding="utf-8") as f:
    SUBMUNIS = json.load(f)["data"]

with open(DATA_DIR / "pgsc_barangay.json", "r", encoding="utf-8") as f:
    BARANGAYS = json.load(f)["data"]



@app.get("/", response_class=HTMLResponse)
def homepage():
    return f"""
        <html>
            <head>
                <title>{app.title}</title>
            </head>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1>
                    <img src="/src/img/PAFHRMC.png" style="width:40px; height:40px; border-radius:50%; vertical-align:middle; margin-right:8px;">
                    {app.title}
                    <img src="/src/img/PAF.png" style="width:40px; height:40px; border-radius:50%; vertical-align:middle; margin-right:8px;">  
                </h1>
                <p>Welcome! This is a local PSGC-based geographic API service created for PAFHRMC.</p>
                <p><b>Version:</b> {app.version}</p>
                
                <h2>Available Endpoints</h2>
                <ul>
                    <li><a href="/health" target="_blank">/health</a> – API health check</li>
                    <li><a href="/regions" target="_blank">/regions</a> – Get all regions</li>
                    <li><a href="/provinces" target="_blank">/provinces</a> – Get all provinces</li>
                    <li><a href="/cities" target="_blank">/cities</a> – Get all cities</li>
                    <li><a href="/submunicipalities" target="_blank">/submunicipalities</a> – Get all submunicipalities</li>
                    <li><a href="/barangays" target="_blank">/barangays</a> – Get all barangays <code>(with Limit Parameters, will crash it load all)</code>.</li>
                </ul>
                <h2>Interactive API Docs</h2>
                <ul>
                    <li><a href="/docs" target="_blank">/docs</a> – Swagger UI</li>
                    <li><a href="/redoc" target="_blank">/redoc</a> – ReDoc UI</li>
                </ul>

                <p style="margin-top:20px; font-size: 12px; color: gray;">
                    Powered by FastAPI · PSGC JSON Data
                </p>
            </body>
        </html>
    """
    
# Checks API Health
@app.get("/health")
def root():
    return {
        "message": f"Hi, {app.title} is working!",
        "version": app.version
    }



############################## REGION ###############################
# Get All Regions
@app.get("/regions")
def get_all_regions():
    return REGIONS

# Get Certain Region by Region Code
@app.get("/regions/{region_code}/getcertain")
def get_certain_region(region_code: str):
    region = next((r for r in REGIONS if r["psgc10DigitCode"] == region_code), None)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region



############################## PROVINCE ###############################
# Get All Provinces
@app.get("/provinces")
def get_all_provinces():
    return PROVINCES

# Get Certain Province by Province Code
@app.get("/provinces/{province_code}/getcertain")
def get_certain_province(province_code: str):
    province = next((p for p in PROVINCES if p["psgc10DigitCode"] == province_code), None)
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    return province

# Get Provinces by Region Code
@app.get("/regions/{region_code}/provinces")
def get_provinces_by_region(region_code: str):
    return [p for p in PROVINCES if p["regionCode"] == region_code]



########################## CITY MUNICIPALITY ###########################
# Get All Cities
@app.get("/cities")
def get_all_cities():
    return CITIES

# Get Certain City by City Code
@app.get("/cities/{city_code}/getcertain")
def get_certain_city(city_code: str):
    city = next((c for c in CITIES if c["psgc10DigitCode"] == city_code), None)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city

# Get Cities by Region Code
@app.get("/regions/{region_code}/cities")
def get_cities_by_region(region_code: str):
    return [c for c in CITIES if c["regionCode"] == region_code]

# Get Cities by Province Code
@app.get("/provinces/{province_code}/cities")
def get_cities_by_province(province_code: str):
    return [c for c in CITIES if c["provinceCode"] == province_code]



########################### SUB MUNICIPALITY ############################
# Get all Sub Municipalities
@app.get("/submunicipalities")
def get_all_submunicipalities():
    return SUBMUNIS

# Get Certain Sub Municipality by Submunicipality Code
@app.get("/submunicipalities/{submuni_code}/getcertain")
def get_certain_submunicipality(submuni_code: str):
    submuni = next((s for s in SUBMUNIS if s["psgc10DigitCode"] == submuni_code), None)
    if not submuni:
        raise HTTPException(status_code=404, detail="Submunicipality not found")
    return submuni

# Get Submunicipalities by Region Code
@app.get("/regions/{region_code}/submunicipalities")
def get_submunis_by_region(region_code: str):
    return [s for s in SUBMUNIS if s["regionCode"] == region_code]

# Get Submunicipalities by City Code
@app.get("/cities/{city_code}/submunicipalities")
def get_submunis_by_city(city_code: str):
    return [s for s in SUBMUNIS if s["cityMunicipalityCode"] == city_code]



################################ BARANGAY ################################
# Get All Barangays
@app.get("/barangays")
def get_all_barangays(request: Request, skip: int = 0, limit: int = 50):
    # If no query parameters are passed at all → redirect
    if not request.query_params:
        return RedirectResponse(url=f"/barangays?limit={limit}")
    return BARANGAYS[skip: skip + limit]

# Get Certain Barangay by Barangay Code
@app.get("/barangays/{barangay_code}/getcertain")
def get_certain_barangay(barangay_code: str):
    barangay = next((b for b in BARANGAYS if b["psgc10DigitCode"] == barangay_code), None)
    if not barangay:
        raise HTTPException(status_code=404, detail="Barangay not found")
    return barangay

# Get Barangays by City Code
@app.get("/cities/{city_code}/barangays")
def get_barangays_by_city(city_code: str):
    return [b for b in BARANGAYS if b["cityMunicipalityCode"] == city_code]

# Get Barangays by Submunicipality Code
@app.get("/submunicipalities/{submuni_code}/barangays")
def get_barangays_by_submuni(submuni_code: str):
    return [b for b in BARANGAYS if b.get("subMunicipalityCode") == submuni_code]
