import json
import os


def get_config_env(key, default=None):
    value = os.getenv(key, default)
    if value is None:
        raise EnvironmentError(f"Config Error - Environment variable '{key}' is not set.")
    return value


def get_config_file(key):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(current_dir), '..', 'config', 'config.json')

    try:
        with open(config_path, "r") as config_file:
            config = json.load(config_file)
            return config.get(key, None)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Config Error - Not found config file: {config_path}, error message: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Config Error - Parsing config file failed: {e}")
    except KeyError as e:
        raise KeyError(f"Config Error - Not fount '{key}' in config file: {config}, error message: {e}")


class Config:
    GRAFANA_URLS = get_config_file("GRAFANA_URLS")

    SLACK_BOT_TOKEN = get_config_env("SLACK_BOT_TOKEN")
    SLACK_CHANNEL_ID = get_config_env("SLACK_CHANNEL_ID")
    SIGNING_SECRET = get_config_env("SIGNING_SECRET")

    ALERTMANAGER_URLS = get_config_file("ALERTMANAGER_URLS")
