from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

PAGE_SIZE = 5


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