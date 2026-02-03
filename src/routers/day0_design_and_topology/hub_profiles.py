"""
Day 0: Hub Profiles.

Defines WAN Edge configurations for datacenter/hub sites.
Hub profiles create overlay endpoints that spoke sites connect to.
Must be created BEFORE WAN Edge templates (spoke templates).

Mist API Reference:
- GET /api/v1/orgs/{org_id}/hubprofiles - List hub profiles
- POST /api/v1/orgs/{org_id}/hubprofiles - Create hub profile
- GET /api/v1/orgs/{org_id}/hubprofiles/{hubprofile_id} - Get hub profile
- PUT /api/v1/orgs/{org_id}/hubprofiles/{hubprofile_id} - Update hub profile
- DELETE /api/v1/orgs/{org_id}/hubprofiles/{hubprofile_id} - Delete hub profile
"""
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.mist_engine import MistEngine
from src.services.redis import get_api_host, get_org_id


router = APIRouter(prefix="/hub-profiles", tags=["Hub Profiles - Day 0"])


# =============================================================================
# Enums
# =============================================================================

class WanType(str, Enum):
    """WAN interface type."""
    BROADBAND = "broadband"
    LTE = "lte"
    MPLS = "mpls"
    ETHERNET = "ethernet"


class PathPreference(str, Enum):
    """Traffic steering path preference."""
    ORDERED = "ordered"
    WEIGHTED = "weighted"
    ECMP = "ecmp"


# =============================================================================
# Models
# =============================================================================

class WanInterface(BaseModel):
    """WAN interface configuration for hub."""
    name: str = Field(..., description="Interface name", examples=["wan0", "wan1"])
    type: WanType = Field(default=WanType.BROADBAND, description="WAN link type")
    ip: str | None = Field(None, description="Static IP address (required for hub)")
    netmask: str | None = Field(None, description="Subnet mask")
    gateway: str | None = Field(None, description="Default gateway")
    weight: int = Field(default=1, ge=1, le=100, description="Path weight for weighted steering")


class LanNetwork(BaseModel):
    """LAN network attached to hub."""
    name: str = Field(..., description="Network name")
    vlan_id: int | None = Field(None, ge=1, le=4094, description="VLAN ID")
    subnet: str | None = Field(None, description="Subnet in CIDR notation")


class HubProfileCreate(BaseModel):
    """Request payload for creating a hub profile."""
    name: str = Field(..., description="Hub profile name", examples=["DC-West-Hub", "DC-East-Hub"])
    wan: list[WanInterface] = Field(default_factory=list, description="WAN interface configurations")
    lan: list[LanNetwork] = Field(default_factory=list, description="LAN networks")
    path_preference: PathPreference = Field(default=PathPreference.ORDERED, description="Traffic steering preference")
    bgp_enabled: bool = Field(default=False, description="Enable BGP routing")
    ospf_enabled: bool = Field(default=False, description="Enable OSPF routing")


class HubProfileUpdate(BaseModel):
    """Request payload for updating a hub profile."""
    name: str | None = Field(None, description="Hub profile name")
    wan: list[WanInterface] | None = Field(None, description="WAN interface configurations")
    lan: list[LanNetwork] | None = Field(None, description="LAN networks")
    path_preference: PathPreference | None = Field(None, description="Traffic steering preference")
    bgp_enabled: bool | None = Field(None, description="Enable BGP routing")
    ospf_enabled: bool | None = Field(None, description="Enable OSPF routing")


class HubProfile(BaseModel):
    """Hub profile response model."""
    id: str
    name: str
    wan: list[dict] = Field(default_factory=list)
    lan: list[dict] = Field(default_factory=list)
    path_preference: str | None = None
    bgp_enabled: bool = False
    ospf_enabled: bool = False
    org_id: str | None = None
    created_time: float | None = None
    modified_time: float | None = None


