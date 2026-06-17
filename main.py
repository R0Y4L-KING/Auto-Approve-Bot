# MADE BY: @ModappsKing | t.me/ModappsKing
# Auto Approve Bot — Rebranded for MOD APPS KING

import logging
import os
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatJoinRequestHandler,
    CommandHandler,
    ContextTypes,
)

# ============================================================
# Bot Configuration — EDIT THESE BEFORE RUNNING
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

UPDATES_CHANNEL = "ModappsKing"
MORE_BOTS_CHANNEL = "ModappsKing"

START_TIME = time.time()

TOTAL_APPROVED = 0
TOTAL_ERRORS = 0

# ============================================================
# Logging Setup
# ============================================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("ModappsKing_AutoApprove")

# ============================================================
# Text Templates
# ============================================================

WELCOME_TEXT = """
<b>🤖 MOD APPS KING — Auto Approve Bot</b>

Hey <a href="tg://user?id={user_id}">{first_name}</a>! 👋

I automatically approve join requests for your groups and channels.

<b>📋 Setup Guide:</b>
1️⃣ Add this bot to your group or channel
2️⃣ Promote it as <b>Administrator</b>
3️⃣ Enable <b>Manage Join Requests</b> permission
4️⃣ Turn on join requests in your chat settings
5️⃣ Done! Requests will be approved instantly ✅

<b>⚡ Commands:</b>
/start — Main panel
/help — Setup guide
/status — Bot stats
/disclaimer — Usage notice
/about — Bot info

<b>📢 Channel:</b> @ModappsKing
"""

HELP_TEXT = """
<b>📖 Setup Help — MOD APPS KING Bot</b>

<b>For Groups:</b>
• Open group Settings → Administrators
• Add this bot → Enable <b>Add Members</b> or <b>Manage Invite Links</b>
• Go to group Info → Turn on <b>Join Requests</b>

<b>For Channels:</b>
• Open channel Settings → Administrators
• Add this bot with invite/subscriber management rights
• Enable <b>Join Requests</b> from channel settings

<b>⚠️ Important:</b>
Bot must be admin or it cannot approve anything.

<b>Support & Updates:</b> @ModappsKing
"""

DISCLAIMER_TEXT = """
<b>⚠️ Disclaimer — MOD APPS KING Auto Approve Bot</b>

This bot auto-approves Telegram join requests using admin permissions you provide.

<b>Admin Responsibility:</b>
Group/channel owners are fully responsible for member access, content, moderation, and safety.

<b>No Verification:</b>
The bot does not verify user identity, intent, spam risk, or behavior before approving.

<b>No Moderation:</b>
The bot does not monitor, filter, or control messages or media inside your chat.

<b>Privacy:</b>
Only Telegram join request data is processed — no extra data is stored.

Use this bot only for chats where open access is acceptable.

<b>📢 @ModappsKing</b>
"""

ABOUT_TEXT = """
<b>ℹ️ About This Bot</b>

<b>Name:</b> MOD APPS KING Auto Approve Bot
<b>Purpose:</b> Auto-approves group & channel join requests
<b>Mode:</b> Admin-based automation
<b>Database:</b> None (lightweight)
<b>Privacy:</b> No user tracking

<b>Made for:</b> @ModappsKing
<b>Channel:</b> t.me/ModappsKing

<i>Share with friends who run Telegram channels! 🚀</i>
"""

# ============================================================
# Utility Functions
# ============================================================

def uptime_text() -> str:
    seconds = int(time.time() - START_TIME)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def now_text() -> str:
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def is_private(update: Update) -> bool:
    return bool(update.effective_chat and update.effective_chat.type == "private")


def safe_name(user) -> str:
    if not user:
        return "User"
    return user.first_name or user.username or "User"


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Add to Group",
                    url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
                ),
                InlineKeyboardButton(
                    "📢 Add to Channel",
                    url=f"https://t.me/{BOT_USERNAME}?startchannel=true",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📲 Updates Channel",
                    url=f"https://t.me/{UPDATES_CHANNEL}",
                ),
                InlineKeyboardButton(
                    "🎮 More Mods",
                    url=f"https://t.me/{MORE_BOTS_CHANNEL}",
                ),
            ],
            [
                InlineKeyboardButton("📖 Help", callback_data="panel_help"),
                InlineKeyboardButton("⚠️ Disclaimer", callback_data="panel_disclaimer"),
            ],
            [
                InlineKeyboardButton("ℹ️ About", callback_data="panel_about"),
                InlineKeyboardButton("📊 Status", callback_data="panel_status"),
            ],
        ]
    )


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data="panel_home")]]
    )


def approval_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎮 MOD APPS KING",
                    url="https://t.me/ModappsKing",
                )
            ]
        ]
    )


