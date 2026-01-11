"""FastAPI application instance and configuration."""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from watersvc.routes import router

app = FastAPI(
    title="Vercel + FastAPI",
    description="Vercel + FastAPI",
    version="1.0.0",
)


# Redirect root to API docs
@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")


# Include API router
app.include_router(router, prefix="/api")
