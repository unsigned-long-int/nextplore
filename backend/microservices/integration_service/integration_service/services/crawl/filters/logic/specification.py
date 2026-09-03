from abc import ABC, abstractmethod


class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidate) -> bool:
        raise NotImplementedError

    def __and__(self, other: "Specification") -> "Specification":
        from .and_specification import AndSpecification

        return AndSpecification(self, other)

    def __or__(self, other: "Specification") -> "Specification":
        from .or_specification import OrSpecification

        return OrSpecification(self, other)

    def __invert__(self) -> "Specification":
        from .not_specification import NotSpecification

        return NotSpecification(self)
