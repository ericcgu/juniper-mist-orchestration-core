"""
Day 0: Network Definitions.

Defines "who" - network/address groups used in application policies.
Networks represent traffic sources (VLANs, subnets, user groups) that can be
referenced in Day 1 WAN policies.

Mist API Reference:
- GET /api/v1/orgs/{org_id}/networks - List networks
- POST /api/v1/orgs/{org_id}/networks - Create network
- GET /api/v1/orgs/{org_id}/networks/{network_id} - Get network
- PUT /api/v1/orgs/{org_id}/networks/{network_id} - Update network
- DELETE /api/v1/orgs/{org_id}/networks/{network_id} - Delete network
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.mist_engine import MistEngine
from src.services.redis import get_api_host, get_org_id


router = APIRouter(prefix="/networks", tags=["Networks - Day 0"])


# =============================================================================
# Models
# =============================================================================

class NetworkCreate(BaseModel):
    """Request payload for creating a network definition."""
    name: str = Field(..., description="Network name", examples=["Corporate-LAN", "Guest-WiFi"])
    subnet: str | None = Field(None, description="Subnet in CIDR notation", examples=["10.0.0.0/24"])
    vlan_id: int | None = Field(None, ge=1, le=4094, description="VLAN ID")
    disallow_mist_services: bool = Field(default=False, description="Disable Mist cloud services on this network")
    gateway: str | None = Field(None, description="Gateway IP address")
    gateway6: str | None = Field(None, description="IPv6 gateway address")
    isolation: bool = Field(default=False, description="Enable client isolation")
    internet_access: bool = Field(default=True, description="Allow internet access")


class NetworkUpdate(BaseModel):
    """Request payload for updating a network."""
    name: str | None = Field(None, description="Network name")
    subnet: str | None = Field(None, description="Subnet in CIDR notation")
    vlan_id: int | None = Field(None, ge=1, le=4094, description="VLAN ID")
    disallow_mist_services: bool | None = Field(None, description="Disable Mist cloud services")
    gateway: str | None = Field(None, description="Gateway IP address")
    gateway6: str | None = Field(None, description="IPv6 gateway address")
    isolation: bool | None = Field(None, description="Enable client isolation")
    internet_access: bool | None = Field(None, description="Allow internet access")


class Network(BaseModel):
    """Network response model."""
    id: str
    name: str
    subnet: str | None = None
    vlan_id: int | None = None
    disallow_mist_services: bool = False
    gateway: str | None = None
    gateway6: str | None = None
    isolation: bool = False
    internet_access: bool = True
    org_id: str | None = None


class NetworkListResponse(BaseModel):
    """List networks response."""
    networks: list[Network]
    count: int


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/", response_model=NetworkListResponse, summary="List all networks")
async def list_networks():
    """
    List all network definitions in the organization.

    Networks define traffic source groups (the "who") for application policies.
    They can represent VLANs, subnets, or logical groupings of users/devices.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    data = await engine.get(f"/api/v1/orgs/{org_id}/networks")

    networks = [
        Network(
            id=n.get("id", ""),
            name=n.get("name", ""),
            subnet=n.get("subnet"),
            vlan_id=n.get("vlan_id"),
            disallow_mist_services=n.get("disallow_mist_services", False),
            gateway=n.get("gateway"),
            gateway6=n.get("gateway6"),
            isolation=n.get("isolation", False),
            internet_access=n.get("internet_access", True),
            org_id=n.get("org_id"),
        )
        for n in data
    ]

    return NetworkListResponse(networks=networks, count=len(networks))


@router.post("/", response_model=Network, summary="Create network definition")
async def create_network(request: NetworkCreate):
    """
    Create a new network definition.

    Networks are used in application policies to define traffic sources.
    Examples:
    - Corporate-LAN: subnet="10.0.0.0/8", vlan_id=100
    - Guest-WiFi: subnet="192.168.100.0/24", isolation=true
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    payload = request.model_dump(exclude_none=True)
    result = await engine.post(f"/api/v1/orgs/{org_id}/networks", json=payload)

    return Network(
        id=result.get("id", ""),
        name=result.get("name", request.name),
        subnet=result.get("subnet"),
        vlan_id=result.get("vlan_id"),
        disallow_mist_services=result.get("disallow_mist_services", False),
        gateway=result.get("gateway"),
        gateway6=result.get("gateway6"),
        isolation=result.get("isolation", False),
        internet_access=result.get("internet_access", True),
        org_id=result.get("org_id"),
    )


@router.get("/{network_id}", response_model=Network, summary="Get network details")
async def get_network(network_id: str):
    """Get detailed information about a specific network definition."""
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    result = await engine.get(f"/api/v1/orgs/{org_id}/networks/{network_id}")

    return Network(
        id=result.get("id", network_id),
        name=result.get("name", ""),
        subnet=result.get("subnet"),
        vlan_id=result.get("vlan_id"),
        disallow_mist_services=result.get("disallow_mist_services", False),
        gateway=result.get("gateway"),
        gateway6=result.get("gateway6"),
        isolation=result.get("isolation", False),
        internet_access=result.get("internet_access", True),
        org_id=result.get("org_id"),
    )


@router.put("/{network_id}", response_model=Network, summary="Update network")
async def update_network(network_id: str, request: NetworkUpdate):
    """Update an existing network definition."""
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    payload = request.model_dump(exclude_none=True)
    result = await engine.put(f"/api/v1/orgs/{org_id}/networks/{network_id}", json=payload)

    return Network(
        id=result.get("id", network_id),
        name=result.get("name", ""),
        subnet=result.get("subnet"),
        vlan_id=result.get("vlan_id"),
        disallow_mist_services=result.get("disallow_mist_services", False),
        gateway=result.get("gateway"),
        gateway6=result.get("gateway6"),
        isolation=result.get("isolation", False),
        internet_access=result.get("internet_access", True),
        org_id=result.get("org_id"),
    )


@router.delete("/{network_id}", summary="Delete network")
async def delete_network(network_id: str):
    """
    Delete a network definition.

    WARNING: This may affect application policies that reference this network.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    await engine.delete(f"/api/v1/orgs/{org_id}/networks/{network_id}")

    return {"id": network_id, "status": "deleted"}