def status_text() -> str:
    return f"""
<b>📊 Bot Status — MOD APPS KING</b>

<b>Status:</b> ✅ Running
<b>Uptime:</b> {uptime_text()}
<b>Total Approved:</b> {TOTAL_APPROVED}
<b>Total Errors:</b> {TOTAL_ERRORS}
<b>Checked At:</b> {now_text()}

<b>Channel:</b> @ModappsKing
"""


async def notify_owner(context: ContextTypes.DEFAULT_TYPE, text: str):
    if not OWNER_ID:
        return
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except TelegramError:
        pass

# ============================================================
# Command Handlers
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = safe_name(user)
    text = WELCOME_TEXT.format(user_id=user.id, first_name=first_name)
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(),
        disable_web_page_preview=True,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=HELP_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard(),
        disable_web_page_preview=True,
    )


async def disclaimer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=DISCLAIMER_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard(),
        disable_web_page_preview=True,
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=ABOUT_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard(),
        disable_web_page_preview=True,
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=status_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard(),
        disable_web_page_preview=True,
    )

# ============================================================
# Callback Handler
# ============================================================

async def panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user
    first_name = safe_name(user)

    if data == "panel_home":
        text = WELCOME_TEXT.format(user_id=user.id, first_name=first_name)
        keyboard = main_keyboard()
    elif data == "panel_help":
        text = HELP_TEXT
        keyboard = back_keyboard()
    elif data == "panel_disclaimer":
        text = DISCLAIMER_TEXT
        keyboard = back_keyboard()
    elif data == "panel_about":
        text = ABOUT_TEXT
        keyboard = back_keyboard()
    elif data == "panel_status":
        text = status_text()
        keyboard = back_keyboard()
    else:
        text = "Unknown option."
        keyboard = back_keyboard()

    try:
        await query.message.edit_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    except BadRequest:
        await query.message.reply_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

# ============================================================
# Join Request Handler
# ============================================================

async def approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_APPROVED
    global TOTAL_ERRORS

    request = update.chat_join_request
    if not request:
        return

    chat = request.chat
    user = request.from_user

    try:
        await context.bot.approve_chat_join_request(
            chat_id=chat.id,
            user_id=user.id,
        )
        TOTAL_APPROVED += 1
        logger.info("✅ Approved user %s in chat %s", user.id, chat.id)

    except Forbidden:
        TOTAL_ERRORS += 1
        logger.warning("❌ Missing permission in chat %s", chat.id)
        return
    except BadRequest as error:
        TOTAL_ERRORS += 1
        logger.warning("❌ Bad request: %s", error)
        return
    except TelegramError as error:
        TOTAL_ERRORS += 1
        logger.error("❌ Telegram error: %s", error)
        return

    user_name = safe_name(user)
    approved_text = f"""
👋 Hey <a href="tg://user?id={user.id}">{user_name}</a>!

✅ Your request to join <b>{chat.title}</b> has been <b>approved</b>!

Enjoy the chat. Check out more mods 👇
"""

    target_chat = chat.id if chat.type in ("group", "supergroup") else user.id

    try:
        await context.bot.send_message(
            chat_id=target_chat,
            text=approved_text,
            parse_mode=ParseMode.HTML,
            reply_markup=approval_keyboard(),
            disable_web_page_preview=True,
        )
    except (Forbidden, BadRequest, TelegramError):
        pass

# ============================================================
# Error Handler
# ============================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_ERRORS
    TOTAL_ERRORS += 1
    logger.error("Unhandled exception", exc_info=context.error)

# ============================================================
# Startup Validation
# ============================================================

def validate_config():
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN env var missing!")
    if not BOT_USERNAME:
        raise RuntimeError("❌ BOT_USERNAME env var missing!")
    if BOT_USERNAME.startswith("@"):
        raise RuntimeError("❌ BOT_USERNAME must be without the @ symbol.")
    if OWNER_ID == 0:
        raise RuntimeError("❌ OWNER_ID env var missing!")

# ============================================================
# App Builder
# ============================================================

def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("disclaimer", disclaimer_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CallbackQueryHandler(panel_callback, pattern="^panel_"))
    app.add_handler(ChatJoinRequestHandler(approve_join_request))
    app.add_error_handler(error_handler)
    return app

# ============================================================
# Main Runner
# ============================================================

# ============================================================
# Dummy Web Server (required for Render free tier)
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MOD APPS KING Bot is running!")

    def log_message(self, format, *args):
        pass  # Suppress HTTP logs


def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("🌐 Web server running on port %s", port)
    server.serve_forever()


# ============================================================
# Main Runner
# ============================================================

def main():
    validate_config()
    app = build_app()

    logger.info("🚀 MOD APPS KING Auto Approve Bot started!")
    logger.info("📢 Channel: t.me/ModappsKing")
    logger.info("👤 Bot: @%s", BOT_USERNAME)

    # Start web server in background thread (Render requirement)
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Run bot (main thread)
    app.run_polling(
        allowed_updates=["message", "callback_query", "chat_join_request"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
