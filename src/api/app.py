"""Flask application factory."""

from __future__ import annotations

import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .routes import venues_bp

log = logging.getLogger(__name__)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):
        return jsonify({"error": exc.name, "message": exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        log.exception("Unhandled error: %s", exc)
        return jsonify({"error": "Internal Server Error", "message": str(exc)}), 500


def _register_cors(app: Flask) -> None:
    """Allow the Vite dev server to call the API directly."""

    @app.after_request
    def add_cors_headers(response):
        response.headers.setdefault("Access-Control-Allow-Origin", "*")
        response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type")
        response.headers.setdefault("Access-Control-Allow-Methods", "GET, OPTIONS")
        return response


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False

    if config:
        app.config.update(config)

    app.register_blueprint(venues_bp)
    _register_error_handlers(app)
    _register_cors(app)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app
