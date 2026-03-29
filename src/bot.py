import asyncio
import logging
import threading

import math

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand, FSInputFile
from aiogram.filters import CommandStart, Command

from flask import Flask, jsonify

from config import BOT_TOKEN
from gemini import parse_receipt
from database import Database

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Flask app (health check / web server)
# ---------------------------------------------------------------------------
flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return "OK"


@flask_app.route("/health")
def health():
    return jsonify({
        "schemaVersion": 1,
        "label": "bot",
        "message": "online",
        "color": "brightgreen"
    })


def run_flask():
    """Run Flask in a background daemon thread so it doesn't block the bot."""
    flask_app.run(host="0.0.0.0", port=10000)


# ---------------------------------------------------------------------------
# Aiogram bot
# ---------------------------------------------------------------------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

PAGE_SIZE = 5

COMMANDS_PLAIN = {
    "start": "Start work",
    "help": "Help with commands",
    "download": "Download your data in .xlsx format",
    "list": "View all your reciept data"
}

COMMANDS = [BotCommand(command=key, description=val) for key, val in COMMANDS_PLAIN.items()]

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("The bot is running. Send me photos of your receipts, one at a time.")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("To add receipt, just send me its photo.\n" \
    "List of available commands:\n" + "\n".join(f"/{key} — {val}" for key, val in COMMANDS_PLAIN.items()))

@dp.message(Command("download"))
async def cmd_download(message: Message):
    path = db.get_xlsx_path(message.from_user.id)
    if path is None:
        await message.answer("You don't have any receipts yet.")
        return
    await message.answer_document(FSInputFile(path))

# @dp.message(Command("list"))
# async def cmd_view(message: Message):
#     rows = db.get_receipts(message.from_user.id)
#     if not rows:
#         await message.answer("You don't have any receipts yet.")
#         return

#     text = "\n".join(
#         f"🧾 {r['Date']} | {r['Store']}\n  {r['Item']} — {r['Price']} грн"
#         for r in rows
#     )
#     # Split into chunks of 4096 chars if needed
#     for chunk in [text[i:i+4096] for i in range(0, len(text), 4096)]:
#         await message.answer(chunk)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def group_by_uuid(rows: list[dict]) -> list[dict]:
    """Collapse flat rows into one receipt dict per UUID."""
    seen = {}
    order = []
    for row in rows:
        uid = row["UUID"]
        if uid not in seen:
            seen[uid] = {
                "uuid":  uid,
                "date":  row["Date"],
                "store": row["Store"],
                "items": [],
            }
            order.append(uid)
        seen[uid]["items"].append({"name": row["Item"], "price": row["Price"]})
    return [seen[uid] for uid in order]
 
 
def build_list_keyboard(page: int, total_pages: int, receipts: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
 
    # One button per receipt on this page
    start = page * PAGE_SIZE
    for i, r in enumerate(receipts, start=1):
        label = f"{start + i}) {r['store']}  {r['date']}"
        buttons.append([InlineKeyboardButton(
            text=label,
            callback_data=f"receipt:{r['uuid']}"
        )])
 
    # Pagination row
    nav = []
    nav.append(InlineKeyboardButton(text="⏮", callback_data=f"page:0"))
    nav.append(InlineKeyboardButton(text="◀", callback_data=f"page:{max(0, page - 1)}"))
 
    # Up to 5 page number buttons centred around current page
    total_shown = min(5, total_pages)
    start_p = max(0, min(page - total_shown // 2, total_pages - total_shown))
    for p in range(start_p, start_p + total_shown):
        label = f"[{p + 1}]" if p == page else str(p + 1)
        nav.append(InlineKeyboardButton(text=label, callback_data=f"page:{p}"))
 
    nav.append(InlineKeyboardButton(text="▶", callback_data=f"page:{min(total_pages - 1, page + 1)}"))
    nav.append(InlineKeyboardButton(text="⏭", callback_data=f"page:{total_pages - 1}"))
    buttons.append(nav)
 
    return InlineKeyboardMarkup(inline_keyboard=buttons)
 
 
def build_receipt_keyboard(page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀ Back to list", callback_data=f"page:{page}")
    ]])
 
 
def format_list_text(page: int, total_pages: int, all_receipts: list[dict]) -> str:
    total = len(all_receipts)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    return (
        f"📋 *Your receipts*\n"
        f"Page {page + 1} of {total_pages}  ({start + 1}–{end} of {total})\n\n"
        f"Select a receipt to view details:"
    )
 
 
def format_receipt_text(r: dict) -> str:
    lines = [f"🧾 *{r['store']}* — {r['date']}\n"]
    total = 0
    for item in r["items"]:
        lines.append(f"{str(item['price']).rjust(8)} | {item['name']}")
        total += item["price"]
    lines.append(f"\n💰 *Total: {total:.2f}*")
    return "\n".join(lines)
 
 
# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
 
@dp.message(Command("list"))
async def cmd_list(message: Message):
    rows = db.get_receipts(message.from_user.id)
    if not rows:
        await message.answer("You don't have any receipts yet.")
        return
 
    all_receipts = group_by_uuid(rows)
    total_pages = math.ceil(len(all_receipts) / PAGE_SIZE)
    page = 0
    page_receipts = all_receipts[page * PAGE_SIZE: page * PAGE_SIZE + PAGE_SIZE]
 
    await message.answer(
        format_list_text(page, total_pages, all_receipts),
        parse_mode="Markdown",
        reply_markup=build_list_keyboard(page, total_pages, page_receipts),
    )
 
 
@dp.callback_query(F.data.startswith("page:"))
async def cb_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
 
    rows = db.get_receipts(callback.from_user.id)
    if not rows:
        await callback.answer("No receipts found.")
        return
 
    all_receipts = group_by_uuid(rows)
    total_pages = math.ceil(len(all_receipts) / PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    page_receipts = all_receipts[page * PAGE_SIZE: page * PAGE_SIZE + PAGE_SIZE]
 
    await callback.message.edit_text(
        format_list_text(page, total_pages, all_receipts),
        parse_mode="Markdown",
        reply_markup=build_list_keyboard(page, total_pages, page_receipts),
    )
    await callback.answer()
 
 
@dp.callback_query(F.data.startswith("receipt:"))
async def cb_receipt(callback: CallbackQuery):
    target_uuid = callback.data.split(":", 1)[1]
 
    rows = db.get_receipts(callback.from_user.id)
    if not rows:
        await callback.answer("No receipts found.")
        return
 
    all_receipts = group_by_uuid(rows)
    receipt = next((r for r in all_receipts if r["uuid"] == target_uuid), None)
    if receipt is None:
        await callback.answer("Receipt not found.")
        return
 
    # Figure out which page this receipt lives on to wire up the Back button
    idx = next(i for i, r in enumerate(all_receipts) if r["uuid"] == target_uuid)
    page = idx // PAGE_SIZE
 
    await callback.message.edit_text(
        format_receipt_text(receipt),
        parse_mode="Markdown",
        reply_markup=build_receipt_keyboard(page),
    )
    await callback.answer()
 

@dp.message(lambda message: message.photo)
async def handle_photo(message: Message):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)
    image_bytes = file_bytes.read()

    await message.answer("Working on this receipt...")
    try:
        result = parse_receipt(image_bytes)
        db.save_receipt(message.from_user.id, result)
        await message.answer("✅ Saved")
    except Exception as e:
        logging.exception("Error processing receipt")
        await message.answer("❌ An error occured, try once more.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def main():
    # Start Flask in a background daemon thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("Flask server started on port 10000")

    # Start aiogram polling (runs forever)
    await bot.set_my_commands(COMMANDS)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())