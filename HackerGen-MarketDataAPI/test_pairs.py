import asyncio
import os
from dotenv import load_dotenv
from pyquotex.stable_api import Quotex

load_dotenv()

email = os.getenv("QUOTEX_EMAIL")
password = os.getenv("QUOTEX_PASSWORD")

async def main():
    client = Quotex(email=email, password=password, lang="en")
    connected, reason = await client.connect()

    if connected:
        print("✅ Connected!")
        await client.change_account("PRACTICE")

        assets = client.get_all_asset_name()
        print("Sample assets:")
        print(assets[:10])  # Sirf pehli 10 dikhao
        print(f"\nTotal assets: {len(assets)}")
    else:
        print(f"❌ Failed: {reason}")

    await client.close()

asyncio.run(main())