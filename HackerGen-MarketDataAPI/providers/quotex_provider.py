import os
from dotenv import load_dotenv
from pyquotex.stable_api import Quotex
from providers.base_provider import BaseProvider
from logger_setup import logger

load_dotenv()


class QuotexProvider(BaseProvider):
    def __init__(self):
        self.email = os.getenv("QUOTEX_EMAIL")
        self.password = os.getenv("QUOTEX_PASSWORD")
        self.client = Quotex(email=self.email, password=self.password, lang="en")
        self.connected = False

    async def connect(self):
        try:
            connected, reason = await self.client.connect()
            self.connected = connected
            if connected:
                await self.client.change_account("PRACTICE")
                logger.info("Quotex provider connected successfully")
            else:
                logger.error("Quotex provider connection failed: " + str(reason))
            return connected, reason
        except Exception as e:
            self.connected = False
            logger.error("Exception during connect(): " + str(e))
            return False, str(e)

    async def ensure_connected(self):
        try:
            is_alive = await self.client.check_connect()
        except Exception:
            is_alive = False

        if not is_alive or not self.connected:
            logger.warning("Connection lost or not established. Attempting to reconnect...")
            connected, reason = await self.connect()
            if not connected:
                logger.error("Reconnect attempt failed: " + str(reason))
                return False, reason
            logger.info("Reconnect successful")
            return True, None

        return True, None

    async def get_latest_candles(self, symbol: str, count: int = 60, max_retries: int = 3):
        import asyncio
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                connected, reason = await self.ensure_connected()
                if not connected:
                    last_error = "Quotex not connected: " + str(reason)
                    logger.warning("Attempt " + str(attempt) + "/" + str(max_retries) + " failed: " + last_error)
                    await asyncio.sleep(attempt * 2)
                    continue

                candles = await self.client.get_historical_candles(
                    symbol,
                    amount_of_seconds=count * 60,
                    period=60
                )

                if not candles:
                    last_error = "No data returned for symbol '" + symbol + "'. Symbol may be invalid or market closed."
                    logger.warning("Attempt " + str(attempt) + "/" + str(max_retries) + ": " + last_error)
                    await asyncio.sleep(attempt * 2)
                    continue

                standardized = []
                skipped = 0

                for c in candles:
                    try:
                        open_price = float(c.get("open"))
                        high = float(c.get("high"))
                        low = float(c.get("low"))
                        close = float(c.get("close"))
                        timestamp = c.get("time")

                        if timestamp is None:
                            skipped += 1
                            continue
                        if high < low:
                            skipped += 1
                            continue
                        if high < open_price or high < close:
                            skipped += 1
                            continue
                        if low > open_price or low > close:
                            skipped += 1
                            continue

                        standardized.append({
                            "symbol": symbol,
                            "timeframe": "M1",
                            "timestamp": timestamp,
                            "open": open_price,
                            "high": high,
                            "low": low,
                            "close": close,
                            "source": "quotex"
                        })

                    except (ValueError, TypeError):
                        skipped += 1
                        continue

                if skipped > 0:
                    logger.warning("Validation skipped " + str(skipped) + " invalid candle(s) for " + symbol)

                return standardized

            except Exception as e:
                self.connected = False
                last_error = "Provider error: " + str(e)
                logger.error("Attempt " + str(attempt) + "/" + str(max_retries) + " exception: " + last_error)
                await asyncio.sleep(attempt * 2)
                continue

        logger.error("All " + str(max_retries) + " attempts failed for " + symbol)
        return {"error": True, "message": last_error}

    async def get_available_pairs(self):
        try:
            connected, reason = await self.ensure_connected()
            if not connected:
                return {"error": True, "message": "Quotex not connected: " + str(reason)}

            assets = self.client.get_all_asset_name()
            pairs = []
            for a in assets:
                pairs.append({"symbol": a[0], "display_name": a[1]})
            return pairs

        except Exception as e:
            logger.error("Provider error in get_available_pairs: " + str(e))
            return {"error": True, "message": "Provider error: " + str(e)}

    async def get_provider_status(self):
        try:
            is_alive = await self.client.check_connect()
        except Exception:
            is_alive = False

        if is_alive and self.connected:
            return "HEALTHY"
        return "OFFLINE"

    async def close(self):
        try:
            await self.client.close()
            logger.info("Quotex provider connection closed")
        except Exception as e:
            logger.error("Error while closing connection: " + str(e))