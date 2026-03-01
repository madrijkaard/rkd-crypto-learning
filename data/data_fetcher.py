import pandas as pd
from typing import Dict, List

from config import USE_FUTURES
from data.binance_client import BinanceClient


class DataFetcher:

    def __init__(self):
        self.client = BinanceClient(use_futures=USE_FUTURES)

    def fetch_symbol(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> pd.DataFrame:

        raw = self.client.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )

        df = pd.DataFrame(
            raw,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        )

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["symbol"] = symbol
        df = df.sort_values("timestamp").reset_index(drop=True)

        return df

    def fetch_multiple(
        self,
        symbols: List[str],
        timeframe: str,
        limit: int,
    ) -> Dict[str, pd.DataFrame]:

        market_data = {}

        for symbol in symbols:
            df = self.fetch_symbol(symbol, timeframe, limit)
            print(f"Baixando {symbol}... [{len(df)} candles]")
            market_data[symbol] = df

        market_data = self._align_dataframes(market_data)

        return market_data

    def _align_dataframes(
        self,
        market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:

        print("Alinhando timestamps com BTC...")

        base_symbol = "BTC/USDT"
        if base_symbol not in market_data:
            raise ValueError(f"{base_symbol} não encontrado nos dados.")

        btc_ts = set(market_data[base_symbol]["timestamp"])
        aligned_data = {base_symbol: market_data[base_symbol]}

        for symbol, df in market_data.items():
            if symbol == base_symbol:
                continue

            common_ts = btc_ts.intersection(df["timestamp"])
            if len(common_ts) < 50:
                print(f"Ignorando {symbol} (timestamps insuficientes: {len(common_ts)})")
                continue

            df_aligned = df[df["timestamp"].isin(common_ts)].sort_values("timestamp").reset_index(drop=True)
            aligned_data[symbol] = df_aligned
            print(f"{symbol} alinhado [{len(df_aligned)} candles]")

        print(f"Total de símbolos após alinhamento: {len(aligned_data)}")

        return aligned_data