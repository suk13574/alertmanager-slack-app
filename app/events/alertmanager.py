import logging
import traceback

from slack_sdk.errors import SlackApiError

from app import slack_app
from src.manager.alertmanager.alerts_manager import AlertsManager
from src.manager.grafana.renderer_manager import RendererManager
from src.manager.alertmanager.silences_manager import SilencesManager

silences_manager = SilencesManager()
renderer_manager = RendererManager()
alerts_manager = AlertsManager()


@slack_app.action("silence_button")
def silences(ack, body, client):
    ack()

    trigger_id = body["trigger_id"]

    for action in body["actions"]:
        try:
            action_value = action["value"]
            block = body["view"]["blocks"]
            view = silences_manager.open_modal_silence(block, action_value)

            client.views_push(trigger_id=trigger_id, view=view)

        except SlackApiError as e:
            logging.error(f"[Slack command] - /overview: {e}")
        except Exception as e:
            logging.error(f"[Slack action] - silence_button: {traceback.format_exc()}")


@slack_app.view("silence_modal")
def submit_silence(ack, client, body, context, view):
    try:
        message = silences_manager.create_silence(view)
        # client.chat_postMessage(channel=context["default_channel"], text=message)
        result_view = silences_manager.open_modal_result(message)

        ack(response_action="update", view=result_view)

    except SlackApiError as e:
        logging.error(f"[Slack command] - /overview: {e}")
    except Exception as e:
        logging.error(f"[Slack submit] silence_modal: {traceback.format_exc()}")


