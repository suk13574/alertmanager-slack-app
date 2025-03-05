import logging

import requests


class AlertmanagerAPI:
    def __init__(self):
        self.alertmanager_urls = {}
        self.endpoint = None

    def init_alertmanager_urls(self, alertmanager_urls, endpoint="k-mon01"):
        self.alertmanager_urls = alertmanager_urls
        self.set_endpoint(endpoint)

    def set_endpoint(self, endpoint: str):
        if endpoint not in self.alertmanager_urls.keys():
            return False
        self.endpoint = self.alertmanager_urls.get(endpoint)
        return True

    def _request(self, verb, url, body={}):
        logging.info(f"[Request Alertmanager] URL: {url}, verb: {verb}")
        if verb == "get":
            res = requests.get(url, verify=False)
        elif verb == "post":
            headers = {"Content-Type": "application/json"}

            res = requests.post(url, headers=headers, json=body)
        else:
            raise SyntaxError("Verb is not correct.")

        if res.status_code >= 400:
            logging.error(f"Alertmanger API Error - request url: {url}, http status code: {res.status_code}, body: {res.json()}")
            raise requests.HTTPError(f"Alertmanger API Error - http status code: {res.status_code}, body: {res.json()}")
        else:
            return res.json()

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
