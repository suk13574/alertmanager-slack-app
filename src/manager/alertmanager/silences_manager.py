import calendar
import logging
import traceback
from datetime import datetime, timezone, timedelta

from app.services.alertmanater import alertmanager_api


class SilencesManager:
    def __init__(self):
        pass

    def get_silences(self):
        silences = alertmanager_api.get_silences()

        silence_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":mag_right: Silence List"
                }
            },
            {"type": "divider"}
        ]

        for silence in silences:
            if silence["status"]["state"] == "active":
                silence_blocks.extend([
                    self.make_block_silence(silence),
                    {"type": "divider"}
                ])
        return silence_blocks

    def make_block_silence(self, silence):
        return {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self.get_label(silence.get("matchers", []))
                },
                "fields": [
                    {"type": "mrkdwn", "text": f"*Start:* ```{silence.get("startsAt")}```"},
                    {"type": "mrkdwn", "text": f"*End:* ```{silence.get("endsAt")}```" },
                    {"type": "mrkdwn", "text": f"*createdBy:* ```{silence.get("createdBy")}```"},
                    {"type": "mrkdwn", "text": f"*Comment:* ```{silence.get("comment")}```"}
                ],
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Update"
                    },
                    "value": silence["id"],
                    "action_id": "silence_button",
                    "style": "primary"
                }
            }

    @staticmethod
    def get_label(matchers):
        label_str = ""

        for matcher in matchers:
            key = matcher["name"]
            value = matcher["value"]
            # is_equal = matcher["isEqual"]
            # is_regex = matcher["isRegex"]

            label_str += f"`{key}:{value}`\n"
        return label_str

    def create_silence(self, view):
        try:
            state_values = view["state"]["values"]
            private_metadata = view.get("private_metadata", None)

            dt = state_values["silence_datetime_block"]["datetime_input"]["selected_date_time"]
            creator = state_values["silence_creator_block"]["creator_input"]["value"]
            description = state_values["silence_description_block"]["description_input"]["value"]
            labels = state_values["silence_labels_block"]["labels_input"]["value"]

            end_time = datetime.fromtimestamp(dt, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            start_time = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

            body = {
                "matchers": self.make_matchers(labels),
                "startsAt": start_time,
                "endsAt": end_time,
                "createdBy": creator,
                "comment": description
            }

            if private_metadata:
                body.update({"id": private_metadata})

            alertmanager_api.post_silences(body)
        except Exception as e:
            logging.error(f"Create Silence Error - {traceback.format_exc()}")
            return f"❌ Silence 설정 처리 중 오류가 발생했습니다: \n{str(e)}"

        return "✅ Silence 설정이 성공적으로 처리되었습니다."

    def open_modal_silence(self, blocks, action_value):
        block = self.extract_block(blocks, action_value)
        labels = block["text"]["text"]
        is_update, initial_values = self.extract_fields(block)

        modal = {
            "type": "modal",
            "callback_id": "silence_modal",
            "title": {
                "type": "plain_text",
                "text": "Silence",
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit",
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel",
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "silence_datetime_block",
                    "label": {
                        "type": "plain_text",
                        "text": "End date (default: +2h)",
                    },
                    "element": {
                        "type": "datetimepicker",
                        "action_id": "datetime_input",
                        "initial_date_time": initial_values["datetime_input"]
                    }
                },
                {
                    "type": "input",
                    "block_id": "silence_creator_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Creator"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "creator_input",
                        "initial_value": initial_values["creator_input"]
                    }
                },
                {
                    "type": "input",
                    "block_id": "silence_description_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Description"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "description_input",
                        "initial_value": initial_values["description_input"]
                    }
                },
                {
                    "type": "input",
                    "block_id": "silence_labels_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Labels (key:value 형태로 작성해주세요.)"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "labels_input",
                        "initial_value": labels.replace("`", ""),
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "key:value 형태로 작성해주세요."
                        }
                    }
                },
            ]
        }

        if is_update:
            modal.update({
                "private_metadata": action_value
            })

        return modal

    @staticmethod
    def make_matchers(labels: str):
        matchers = []

        for label in labels.split('\n'):
            if label.strip():
                key, value = label.split(":", 1)
                matchers.append({
                    "name": key.strip(),
                    "value": value.strip(),
                    "isRegex": False,
                    "isEqual": True
                })
        return matchers

    @staticmethod
    def extract_block(blocks, button_value):
        for block in blocks:
            if block.get("type") == "section" and "accessory" in block:
                accessory = block["accessory"]

                if accessory.get("type") == "button" and accessory.get("value") == button_value:
                    return block

    @staticmethod
    def extract_labels(blocks, button_value):
        for block in blocks:
            if block.get("type") == "section" and "accessory" in block:
                accessory = block["accessory"]

                if accessory.get("type") == "button" and accessory.get("value") == button_value:
                    return block["text"]["text"]

    @staticmethod
    def extract_fields(block):
        initial_values = {
            "datetime_input": int((datetime.now() + timedelta(hours=2)).timestamp()),
            "creator_input": "",
            "description_input": "",
        }

        if "fields" in block:
            for field in block["fields"]:
                text = field["text"]
                if "*End:*" in text:
                    dt = datetime.strptime(text.split("```")[1], "%Y-%m-%dT%H:%M:%S.%fZ")
                    initial_values["datetime_input"] = int(calendar.timegm(dt.utctimetuple()))
                elif "*createdBy:*" in text:
                    initial_values["creator_input"] = text.split("```")[1]
                elif "*Comment:*" in text:
                    initial_values["description_input"] = text.split("```")[1]
            return True, initial_values
        else:
            return False, initial_values
