import logging
import traceback

import requests

from app import slack_app
from app.errors.set_endpoint_error import SetEndpointError

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
        logging.error(f"[Slack command error] - /overview: {traceback.format_exc()}")


@slack_app.action("overview_actions_alertmanager_alerts_button")
def overview_alerts(ack, body, say, client):
    ack()
    try:
        trigger_id = body["trigger_id"]

        values = body["state"]["values"]
        endpoint = (values.get("alertmanager_urls_radio_button_block", {}).get("alertmanager_urls_radio_button_action", {})
                    .get("selected_option", {}).get("value", None))

        if not alertmanager_api.set_endpoint(endpoint):
            raise SetEndpointError(endpoint, "alertmanager")

        view = alerts_manager.open_modal_alerts()
        client.views_open(trigger_id=trigger_id, view=view)
        # say(blocks=blocks, text="alerts 조회")

    except SetEndpointError as e:
        logging.error(f"[Set endpoint error] - {e}")
        say(text=f"❌ endpoint 설정에 실패했습니다. 로그와 config 설정을 확인해주세요")
    except Exception as e:
        logging.error(f"[Slack action error] - overview_actions_alertmanager_alerts_button: {traceback.format_exc()}")


@slack_app.action("overview_actions_alertmanager_silences_button")
def overview_silences(ack, body, say, client):
    ack()
    try:
        trigger_id = body["trigger_id"]

        values = body["state"]["values"]
        endpoint = (values.get("alertmanager_urls_radio_button_block", {}).get("alertmanager_urls_radio_button_action", {})
                    .get("selected_option", {}).get("value", None))
        if not alertmanager_api.set_endpoint(endpoint):
            raise SetEndpointError(endpoint, "alertmanager")

        view = silences_manager.open_modal_silence_list()

        client.views_open(trigger_id=trigger_id, view=view)
        # say(blocks=blocks, text="silences 조회")
    except SetEndpointError as e:
        logging.error(f"[Set endpoint error] - {e}")
        say(text=f"❌ endpoint 설정에 실패했습니다. 로그와 config 설정을 확인해주세요")
    except Exception as e:
        logging.error(f"[Slack action error] - overview_actions_alertmanager_silences_button: {traceback.format_exc()}")


@slack_app.action("overview_actions_grafana_panel_button")
def overview_panel(ack, context, body, client, say):
    ack()
    try:
        trigger_id = body["trigger_id"]

        values = body["state"]["values"]
        endpoint = (values.get("grafana_urls_radio_button_block", {}).get("grafana_urls_radio_button_action", {})
                    .get("selected_option", {}).get("value", None))

        if not grafana_api.set_endpoint(endpoint):
            raise SetEndpointError(endpoint, "grafana")

        view = renderer_manager.open_modal_ds_image()
        client.views_open(trigger_id=trigger_id, view=view)
    except SetEndpointError as e:
        logging.error(f"[Set endpoint error] - {e}")
        say(text=f"❌ endpoint 설정에 실패했습니다. 로그와 config 설정을 확인해주세요")
    except requests.HTTPError as e:
        if "Unauthorized" in e.args[0]:
            message = "❌ Grafana Token Error - Grafana 접근 권한이 없습니다."
        else:
            message = "❌ Grafana API 호출 중 에러가 발생했습니다."
        client.chat_postMessage(channel=context["default_channel"], text=message)
    except Exception as e:
        logging.error(f"[Slack action error] - overview_actions_grafana_panel_button: {traceback.format_exc()}")