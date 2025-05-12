import logging

import requests

from app.errors.alertmanager_not_initialized_error import AlertmanagerNotInitializedError
from src.manager.common.common_api import CommonAPI


class AlertmanagerAPI(CommonAPI):
    def __init__(self):
        self.alertmanager_urls = {}
        self.endpoint = None
        self.endpoint_key = None
        super().__init__()

    def init_alertmanager_urls(self, alertmanager_urls):
        self.alertmanager_urls = alertmanager_urls

        default_endpoint = self._find_default_endpoint()

        if not self.set_endpoint(default_endpoint):
            logging.warning("[Uninitialized] Alertmanager API is not initialized properly.")
        else:
            logging.info("[Initialized] AlertmanagerAPI is initialized")

    def _find_default_endpoint(self):
        if not self.alertmanager_urls:
            return None

        for name, config in self.alertmanager_urls.items():
            if config.get("default", False):
                return name

        return next(iter(self.alertmanager_urls), None)

    def set_endpoint(self, endpoint: str):
        if not self.alertmanager_urls or endpoint not in self.alertmanager_urls.keys():
            return False

        self.endpoint_key = endpoint
        self.endpoint = self.alertmanager_urls.get(endpoint).get("url")
        return True

    def _is_initialized(self):
        if not self.alertmanager_urls or not self.endpoint:
            # logging.warning("[Uninitialized] Alertmanager API is not initialized properly.")
            return False
        return True

    def _request(self, verb, url, body=None, header=None, **kwargs):
        if not self._is_initialized():
            logging.error("[Alertmanager API] - Alertmanager API is not initialized")
            raise AlertmanagerNotInitializedError

        return super()._request(verb, url, body, header, logging_instance_name="Alertmanager API")

    def get_alerts(self):
        verb = "get"
        path = "/api/v2/alerts"
        url = f"{self.endpoint}{path}"

        queries = "?silenced=false"

        return self._request(verb, url + queries).json()

    def get_silences(self):
        verb = "get"
        path = "/api/v2/silences"
        url = f"{self.endpoint}{path}"

        queries = "?active=true"

        return self._request(verb, url + queries).json()

    def post_silences(self, body):
        verb = "post"
        path = "/api/v2/silences"
        url = f"{self.endpoint}{path}"

        return self._request(verb, url, body).json()
