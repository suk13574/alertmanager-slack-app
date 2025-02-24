from app.services.alertmanater import alertmanager_api


class AlertsManager:
    def __init__(self):
        self.main_label = "instance_name"

    def alerts(self):
        alerts = alertmanager_api.get_alerts()

        alert_template_body = {}
        for alert in alerts:
            if alert["status"]["silencedBy"]:
                continue

            main_label = alert["labels"].get(self.main_label, '-')
            alert_template_body.setdefault(main_label, []).append(
                self.make_template_body(alert["labels"], alert["fingerprint"]))

        return self.make_alert_template(alert_template_body)

    @staticmethod
    def make_template_body(labels: dict, fingerprint: str):
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
    def make_alert_template(alert_templates: dict):
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
