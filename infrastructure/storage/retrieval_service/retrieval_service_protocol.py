import pandas as pd

from typing import Protocol, runtime_checkable


@runtime_checkable
class RetrievalServiceProtocol(Protocol):
    def retrieve_vectors(self) -> pd.DataFrame:
        pass
