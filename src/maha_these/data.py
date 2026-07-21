from pathlib import Path

import pandas as pd


def load_csv(path: str | Path, **kwargs) -> pd.DataFrame:
    """Load a CSV file with pandas."""
    return pd.read_csv(Path(path), **kwargs)


def save_csv(dataframe: pd.DataFrame, path: str | Path, **kwargs) -> None:
    """Save a DataFrame to CSV."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False, **kwargs)
