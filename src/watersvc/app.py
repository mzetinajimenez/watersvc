"""FastAPI application instance and configuration."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from watersvc.database.connection import close_database
from watersvc.routers import auth, intakes, profile, stats


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


# CORS — permissive for mobile client and Swagger UI testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Redirect root to API docs
@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")


# Include routers
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(profile.router, prefix="/api", tags=["Profile"])
app.include_router(intakes.router, prefix="/api", tags=["Intakes"])
app.include_router(stats.router, prefix="/api", tags=["Statistics"])
