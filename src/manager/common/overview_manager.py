from app.services.alertmanater import alertmanager_api
from app.services.grafana import grafana_api


class OverviewManager:
    def __init__(self):
        pass

    def get_overview(self, user):
        blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Hello {user} 🖐️ *"
            }
        }]

        alertmanager_endpoint_key = alertmanager_api.endpoint_key
        if alertmanager_endpoint_key:
            urls = alertmanager_api.alertmanager_urls.keys()
            actions = [
                {"text": "Get Alerts", "value": "alerts"},
                {"text": "Get Silences", "value": "silences"}
            ]
            blocks.extend(self.make_block_connedted("Alertmanager", alertmanager_endpoint_key, urls, actions))
        else:
            blocks.extend(self.make_block_not_connedted("Alertmanager"))

        grafana_endpoint_key = grafana_api.endpoint_key
        if grafana_endpoint_key:
            urls = grafana_api.grafana_urls.keys()
            actions = [
                {"text": "Get Panel", "value": "panel"}
            ]
            blocks.extend(self.make_block_connedted("Grafana", grafana_endpoint_key, urls, actions))
        else:
            blocks.extend(self.make_block_not_connedted("Grafana"))

        return blocks

    def make_block_not_connedted(self, service):
        return [
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🌈 *{service}*"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{service} is not Connected!*"
                }
            }
        ]

    def make_block_connedted(self, service, init_url, urls, actions):

        url_options = [
            {
                "value": url,
                "text": {
                    "type": "plain_text",
                    "text": url
                }
            } for url in urls]

        button_element = [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": action["text"],
                },
                "value": action["value"],
                "action_id": f"overview_actions_{service.lower()}_{action["value"]}_button"
            } for action in actions
        ]

        return [
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🌈 *{service}*"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "block_id": f"{service.lower()}_urls_radio_button_block",
                "label": {
                    "type": "plain_text",
                    "text": f"{service} is Connected!",
                },
                "dispatch_action": False,
                "element": {
                    "type": "radio_buttons",
                    "action_id": f"{service.lower()}_urls_radio_button_action",
                    "initial_option": {
                        "value": init_url,
                        "text": {
                            "type": "plain_text",
                            "text": init_url
                        }
                    },
                    "options": url_options
                }
            },
            {
                "type": "actions",
                "block_id": f"{service.lower()}_actions_button_block",
                "elements": button_element
            }
        ]
