import asyncio
import os
from dotenv import load_dotenv
from pyquotex.stable_api import Quotex

# .env file se email/password load karo
load_dotenv()

email = os.getenv("QUOTEX_EMAIL")
password = os.getenv("QUOTEX_PASSWORD")

async def main():
    client = Quotex(email=email, password=password, lang="en")

    print("Connecting to Quotex...")
    connected, reason = await client.connect()

    if connected:
        print("✅ Connected successfully!")

        # Demo account use karo (real account nahi)
        await client.change_account("PRACTICE")
        print("✅ Switched to DEMO/PRACTICE account")

        # Balance check karo
        balance = await client.get_balance()
        print(f"Demo balance: {balance}")

        # Thoda sa candle data mangwao
        candles = await client.get_historical_candles(
            "USDBDT_otc",
            amount_of_seconds=3600,   # 1 hour ka data
            period=60                 # M1 (1 minute) candles
        )
        print("Sample candles received:")
        print(candles[:3])  # Sirf pehli 3 candles dikhao

    else:
        print(f"❌ Connection failed: {reason}")

    await client.close()

asyncio.run(main())