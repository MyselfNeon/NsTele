# plugins/keep_alive.py
import asyncio
import logging
import aiohttp
import os

KEEP_ALIVE_URL = os.environ.get("KEEP_ALIVE_URL", "https://nstele.onrender.com/")

async def keep_alive():
    """Send a request every 300 seconds to keep the bot alive (if required)."""
    if not KEEP_ALIVE_URL:
        logging.warning("KEEP_ALIVE_URL not set — skipping keep-alive task.")
        return

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(KEEP_ALIVE_URL) as resp:
                    if resp.status == 200:
                        logging.info("✅ Keep-alive ping successful.")
                    else:
                        logging.warning(f"⚠️ Keep-alive returned status {resp.status}")
            except Exception as e:
                logging.error(f"❌ Keep-alive request failed: {e}")
            await asyncio.sleep(300)


def start(loop=None):
    """Start the keep-alive task."""
    if KEEP_ALIVE_URL:
        loop = loop or asyncio.get_event_loop()
        loop.create_task(keep_alive())
        logging.info("🌐 Keep-alive task started.")
