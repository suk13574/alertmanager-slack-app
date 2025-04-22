import logging
import traceback

from app import slack_app
from app.services.slack_cilent import slack_api
from src.manager.alertmanager.alerts_manager import AlertsManager
from src.manager.grafana.panel_image_manager import PanelImageManager
from src.manager.alertmanager.silences_manager import SilencesManager

silences_manager = SilencesManager()
dashboard_manager = PanelImageManager()
alerts_manager = AlertsManager()


@slack_app.action("silence_button")
def silences(ack, body, say):
    ack()
    trigger_id = body["trigger_id"]

    for action in body["actions"]:
        try:
            action_value = action["value"]
            block = body["message"]["blocks"]
            view = silences_manager.open_modal_silence(block, action_value)

            slack_api.open_view(trigger_id=trigger_id, view=view)

        except Exception as e:
            logging.error(f"Slack action error - silence_button: {traceback.format_exc()}")


@slack_app.view("silence_modal")
def submit_silence(ack, body, client, view):
    ack()

    try:
        message = silences_manager.create_silence(view)
        slack_api.chat_post_message(text=message)
    except Exception as e:
        logging.error(f"Slack submit error - silence_modal: {traceback.format_exc()}")


