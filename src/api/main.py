"""Entry point: `python -m src.api.main`."""

from __future__ import annotations

import logging
import os

from .app import create_app

logging.basicConfig(level=logging.INFO)

app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.environ.get("API_HOST", "127.0.0.1"),
        port=int(os.environ.get("API_PORT", "8000")),
        debug=os.environ.get("API_DEBUG", "").lower() in {"1", "true", "yes"},
    )
