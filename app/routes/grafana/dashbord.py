import logging
import traceback

from flask import Blueprint, request, jsonify

from app.services.slack_cilent import slack_api
from src.manager.grafana.panel_image_manager import PanelImageManager

dashboard_bp = Blueprint("dashboard", __name__)
dashboard_manager = PanelImageManager()


@dashboard_bp.before_request
def log_request():
    data = request.form

    command = data.get("command", "")
    user_name = data.get("user_name", "not found username")
    user_id = data.get("user_id", "not found user id")

    logging.info(f"[Slack Command Request] User Name: {user_name}, User ID: {user_id}, Command: {command}")


@dashboard_bp.route("/panel", methods=["POST"])
def panel():
    try:
        data = request.form
        trigger_id = data.get("trigger_id", "")

        view = dashboard_manager.open_modal_ds_image()
        slack_api.open_view(trigger_id=trigger_id, view=view)

        return "", 200
    except Exception as e:
        logging.error(f"Command Error - command /panel: {traceback.format_exc()}")
        return jsonify({"error": str(e), "message": str(e)}), 500
