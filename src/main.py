from fastapi import FastAPI, APIRouter, Depends
from fastapi.responses import RedirectResponse
from .config import Settings, get_settings

app = FastAPI(
    title="Juniper Mist - Multi Site Provisioning Service API",
    version="1.0.0"
)

status_router = APIRouter(tags=["status"])

@app.get("/status", tags=["Status"], summary="Get the status of the service")
async def status():
    return {"status": "ok"}

@app.get("/settings", tags=["Settings"], summary="Get the test variable from .env")
async def get_test_variable(settings: Settings = Depends(get_settings)):
    return {"test_variable": settings.test_variable}

app.include_router(status_router)

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")