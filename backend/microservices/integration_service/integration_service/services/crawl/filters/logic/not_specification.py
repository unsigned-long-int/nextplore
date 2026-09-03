from .specification import Specification


class NotSpecification(Specification):
    def __init__(self, spec: Specification) -> None:
        self.spec = spec

    def is_satisfied_by(self, candidate) -> bool:
        return not self.spec.is_satisfied_by(candidate)
