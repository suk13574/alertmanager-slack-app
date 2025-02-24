import json
import logging

from flask import Blueprint, request, jsonify

from app.services.slack_cilent import slack_api
from src.manager.silences_manager import SilencesManager

interactions_bp = Blueprint("interactions", __name__)
silences_manager = SilencesManager()


@interactions_bp.before_request
def log_request():
    payload = request.form.get("payload", "")
    interaction_data = json.loads(payload)

    interaction_type = interaction_data.get("type", "")
    user_name = interaction_data.get("user", {}).get("username", "not found username")
    user_id = interaction_data.get("user", {}).get("id", "not found user id")

    logging.info(f"[Slack Interaction Request] User Name: {user_name}, User ID: {user_id}, Type: {interaction_type}")


@interactions_bp.route("/interactions", methods=["POST"])
def slack_interactions():
    payload = request.form.get("payload")
    if not payload:
        logging.error(f"Error - interactions don't have payload: payload - {payload}")
        return jsonify({"error": "No payload provided"}), 400

    interaction_data = json.loads(payload)
    interaction_type = interaction_data.get("type")

    if interaction_type == "block_actions":
        return handle_block_actions(interaction_data)
    elif interaction_type == "view_submission":
        return handle_view_submission(interaction_data)

    logging.error(f"Error - unknown interaction_type: {interaction_type}")
    return jsonify({"error": "Unknown interaction type"}), 400


def handle_block_actions(interaction_data):
    actions = interaction_data["actions"]
    trigger_id = interaction_data["trigger_id"]

    for action in actions:
        action_id = action["action_id"]
        action_value = action["value"]

        if action_id == "silence_button":
            block = interaction_data["message"]["blocks"]
            view = silences_manager.silence_modal(block, action_value)

            try:
                slack_api.open_view(trigger_id=trigger_id, view=view)
            except Exception as e:
                logging.error(f"Error - creating the silence modal: {e}")
                return jsonify({"error": str(e)}), 500
        else:
            logging.error(f"Error - unknown action_id: {action_id}")
            return jsonify({"error": "Unknown action_id"}), 400

        return "", 200


def handle_view_submission(interaction_data):
    callback_id = interaction_data["view"]["callback_id"]

    if callback_id == "silence_modal":
        view = interaction_data["view"]

        try:
            message = silences_manager.create_silence(view)
            slack_api.chat_post_message(text=message)
            return "", 200
        except Exception as e:
            logging.error(f"Create Silence Error: {e}")
            return jsonify({"error": str(e)}), 500

    logging.error(f"Error - unknown callback_id: {callback_id}")
    return jsonify({"error": "Unknown callback_id"}), 400
