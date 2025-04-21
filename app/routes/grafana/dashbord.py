import logging
import traceback

from flask import Blueprint, request, jsonify

from app.errors.GrafanaNotInitializedError import GrafanaNotInitializedError
from app.services.slack_cilent import slack_api
from app.services.slack_verifier import get_slack_verifier
from src.manager.grafana.panel_image_manager import PanelImageManager

dashboard_bp = Blueprint("dashboard", __name__)
dashboard_manager = PanelImageManager()


@dashboard_bp.before_request
def log_request():
    raw_body = request.get_data()
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")

    if not get_slack_verifier().is_valid(raw_body, timestamp, signature):
        logging.warning(f"[Not Verified Singing Signature] Signature: {signature}, Timestamp: {timestamp}, Body: {raw_body}")
        return jsonify({"error": "500", "message": "Not verified signature"}), 401

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
    except GrafanaNotInitializedError as e:
        slack_api.chat_post_message(text=e.message)
        return jsonify({"error": str(e), "message": str(e)}), 500
    except Exception as e:
        logging.error(f"Command Error - command /panel: {traceback.format_exc()}")
        return jsonify({"error": str(e), "message": str(e)}), 500
