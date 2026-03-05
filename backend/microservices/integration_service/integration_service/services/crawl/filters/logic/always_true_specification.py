from integration_service.database.repositories import IntegrationRepository
from .specification import Specification


class DefaultSpec(Specification):
    def __init__(self, repo: IntegrationRepository) -> None:
        self.repo = repo

    def is_satisfied_by(self, candidate) -> bool:
        return True
    