import logging

from app import slack_app, Config


@slack_app.use
def global_middleware(body, context, next):

    if body.get("command", None):
        logging.info(f"[Request] type: command, user: {body.get("user", "unknown")}, command: {body.get("command")}")
    elif body.get("type") == "view_submission":
        logging.info(f"[Request] type: {body.get("type")}, user: {body.get("user", "unknown")}, modal: {body.get("view", {}).get("callback_id", "unknown")}")
    elif body.get("type") == "block_actions":
        actions = ", ".join([action.get("action_id") for action in body.get("actions", [])])
        logging.info(f"[Request] type: {body.get("type")}, user: {body.get("user", "unknown")}, actions: {actions}")
    else:
        logging.info(f"[Request] type: {body.get("type")}, user: {body.get("user", "unknown")}")

    context["default_channel"] = Config.SLACK_CHANNEL_ID

    next()