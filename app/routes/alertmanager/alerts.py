import logging
import traceback

from flask import Blueprint, request, jsonify
from slack_sdk.errors import SlackApiError

from app.services.slack_cilent import slack_api
from src.manager.alertmanager.alerts_manager import AlertsManager

alerts_bp = Blueprint("alerts", __name__)
alerts_manager = AlertsManager()


@alerts_bp.before_request
def log_request():
    data = request.form

    command = data.get("command", "")
    user_name = data.get("user_name", "not found username")
    user_id = data.get("user_id", "not found user id")

    logging.info(f"[Slack Command Request] User Name: {user_name}, User ID: {user_id}, Command: {command}")


@alerts_bp.route("/alerts", methods=["POST"])
def alerts():
    try:
        blocks = alerts_manager.alerts()
        slack_api.chat_post_message(text=f"alerts list 조회", blocks=blocks)
        return "", 200
    except SlackApiError as e:
        logging.error(f"SlackApiError: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logging.error(f"Command Error - command /alerts: {traceback.format_exc()}")
        return jsonify({"error": str(e), "message": str(e)}), 500
