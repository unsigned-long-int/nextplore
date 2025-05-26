import h5py
import pandas as pd

from pathlib import Path
from dataclasses import dataclass


@dataclass
class HDF5IngestionService:
    hdf5_path: Path

    def ingest_vectors(self, vectors: pd.DataFrame) -> None:
        with h5py.File(self.hdf5_path, 'w') as h5f:
            h5f.create_dataset('table_meta', data=vectors.values)
            h5f.attrs['columns'] = ','.join(vectors.columns)
