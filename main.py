import logging
import os
from pathlib import Path
import json

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from security import env_flag, require_api_key

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="[%(levelname)s] %(asctime)s %(name)s - %(message)s")

# Swagger / ReDoc / landing page are development helpers only.
ENABLE_DOCS = env_flag("ENABLE_DOCS", False)

app = FastAPI(
    title="Philippine Address API (PSGC)",
    version="1.1",
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None,
)

# Server-to-server service: no CORS by default. Only enable for explicit origins.
_cors_origins = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["X-Internal-Key", "Content-Type"],
    )


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


# Every data route requires the shared X-Internal-Key; only /ping is public.
router = APIRouter(dependencies=[Depends(require_api_key)])

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



if ENABLE_DOCS:
    app.mount("/src/img", StaticFiles(directory="src/img"), name="img")

    @app.get("/", response_class=HTMLResponse)
    def homepage():
        return f"""
        <html><head><title>{app.title}</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1>{app.title}</h1>
            <p>Development mode (ENABLE_DOCS=true). All endpoints except /ping need the
            <code>X-Internal-Key</code> header. Use the Authorize button in <a href="/docs">/docs</a>.</p>
        </body></html>
        """


# Liveness (no data, no side effects)
@app.get("/ping")
def ping():
    return {"status": "ok"}


# Checks API Health
@router.get("/health")
def root():
    return {
        "message": f"Hi, {app.title} is working!",
        "version": app.version
    }

############################## Island ###############################
# Get All Island
@router.get("/islands")
def get_island_groups():
    islands = sorted({r["islandGroup"] for r in REGIONS if r.get("islandGroup")})
    return islands

# Get All Region by Island
@router.get("/islands/{island}/regions")
def get_regions_by_island(island: str):
    regions = [r for r in REGIONS if r.get("islandGroup", "").lower() == island.lower()]
    
    if not regions:
        raise HTTPException(status_code=404, detail="Island group not found")
    
    return regions

############################## REGION ###############################
# Get All Regions
@router.get("/regions")
def get_all_regions():
    return REGIONS

# Get Certain Region by Region Code
@router.get("/regions/{region_code}/getcertain")
def get_certain_region(region_code: str):
    region = next((r for r in REGIONS if r["psgc10DigitCode"] == region_code), None)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region



############################## PROVINCE ###############################
# Get All Provinces
@router.get("/provinces")
def get_all_provinces():
    return PROVINCES

# Get Certain Province by Province Code
@router.get("/provinces/{province_code}/getcertain")
def get_certain_province(province_code: str):
    province = next((p for p in PROVINCES if p["psgc10DigitCode"] == province_code), None)
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    return province

# Get Provinces by Region Code
@router.get("/regions/{region_code}/provinces")
def get_provinces_by_region(region_code: str):
    return [p for p in PROVINCES if p["regionCode"] == region_code]



########################## CITY MUNICIPALITY ###########################
# Get All Cities
@router.get("/cities")
def get_all_cities():
    return CITIES

# Get Certain City by City Code
@router.get("/cities/{city_code}/getcertain")
def get_certain_city(city_code: str):
    city = next((c for c in CITIES if c["psgc10DigitCode"] == city_code), None)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city

# Get Cities by Region Code
@router.get("/regions/{region_code}/cities")
def get_cities_by_region(region_code: str):
    return [c for c in CITIES if c["regionCode"] == region_code]

# Get Cities by Province Code
@router.get("/provinces/{province_code}/cities")
def get_cities_by_province(province_code: str):
    return [c for c in CITIES if c["provinceCode"] == province_code]



########################### SUB MUNICIPALITY ############################
# Get all Sub Municipalities
@router.get("/submunicipalities")
def get_all_submunicipalities():
    return SUBMUNIS

# Get Certain Sub Municipality by Submunicipality Code
@router.get("/submunicipalities/{submuni_code}/getcertain")
def get_certain_submunicipality(submuni_code: str):
    submuni = next((s for s in SUBMUNIS if s["psgc10DigitCode"] == submuni_code), None)
    if not submuni:
        raise HTTPException(status_code=404, detail="Submunicipality not found")
    return submuni

# Get Submunicipalities by Region Code
@router.get("/regions/{region_code}/submunicipalities")
def get_submunis_by_region(region_code: str):
    return [s for s in SUBMUNIS if s["regionCode"] == region_code]

# Get Submunicipalities by City Code
@router.get("/cities/{city_code}/submunicipalities")
def get_submunis_by_city(city_code: str):
    return [s for s in SUBMUNIS if s["cityMunicipalityCode"] == city_code]


################################ BARANGAY ################################
# Get All Barangays
@router.get("/barangays")
def get_all_barangays(request: Request, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=1000)):
    # If no query parameters are passed at all → redirect
    if not request.query_params:
        return RedirectResponse(url=f"/barangays?limit={limit}")
    return BARANGAYS[skip: skip + limit]

# Get Certain Barangay by Barangay Code
@router.get("/barangays/{barangay_code}/getcertain")
def get_certain_barangay(barangay_code: str):
    barangay = next((b for b in BARANGAYS if b["psgc10DigitCode"] == barangay_code), None)
    if not barangay:
        raise HTTPException(status_code=404, detail="Barangay not found")
    return barangay

# Get Barangays by City Code
@router.get("/cities/{city_code}/barangays")
def get_barangays_by_city(city_code: str):
    return [b for b in BARANGAYS if b["cityMunicipalityCode"] == city_code]

# Get Barangays by Submunicipality Code
@router.get("/submunicipalities/{submuni_code}/barangays")
def get_barangays_by_submuni(submuni_code: str):
    return [b for b in BARANGAYS if b.get("subMunicipalityCode") == submuni_code]


app.include_router(router)
