from app.services.alertmanater import alertmanager_api
from app.services.slack_cilent import slack_api
from app.services.grafana import grafana_api
from app.services.slack_verifier import slack_verifier, init_slack_verifier

from app.utils.config import Config, get_config_file
from app.utils.logger import setup_logging

from slack_bolt import App

# Setup logging
setup_logging()

# Setup config
grafana_api.init_grafana(grafana_urls=Config.GRAFANA_URLS)
alertmanager_api.init_alertmanager_urls(Config.ALERTMANAGER_URLS)
slack_api.init_slack(token=Config.SLACK_BOT_TOKEN, channel=Config.SLACK_CHANNEL_ID)
# init_slack_verifier(signing_secret=app.config.get("SIGNING_SECRET"))

SLACK_BOT_TOKEN = Config.SLACK_BOT_TOKEN
slack_app = App(token=SLACK_BOT_TOKEN)