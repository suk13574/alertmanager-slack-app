from flask import Flask

from app.routes.alerts import alerts_bp
from app.routes.interactions import interactions_bp
from app.routes.silences import silences_bp
from app.routes.set import set_bp

from app.services.alertmanater import alertmanager_api
from app.services.slack_cilent import slack_api

from app.utils.config import Config
from app.utils.logger import setup_logging


def create_app():
    app = Flask(__name__)

    # Setup logging
    setup_logging()

    # Setup config
    app.config.from_object(Config)
    alertmanager_api.init_alertmanager_urls(app.config.get("ALERTMANAGER_URLS"))
    slack_api.init_slack(token=app.config.get("SLACK_BOT_TOKEN"), channel=app.config.get("SLACK_CHANNEL_ID"))

    # Register Blueprints
    app.register_blueprint(alerts_bp, url_prefix="/slack")
    app.register_blueprint(silences_bp, url_prefix="/slack")
    app.register_blueprint(interactions_bp, url_prefix="/slack")
    app.register_blueprint(set_bp, url_prefix="/slack")

    return app
