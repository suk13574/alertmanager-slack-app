import json
import logging
import traceback
from threading import Thread

from flask import Blueprint, request, jsonify

from app.services.slack_cilent import slack_api
from app.services.slack_verifier import get_slack_verifier
from app.services.alertmanater import alertmanager_api
from app.services.grafana import grafana_api
from src.manager.alertmanager.alerts_manager import AlertsManager
from src.manager.grafana.panel_image_manager import PanelImageManager
from src.manager.alertmanager.silences_manager import SilencesManager


interactions_bp = Blueprint("interactions", __name__)
silences_manager = SilencesManager()
dashboard_manager = PanelImageManager()
alerts_manager = AlertsManager()


@interactions_bp.before_request
def log_request():
    raw_body = request.get_data()
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")

    if not get_slack_verifier().is_valid(raw_body, timestamp, signature):
        logging.warning(f"[Not Verified Singing Signature] Signature: {signature}, Timestamp: {timestamp}, Body: {raw_body}")
        return jsonify({"error": "500", "message": "Not verified signature"}), 401

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
        logging.error(f"Slack Interaction Error - interactions don't have payload: payload - {traceback.format_exc()}")
        return jsonify({"error": "No payload provided"}), 400

    interaction_data = json.loads(payload)
    interaction_type = interaction_data.get("type")

    if interaction_type == "block_actions":
        return handle_block_actions(interaction_data)
    elif interaction_type == "view_submission":
        return handle_view_submission(interaction_data)

    logging.error(f"Slack Interaction Error - unknown interaction_type: {interaction_type}")
    return jsonify({"error": "Unknown interaction type"}), 400


