"""
Inventory Router - Day 0: Supply Chain Logistics
Handles device assignment and claim operations.

Mist API Reference:
- GET /api/v1/orgs/{org_id}/inventory - List inventory
- POST /api/v1/orgs/{org_id}/inventory - Claim devices
- PUT /api/v1/orgs/{org_id}/inventory - Update inventory (assign/unassign)
"""
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services.mist_engine import MistEngine
from src.services.redis import get_api_host, get_org_id


router = APIRouter(prefix="/inventory", tags=["Inventory - Day 0"])


# =============================================================================
# Enums
# =============================================================================

class DeviceType(str, Enum):
    """Mist device types for inventory filtering."""
    GATEWAY = "gateway"  # SSR/SRX WAN Edge
    SWITCH = "switch"    # EX Series
    AP = "ap"            # Access Point


# =============================================================================
# Models
# =============================================================================

class DeviceAssignment(BaseModel):
    """Device assignment request."""
    serial_numbers: list[str] = Field(..., description="List of device serial numbers")
    site_id: str = Field(..., description="Target site ID")
    managed: bool = Field(default=True, description="Enable Mist management")


class ClaimDevice(BaseModel):
    """Claim device request."""
    claim_codes: list[str] = Field(..., description="Device claim codes")


class UnassignDevice(BaseModel):
    """Unassign device request."""
    serial_numbers: list[str] = Field(..., description="List of device serial numbers")


class InventoryDevice(BaseModel):
    """Device in inventory."""
    serial: str
    mac: str | None = None
    model: str | None = None
    type: DeviceType | None = None
    site_id: str | None = None
    site_name: str | None = None
    name: str | None = None
    connected: bool = False


class InventoryResponse(BaseModel):
    """Inventory list response."""
    devices: list[InventoryDevice]
    count: int
    limit: int
    page: int


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/", summary="List all inventory devices")
async def list_inventory(
    type: DeviceType | None = Query(None, description="Filter by device type"),
    unassigned: bool = Query(False, description="Only show unassigned devices"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    page: int = Query(1, ge=1, description="Page number"),
) -> InventoryResponse:
    """
    List all devices in the organization inventory.

    - **type**: Filter by device type (gateway, switch, ap)
    - **unassigned**: Filter to devices not yet assigned to a site
    - **limit**: Results per page (max 1000)
    - **page**: Page number for pagination
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    params = {"limit": limit, "page": page}
    if type:
        params["type"] = type.value
    if unassigned:
        params["unassigned"] = "true"

    data = await engine.get(f"/api/v1/orgs/{org_id}/inventory", params=params)

    devices = [
        InventoryDevice(
            serial=d.get("serial", ""),
            mac=d.get("mac"),
            model=d.get("model"),
            type=d.get("type"),
            site_id=d.get("site_id"),
            site_name=d.get("site_name"),
            name=d.get("name"),
            connected=d.get("connected", False),
        )
        for d in data
    ]

    return InventoryResponse(
        devices=devices,
        count=len(devices),
        limit=limit,
        page=page
    )


@router.get("/{serial}", summary="Get device details")
async def get_device(serial: str) -> InventoryDevice:
    """Get detailed information about a specific device by serial number."""
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    data = await engine.get(f"/api/v1/orgs/{org_id}/inventory", params={"serial": serial})

    if not data:
        return InventoryDevice(serial=serial, connected=False)

    d = data[0] if isinstance(data, list) else data
    return InventoryDevice(
        serial=d.get("serial", serial),
        mac=d.get("mac"),
        model=d.get("model"),
        type=d.get("type"),
        site_id=d.get("site_id"),
        site_name=d.get("site_name"),
        name=d.get("name"),
        connected=d.get("connected", False),
    )


@router.post("/assign", summary="Step 2: Assign Devices to Sites")
async def assign_devices(request: DeviceAssignment):
    """
    **Step 2: Assign Devices to Sites (Day 0)**

    Assigns claimed devices to a specific site. Requires the Site ID
    from Step 1. Devices will adopt site-specific configurations
    once assigned.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    payload = [
        {
            "op": "assign",
            "site_id": request.site_id,
            "macs": [],
            "serials": request.serial_numbers,
            "managed": request.managed,
        }
    ]

    result = await engine.put(f"/api/v1/orgs/{org_id}/inventory", json=payload)

    return {
        "site_id": request.site_id,
        "devices_assigned": len(request.serial_numbers),
        "serial_numbers": request.serial_numbers,
        "status": "assigned",
        "result": result,
    }


@router.post("/claim", summary="Claim devices to organization")
async def claim_devices(request: ClaimDevice):
    """
    Claim devices to the organization using claim codes.
    Devices must be claimed before they can be assigned to sites.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    result = await engine.post(f"/api/v1/orgs/{org_id}/inventory", json=request.claim_codes)

    return {
        "org_id": org_id,
        "claimed_count": len(request.claim_codes),
        "status": "claimed",
        "result": result,
    }


@router.post("/unassign", summary="Unassign devices from site")
async def unassign_devices(request: UnassignDevice):
    """
    Unassign devices from their current site.
    Devices remain in org inventory but are no longer site-assigned.
    """
    api_host, org_id = get_api_host(), get_org_id()
    if not api_host or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing api_host or org_id. Call POST /org/self first."
        )

    engine = MistEngine(host=api_host)
    payload = [
        {
            "op": "unassign",
            "macs": [],
            "serials": request.serial_numbers,
        }
    ]

    result = await engine.put(f"/api/v1/orgs/{org_id}/inventory", json=payload)

    return {
        "serial_numbers": request.serial_numbers,
        "status": "unassigned",
        "result": result,
    }
