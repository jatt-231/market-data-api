import asyncio
import os
import csv
from dotenv import load_dotenv
from pyquotex.stable_api import Quotex

load_dotenv()

email = os.getenv("QUOTEX_EMAIL")
password = os.getenv("QUOTEX_PASSWORD")

SYMBOL = "USDBDT_otc"
TOTAL_CANDLES = 100000   # 1 lakh candles
PERIOD = 60              # M1 (1 minute)

def progress(current, total, percent, message):
    print(f"Progress: {percent}% ({current}/{total}) - {message}")

async def main():
    client = Quotex(email=email, password=password, lang="en")

    print("Connecting to Quotex...")
    connected, reason = await client.connect()

    if not connected:
        print(f"❌ Connection failed: {reason}")
        return

    print("✅ Connected!")
    await client.change_account("PRACTICE")

    amount_of_seconds = TOTAL_CANDLES * PERIOD

    print(f"Fetching {TOTAL_CANDLES} candles for {SYMBOL}... (ye time lega, sabar karein)")

    candles = await client.get_historical_candles(
        SYMBOL,
        amount_of_seconds=amount_of_seconds,
        period=PERIOD,
        max_workers=5,
        progress_callback=progress
    )

    print(f"✅ Total candles received: {len(candles)}")

    # CSV file mein save karo
    filename = f"{SYMBOL}_M1_history.csv"
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["symbol", "timeframe", "timestamp", "open", "high", "low", "close"])
        for c in candles:
            writer.writerow([
                SYMBOL,
                "M1",
                c.get("time"),
                c.get("open"),
                c.get("high"),
                c.get("low"),
                c.get("close")
            ])

    print(f"✅ Data saved to {filename}")

    await client.close()

asyncio.run(main())