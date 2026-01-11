"""Vercel entry point that exposes the FastAPI app."""

from watersvc import app

# Vercel expects a variable named 'app' in this module
__all__ = ["app"]
