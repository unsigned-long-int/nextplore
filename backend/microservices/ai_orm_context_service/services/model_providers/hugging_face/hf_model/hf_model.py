from dataclasses import dataclass


@dataclass(frozen=True)
class HFModel:
    model_id: str
    hf_path: str
    max_tokens: int
