from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html

app = FastAPI(
    title="Juniper Mist - Multi Site Provisioning Service API",
    version="1.0.0"
)

status_router = APIRouter(tags=["status"])

@app.get("/status", tags=["status"], summary="Get the status of the service")
async def status():
    return {"status": "ok"}

app.include_router(status_router)

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")