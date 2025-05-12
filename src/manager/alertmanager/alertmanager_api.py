import logging

import requests

from app.errors.alertmanager_not_initialized_error import AlertmanagerNotInitializedError


class AlertmanagerAPI:
    def __init__(self):
        self.alertmanager_urls = {}
        self.endpoint = None
        self.endpoint_key = None

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

    def _request(self, verb, url, body={}):
        if not self._is_initialized():
            logging.error("[Alertmanager API Error] - Alertmanager API is not initialized")
            raise AlertmanagerNotInitializedError

        logging.info(f"[Request Alertmanager] URL: {url}, verb: {verb}")

        try:
            if verb == "get":
                res = requests.get(url, verify=False)
            elif verb == "post":
                headers = {"Content-Type": "application/json"}

                res = requests.post(url, headers=headers, json=body)
            else:
                raise SyntaxError("[Alertmanager API Error] - Verb is not correct. verb: {verb}")

            if res.status_code >= 400:
                logging.error(f"[Alertmanger API Error] - request url: {url}, http status code: {res.status_code}, body: {res.json()}")
                raise requests.HTTPError(f"[Alertmanger API Error] - http status code: {res.status_code}, body: {res.json()}")
            else:
                return res.json()
        except requests.exceptions.SSLError as e:
            logging.error(f"[Grafana API SSL Error] - request url: {url}, error message: {e}")
            raise requests.exceptions.SSLError

    def get_alerts(self):
        verb = "get"
        path = "/api/v2/alerts"
        url = f"{self.endpoint}{path}"

        queries = "?silenced=false"

        return self._request(verb, url + queries)

    def get_silences(self):
        verb = "get"
        path = "/api/v2/silences"
        url = f"{self.endpoint}{path}"

        queries = "?active=true"

        return self._request(verb, url + queries)

    def post_silences(self, body):
        verb = "post"
        path = "/api/v2/silences"
        url = f"{self.endpoint}{path}"

        return self._request(verb, url, body)
