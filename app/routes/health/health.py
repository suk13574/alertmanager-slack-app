import logging

from flask import Blueprint


health_bp = Blueprint("health", __name__)


@health_bp.before_request
def log_request():
    logging.info(f"health check")


@health_bp.route("/", methods=["GET"])
def health_check():
    return "ok", 200
