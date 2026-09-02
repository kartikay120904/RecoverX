"""Compatibility entrypoint for running `uvicorn app.main:app` from backend."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
project_root_path = str(PROJECT_ROOT)

if project_root_path not in sys.path:
    sys.path.insert(0, project_root_path)

from backend.app.api.main import app

__all__ = ["app"]