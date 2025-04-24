class SetEndpointError(Exception):
    def __init__(self, endpoint, service, message=None):
        self.endpoint = endpoint
        self.service = service
        self.message = message or f"Endpoint is not changed. service: {service}, endpoint: {endpoint}"
        super().__init__(self.message)
