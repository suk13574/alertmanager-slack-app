from app.services.alertmanater import alertmanager_api


class AlertsManager:
    def __init__(self):
        self.main_label = "instance_name"

    def alerts(self) -> list[dict]:
        alerts = alertmanager_api.get_alerts()

        alert_template_body = {}
        for alert in alerts:
            if alert["status"]["silencedBy"]:
                continue

            main_label = alert["labels"].get(self.main_label, '-')
            alert_template_body.setdefault(main_label, []).append(
                self.make_block_alert(alert["labels"], alert["fingerprint"]))

        return self.make_block_alerts(alert_template_body)

    @staticmethod
    def make_block_alert(labels: dict, fingerprint: str) -> dict:
        label_str = [f"`{key}:{value}`\n" for key, value in labels.items()]

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{''.join(label_str)}"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "emoji": True,
                    "text": "Silence"
                },
                "action_id": "silence_button",
                "value": f"{fingerprint}"
            }
        }

    @staticmethod
    def make_block_alerts(alert_templates: dict) -> list[dict]:
        blocks = [{
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":mag: Firing Alert List"
            }
        }]

        for main_label, label_str in alert_templates.items():
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{main_label}*"
                    }
                },
                {"type": "divider"}
            ])

            blocks.extend(label_str)

            blocks.append({"type": "divider"})

        return blocks

    def open_modal_alerts(self):
        alerts_blocks = self.alerts()

        return {
            "type": "modal",
            "callback_id": "alerts_modal",
            "title": {
                "type": "plain_text",
                "text": "List of firing alerts"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": alerts_blocks
        }
