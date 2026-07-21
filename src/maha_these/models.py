from dataclasses import dataclass

import joblib


@dataclass
class ModelArtifact:
    model: object
    name: str = "model"

    def save(self, path: str) -> None:
        joblib.dump(self.model, path)


def load_model(path: str) -> object:
    return joblib.load(path)
