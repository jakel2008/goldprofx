"""Render/Gunicorn entrypoint.

Keeps backward compatibility with `gunicorn app:app` while serving
the canonical application from `wsgi.py`.
"""
from wsgi import app

__all__ = ["app"]
