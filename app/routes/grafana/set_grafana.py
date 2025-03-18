import logging
import traceback

from flask import Blueprint, request, jsonify

from app.services.slack_cilent import slack_api
from src.manager.grafana.set_grafana_manager import SetGrafanaManager

set_grafana_bp = Blueprint("set_grafana", __name__)
set_grafana_manager = SetGrafanaManager()


@set_grafana_bp.before_request
def log_request():
    data = request.form

    command = data.get("command", "")
    user_name = data.get("user_name", "not found username")
    user_id = data.get("user_id", "not found user id")

    logging.info(f"[Slack Command Request] User Name: {user_name}, User ID: {user_id}, Command: {command}")


@set_grafana_bp.route("/set_grafana", methods=["POST"])
def set_alertmanager():
    try:
        text = request.form.get("text")
        message = set_grafana_manager.set_grafana_url(text)
        slack_api.chat_post_message(text=message)
        return "", 200
    except Exception as e:
        logging.error(f"Command Error - command /set: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
