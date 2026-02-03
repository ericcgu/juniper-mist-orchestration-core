"""
Day 0: Site Provisioning.

Orchestrates the creation and initialization of new physical sites via the Mist API.

Mist API Reference:
- GET /api/v1/orgs/{org_id}/sites - List sites
- POST /api/v1/orgs/{org_id}/sites - Create site
- GET /api/v1/sites/{site_id} - Get site
- PUT /api/v1/sites/{site_id} - Update site
- DELETE /api/v1/sites/{site_id} - Delete site
"""
import fnc
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services.mist_engine import MistEngine
from src.services.redis import get_api_host, get_org_id


router = APIRouter(prefix="/sites", tags=["Sites - Day 0"])


# =============================================================================
# Models
# =============================================================================

class SiteCreate(BaseModel):
    """Request payload for creating a new Mist site."""
    name: str = Field(..., description="Site display name", examples=["Branch-Austin-001"])
    address: str | None = Field(None, description="Physical street address")
    timezone: str = Field(default="America/Chicago", description="IANA timezone")
    country_code: str = Field(default="US", description="ISO 3166-1 alpha-2 country code")
    latlng: dict | None = Field(None, description="Geo coordinates {lat, lng}")
    notes: str | None = Field(None, description="Optional notes for the site")


class SiteUpdate(BaseModel):
    """Request payload for updating a site."""
    name: str | None = Field(None, description="Site display name")
    address: str | None = Field(None, description="Physical street address")
    timezone: str | None = Field(None, description="IANA timezone")
    country_code: str | None = Field(None, description="ISO 3166-1 alpha-2 country code")
    latlng: dict | None = Field(None, description="Geo coordinates {lat, lng}")
    notes: str | None = Field(None, description="Optional notes")


class Site(BaseModel):
    """Site response model."""
    id: str
    name: str
    address: str | None = None
    timezone: str | None = None
    country_code: str | None = None
    latlng: dict | None = None
    notes: str | None = None
    org_id: str | None = None


class SiteListResponse(BaseModel):
    """List sites response."""
    sites: list[Site]
    count: int


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/", response_model=SiteListResponse, summary="List all sites")
async def list_sites(
    site_name: str | None = Query(None, description="Filter by site name"),
):
    """
    List all sites in the organization.

    If site_name is provided, filters to sites matching that name.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    data = await engine.get(f"/api/v1/orgs/{org_id}/sites")

    # Filter by site_name if provided
    if site_name:
        data = fnc.filter(lambda s: s.get("name") == site_name, data)

    sites = [
        Site(
            id=s.get("id", ""),
            name=s.get("name", ""),
            address=s.get("address"),
            timezone=s.get("timezone"),
            country_code=s.get("country_code"),
            latlng=s.get("latlng"),
            notes=s.get("notes"),
            org_id=s.get("org_id"),
        )
        for s in data
    ]

    return SiteListResponse(sites=sites, count=len(sites))


@router.post("/", response_model=Site, summary="Step 1: Create a new site")
async def create_site(request: SiteCreate):
    """
    **Step 1: Create Site (Day 0)**

    Creates a new site container in the Mist organization.
    This is the Digital Twin of the physical location.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    payload = request.model_dump(exclude_none=True)
    result = await engine.post(f"/api/v1/orgs/{org_id}/sites", json=payload)

    return Site(
        id=result.get("id", ""),
        name=result.get("name", request.name),
        address=result.get("address"),
        timezone=result.get("timezone"),
        country_code=result.get("country_code"),
        latlng=result.get("latlng"),
        notes=result.get("notes"),
        org_id=result.get("org_id"),
    )


@router.get("/{site_id}", response_model=Site, summary="Get site details")
async def get_site(site_id: str):
    """Get detailed information about a specific site."""
    api_host = get_api_host()
    if not api_host:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    result = await engine.get(f"/api/v1/sites/{site_id}")

    return Site(
        id=result.get("id", site_id),
        name=result.get("name", ""),
        address=result.get("address"),
        timezone=result.get("timezone"),
        country_code=result.get("country_code"),
        latlng=result.get("latlng"),
        notes=result.get("notes"),
        org_id=result.get("org_id"),
    )


@router.put("/{site_id}", response_model=Site, summary="Update site")
async def update_site(site_id: str, request: SiteUpdate):
    """Update an existing site's configuration."""
    api_host = get_api_host()
    if not api_host:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    payload = request.model_dump(exclude_none=True)
    result = await engine.put(f"/api/v1/sites/{site_id}", json=payload)

    return Site(
        id=result.get("id", site_id),
        name=result.get("name", ""),
        address=result.get("address"),
        timezone=result.get("timezone"),
        country_code=result.get("country_code"),
        latlng=result.get("latlng"),
        notes=result.get("notes"),
        org_id=result.get("org_id"),
    )


@router.delete("/{site_id}", summary="Delete site")
async def delete_site(site_id: str):
    """
    Delete a site from the organization.

    WARNING: This will remove all site-specific configurations.
    Devices assigned to this site will become unassigned.
    """
    api_host = get_api_host()
    if not api_host:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    await engine.delete(f"/api/v1/sites/{site_id}")

    return {"id": site_id, "status": "deleted"}
