import h5py
import ast
import pandas as pd

from dataclasses import dataclass
from pathlib import Path


@dataclass
class HDF5RetrievalService:
    hdf5_path: Path

    def retrieve_vectors(self) -> pd.DataFrame:
        with h5py.File(self.hdf5_path, 'r') as h5f:
            data = h5f['table_meta'][:]
            columns = h5f.attrs['columns'].split(',')
        vector_matrix = pd.DataFrame(data, columns=columns)
        vector_matrix['embedding'] = vector_matrix['embedding'].apply(
            ast.literal_eval
        )
        return vector_matrix
