from app.services.grafana import grafana_api


class SetGrafanaManager:
    def __init__(self):
        pass

    def set_grafana_url(self, text):
        is_success = grafana_api.set_endpoint(text)

        if is_success:
            return f"✅ Grafana URL이 {text}로 변경되었습니다."
        else:
            return f"❌ /set의 매개변수가 잘못되었습니다: {text} (scp)만 가능"