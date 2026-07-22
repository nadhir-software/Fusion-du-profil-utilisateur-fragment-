"""MLflowTracker — logging des expériences scientifiques.

Fine façade autour de MLflow pour uniformiser le logging des campagnes
EXP-01..05. MLflow importé paresseusement.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


class MLflowTracker:
    """Wrapper minimal pour le tracking MLflow."""

    def __init__(
        self,
        tracking_uri: str = "./mlruns",
        experiment_name: str = "federated_profiling",
    ) -> None:
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self._mlflow = None

    @property
    def mlflow(self):
        if self._mlflow is None:
            import mlflow  # import paresseux

            mlflow.set_tracking_uri(self.tracking_uri)
            mlflow.set_experiment(self.experiment_name)
            self._mlflow = mlflow
        return self._mlflow

    @contextmanager
    def run(self, run_name: str) -> Iterator[Any]:
        """Contexte de run MLflow."""
        with self.mlflow.start_run(run_name=run_name) as active:
            yield active

    def log_params(self, params: dict[str, Any]) -> None:
        self.mlflow.log_params(params)

    def log_metrics(self, metrics: dict[str, float]) -> None:
        self.mlflow.log_metrics(metrics)
