from app import slack_app
from app.utils.config import Config
from slack_bolt.adapter.socket_mode import SocketModeHandler
import app.events.overview
import app.events.alertmanager
import app.events.grafana


if __name__ == "__main__":
    handler = SocketModeHandler(slack_app, Config.SLACK_BOT_SOCKET_MODE_TOKEN)
    handler.start()
