import logging
import traceback

from flask import Blueprint, request, jsonify

from app.services.slack_cilent import slack_api
from app.services.slack_verifier import get_slack_verifier
from src.manager.alertmanager.set_aert_manager import SetAlertManager

set_alert_bp = Blueprint("set_alert", __name__)
set_alert_manager = SetAlertManager()


@set_alert_bp.before_request
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


@set_alert_bp.route("/set_alert", methods=["POST"])
def set_alertmanager():
    try:
        text = request.form.get("text")
        message = set_alert_manager.set_alertmanager_url(text)
        slack_api.chat_post_message(text=message)
        return "", 200
    except Exception as e:
        logging.error(f"Command Error - command /set: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
