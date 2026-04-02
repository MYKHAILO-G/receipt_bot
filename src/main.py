import asyncio
import logging
import threading

import bot
import web

async def main():
    # Start Flask in a background daemon thread
    threading.Thread(target=web.run, daemon=True).start()
    logging.info("Flask server started on port 10000")

    # Start aiogram polling (runs forever)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())