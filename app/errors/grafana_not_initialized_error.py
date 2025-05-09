class GrafanaNotInitializedError(Exception):
    def __init__(self, message="Grafana API is not initialized. Check Config."):
        self.message = message
        super().__init__(self.message)