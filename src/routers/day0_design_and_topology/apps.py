"""
Day 0: Application Signatures.

Defines global "Interesting Traffic" signatures for traffic classification.
These application definitions are referenced by Day 1 WAN policies for AppQoE steering.

Mist API Reference:
- GET /api/v1/orgs/{org_id}/services - List applications
- POST /api/v1/orgs/{org_id}/services - Create application
- GET /api/v1/orgs/{org_id}/services/{service_id} - Get application
- PUT /api/v1/orgs/{org_id}/services/{service_id} - Update application
- DELETE /api/v1/orgs/{org_id}/services/{service_id} - Delete application
"""
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.mist_engine import MistEngine
from src.services.redis import get_api_host, get_org_id


router = APIRouter(prefix="/apps", tags=["Applications - Day 0"])


# =============================================================================
# Enums
# =============================================================================

class AppType(str, Enum):
    """Application type classification."""
    CUSTOM = "custom"
    STANDARD = "standard"


class TrafficClass(str, Enum):
    """Traffic class for QoS prioritization."""
    BEST_EFFORT = "best_effort"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# Models
# =============================================================================

class AppCreate(BaseModel):
    """Request payload for creating an application signature."""
    name: str = Field(..., description="Application name", examples=["Zoom", "Salesforce"])
    type: AppType = Field(default=AppType.CUSTOM, description="Application type")
    hostnames: list[str] = Field(default_factory=list, description="Hostname patterns", examples=[["*.zoom.us", "zoom.us"]])
    ips: list[str] = Field(default_factory=list, description="IP addresses/CIDR ranges")
    protocol: str | None = Field(None, description="Protocol (tcp, udp, any)")
    port: str | None = Field(None, description="Port or port range (e.g., '443', '8000-8100')")
    dscp: int | None = Field(None, ge=0, le=63, description="DSCP marking value")
    traffic_class: TrafficClass = Field(default=TrafficClass.BEST_EFFORT, description="Traffic class for QoS")
    description: str | None = Field(None, description="Application description")


class AppUpdate(BaseModel):
    """Request payload for updating an application."""
    name: str | None = Field(None, description="Application name")
    hostnames: list[str] | None = Field(None, description="Hostname patterns")
    ips: list[str] | None = Field(None, description="IP addresses/CIDR ranges")
    protocol: str | None = Field(None, description="Protocol")
    port: str | None = Field(None, description="Port or port range")
    dscp: int | None = Field(None, ge=0, le=63, description="DSCP marking value")
    traffic_class: TrafficClass | None = Field(None, description="Traffic class")
    description: str | None = Field(None, description="Application description")


class App(BaseModel):
    """Application response model."""
    id: str
    name: str
    type: str | None = None
    hostnames: list[str] = Field(default_factory=list)
    ips: list[str] = Field(default_factory=list)
    protocol: str | None = None
    port: str | None = None
    dscp: int | None = None
    traffic_class: str | None = None
    description: str | None = None
    org_id: str | None = None


class AppListResponse(BaseModel):
    """List applications response."""
    apps: list[App]
    count: int


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/", response_model=AppListResponse, summary="List all applications")
async def list_apps():
    """
    List all application signatures in the organization.

    These define "Interesting Traffic" for traffic classification and AppQoE.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    data = await engine.get(f"/api/v1/orgs/{org_id}/services")

    apps = [
        App(
            id=a.get("id", ""),
            name=a.get("name", ""),
            type=a.get("type"),
            hostnames=a.get("hostnames", []),
            ips=a.get("ips", []),
            protocol=a.get("protocol"),
            port=a.get("port"),
            dscp=a.get("dscp"),
            traffic_class=a.get("traffic_class"),
            description=a.get("description"),
            org_id=a.get("org_id"),
        )
        for a in data
    ]

    return AppListResponse(apps=apps, count=len(apps))


@router.post("/", response_model=App, summary="Create application signature")
async def create_app(request: AppCreate):
    """
    Create a new application signature.

    Application signatures define traffic patterns (hostnames, IPs, ports)
    that can be used for traffic classification and QoS policies.

    Examples:
    - Zoom: hostnames=["*.zoom.us"], traffic_class="high"
    - Salesforce: hostnames=["*.salesforce.com", "*.force.com"]
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    payload = request.model_dump(exclude_none=True)
    result = await engine.post(f"/api/v1/orgs/{org_id}/services", json=payload)

    return App(
        id=result.get("id", ""),
        name=result.get("name", request.name),
        type=result.get("type"),
        hostnames=result.get("hostnames", []),
        ips=result.get("ips", []),
        protocol=result.get("protocol"),
        port=result.get("port"),
        dscp=result.get("dscp"),
        traffic_class=result.get("traffic_class"),
        description=result.get("description"),
        org_id=result.get("org_id"),
    )


@router.get("/{app_id}", response_model=App, summary="Get application details")
async def get_app(app_id: str):
    """Get detailed information about a specific application signature."""
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    result = await engine.get(f"/api/v1/orgs/{org_id}/services/{app_id}")

    return App(
        id=result.get("id", app_id),
        name=result.get("name", ""),
        type=result.get("type"),
        hostnames=result.get("hostnames", []),
        ips=result.get("ips", []),
        protocol=result.get("protocol"),
        port=result.get("port"),
        dscp=result.get("dscp"),
        traffic_class=result.get("traffic_class"),
        description=result.get("description"),
        org_id=result.get("org_id"),
    )


@router.put("/{app_id}", response_model=App, summary="Update application")
async def update_app(app_id: str, request: AppUpdate):
    """Update an existing application signature."""
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    payload = request.model_dump(exclude_none=True)
    result = await engine.put(f"/api/v1/orgs/{org_id}/services/{app_id}", json=payload)

    return App(
        id=result.get("id", app_id),
        name=result.get("name", ""),
        type=result.get("type"),
        hostnames=result.get("hostnames", []),
        ips=result.get("ips", []),
        protocol=result.get("protocol"),
        port=result.get("port"),
        dscp=result.get("dscp"),
        traffic_class=result.get("traffic_class"),
        description=result.get("description"),
        org_id=result.get("org_id"),
    )


@router.delete("/{app_id}", summary="Delete application")
async def delete_app(app_id: str):
    """
    Delete an application signature.

    WARNING: This may affect WAN policies that reference this application.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    await engine.delete(f"/api/v1/orgs/{org_id}/services/{app_id}")

    return {"id": app_id, "status": "deleted"}
