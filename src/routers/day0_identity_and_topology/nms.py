"""
Day 0: NMS Configuration.

Manages the network management system profile stored in Redis for Zero Touch Provisioning (ZTP).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.redis import get_redis_client

router = APIRouter(prefix="/nms", tags=["day 0 - nms"])
NMS_KEY = "nms_profile"


# =============================================================================
# Models
# =============================================================================

class DeploymentProfile(BaseModel):
    """
    Physical and logical intent for a site deployment.
    Grouped by: Physical (Routers → Switches → APs) then Logical (VLANs/IPs).
    """
    # Routers (SSR)
    ssr1_mac: str | None = Field(None, examples=["020001263c58"])
    ssr2_mac: str | None = Field(None, examples=["020001bf1586"])
    ssr3_mac: str | None = Field(None, examples=["020001eb4521"])
    ssr4_mac: str | None = Field(None, examples=["020001263c58"])

    # Switches (EX)
    ex1_mac: str | None = Field(None, examples=["d081c527cb80"])

    # Access Points (AP)
    ap1_mac: str | None = Field(None, examples=["ac2316ed5147"])

    # VLANs
    mgmt_vlan: int | None = Field(None, ge=1, le=4094, examples=[3623])
    vlan_1: int | None = Field(None, ge=1, le=4094, examples=[3666])
    vlan_2: int | None = Field(None, ge=1, le=4094, examples=[3667])

    # Switch Management
    ex_ip: str | None = Field(None, examples=["10.210.6.26"])
    ex_gateway: str | None = Field(None, examples=["10.210.6.30"])


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/", summary="Save the NMS profile for site deployment.")
async def set_profile(profile: DeploymentProfile):
    """
    Persists the NMS profile to Redis for Zero Touch Provisioning.

    Accepts device MAC addresses and network configuration that will be used
    during site provisioning workflows.
    """
    redis_client = get_redis_client()
    redis_client.set(NMS_KEY, profile.model_dump_json())
    return {"status": "saved", "profile": profile.model_dump()}


@router.get("/", summary="Fetch the active NMS profile configuration.")
async def get_profile():
    """Retrieves the current NMS profile from Redis for use in provisioning workflows."""
    redis_client = get_redis_client()
    data = redis_client.get(NMS_KEY)

    if not data:
        raise HTTPException(status_code=404, detail="NMS profile not found")

    profile = DeploymentProfile.model_validate_json(data)
    return {"profile": profile.model_dump(), "status": "found"}


@router.delete("/", summary="Clear the NMS profile from storage.")
async def delete_profile():
    """Removes the NMS profile from Redis, allowing a fresh start for a new site."""
    redis_client = get_redis_client()
    redis_client.delete(NMS_KEY)
    return {"status": "deleted"}