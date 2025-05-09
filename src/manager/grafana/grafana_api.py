import logging
from functools import lru_cache

import requests

from app.errors.grafana_not_initialized_error import GrafanaNotInitializedError


class GrafanaAPI:
    def __init__(self):
        self.grafana_urls = {}
        self.endpoint = None
        self.endpoint_key = None
        self.token = None

    def init_grafana(self, grafana_urls):
        self.grafana_urls = grafana_urls
        default_endpoint = self._find_default_endpoint()

        if not self.set_endpoint(default_endpoint):
            logging.warning("[Uninitialized] Grafana API is not initialized properly.")
        else:
            logging.info("[Initialized] GrafanaAPI is initialized")

    def _find_default_endpoint(self):
        if not self.grafana_urls:
            return None

        for name, config in self.grafana_urls.items():
            if config.get("default", False):
                return name

        return next(iter(self.grafana_urls), None)

    def set_endpoint(self, endpoint: str):
        if not self.grafana_urls or endpoint not in self.grafana_urls.keys():
            return False

        self.endpoint_key = endpoint
        self.endpoint = self.grafana_urls.get(endpoint).get("url")
        self.token = self.grafana_urls.get(endpoint).get("token")
        return True

    def _is_initialized(self):
        if not self.grafana_urls or not self.endpoint or not self.token:
            # logging.warning("[Uninitialized] Grafana API is not initialized properly.")
            return False
        return True

    def _request(self, verb, url, body={}, header={}):
        if not self._is_initialized():
            logging.error("[Grafana API Error] - Grafana API is not initialized")
            raise GrafanaNotInitializedError

        header["Authorization"] = f"Bearer {self.token}"
        header.setdefault("Content-Type", "application/json")

        logging.info(f"[Request Grafana API] - verb: {verb}, url: {url}")

        if verb == "get":
            res = requests.get(url, verify=False, headers=header)
        elif verb == "post":
            if not header.get("Content-Type", None):
                header["Content-Type"] = "application/json"
                res = requests.post(url, headers=header, json=body)
            else:
                res = requests.post(url, headers=header, data=body)
        else:
            raise SyntaxError(f"[Grafana API Error] - Verb is not correct. verb: {verb}")

        if res.status_code >= 400:
            logging.error(
                f"[Grafana API Error] - request url: {url}, http status code: {res.status_code}, body: {res.text}")
            raise requests.HTTPError(f"[Grafana API Error] - http status code: {res.status_code}, body: {res.text}")
        else:
            return res

    def list_dash_folder(self):
        verb = "get"
        path = "/api/search?type=dash-folder"
        url = f"{self.endpoint}{path}"

        return self._request(verb, url).json()

    def list_dash_in_folder(self, folder_id=0):
        verb = "get"
        path = f"/api/search?folderIds={folder_id}&type=dash-db"
        url = f"{self.endpoint}{path}"

        return self._request(verb, url).json()

    def list_dash_all(self):
        verb = "get"
        path = "/api/search"
        url = f"{self.endpoint}{path}"

        return self._request(verb, url).json()

    @lru_cache(maxsize=500)
    def get_dashboard(self, uid):
        verb = "get"
        path = f"/api/dashboards/uid/{uid}"
        url = f"{self.endpoint}{path}"

        return self._request(verb, url).json()

    def redner_image(self, ds_uid, ds_name, time_from, time_to, panel_id, add_query=None):
        verb = "get"
        path = f"/render/d-solo/{ds_uid}/{ds_name}"
        query = f"?orgId=1&from={time_from}&to={time_to}&panelId={panel_id}&width=1000&height=500&tz=Asia%2FSeoul"

        if add_query:
            query += add_query

        url = f"{self.endpoint}{path}{query}"
        return self._request(verb, url)

    def list_label_value(self, ds_uid, label_filter):
        verb = "post"
        path = f"/api/datasources/uid/{ds_uid}/resources/api/v1/series"
        body = f"match[]={label_filter}"
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        url = f"{self.endpoint}{path}"

        return self._request(verb, url, body, header).json()

    def query_label_value(self, ds_uid, label_query):
        verb = "get"
        path = f"/api/datasources/uid/{ds_uid}/resources/api/v1/query"
        query = f"?query={label_query}"

        url = f"{self.endpoint}{path}{query}"

        return self._request(verb, url).json()
