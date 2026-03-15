"""FastAPI application instance and configuration."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from watersvc.database.connection import close_database
from watersvc.routers import intakes, profile, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: nothing (lazy DB init on first request)
    yield
    # Shutdown: close database connections
    await close_database()


app = FastAPI(
    title="watersvc API",
    description="API for tracking daily water intake with multi-unit support and statistics",
    version="1.0.0",
    lifespan=lifespan,
)


# Redirect root to API docs
@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")


# Include water tracking routers
app.include_router(profile.router, prefix="/api", tags=["Profile"])
app.include_router(intakes.router, prefix="/api", tags=["Intakes"])
app.include_router(stats.router, prefix="/api", tags=["Statistics"])
