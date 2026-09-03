from .specification import Specification


class AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification) -> None:
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Specification) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(
            candidate
        )
