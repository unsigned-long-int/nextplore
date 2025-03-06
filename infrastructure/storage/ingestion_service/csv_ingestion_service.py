import pandas as pd

from pathlib import Path
from dataclasses import dataclass


@dataclass
class CSVIngestionService:
    csv_path: Path

    def ingest_vectors(self, vectors: pd.DataFrame) -> None:
        vectors.to_csv(self.csv_path, index=False)
