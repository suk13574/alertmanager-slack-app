import logging
import re
import traceback

from app import slack_app
from src.manager.alertmanager.silences_manager import SilencesManager
from src.manager.grafana.renderer_manager import RendererManager

silences_manager = SilencesManager()
renderer_manager = RendererManager()


@slack_app.action("grafana_ds_folder_static_select")
def folder(ack, body, client):
    ack()

    for action in body["actions"]:
        try:
            title = action["selected_option"]["text"]["text"]
            folder_id = action["selected_option"]["value"]

            view_id = body["view"]["id"]
            view_hash = body["view"]["hash"]
            view = body["view"]

            new_view = renderer_manager.update_modal_dashboard(view, title, folder_id)
            client.views_update(view_id=view_id, view_hash=view_hash, view=new_view)

        except Exception as e:
            logging.error(f"[Slack action error] - grafana_ds_folder_static_select: {traceback.format_exc()}")


@slack_app.action("grafana_dashboard_static_select")
def dashboard(ack, body, client):
    ack()

    for action in body["actions"]:
        try:
            ds_url = action["selected_option"]["value"]
            view_id = body["view"]["id"]
            view_hash = body["view"]["hash"]
            view = body["view"]
            new_view = renderer_manager.update_modal_panel(view, ds_url)

            client.views_update(view_id=view_id, view_hash=view_hash, view=new_view)

        except Exception as e:
            logging.error(f"[Slack action error] - grafana_dashboard_static_select: {traceback.format_exc()}")


@slack_app.action("is_variables_radio_button")
def is_variables(ack, body, client):
    ack()

    for action in body["actions"]:
        try:
            selected_data = action["selected_option"]
            view_id = body["view"]["id"]
            view_hash = body["view"]["hash"]
            view = body["view"]
            new_view = renderer_manager.update_modal_variables(view, selected_data)

            client.views_update(view_id=view_id, view_hash=view_hash, view=new_view)
        except Exception as e:
            logging.error(f"[Slack action error] - is_variables_radio_button: {traceback.format_exc()}")


@slack_app.action(re.compile(r"^custom_var_radio_button_.*$"))
def custom_variables(ack, body, client):
    ack()

    for action in body["actions"]:
        try:
            action_id = action["action_id"]
            custom_var_name = action_id.split("_")[-1]

            selected_data = action["selected_option"]
            view_id = body["view"]["id"]
            view_hash = body["view"]["hash"]
            view = body["view"]

            new_view = renderer_manager.update_modal_query_var(view, selected_data, custom_var_name)

            client.views_update(view_id=view_id, view_hash=view_hash, view=new_view)
        except Exception as e:
            logging.error(f"[Slack action error] - {action["action_id"]}: {traceback.format_exc()}")


@slack_app.view("ds_image_modal")
def submit_panel(ack, context, client, view):
    ack()

    try:
        is_success, result = renderer_manager.rendering_panel_image(view)
        if is_success:
            client.files_upload_v2(channel=context["default_channel"],
                                   file=result,
                                   filename="grafana_panel.png",
                                   title="Grafana Panel Image 📊",
                                   initial_comment="Grafana Panel Image 📊")
        else:
            client.chat_postMessage(channel=context["default_channel"], text=result)
    except Exception as e:
        logging.error(f"[Slack submit error] - ds_image_modal: {traceback.format_exc()}")
