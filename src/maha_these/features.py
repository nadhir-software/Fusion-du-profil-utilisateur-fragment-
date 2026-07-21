import pandas as pd


def basic_feature_summary(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a compact feature summary for quick exploration."""
    return pd.DataFrame(
        {
            "dtype": dataframe.dtypes.astype(str),
            "missing_values": dataframe.isna().sum(),
            "missing_rate": dataframe.isna().mean(),
        }
    )