def handle_block_actions(interaction_data):
    actions = interaction_data["actions"]
    trigger_id = interaction_data["trigger_id"]

    for action in actions:
        action_id = action["action_id"]
        logging.info(f"block_actions id: {action_id}")

        if action_id == "silence_button":
            action_value = action["value"]
            block = interaction_data["message"]["blocks"]
            view = silences_manager.open_modal_silence(block, action_value)

            try:
                slack_api.open_view(trigger_id=trigger_id, view=view)
            except Exception as e:
                logging.error(f"Slack Interaction Error - creating the silence modal: {traceback.format_exc()}")
                return jsonify({"error": str(e)}), 500
        elif action_id == "grafana-ds-folder-static_select":
            title = action["selected_option"]["text"]["text"]
            folder_id = action["selected_option"]["value"]

            try:
                view_id = interaction_data["view"]["id"]
                view_hash = interaction_data["view"]["hash"]
                view = interaction_data["view"]
                new_view = dashboard_manager.update_modal_dashboard(view, title, folder_id)
                slack_api.update_view(view_id=view_id, view_hash=view_hash, view=new_view)
                return "", 200
            except Exception as e:
                error_details = traceback.format_exc()
                logging.error(f"Slack Interaction Error - block action({action_id}): {error_details}")
                return jsonify({"error": str(e)}), 500
        elif action_id == "grafana-dashboard-static_select":
            try:
                ds_url = action["selected_option"]["value"]
                view_id = interaction_data["view"]["id"]
                view_hash = interaction_data["view"]["hash"]
                view = interaction_data["view"]
                new_view = dashboard_manager.update_modal_panel(view, ds_url)

                slack_api.update_view(view_id=view_id, view_hash=view_hash, view=new_view)
            except Exception as e:
                error_details = traceback.format_exc()
                logging.error(f"Slack Interaction Error - block action({action_id}): {error_details}")
                return jsonify({"error": str(e)}), 500

        elif action_id == "is_variables_radio_button":
            try:
                selected_data = action["selected_option"]
                view_id = interaction_data["view"]["id"]
                view_hash = interaction_data["view"]["hash"]
                view = interaction_data["view"]
                new_view = dashboard_manager.update_modal_variables(view, selected_data)

                slack_api.update_view(view_id=view_id, view_hash=view_hash, view=new_view)

            except Exception as e:
                logging.error(f"Slack Interaction Error - block action({action_id}): {traceback.format_exc()}")
                return jsonify({"error": str(e)}), 500

        elif action_id.startswith("custom_var_radio_button"):
            try:
                custom_var_name = action_id.split("_")[-1]

                selected_data = action["selected_option"]
                view_id = interaction_data["view"]["id"]
                view_hash = interaction_data["view"]["hash"]
                view = interaction_data["view"]

                new_view = dashboard_manager.update_modal_query_var(view, selected_data, custom_var_name)

                slack_api.update_view(view_id=view_id, view_hash=view_hash, view=new_view)

            except Exception as e:
                logging.error(f"Slack Interaction Error - block action({action_id}): {traceback.format_exc()}")
                return jsonify({"error": str(e)}), 500

        elif action_id.startswith("overview_actions_"):
            # print(json.dumps(interaction_data, indent=4))
            values = interaction_data.get("state", {}).get("values", {})

            try:
                what_action = action_id.split("_")[-1]
                service = action_id.split("_")[-2]

                if service == "alertmanager":
                    target_api = alertmanager_api
                    target_endpoint = values.get("alertmanager_urls_radio_button_block", {}).get(
                        "alertmanager_urls_radio_button_action", {}).get("selected_option", {}).get("value", None)
                elif service == "grafana":
                    target_api = grafana_api
                    target_endpoint = values.get("grafana_urls_radio_button_block", {}).get(
                        "grafana_urls_radio_button_action", {}).get("selected_option", {}).get("value", None)
                else:
                    return jsonify({"error": f"Unknown service: {service}"}, 500)

                is_changed = target_api.set_endpoint(target_endpoint)
                if not is_changed:
                    raise Exception(f"set_endpoint Error - service: {service}, endpoint: {target_endpoint}")

                if what_action == "alerts":
                    blocks = alerts_manager.alerts()
                    slack_api.chat_post_message(text=f"alerts list 조회", blocks=blocks)
                elif what_action == "silences":
                    blocks = silences_manager.get_silences()
                    slack_api.chat_post_message(text=f"silence list 조회", blocks=blocks)
                elif what_action == "panel":
                    view = dashboard_manager.open_modal_ds_image()
                    slack_api.open_view(trigger_id=trigger_id, view=view)
                    return jsonify({"error": f"Unknown action: {what_action}"}, 500)

            except Exception as e:
                logging.error(f"Slack Interaction Error - block action({action_id}): {traceback.format_exc()}")
                return jsonify({"error": str(e)}), 500

        else:
            logging.error(f"Slack Interaction Error - unknown action_id: {action_id}")
            return jsonify({"error": "Unknown action_id"}), 400

        return "", 200


def handle_view_submission(interaction_data):
    callback_id = interaction_data["view"]["callback_id"]

    logging.info(f"view_submission id: {callback_id}")

    if callback_id == "silence_modal":
        view = interaction_data["view"]

        try:
            message = silences_manager.create_silence(view)
            slack_api.chat_post_message(text=message)
            return "", 200
        except Exception as e:
            logging.error(f"Slack Interaction Error - During create silence: {traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500
    elif callback_id == "ds_image_modal":
        view = interaction_data["view"]

        try:
            def process_image_async():
                is_success, result = dashboard_manager.create_dashboard_image(view)
                if is_success:
                    slack_api.upload_file(file=result,
                                          filename="grafana_panel.png",
                                          title="Grafana Panel Image 📊",
                                          initial_comment="Here is the Grafana panel image.")
                else:
                    slack_api.chat_post_message(text=result)

            # 비동기 스레드 시작
            Thread(target=process_image_async).start()
            return "", 200
        except Exception as e:
            logging.error(f"Slack Interaction Error - During create dashboard image: {traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500

    else:
        logging.error(f"Slack Interaction Error - unknown callback_id: {callback_id}")
        return jsonify({"error": "Unknown callback_id"}), 400
