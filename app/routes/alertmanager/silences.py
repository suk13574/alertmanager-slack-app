import logging
import traceback

from flask import jsonify, Blueprint, request

from app.services.slack_cilent import slack_api
from app.services.slack_verifier import get_slack_verifier
from src.manager.alertmanager.silences_manager import SilencesManager

silences_bp = Blueprint("silences", __name__)
silences_manager = SilencesManager()


@silences_bp.before_request
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


@silences_bp.route("/silences", methods=["POST"])
def silences():
    try:
        blocks = silences_manager.get_silences()
        slack_api.chat_post_message(text=f"silence list 조회", blocks=blocks)
        return "", 200
    except Exception as e:
        logging.error(f"Command Error - command /silences: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
