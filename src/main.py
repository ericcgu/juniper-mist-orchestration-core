from fastapi import FastAPI, APIRouter, Depends
from fastapi.responses import RedirectResponse
from src.config import Settings, get_settings
from src.routers.day0_design_and_topology import org, nms, sites, apps, inventory

# OpenAPI tag definitions for Swagger UI grouping.
tags_metadata = [
    {
        "name": "day 0 - organization",
        "description": "Control plane identity and reachability. Validates API credentials and resolves organization context.",
    },
    {
        "name": "day 0 - nms",
        "description": "Network management system configuration. Stores device MACs, VLANs, and switch management details.",
    },
    {
        "name": "Sites - Day 0",
        "description": "Orchestrates the lifecycle (CRUD) of physical site objects and site variables within the Mist org.",
    },
    {
        "name": "Applications - Day 0",
        "description": "Global application signatures for traffic classification and AppQoE steering.",
    },
    {
        "name": "Inventory - Day 0",
        "description": "Device claim and assignment operations for Zero Touch Provisioning.",
    },
    {
        "name": "system",
        "description": "Service health and configuration endpoints.",
    },
]

app = FastAPI(
    title="Juniper Mist - Multi-Site Provisioning Service",
    description="Automates network infrastructure provisioning using the Juniper Mist Cloud API.",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

status_router = APIRouter(tags=["system"])


@app.get("/status", tags=["system"], summary="Check service health.")
async def status():
    """Returns the current health status of the provisioning service."""
    return {"status": "ok"}


@app.get("/settings", tags=["system"], summary="Retrieve environment configuration.")
async def get_test_variable(settings: Settings = Depends(get_settings)):
    """Returns the test variable from the environment configuration."""
    return {"test_variable": settings.test_variable}

app.include_router(status_router)
app.include_router(org.router)
app.include_router(nms.router)
app.include_router(sites.router)
app.include_router(apps.router)
app.include_router(inventory.router)

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")