from typing import List 


class IntegrationCrawlRemoteError(Exception):
    def __init__(self, message: str, failed_ids: List[str] = None):
        self.message = message
        self.failed_ids = failed_ids or []
        
        super().__init__(message)
