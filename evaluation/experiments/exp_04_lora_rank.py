"""EXP-04 — Ablation du rang LoRA r ∈ {4, 8, 16, 32}.

Étudie le compromis qualité/coût en faisant varier le rang LoRA et en
mesurant précision, cohérence sémantique et volume des Δθ.
"""

from __future__ import annotations

from typing import Any

from evaluation.mlflow_tracker import MLflowTracker


class Exp04LoraRank:
    """Runner de l'expérience EXP-04."""

    LORA_RANKS = (4, 8, 16, 32)

    def __init__(self, data: Any, tracker: MLflowTracker | None = None) -> None:
        self.data = data
        self.tracker = tracker or MLflowTracker()

    def run(self) -> dict[int, dict[str, float]]:
        # TODO(Phase 3): entraîner par rang LoRA et mesurer qualité + volume Δθ.
        raise NotImplementedError("EXP-04 à brancher (Phase 3).")
