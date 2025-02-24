import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackAPI:
    def __init__(self):
        self.channel = None
        self.slack_client = None

    def init_slack(self, token, channel):
        self.slack_client = WebClient(token)
        self.channel = channel

    def chat_post_message(self, text, blocks=None):
        try:
            if blocks:
                self.slack_client.chat_postMessage(channel=self.channel, blocks=blocks, text=text)
            else:
                self.slack_client.chat_postMessage(channel=self.channel, text=text)
        except SlackApiError as e:
            logging.error(f"Error - Slack API: {e.response['error']}")
            raise SlackApiError
        except Exception as e:
            logging.error(f"Error - while sending Slack message: {e}")
            raise Exception

    def open_view(self, trigger_id, view):
        try:
            self.slack_client.views_open(trigger_id=trigger_id, view=view)
        except SlackApiError as e:
            logging.error(f"Error - Slack API: {e.response['error']}")
        except Exception as e:
            logging.error(f"Error - while sending Slack message: {e}")
