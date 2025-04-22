class AlertmanagerNotInitializedError(Exception):
    """Raised when the Alertmanager API is not properly initialized."""
    def __init__(self, message="Alertmanager API is not initialized. Check Config."):
        self.message = message
        super().__init__(self.message)