from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="Juniper Mist Mega Lab API",
    version="1.0.0"
)

@app.get("/")
def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.get("/status")
async def status():
    return {"status": "ok"}