import logging
import math

from aiogram import F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, CallbackQuery, FSInputFile, Message

from ai.gemini import parse_receipt
from bot.frontend import PAGE_SIZE, build_list_keyboard, build_receipt_keyboard, format_list_text, format_receipt_text, group_by_uuid
from bot.router import router
from data.database import db

logging.basicConfig(level=logging.INFO)

COMMANDS_PLAIN = {
    "start": "Start work",
    "help": "Help with commands",
    "download": "Download your data in .xlsx format",
    "list": "View all your reciept data"
}

COMMANDS = [BotCommand(command=key, description=val) for key, val in COMMANDS_PLAIN.items()]

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("The bot is running. Send me photos of your receipts, one at a time.")


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("To add receipt, just send me its photo.\n" \
    "List of available commands:\n" + "\n".join(f"/{key} — {val}" for key, val in COMMANDS_PLAIN.items()))

@router.message(Command("download"))
async def cmd_download(message: Message):
    path = db.get_xlsx_path(message.from_user.id)
    if path is None:
        await message.answer("You don't have any receipts yet.")
        return
    await message.answer_document(FSInputFile(path))
 
@router.message(Command("list"))
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
 
 
@router.callback_query(F.data.startswith("page:"))
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
 
 
@router.callback_query(F.data.startswith("receipt:"))
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
 

@router.message(lambda message: message.photo)
async def handle_photo(message: Message, bot: Bot):
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
