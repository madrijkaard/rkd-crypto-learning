import ccxt
import time


class BinanceClient:

    def __init__(self, use_futures: bool = False):
        self.use_futures = use_futures
        self.exchange = self._create_exchange()

    def _create_exchange(self):

        if self.use_futures:
            exchange = ccxt.binance({
                "enableRateLimit": True,
                "options": {"defaultType": "future"}
            })
        else:
            exchange = ccxt.binance({
                "enableRateLimit": True
            })

        return exchange

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 1000):
        
        try:
            data = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit
            )

            time.sleep(self.exchange.rateLimit / 1000)

            return data

        except Exception as e:
            raise RuntimeError(f"Erro ao buscar OHLCV para {symbol}: {str(e)}")