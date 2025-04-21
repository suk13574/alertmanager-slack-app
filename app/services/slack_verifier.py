import logging

from slack_sdk.signature import SignatureVerifier

slack_verifier = None


def init_slack_verifier(signing_secret: str = None):
    global slack_verifier
    if slack_verifier is None:
        slack_verifier = SignatureVerifier(signing_secret)
        logging.info("[Initialized] Slack SignatureVerifier is initialized")
        return True
    return True


def get_slack_verifier():
    global slack_verifier

    if slack_verifier:
        return slack_verifier
    logging.warning("[Uninitialized] SignatureVerifier is None")

    return None