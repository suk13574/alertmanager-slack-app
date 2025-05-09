from app.services.alertmanater import alertmanager_api
from app.services.grafana import grafana_api

from app.utils.config import Config, get_config_file
from app.utils.logger import setup_logging

from slack_bolt import App

# Setup logging
setup_logging()

# Setup config
grafana_api.init_grafana(grafana_urls=Config.GRAFANA_URLS)
alertmanager_api.init_alertmanager_urls(Config.ALERTMANAGER_URLS)

SLACK_BOT_TOKEN = Config.SLACK_BOT_TOKEN
slack_app = App(token=SLACK_BOT_TOKEN)