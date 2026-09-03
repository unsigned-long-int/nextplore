from .specification import Specification


class AlwaysTrueSpec(Specification):
    def is_satisfied_by(self, candidate) -> bool:
        return True
