from flask import Flask

from app.routes.health.health import health_bp
from app.routes.slack.interactions import interactions_bp
from app.routes.alertmanager.alerts import alerts_bp
from app.routes.alertmanager.silences import silences_bp
from app.routes.alertmanager.set_alert import set_alert_bp
from app.routes.grafana.dashbord import dashboard_bp
from app.routes.grafana.set_grafana import set_grafana_bp

from app.services.alertmanater import alertmanager_api
from app.services.slack_cilent import slack_api
from app.services.grafana import grafana_api
from app.services.slack_verifier import slack_verifier, init_slack_verifier

from app.utils.config import Config
from app.utils.logger import setup_logging


def create_app():
    app = Flask(__name__)

    # Setup logging
    setup_logging()

    # Setup config
    app.config.from_object(Config)
    grafana_api.init_grafana(grafana_urls=app.config.get("GRAFANA_URLS"))
    alertmanager_api.init_alertmanager_urls(app.config.get("ALERTMANAGER_URLS"))
    slack_api.init_slack(token=app.config.get("SLACK_BOT_TOKEN"), channel=app.config.get("SLACK_CHANNEL_ID"))
    init_slack_verifier(signing_secret=app.config.get("SIGNING_SECRET"))

    # Register Blueprints
    app.register_blueprint(interactions_bp, url_prefix="/slack")

    # alertmanager
    app.register_blueprint(alerts_bp, url_prefix="/slack/am")
    app.register_blueprint(silences_bp, url_prefix="/slack/am")
    app.register_blueprint(set_alert_bp, url_prefix="/slack/am")

    # grafana
    app.register_blueprint(dashboard_bp, url_prefix="/slack/grafana")
    app.register_blueprint(set_grafana_bp, url_prefix="/slack/grafana")

    # main
    app.register_blueprint(health_bp)

    return app
