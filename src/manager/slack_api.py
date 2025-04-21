import logging
import traceback

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
            logging.error(f"Slack API Error - {e.response['error']}")
            raise SlackApiError
        except Exception as e:
            logging.error(f"Slack API Error - while sending Slack message: {traceback.format_exc()}")
            raise Exception

    def open_view(self, trigger_id, view):
        try:
            self.slack_client.views_open(trigger_id=trigger_id, view=view)
        except SlackApiError as e:
            logging.error(f"Slack API Error - {e.response['error']}")
        except Exception as e:
            logging.error(f"Slack API Error - while sending Slack message: {traceback.format_exc()}")

    def update_view(self, view_id, view_hash, view):
        try:
            self.slack_client.views_update(view_id=view_id, hash=view_hash, view=view)
        except SlackApiError as e:
            logging.error(f"Slack API Error - {traceback.format_exc()}")
        except Exception as e:
            logging.error(f"Slack API Error - while sending Slack message: {traceback.format_exc()}")

    def upload_file(self, file, filename, title, initial_comment=""):
        try:
            self.slack_client.files_upload_v2(
                channel=self.channel, file=file, filename=filename, title=title, initial_comment=initial_comment)
        except SlackApiError as e:
            logging.error(f"Slack API Error - {traceback.format_exc()}")
        except Exception as e:
            logging.error(f"Slack API Error - while sending Slack message: {traceback.format_exc()}")
