import os
import csv
import asyncio
import time
from fastapi import FastAPI, Header, HTTPException
from dotenv import load_dotenv
from providers.quotex_provider import QuotexProvider
from logger_setup import logger

load_dotenv()

API_KEY = os.getenv("API_KEY")
CACHE_SYMBOL = "USDBDT_otc"
CACHE_REFRESH_SECONDS = 10
WATCHDOG_INTERVAL_SECONDS = 15

app = FastAPI(title="Hacker Gen Market Data API", version="0.1.0")

quotex_provider = QuotexProvider()

candle_cache = {
    "data": None,
    "last_updated": None
}

watchdog_status = {
    "last_check": None,
    "last_healthy": None,
    "consecutive_failures": 0
}


def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


async def background_cache_updater():
    while True:
        try:
            result = await quotex_provider.get_latest_candles(CACHE_SYMBOL, 60)
            if isinstance(result, list):
                candle_cache["data"] = result
                candle_cache["last_updated"] = time.time()
            else:
                logger.warning("Background cache update failed")
        except Exception as e:
            logger.error("Background cache updater exception: " + str(e))
        await asyncio.sleep(CACHE_REFRESH_SECONDS)


async def connection_watchdog():
    """
    Dedicated health watchdog. Data fetching se alag.
    Sirf connection health check karta hai aur zaroorat par reconnect trigger karta hai.
    """
    while True:
        watchdog_status["last_check"] = time.time()
        try:
            status = await quotex_provider.get_provider_status()
            if status == "HEALTHY":
                watchdog_status["last_healthy"] = time.time()
                watchdog_status["consecutive_failures"] = 0
            else:
                watchdog_status["consecutive_failures"] += 1
                logger.warning("Watchdog: provider unhealthy (failure #" + str(watchdog_status["consecutive_failures"]) + "). Triggering reconnect...")
                connected, reason = await quotex_provider.connect()
                if connected:
                    logger.info("Watchdog: reconnect successful")
                else:
                    logger.error("Watchdog: reconnect failed: " + str(reason))
        except Exception as e:
            watchdog_status["consecutive_failures"] += 1
            logger.error("Watchdog exception: " + str(e))

        await asyncio.sleep(WATCHDOG_INTERVAL_SECONDS)


@app.get("/")
def read_root():
    return {"message": "Hacker Gen Market Data API is running!"}


@app.get("/health")
async def health_check():
    status = await quotex_provider.get_provider_status()
    return {"api_status": "HEALTHY", "quotex_provider_status": status}


@app.get("/status")
async def get_status(x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    provider_status = await quotex_provider.get_provider_status()
    cache_age = None
    if candle_cache["last_updated"]:
        cache_age = round(time.time() - candle_cache["last_updated"], 1)

    watchdog_last_healthy_ago = None
    if watchdog_status["last_healthy"]:
        watchdog_last_healthy_ago = round(time.time() - watchdog_status["last_healthy"], 1)

    return {
        "api": "RUNNING",
        "quotex_provider": provider_status,
        "connected": quotex_provider.connected,
        "cache_age_seconds": cache_age,
        "watchdog": {
            "last_healthy_seconds_ago": watchdog_last_healthy_ago,
            "consecutive_failures": watchdog_status["consecutive_failures"]
        }
    }


@app.get("/pairs")
async def get_pairs(x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    result = await quotex_provider.get_available_pairs()
    if isinstance(result, dict) and result.get("error"):
        return {"status": "ERROR", "message": result.get("message")}
    return {"status": "OK", "count": len(result), "pairs": result}


@app.get("/candles")
async def get_candles(symbol: str = "USDBDT_otc", count: int = 60, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    logger.info("Candles requested: symbol=" + symbol + " count=" + str(count))

    if symbol == CACHE_SYMBOL and candle_cache["data"] is not None:
        cached = candle_cache["data"][-count:]
        return {
            "status": "OK",
            "symbol": symbol,
            "count": len(cached),
            "source": "cache",
            "cache_age_seconds": round(time.time() - candle_cache["last_updated"], 1),
            "candles": cached
        }

    result = await quotex_provider.get_latest_candles(symbol, count)
    if isinstance(result, dict) and result.get("error"):
        return {"status": "ERROR", "symbol": symbol, "message": result.get("message")}
    return {"status": "OK", "symbol": symbol, "count": len(result), "source": "live", "candles": result}


@app.get("/history")
async def get_history(symbol: str = "USDBDT_otc", limit: int = 500, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    filename = symbol + "_M1_history.csv"
    try:
        candles = []
        with open(filename, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                candles.append({
                    "symbol": row["symbol"],
                    "timeframe": row["timeframe"],
                    "timestamp": int(row["timestamp"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"])
                })
        limited_candles = candles[-limit:]
        return {
            "status": "OK",
            "symbol": symbol,
            "total_available": len(candles),
            "returned": len(limited_candles),
            "candles": limited_candles
        }
    except FileNotFoundError:
        logger.error("History file not found for symbol " + symbol)
        return {"status": "ERROR", "message": "No historical data file found for symbol " + symbol}


@app.on_event("startup")
async def startup_event():
    logger.info("Hacker Gen Market Data API starting up...")
    connected, reason = await quotex_provider.connect()
    if not connected:
        logger.error("Startup connection failed: " + str(reason))

    asyncio.create_task(background_cache_updater())
    logger.info("Background cache updater started")

    asyncio.create_task(connection_watchdog())
    logger.info("Connection watchdog started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Hacker Gen Market Data API shutting down...")
    await quotex_provider.close()