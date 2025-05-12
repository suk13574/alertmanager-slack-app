import logging
import ssl
import subprocess
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter


class CommonAPI:
    def __init__(self):
        pass

    def get_tls_info_openssl(self, host):
        """ host의 TLS 프로토콜, TLS 버전을 반환 """
        protocol = None
        cipher = None

        result = subprocess.run(
            ["openssl", "s_client", "-connect", f"{host}:443", "-tls1_2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            input='',
        )

        if result.returncode != 0:
            print("OpenSSL error:", result.stderr)
            return

        for line in result.stdout.splitlines():
            if "Protocol" in line or "Cipher" in line:
                if len(str(line).split(":")) >= 2:
                    if "Protocol" in str(line).split(":")[0].strip():
                        protocol = str(line).split(":")[-1].strip()
                    elif "Cipher" in str(line).split(":")[0].strip():
                        cipher = str(line).split(":")[-1].strip()

        return protocol, cipher

    def session_request(self,  verb, url, body={}, header={}):
        """ host에서 요구하는 cipher로 request """
        class TLS12Adapter(HTTPAdapter):
            def __init__(self, cipher, *args, **kwargs):
                self.cipher = cipher
                super().__init__(*args, **kwargs)

            def init_poolmanager(self, *args, **kwargs):
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                ctx.set_ciphers(self.cipher)
                kwargs['ssl_context'] = ctx
                return super().init_poolmanager(*args, **kwargs)

            def proxy_manager_for(self, *args, **kwargs):
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                ctx.set_ciphers(self.cipher)
                kwargs['ssl_context'] = ctx
                return super().proxy_manager_for(*args, **kwargs)

        try:
            host = urlparse(url).hostname
            protocol, cipher = self.get_tls_info_openssl(host)
            logging.info(f"[TLS] - host: {host}, protocol: {protocol}, cipher: {cipher}")

            if protocol != "TLSv1.2":
                logging.warning(f"[TLS] - Expected TLSv1.2 but got {protocol}")

            session = requests.Session()
            session.mount('https://', TLS12Adapter(cipher))

            if verb == "get":
                res = session.get(url, headers=header, verify=False)
            elif verb == "post":
                res = session.post(url, headers=header, json=body, verify=False)
            else:
                raise ValueError(f"[API] - Verb is not correct. verb: {verb}")

            if res.status_code >= 400:
                logging.error(
                    f"[API] - request url: {url}, http status code: {res.status_code}, body: {res.text}")
                raise requests.HTTPError(f"[API] - http status code: {res.status_code}, body: {res.text}")
            else:
                return res
        except requests.exceptions.SSLError as e:
            logging.error(f"[API] - request url: {url}, error message: {e}")
            raise requests.HTTPError(f"[Grafana API] - {e}")

