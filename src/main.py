from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html

app = FastAPI(
    title="Juniper Mist - Multi Site Provisioning Service API",
    version="1.0.0"
)


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.get("/status")
async def status():
    return {"status": "ok"}