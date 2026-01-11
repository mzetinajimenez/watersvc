"""WaterSVC - FastAPI service on Vercel."""

__version__ = "1.0.0"

from watersvc.app import app

__all__ = ["app", "__version__"]
