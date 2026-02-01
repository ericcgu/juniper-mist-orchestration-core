"""
Day 0: Deployment Context.

Manages the deployment context stored in Redis for Zero Touch Provisioning (ZTP).

ZTP allows network devices to be automatically configured when they first connect
to the network. By pre-registering phsyical device unique identifiers (e.g., MAC addresses), the Mist Cloud can
recognize and provision devices without manual intervention.

Context includes:
1. Physical Inventory - Device MAC addresses for ZTP claim/assignment
2. Logical Topology - VLANs for network segmentation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.redis import get_redis_client

router = APIRouter(prefix="/context", tags=["Day 0 - Context"])
CONTEXT_KEY = "deployment_context"


# =============================================================================
# Models
# =============================================================================

class DeploymentContext(BaseModel):
    """
    Physical and logical intent for a site deployment.
    Grouped by: Physical (Routers → Switches → APs) then Logical (VLANs/IPs).
    """
    # Routers (SSR)
    ssr1_mac: str | None = Field(None, example="020001263c58")
    ssr2_mac: str | None = Field(None, example="020001bf1586")
    ssr3_mac: str | None = Field(None, example="020001eb4521")
    ssr4_mac: str | None = Field(None, example="020001263c58")
    
    # Switches (EX)
    ex1_mac: str | None = Field(None, example="d081c527cb80")
    
    # Access Points (AP)
    ap1_mac: str | None = Field(None, example="ac2316ed5147")
    
    # VLANs
    mgmt_vlan: int | None = Field(None, ge=1, le=4094, example=3623)
    vlan_1: int | None = Field(None, ge=1, le=4094, example=3666)
    vlan_2: int | None = Field(None, ge=1, le=4094, example=3667)
    
    # Switch Management
    ex_ip: str | None = Field(None, example="10.210.6.26")
    ex_gateway: str | None = Field(None, example="10.210.6.30")


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/", summary="Set Deployment Context")
async def set_context(context: DeploymentContext):
    """
    Saves the deployment context to Redis.
    
    Pass device MACs and network config for ZTP provisioning.
    """
    redis_client = get_redis_client()
    redis_client.set(CONTEXT_KEY, context.model_dump_json())
    return {"status": "saved", "context": context.model_dump()}


@router.get("/", summary="Get Deployment Context")
async def get_context():
    """Retrieves the current deployment context from Redis."""
    redis_client = get_redis_client()
    data = redis_client.get(CONTEXT_KEY)
    
    if not data:
        raise HTTPException(status_code=404, detail="Deployment context not found")
    
    context = DeploymentContext.model_validate_json(data)
    return {"context": context.model_dump(), "status": "found"}


@router.delete("/", summary="Clear deployment context")
async def delete_context():
    """Removes the deployment context from Redis."""
    redis_client = get_redis_client()
    redis_client.delete(CONTEXT_KEY)
    return {"status": "deleted"}