import numpy as np
import pandas as pd


class FeatureEngineer:

    def __init__(self, base_symbol: str):
        self.base_symbol = base_symbol

    def build_feature_matrix(self, data_dict: dict) -> pd.DataFrame:

        if self.base_symbol not in data_dict:
            raise ValueError(f"{self.base_symbol} não encontrado nos dados.")

        btc_df = self._prepare_dataframe(data_dict[self.base_symbol])

        features = []

        for symbol, df in data_dict.items():
            if symbol == self.base_symbol:
                continue

            alt_df = self._prepare_dataframe(df)
            merged = self._align_dataframes(alt_df, btc_df)

            if merged.empty or len(merged) < 50:
                continue

            symbol_features = self._compute_features(merged, symbol)
            features.append(symbol_features)

        if not features:
            raise ValueError("Nenhuma feature foi gerada.")

        return pd.DataFrame(features).set_index("symbol")

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:

        df = df.copy()
        if "timestamp" not in df.columns or "close" not in df.columns:
            raise ValueError("DataFrame precisa conter 'timestamp' e 'close'.")

        df = df.sort_values("timestamp")
        df["return"] = df["close"].pct_change()
        df = df.dropna()
        return df

    def _align_dataframes(self, alt_df: pd.DataFrame, btc_df: pd.DataFrame) -> pd.DataFrame:

        merged = pd.merge(
            alt_df,
            btc_df,
            on="timestamp",
            suffixes=("_alt", "_btc"),
            how="inner"
        )

        merged = merged.dropna()
        return merged

    def _compute_features(self, df: pd.DataFrame, symbol: str) -> dict:

        df = df.copy()
        df["date"] = df["timestamp"].dt.date

        daily_vol_abs = df.groupby("date")["return_alt"].std().dropna().mean()
        daily_vol_abs = 0 if np.isnan(daily_vol_abs) else daily_vol_abs

        correlation = df["return_alt"].corr(df["return_btc"])
        correlation = 0 if np.isnan(correlation) else correlation

        return {
            "symbol": symbol,
            "vol_abs": float(daily_vol_abs),
            "correlation_btc": float(correlation),
        }