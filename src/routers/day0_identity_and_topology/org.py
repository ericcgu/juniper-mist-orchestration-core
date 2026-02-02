"""
Day 0: Control Plane Identity & Reachability.

This module acts as the 'Genesis' check for the automation pipeline. 
It performs a Layer 7 handshake with the Mist Cloud to validate:
1. **Authentication:** Resolution of the User and Organization Context.
2.  **Identity:** Handles the initial connection to the Mist API /self endpoint.
3.  **Reachability:** Availability of the specific Regional Cloud (Global vs. EU).
"""
import fnc
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services.mist_engine import MistEngine
from src.services.redis import get_redis_client


router = APIRouter(prefix="/org", tags=["day 0 - organization"])


# =============================================================================
# Request Models
# =============================================================================

class SelfRequest(BaseModel):
    """Request model for retrieving self/organization info."""
    api_host: str | None = Field(
        default="api.ac2.mist.com",
        description="Mist API host (e.g., api.mist.com, api.eu.mist.com)"
    )
    org_id: str | None = Field(
        default=None,
        description="Organization ID. If not provided, will be extracted from API response."
    )


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/self", summary="Validate API credentials and resolve organization context.")
async def get_self(
    request: SelfRequest = SelfRequest()
):
    """
    Performs a Layer 7 handshake with the Mist Cloud to validate authentication
    and resolve organization identity.

    This endpoint calls the Mist API `/api/v1/self` to retrieve the authenticated
    user and organization details. If `org_id` is not provided, it will be
    extracted from the last org-scoped privilege in the response.

    Use this endpoint to verify API credentials before proceeding with provisioning.
    """
    engine = MistEngine(host=request.api_host)
    result = await engine.get_self()
    
    # Determine org_id: use provided value or extract from privileges
    org_id = request.org_id
    if not org_id:
        # Find the last org-scoped privilege
        privileges = result.get("privileges", [])
        org_priv = fnc.findlast({"scope": "org"}, privileges)
        if org_priv:
            org_id = org_priv.get("org_id")
    
    # Save to Redis
    redis_client = get_redis_client()
    redis_client.set("api_host", request.api_host)
    if org_id:
        redis_client.set("org_id", org_id)
    
    return result
