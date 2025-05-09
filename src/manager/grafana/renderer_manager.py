import json
import re
from functools import lru_cache
from typing import Union, Tuple

from app.services.grafana import grafana_api

import logging
import traceback


class RendererManager:
    GRAFANA_LABEL_MAP = {}

    def __init__(self):
        pass

    def open_modal_ds_image(self) -> dict:
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

    def update_modal(self, view: dict, required_blocks: list, additional_blocks: list, is_submit=False) -> dict:
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

    def update_modal_dashboard(self, view: dict, title: str, folder_id: str) -> dict:
        required_blocks = ["grafana_folder_block"]

        return self.update_modal(view, required_blocks, self.make_block_dashboard(title, folder_id))

    def update_modal_panel(self, view: dict, dashboard_url: str) -> dict:
        dashboard_uid = dashboard_url.split("/")[-2]
        res = grafana_api.get_dashboard(dashboard_uid)

        required_blocks = ["grafana_folder_block", "grafana_dashboard_block"]

        return self.update_modal(view, required_blocks,
                                 self.make_blocks_panel(res) + self.make_block_is_var(dashboard_uid), is_submit=True)

    def update_modal_variables(self, view: dict, selected_data: dict) -> dict:
        value = selected_data["value"]
        required_blocks = ["grafana_folder_block", "grafana_dashboard_block", "grafana_time_from_block",
                           "grafana_panel_block", "grafana_is_var_block"]

        if value == "no":
            return self.update_modal(view, required_blocks, [])

        custom_vars, query_vars = self.extract_vars(value)

        query_blocks = []
        for query_var in query_vars:
            label_values = self.get_label_value(query_var["ds_uid"], query_var["query"])
            query_blocks.append(self.make_block_query_vars(label_values.get(query_var["label_name"], []), query_var))

        return self.update_modal(view, required_blocks, self.make_block_custom_vars(custom_vars) + query_blocks)

    def update_modal_query_var(self, view: dict, selected_data: dict, custom_var_name: str) -> dict:
        custom_var_value = selected_data.get("value")

        query_var_blocks = []
        required_blocks = []

        for block in view["blocks"]:
            if block["block_id"].startswith("grafana_query_var_"):
                try:
                    var_name = block["block_id"].replace("grafana_query_var_", "").replace("_block", "")
                    option_value = block.get("element", {}).get("options", [])[0].get("value")
                    if not option_value:
                        raise ValueError("option_value is empty. Check value in block options")

                    query_var = RendererManager.GRAFANA_LABEL_MAP.get(var_name, {}).get(option_value)

                    if custom_var_name in query_var.get("query", ""):
                        new_query = self.substitute_variables(query_var["query"], {custom_var_name: custom_var_value})
                        query_var_values = self.get_label_value(query_var["ds_uid"], new_query)

                        new_block = self.make_block_query_vars(query_var_values.get(query_var.get("label_name"), []), query_var)
                        query_var_blocks.append(new_block)
                    else:
                        query_var_blocks.append(block)

                except Exception as e:
                    logging.error(f"[Grafana query error] - {e}")
                    query_var_blocks.append(block)
            else:
                required_blocks.append(block["block_id"])

        return self.update_modal(view, required_blocks, query_var_blocks)

    @staticmethod
    def make_block_custom_vars(custom_vars: list) -> list[dict]:
        blocks = []

        for custom_var in custom_vars:
            var_name = custom_var.get("var_name")
            var_values = custom_var.get("var_values", [])

            options = [{
                "value": var_value,
                "text": {
                    "type": "plain_text",
                    "text": var_value
                }
            } for var_value in var_values]

            blocks.append({
                "type": "section",
                "block_id": f"grafana_custom_var_{var_name}_block",
                "text": {
                    "type": "plain_text",
                    "text": f"(Optional) Choose {var_name}"
                },
                "accessory": {
                    "type": "radio_buttons",
                    "action_id": f"custom_var_radio_button_{var_name}",
                    "options": options
                }
            })

        return blocks

    @staticmethod
    def make_block_query_vars(query_var_values: list, query_var: dict) -> dict:
        var_name = query_var.get("var_name")
        RendererManager.GRAFANA_LABEL_MAP[var_name] = {}

        # options 만들기
        options = []
        for query_var_value in query_var_values:
            RendererManager.GRAFANA_LABEL_MAP[var_name][query_var_value] = query_var
            options.append({
                "text": {
                    "type": "plain_text",
                    "text": query_var_value
                },
                "value": query_var_value
            })

        if not options:
            query_var_value = "no_value"
            RendererManager.GRAFANA_LABEL_MAP[var_name][query_var_value] = query_var
            options = [{
                "text": {
                    "type": "plain_text",
                    "text": query_var_value
                },
                "value": query_var_value
            }]

        # block 만들기
        return {
            "type": "input",
            "block_id": f"grafana_query_var_{var_name}_block",
            "optional": True,
            "label": {
                "type": "plain_text",
                "text": f"Select label - {var_name}"
            },
            "element": {
                "type": "multi_static_select",
                "action_id": f"grafana_var_multi_select_block_{var_name}",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select options"
                },
                "options": options
            }
        }

    @staticmethod
    def make_block_folder() -> list[dict]:
        res = grafana_api.list_dash_folder()

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
                    "action_id": "grafana_ds_folder_static_select"
                }
            }
        ]

        return blocks

    @staticmethod
    def make_block_dashboard(title: str, folder_id: str) -> list[dict]:
        def parse_url(dashboard_url: str) -> str:
            url_split = dashboard_url.split("/d")
            return str(url_split[-1])

        res = grafana_api.list_dash_in_folder(int(folder_id))
        options = [{
                "text": {
                    "type": "plain_text",
                    "text": dashboard["title"],
                },
                # "value": str(dashboard["url"])
                "value": parse_url(parse_url(dashboard["url"]))
            } for dashboard in res]

        blocks = []
        if options:
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
                        "action_id": "grafana_dashboard_static_select"
                    }
                }
            ]

        return blocks

    @staticmethod
    def make_blocks_panel(res: dict) -> list[dict]:
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

        blocks = []
        if options:
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
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "7d"
                                },
                                "value": "now-7d"
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
    def make_block_is_var(dashboard_uid: str) -> list[dict]:
        return [{
            "type": "section",
            "block_id": "grafana_is_var_block",
            "text": {
                "type": "plain_text",
                "text": "need variables?"
            },
            "accessory": {
                "type": "radio_buttons",
                "action_id": "is_variables_radio_button",
                "initial_option": {
                    "value": "no",
                    "text": {
                        "type": "plain_text",
                        "text": "no"
                    }
                },
                "options": [
                    {
                        "value": "no",
                        "text": {
                            "type": "plain_text",
                            "text": "no"
                        }
                    },
                    {
                        "value": dashboard_uid,
                        "text": {
                            "type": "plain_text",
                            "text": "yes"
                        },
                        "description": {
                            "type": "mrkdwn",
                            "text": "choose variables (e.g. instnace_name)"
                        }
                    }
                ]
            }
        }]

    def rendering_panel_image(self, view: dict) -> Tuple[bool, Union[bytes, str]]:
        try:
            state_values = view["state"]["values"]

            time_from = state_values["grafana_time_from_block"]["time_radio_button"]["selected_option"]["value"]
            panel_id = state_values["grafana_panel_block"]["panel_static_select"]['selected_option']["value"]
            dashboard_url = state_values["grafana_dashboard_block"]["grafana_dashboard_static_select"]["selected_option"]["value"]
            dashboard_uid = dashboard_url.split("/")[-2]
            dashboard_name = dashboard_url.split("/")[-1]

            add_query = ""
            for block_id in state_values.keys():
                if block_id.startswith("grafana_custom_var"):
                    label_name = block_id.replace("grafana_custom_var_", "").replace("_block", "")
                    selected_value = state_values[block_id].get(f"custom_var_radio_button_{label_name}", None)
                    if selected_value.get("selected_option", None):
                        label_value = selected_value["selected_option"]["value"]
                        add_query += f"&var-{label_name}={label_value}"
                elif block_id.startswith("grafana_query_var"):
                    label_name = block_id.replace("grafana_query_var_", "").replace("_block", "")
                    selected_value = state_values[block_id].get(f"grafana_var_multi_select_block_{label_name}", None)
                    if selected_value:
                        for selected_option in selected_value.get("selected_options", []):
                            label_value = selected_option.get("text", {}).get("text", None)
                            if label_value and label_value != "none":
                                add_query += f"&var-{label_name}={label_value}"

            res = grafana_api.redner_image(dashboard_uid, dashboard_name, time_from, "now", panel_id, add_query)

            return True, res.content
        except KeyError as e:
            logging.error(f"[Grafana panel image rendering error] - No have key: {e.args[0]}")
        except Exception as e:
            logging.error(f"[Grafana panel image rendering error] - {traceback.format_exc()}")
            return False, f"❌ grafana dashboard image 생성 중 오류가 발생했습니다. 로그를 확인해주세요."

    @staticmethod
    def extract_vars(dashboard_uid: str) -> Tuple[list[dict], list[dict]]:
        res = grafana_api.get_dashboard(dashboard_uid)
        variables = res.get("dashboard", {}).get("templating", {}).get("list", [])

        custom_vars = []
        query_vars = []

        for var in variables:
            if var.get("type") == "custom":
                var_name = var.get("name", "")
                current_value = var.get("current", {}).get("text")
                var_values = [option.get("text") for option in var.get("options", [])]
                custom_vars.append({
                    "var_name": var_name,
                    "current_value": current_value,
                    "var_values": var_values
                })

            elif var.get("type") == "query" and var.get("definition", "").startswith("label_values"):
                var_name = var.get("name", "")
                if var.get("datasource", None) and var.get("definition", None):
                    ds_uid = var["datasource"]["uid"]
                    query = var["definition"]

                    query_split = query.replace("label_values", "").replace("(", "").replace(")", "").split(",")
                    label_name = query_split[-1].strip()
                    query = query_split[0] if len(query_split) == 2 else "none"

                    query_vars.append({
                        "var_name": var_name,
                        "ds_uid": ds_uid,
                        "label_name": label_name,
                        "query": query
                    })

        return custom_vars, query_vars

    @staticmethod
    def substitute_variables(query: str, variables: dict) -> str:
        """문자열에서 $변수명을 찾아서 변수 값으로 치환하는 함수"""

        # 정규 표현식: `$` 다음에 나오는 영숫자 및 `_`을 변수명으로 인식
        pattern = re.compile(r'\$(\w+)')

        def replacer(match):
            var_name = match.group(1)  # 변수명 ($ 없이)
            return variables.get(var_name, match.group(0))  # 변수가 없으면 원래 값 유지

        return pattern.sub(replacer, query)

    @staticmethod
    @lru_cache(maxsize=500)
    def get_label_value(ds_uid: str, query: str) -> dict:
        """ Grafana의 label 조회 """
        res = grafana_api.query_label_value(ds_uid, query)

        if res.get("status") != "success":
            logging.error(f"[Grafana API Error] - Error getting query label, ds_uid={ds_uid}, query={query}"
                          f"\n {traceback.format_exc()}")
            raise Exception

        label_values = {}
        for result in res.get("data", {}).get("result", []):
            metric = result.get("metric", {})
            for label_name in metric.keys() - {"__name__"}:
                label_values.setdefault(label_name, set()).add(metric[label_name])

        return label_values
