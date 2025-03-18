import logging
import requests


class GrafanaAPI:
    def __init__(self):
        self.grafana_urls = {}
        self.endpoint = None
        self.token = None

    def init_grafana(self, token, grafana_urls, endpoint="dev"):
        self.token = token

        self.grafana_urls = grafana_urls
        self.set_endpoint(endpoint)

    def set_endpoint(self, endpoint: str):
        if endpoint not in self.grafana_urls.keys():
            return False
        self.endpoint = self.grafana_urls.get(endpoint)
        return True

    def _request(self, verb, url, body={}, header={}):
        logging.info(f"[Request Grafana] URL: {url}, verb: {verb}")

        header["Authorization"] = f"Bearer {self.token}"
        header.setdefault("Content-Type", "application/json")

        if verb == "get":
            res = requests.get(url, verify=False, headers=header)
        elif verb == "post":
            if not header.get("Content-Type", None):
                header["Content-Type"] = "application/json"
                res = requests.post(url, headers=header, json=body)
            else:
                res = requests.post(url, headers=header, data=body)
        else:
            raise SyntaxError("Verb is not correct.")

        if res.status_code >= 400:
            logging.error(f"Grafana API Error - request url: {url}, http status code: {res.status_code}, body: {res.text}")
            raise requests.HTTPError(f"Grafana API Error - http status code: {res.status_code}, body: {res.text}")
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

