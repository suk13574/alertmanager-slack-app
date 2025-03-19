from functools import lru_cache

import requests

from app.services.grafana import grafana_api
from app.services.slack_cilent import slack_api

import logging
import traceback


class PanelImageManager:
    def __init__(self):
        pass

    def open_modal_ds_image(self):
        return {
            "type": "modal",
            "callback_id": "ds_image_modal",
            "title": {
                "type": "plain_text",
                "text": "Create Panel Image"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": self.make_block_folder()
        }

    def update_modal(self, view, required_blocks, additional_blocks, is_submit=False):
        """기존 블록을 유지하면서 추가 블록을 삽입"""
        base_blocks = [b for b in view["blocks"] if b["block_id"] in required_blocks]
        new_view = {
            "type": "modal",
            "callback_id": view["callback_id"],
            "title": view["title"],
            "close": view.get("close"),
            "blocks": base_blocks + additional_blocks,
        }

        # submit button 추가
        if view.get("submit"):
            new_view["submit"] = view["submit"]
        elif is_submit:
            new_view["submit"] = {
                "type": "plain_text",
                "text": "Submit"
            }

        return new_view

    def update_modal_dashboard(self, view, title, folder_id):
        required_blocks = ["grafana_folder_block"]

        return self.update_modal(view, required_blocks, self.make_block_dashboard(title, folder_id))

    def update_modal_panel(self, view, dashboard_url):
        dashboard_uid = dashboard_url.split("/")[2]
        res = grafana_api.get_dashboard(dashboard_uid)

        required_blocks = ["grafana_folder_block", "grafana_dashboard_block"]

        return self.update_modal(view, required_blocks, self.make_blocks_panel(res) + self.make_blocks_var_job(res),
                                 is_submit=True)

    def update_modal_variables(self, view, selected_data):
        job = selected_data["text"]["text"]
        if job == "none":
            return view  # 변경 없음
        label_info = eval(selected_data["value"])

        required_blocks = ["grafana_folder_block", "grafana_dashboard_block", "grafana_time_from_block",
                           "grafana_panel_block", "divider_block", "header_block", "grafana_var_job_block"]
        return self.update_modal(view, required_blocks,
                                 self.make_blocks_var_instance(job, label_info["ds_uid"], label_info["name"]))

    @staticmethod
    def make_block_folder():
        try:
            res = grafana_api.list_dash_folder()
        except requests.HTTPError as e:
            if "Unauthorized" in e.args[0]:
                slack_api.chat_post_message("❌ Grafana Token Error - Grafana 접근 권한이 없습니다.")
            else:
                slack_api.chat_post_message("❌ Grafana API 호출 중 에러가 발생했습니다.")
            raise requests.HTTPError

        options = [{
            "text": {
                "type": "plain_text",
                "text": "default",
            },
            "value": "0"
        }]
        for folder in res:
            options.append({
                "text": {
                    "type": "plain_text",
                    "text": folder.get("title", "unknown"),
                },
                "value": str(folder["id"])
            })

        blocks = [
            {
                "type": "section",
                "block_id": "grafana_folder_block",
                "text": {
                    "type": "mrkdwn",
                    "text": "Pick a dashboard folder"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a folder"
                    },
                    "options": options,
                    "action_id": "grafana-ds-folder-static_select"
                }
            }
        ]

        return blocks

    @staticmethod
    def make_block_dashboard(title, folder_id):
        res = grafana_api.list_dash_in_folder(int(folder_id))
        options = []
        for dashboard in res:
            options.append({
                "text": {
                    "type": "plain_text",
                    "text": dashboard["title"],
                },
                "value": str(dashboard["url"])
            })
        blocks = [
            {
                "type": "section",
                "block_id": "grafana_dashboard_block",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Pick a dashboard in {title}"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a dashboard"
                    },
                    "options": options,
                    "action_id": "grafana-dashboard-static_select"
                }
            }
        ]

        return blocks

    @staticmethod
    def make_blocks_panel(res: dict):
        def create_option(panel):
            return {
                "text": {
                    "type": "plain_text",
                    "text": panel.get("title", "unknown"),
                },
                "value": str(panel["id"])
            }

        options = []
        panels = res["dashboard"]["panels"]
        for panel in panels:
            if panel.get("type") == "row":
                # Row 패널 내부의 하위 패널들 처리
                for sub_panel in panel.get("panels", []):
                    options.append(create_option(sub_panel))
            else:
                # 일반 패널 처리
                options.append(create_option(panel))

        blocks = [
            {
                "type": "input",
                "block_id": "grafana_time_from_block",
                "element": {
                    "type": "radio_buttons",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "30m"
                            },
                            "value": "now-30m"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "2h"
                            },
                            "value": "now-2h"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "1d"
                            },
                            "value": "now-1d"
                        }
                    ],
                    "action_id": "time_radio_button"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Time",
                }
            },
            {
                "type": "input",
                "block_id": "grafana_panel_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a panel"
                    },
                    "options": options,
                    "action_id": "panel_static_select"
                },
                "label": {
                    "type": "plain_text",
                    "text": "panel"
                }
            }
        ]
        return blocks

    @staticmethod
    def create_dashboard_image(view):
        try:
            state_values = view["state"]["values"]

            time_from = state_values["grafana_time_from_block"]["time_radio_button"]["selected_option"]["value"]
            panel_id = state_values["grafana_panel_block"]["panel_static_select"]['selected_option']["value"]
            dashboard_url = state_values["grafana_dashboard_block"]["grafana-dashboard-static_select"]["selected_option"]["value"]
            dashboard_uid = dashboard_url.split("/")[2:][0]
            dashboard_name = dashboard_url.split("/")[2:][1]

            add_query = None
            job_block = state_values.get("grafana_var_job_block", {}).get("grafana-var-job-static_select")
            job = job_block["selected_option"]["text"]["text"]

            if job != "none":
                job_value = eval(job_block["selected_option"]["value"])
                selected_instances = (state_values.get("grafana_var_instance_block", {})
                                      .get("grafana-var-instance-multi_select_block").get("selected_options", []))
                var_job_name = job_value.get("var_job_name")
                var_instance_name = job_value.get("var_instance_name")

                add_query = f"&var-{var_job_name}={job}"
                add_query += "".join(f"&var-{var_instance_name}={inst['value']}" for inst in selected_instances)

            res = grafana_api.redner_image(dashboard_uid, dashboard_name, time_from, "now", panel_id, add_query)

            return True, res.content
        except Exception as e:
            logging.error(f"[Grafana] Error in create_dashboard_image: {traceback.format_exc()}")
            return False, f"❌ grafana dashboard image 생성 중 오류 발생: {str(e)}"

    def make_blocks_var_job(self, res):
        jobs, var_info = self.extract_var_instance(res)

        job_options = [{
            "text": {
                "type": "plain_text",
                "text": job,
            },
            "value": "none" if job == "none" else str(var_info)
        } for job in jobs]

        blocks = [
            {
                "type": "divider",
                "block_id": "divider_block"
            },
            {
                "type": "header",
                "block_id": "header_block",
                "text": {
                    "type": "plain_text",
                    "text": "(Optaion) variables select",
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "plain_text",
                        "text": "If you don’t want to select a variable, pick 'none'."
                    }
                ]
            },
            {
                "type": "actions",
                "block_id": "grafana_var_job_block",
                "elements": [{
                    "type": "radio_buttons",
                    "options": job_options,
                    "initial_option": {
                        "text": {
                            "type": "plain_text",
                            "text": "none"
                        },
                        "value": "none"
                    },
                    "action_id": "grafana-var-job-static_select"
                }],
            }
        ]
        return blocks

    def make_blocks_var_instance(self, job, ds_uid, label_name):
        label_value = self.get_label_value(ds_uid, job)
        values = list(label_value.get(label_name))

        options = [{
                    "text": {
                        "type": "plain_text",
                        "text": value
                    },
                    "value": value
                }for value in values]

        return [{
            "type": "input",
            "block_id": f"grafana_var_instance_block",
            "optional": True,
            "label": {
                "type": "plain_text",
                "text": f"Select label - label_name"
            },
            "element": {
                "type": "multi_static_select",
                "action_id": f"grafana-var-instance-multi_select_block",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select options"
                },
                "options": options
            }
        }]

    @staticmethod
    def extract_var_instance(res: dict):
        var_job_name = ""
        var_instance_name = ""
        jobs = ["none"]
        var_info = {}

        variables = res.get("dashboard", {}).get("templating", {}).get("list", [])
        for var in variables:
            if var.get("name", "").lower() == "job" and var.get("type") == "custom":
                jobs.extend(option["text"] for option in var.get("options", []))
                var_job_name = var["name"]
            elif "instance" in var.get("name", "").lower() and var.get("query", {}).get("query", "").startswith("label_values"):
                var_instance_name = var["name"]
                ds_uid = var["datasource"]["uid"]
                label_name = var["query"]["query"].replace("label_values", "").replace("(", "").replace(")", "").split(",")[-1].strip()

                var_info = {"ds_uid": ds_uid, "name": label_name}

        var_info["var_job_name"] = var_job_name
        var_info["var_instance_name"] = var_instance_name
        return jobs, var_info

    @staticmethod
    @lru_cache(maxsize=500)
    def get_label_value(ds_uid, job_name):
        label_filter = f"up{{job=\"{job_name}\"}}"
        res = grafana_api.list_label_value(ds_uid, label_filter)

        if res.get("status") != "success":
            logging.error(f"[grafana] dashboard의 variable을 불러오는데 실패했습니다. ds_uid={ds_uid}, lable_filter={label_filter}"
                          f"F \n traceback.format_exc()")
            raise Exception

        label_values = {}
        for data in res.get("data", []):
            for label_name in data.keys() - {"__name__", "job"}:
                label_values.setdefault(label_name, set()).add(data[label_name])

        return label_values
