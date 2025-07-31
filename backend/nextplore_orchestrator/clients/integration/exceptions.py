class IntegrationCrawlRemoteError(Exception):
    def __init__(self, message: str, failed_ids: list[str] = None):
        self.message = message
        self.failed_ids = failed_ids or []
        super().__init__(message)
