import json
import logging
import traceback

from flask import Blueprint, request, jsonify

from app.services.slack_verifier import get_slack_verifier
from app.services.slack_cilent import slack_api
from src.manager.common.overview_manager import OverviewManager

overview_bp = Blueprint("overview", __name__)

overview_manager = OverviewManager()


@overview_bp.before_request
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


@overview_bp.route("/overview", methods=["POST"])
def overview():
    try:
        data = request.form
        user_name = data.get("user_name", "not found username")
        # user_name = "test"

        blocks = overview_manager.get_overview(user_name)
        # print(json.dumps(blocks, indent=4))

        slack_api.chat_post_message(text="overview 조회", blocks=blocks)

        return "", 200
    except Exception as e:
        logging.error(f"Command Error - command /overview: {traceback.format_exc()}")
        return jsonify({"error": str(e), "message": str(e)}), 500
