import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile, Message
from aiogram.filters import CommandStart, Command
from config import BOT_TOKEN
from gemini import parse_receipt
from excel import save_to_excel

from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

app.run(host="0.0.0.0", port=10000)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Отправь фото чека")

@dp.message(Command("help"))
async def start(message: Message):
  await message.answer("бог поможе")

@dp.message(Command("download"))
async def start(message: Message):
    file = FSInputFile("receipts.xlsx")
    await message.answer_document(file)


@dp.message(lambda message: message.photo)
async def handle_photo(message: Message):
    photo = message.photo[-1]

    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)

    image_bytes = file_bytes.read()

    await message.answer("Обрабатываю чек...")

    try:
        result = parse_receipt(image_bytes)
        save_to_excel(result)

        await message.answer("✅ Чек сохранён")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())