class HubProfileListResponse(BaseModel):
    """List hub profiles response."""
    hub_profiles: list[HubProfile]
    count: int


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/", response_model=HubProfileListResponse, summary="List all hub profiles")
async def list_hub_profiles():
    """
    List all hub profiles in the organization.

    Hub profiles define WAN Edge configurations for datacenter sites.
    They create overlay endpoints that spoke sites connect to via IPsec tunnels.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    data = await engine.get(f"/api/v1/orgs/{org_id}/hubprofiles")

    hub_profiles = [
        HubProfile(
            id=h.get("id", ""),
            name=h.get("name", ""),
            wan=h.get("wan", []),
            lan=h.get("lan", []),
            path_preference=h.get("path_preference"),
            bgp_enabled=h.get("bgp_enabled", False),
            ospf_enabled=h.get("ospf_enabled", False),
            org_id=h.get("org_id"),
            created_time=h.get("created_time"),
            modified_time=h.get("modified_time"),
        )
        for h in data
    ]

    return HubProfileListResponse(hub_profiles=hub_profiles, count=len(hub_profiles))


@router.post("/", response_model=HubProfile, summary="Create hub profile")
async def create_hub_profile(request: HubProfileCreate):
    """
    Create a new hub profile for a datacenter WAN Edge device.

    **IMPORTANT**: Hub profiles must be created BEFORE WAN Edge spoke templates,
    as spokes need to reference hub overlay endpoints.

    Hub devices require static IPs for overlay endpoints. The Mist cloud
    automatically generates and installs SSL certificates for the hub.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    payload = request.model_dump(exclude_none=True)
    result = await engine.post(f"/api/v1/orgs/{org_id}/hubprofiles", json=payload)

    return HubProfile(
        id=result.get("id", ""),
        name=result.get("name", request.name),
        wan=result.get("wan", []),
        lan=result.get("lan", []),
        path_preference=result.get("path_preference"),
        bgp_enabled=result.get("bgp_enabled", False),
        ospf_enabled=result.get("ospf_enabled", False),
        org_id=result.get("org_id"),
        created_time=result.get("created_time"),
        modified_time=result.get("modified_time"),
    )


@router.get("/{hubprofile_id}", response_model=HubProfile, summary="Get hub profile details")
async def get_hub_profile(hubprofile_id: str):
    """Get detailed information about a specific hub profile."""
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    result = await engine.get(f"/api/v1/orgs/{org_id}/hubprofiles/{hubprofile_id}")

    return HubProfile(
        id=result.get("id", hubprofile_id),
        name=result.get("name", ""),
        wan=result.get("wan", []),
        lan=result.get("lan", []),
        path_preference=result.get("path_preference"),
        bgp_enabled=result.get("bgp_enabled", False),
        ospf_enabled=result.get("ospf_enabled", False),
        org_id=result.get("org_id"),
        created_time=result.get("created_time"),
        modified_time=result.get("modified_time"),
    )


@router.put("/{hubprofile_id}", response_model=HubProfile, summary="Update hub profile")
async def update_hub_profile(hubprofile_id: str, request: HubProfileUpdate):
    """
    Update an existing hub profile.

    Changes to WAN interfaces may affect spoke connectivity.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    payload = request.model_dump(exclude_none=True)
    result = await engine.put(f"/api/v1/orgs/{org_id}/hubprofiles/{hubprofile_id}", json=payload)

    return HubProfile(
        id=result.get("id", hubprofile_id),
        name=result.get("name", ""),
        wan=result.get("wan", []),
        lan=result.get("lan", []),
        path_preference=result.get("path_preference"),
        bgp_enabled=result.get("bgp_enabled", False),
        ospf_enabled=result.get("ospf_enabled", False),
        org_id=result.get("org_id"),
        created_time=result.get("created_time"),
        modified_time=result.get("modified_time"),
    )


@router.delete("/{hubprofile_id}", summary="Delete hub profile")
async def delete_hub_profile(hubprofile_id: str):
    """
    Delete a hub profile.

    WARNING: This will break connectivity for any spokes referencing this hub.
    Ensure all spoke templates are updated before deleting a hub profile.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    await engine.delete(f"/api/v1/orgs/{org_id}/hubprofiles/{hubprofile_id}")

    return {"id": hubprofile_id, "status": "deleted"}
