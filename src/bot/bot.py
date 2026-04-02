from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from bot.router import router
from bot.commands import COMMANDS

# ---------------------------------------------------------------------------
# Aiogram bot
# ---------------------------------------------------------------------------

bot_instance: Bot = Bot(BOT_TOKEN)
dispatcher_instance: Dispatcher = Dispatcher()
dispatcher_instance.include_router(router)

async def run_bot():
    await bot_instance.set_my_commands(COMMANDS)
    await dispatcher_instance.start_polling(bot_instance)