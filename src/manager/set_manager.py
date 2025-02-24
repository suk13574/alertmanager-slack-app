from app.services.alertmanater import alertmanager_api


class SetManager:
    def __init__(self):
        pass

    def set_alertmanager_url(self, text):
        is_success = alertmanager_api.set_endpoint(text)

        if is_success:
            return f"✅ alertmanager가 {text}로 변경되었습니다."
        else:
            return f"❌ /set의 매개변수가 잘못되었습니다: {text} (k-mon01, kmon02, ncp, ncp-gov)만 가능"

