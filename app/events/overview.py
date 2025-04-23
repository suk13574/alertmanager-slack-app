import logging
import traceback

from app import slack_app

from src.manager.common.overview_manager import OverviewManager
from app.services.alertmanater import alertmanager_api
from app.services.grafana import grafana_api
from src.manager.alertmanager.alerts_manager import AlertsManager
from src.manager.grafana.renderer_manager import RendererManager
from src.manager.alertmanager.silences_manager import SilencesManager

silences_manager = SilencesManager()
renderer_manager = RendererManager()
alerts_manager = AlertsManager()

overview_manager = OverviewManager()


@slack_app.command("/overview")
def overview(ack, say, command):
    ack()

    try:
        user_name = command["user_name"]
        blocks = overview_manager.get_overview(user_name)

        say(blocks=blocks, text="overview 조회")
    except Exception as e:
        logging.error(f"Slack command error - /overview: {traceback.format_exc()}")


@slack_app.action("overview_actions_alertmanager_alerts_button")
def overview_alerts(ack, body, say):
    ack()
    try:
        values = body["state"]["values"]
        endpoint = (values.get("alertmanager_urls_radio_button_block", {}).get("alertmanager_urls_radio_button_action", {})
                    .get("selected_option", {}).get("value", None))
        alertmanager_api.set_endpoint(endpoint)

        blocks = alerts_manager.alerts()
        say(blocks=blocks, text="alerts 조회")
    except Exception as e:
        logging.error(f"Slack action error - overview_actions_alertmanager_alerts_button: {traceback.format_exc()}")


@slack_app.action("overview_actions_alertmanager_silences_button")
def overview_silences(ack, body, say):
    ack()
    try:
        values = body["state"]["values"]
        endpoint = (values.get("alertmanager_urls_radio_button_block", {}).get("alertmanager_urls_radio_button_action", {})
                    .get("selected_option", {}).get("value", None))
        alertmanager_api.set_endpoint(endpoint)

        blocks = silences_manager.get_silences()
        say(blocks=blocks, text="silences 조회")
    except Exception as e:
        logging.error(f"Slack action error - overview_actions_alertmanager_silences_button: {traceback.format_exc()}")


@slack_app.action("overview_actions_grafana_panel_button")
def overview_panel(ack, body, client):
    ack()
    try:
        trigger_id = body["trigger_id"]

        values = body["state"]["values"]
        endpoint = (values.get("grafana_urls_radio_button_block", {}).get("grafana_urls_radio_button_action", {})
                    .get("selected_option", {}).get("value", None))

        grafana_api.set_endpoint(endpoint)

        view = renderer_manager.open_modal_ds_image()
        client.views_open(trigger_id=trigger_id, view=view)
    except Exception as e:
        logging.error(f"Slack action error - overview_actions_grafana_panel_button: {traceback.format_exc()}")