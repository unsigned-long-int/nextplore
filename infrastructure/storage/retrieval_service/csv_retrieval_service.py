import ast
import pandas as pd

from dataclasses import dataclass
from pathlib import Path


@dataclass
class CSVRetrievalService:
    csv_path: Path

    def retrieve_vectors(self) -> pd.DataFrame:
        vector_matrix = pd.read_csv(self.csv_path)
        vector_matrix['embedding'] = vector_matrix['embedding'].apply(
            ast.literal_eval
        )

        return vector_matrix
