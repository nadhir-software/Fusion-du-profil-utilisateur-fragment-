"""FragmentBuilder — construction d'un HuggingFace Dataset par fragment.

Transforme les textes prétraités en un ``datasets.Dataset`` tokenisé,
étiqueté par ``fragment_id`` et ``signal_type``. Dépendances (datasets,
transformers) importées paresseusement.
"""

from __future__ import annotations

from typing import Any

from maha_these.core.data_models import Fragment


class FragmentBuilder:
    """Construit un Dataset local pour un fragment donné."""

    def __init__(self, fragment_id: str, signal_type: str) -> None:
        self.fragment_id = fragment_id
        self.signal_type = signal_type

    def build(self, texts: list[str], user_hash: str) -> tuple[Any, Fragment]:
        """Construit le Dataset HuggingFace et sa métadonnée Fragment.

        Returns:
            (dataset, fragment_meta). ``dataset`` est un ``datasets.Dataset``.
        """
        try:
            from datasets import Dataset  # import paresseux
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "La librairie `datasets` est requise pour FragmentBuilder. "
                "Installez la pile IA : pip install -r requirements-ai.txt"
            ) from exc

        records = [
            {
                "text": t,
                "fragment_id": self.fragment_id,
                "signal_type": self.signal_type,
            }
            for t in texts
        ]
        dataset = Dataset.from_list(records)
        meta = Fragment(
            fragment_id=self.fragment_id,
            signal_type=self.signal_type,  # type: ignore[arg-type]
            user_hash=user_hash,
            n_samples=len(records),
        )
        return dataset, meta
