import logging
import sys
import traceback
import time
import random
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# تنظیمات لاگینگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot_debug.log"),
    ],
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.DEBUG)

# توکن ربات
TOKEN = "7799600612:AAETLSphASwA8_OWHBAVe2B2aB7N6l5uB5E"

# پیام خوشامدگویی
WELCOME_MESSAGE = (
    "🎉 سلام {mention}! به گروه ما خوش اومدی! 🌈\n"
    "قوانین رو با /rules چک کن و حسابی خوش بگذرون! 😎"
)

# قوانین پیش‌فرض
RULES = (
    "📜 قوانین گروه ما:\n"
    "1️⃣ اسپم نکن، قربونت! 😜\n"
    "2️⃣ به همه احترام بذار. ❤\n"
    "3️⃣ لینک و کلمات بد؟ نههه! 🚫"
)

# پاسخ‌های بامزه
CHAT_RESPONSES = {
    r"(?i)سلام": [
        "سلااام! چطور می‌تونم روزتو قشنگ‌تر کنم؟ 😍",
        "سلام عشقم! گروه چه خبره؟ 🌟",
    ],
    r"(?i)خوب": [
        "اووو! خوبی؟ بگو چی تو سرته! 😎",
        "خوب که عالیه! حالا یه بازی کنیم؟ 🎲",
    ],
    r"(?i)خسته": [
        "ای وای، خسته شدی؟ بیا یه بازی کنیم سرحال شی! 😜",
        "خسته؟ 😴 یه کم گپ بزنیم حال بیاد! ☕",
    ],
    r"(?i)خواب": [
        "خواب؟ 😴 برو یه چرت بزن، من اینجام! 😜",
        "خواب میاد؟ بیا یه بحث باحال راه بندازیم! 🌙",
    ],
}

# ایده‌های بحث غیرتکراری
DISCUSSION_STARTERS = [
    "🎬 اگه قرار بود یه فیلم درباره گروهمون بسازن، اسمش چی بود؟ 😎",
    "🍕 آخرین غذایی که خوردی چی بود؟ تعریف کن ببینم! 😋",
    "🦁 اگه یه حیوون بودی، چی بودی و چرا؟ 🤔",
    "🚀 اگه یه ابرقدرت داشتی، چی دوست داشتی باشه؟ 😜",
    "🎶 یه آهنگ بگو که الان تو سرته! 🎧",
    "🏝 اگه می‌تونستی همین الان یه جا سفر کنی، کجا می‌رفتی؟ ✈",
    "😂 بامزه‌ترین خاطره‌ت تو این گروه چیه؟ بگو بخندیم! 😄",
    "🧙‍♂ اگه جادوگر بودی، چه جادویی رو گروه می‌کردی؟ 🪄",
    "🍫 شکلات یا چیپس؟ نظرت چیه؟ 😋",
    "🎮 آخرین بازی که کردی چی بود؟ حال دادی؟ 🕹",
]

# ذخیره داده‌ها
GAME_STATE = {}
WARNINGS = {}
GROUP_SETTINGS = {}
MESSAGE_COUNT = {}
LAST_MESSAGE_TIME = {}
FILTERED_WORDS = {}

async def check_group_only(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        if update.message.chat.type == "private":
            await update.message.reply_text("🚫 اوپس! این دستور فقط تو گروه کار می‌کنه! 😜")
            return False
        return True
    except Exception as e:
        logger.error(f"Error in check_group_only: {str(e)}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Start command from user {update.effective_user.id}")
        if update.message.chat.type != "private":
            await update.message.reply_text("🚫 این دستور فقط تو پی‌وی کار می‌کنه! 😜")
            return
        keyboard = [
            [InlineKeyboardButton("➕ اضافه کردن به گروه", url="t.me/YourBot?startgroup=true")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🌈 سلام! من ربات باحال گروهم! 😍\nمنو به گروهت اضافه کن تا کلی خوش بگذرونیم! 🚀",
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Error in start: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Help command from user {update.effective_user.id}")
        help_text = (
            "🎉 سلام! من اینجام که گروهتو بترکونم! 😎\n"
            "📜 دستورات من:\n"
            "🔹 /start - شروع ربات (فقط پی‌وی)\n"
            "🔹 /help - همین پیام خفن! 😜\n"
            "🔹 /games - بازی‌های باحال (گروه و پی‌وی) 🎲\n"
            "🔹 /panel - پنل مدیریت (فقط ادمین‌ها) ⚙\n"
            "🔹 /tag @username - صدا زدن یکی! 📣\n"
            "🔹 /rules - قوانین گروه 📜\n"
            "🔹 /stats - آمار گروه با جزئیات 📊\n"
            "🔹 /ban, /unban, /mute, /unmute - مدیریت کاربرا 👮\n"
            "🔹 /warn @username - اخطار دادن ⚠\n"
            "🔹 /clean - پاک کردن پیام‌ها 🗑\n"
            "🔹 /pin - پین کردن پیام 📌\n"
            "بیا حال کنیم! 😍"
        )
        await update.message.reply_text(help_text)
    except Exception as e:
        logger.error(f"Error in help_command: {str(e)}")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Rules command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        chat_id = update.effective_chat.id
        rules = GROUP_SETTINGS.get(chat_id, {}).get("rules", RULES)
        await update.message.reply_text(rules)
    except Exception as e:
        logger.error(f"Error in rules: {str(e)}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Stats command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        chat_id = update.effective_chat.id
        member_count = await update.effective_chat.get_member_count()
        msg_count = MESSAGE_COUNT.get(chat_id, {}).get("total", 0)
        users = MESSAGE_COUNT.get(chat_id, {}).get("users", {})
        active_users = len(users)
        top_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:3]
        top_users_text = "\n".join(
            [f"🏅 @{context.bot.get_chat(user_id).username or 'کاربر'}: {count} پیام"
             for user_id, count in top_users if context.bot.get_chat(user_id).username]
        ) if top_users else "هنوز کسی پیام نداده! 😴"
        stats_text = (
            f"📊 آمار خفن گروهمون! 🚀\n"
            f"👥 تعداد اعضا: {member_count} نفر\n"
            f"💬 کل پیام‌ها: {msg_count} تا\n"
            f"🌟 کاربران فعال: {active_users} نفر\n"
            f"🔥 فعال‌ترین اعضا:\n{top_users_text}\n"
            f"بیاین گروهو بترکونیم! 😎"
        )
        await update.message.reply_text(stats_text)
    except Exception as e:
        logger.error(f"Error in stats: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def tag_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Tag command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        if not context.args:
            await update.message.reply_text("❓ اوپس! یه @username بده دیگه! 😅")
            return
        username = context.args[0]
        await update.message.reply_text(f"📣 {username} کجایی؟ زود بیا! 🚨")
    except Exception as e:
        logger.error(f"Error in tag_user: {str(e)}")

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Games command from user {update.effective_user.id}")
        keyboard = [
            [
                InlineKeyboardButton("❌ دوز", callback_data="game_tictactoe"),
                InlineKeyboardButton("⁉ بیست سؤالی", callback_data="game_twenty_questions"),
            ],
            [
                InlineKeyboardButton("✊ سنگ‌کاغذ-قیچی", callback_data="game_rps"),
                InlineKeyboardButton("🔤 حدس کلمه", callback_data="game_word_guess"),
            ],
            [
                InlineKeyboardButton("➕ چالش ریاضی", callback_data="game_math"),
                InlineKeyboardButton("🧠 تست حافظه", callback_data="game_memory"),
            ],
            [
                InlineKeyboardButton("📖 داستان‌ساز", callback_data="game_story"),
                InlineKeyboardButton("📊 نظرسنجی", callback_data="game_poll"),
            ],
            [
                InlineKeyboardButton("😀 چالش ایموجی", callback_data="game_emoji"),
                InlineKeyboardButton("⚡ مسابقه سرعت", callback_data="game_speed"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🎮 وقت بازیه! 😍 یکی از اینا رو انتخاب کن! 👇",
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Error in games: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Panel command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        chat = update.effective_chat
        user = update.effective_user
        admins = await chat.get_administrators()
        if not any(admin.user.id == user.id for admin in admins):
            await update.message.reply_text("🚫 اوه اوه! فقط ادمین‌ها می‌تونن اینجا سرک بکشن! 😜")
            return
        keyboard = [
            [InlineKeyboardButton("👮 مدیریت کاربران", callback_data="manage_users")],
            [InlineKeyboardButton("⚙ تنظیمات گروه", callback_data="settings")],
            [InlineKeyboardButton("📊 آمار و پاکسازی", callback_data="stats_clean")],
            [InlineKeyboardButton("🚫 فیلتر کلمات", callback_data="word_filter")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🎛 پنل مدیریت! 😎 چی دوست داری تنظیم کنی؟", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in panel: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    logger.debug(f"Button callback: {query.data} from user {user_id}")
    try:
        if query.data == "manage_users":
            keyboard = [
                [
                    InlineKeyboardButton("🔴 بن", callback_data="ban"),
                    InlineKeyboardButton("🟢 آنبن", callback_data="unban"),
                ],
                [
                    InlineKeyboardButton("🔇 میوت", callback_data="mute"),
                    InlineKeyboardButton("🔊 آنمیوت", callback_data="unmute"),
                ],
                [InlineKeyboardButton("⚠ اخطار", callback_data="warn")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")],
            ]
            await query.message.edit_text(
                "👮 مدیریت کاربران! 😎 کیو قراره حالشو بگیریم؟ 😜",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "settings":
            antilink = GROUP_SETTINGS.get(chat_id, {}).get("antilink", False)
            word_filter = GROUP_SETTINGS.get(chat_id, {}).get("word_filter", False)
            keyboard = [
                [InlineKeyboardButton(f"🔗 ضد لینک {'✅' if antilink else '❌'}", callback_data="toggle_antilink")],
                [InlineKeyboardButton(f"🚫 فیلتر کلمات {'✅' if word_filter else '❌'}", callback_data="toggle_word_filter")],
                [InlineKeyboardButton("📝 تنظیم خوشامد", callback_data="set_welcome")],
                [InlineKeyboardButton("📜 تنظیم قوانین", callback_data="set_rules")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")],
            ]
            await query.message.edit_text(
                "⚙ تنظیمات گروه! 🛠 چی رو درست کنیم؟ 😄",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "stats_clean":
            keyboard = [
                [InlineKeyboardButton("📊 آمار گروه", callback_data="show_stats")],
                [InlineKeyboardButton("🗑 پاکسازی پیام", callback_data="clean_messages")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")],
            ]
            await query.message.edit_text(
                "📊 آمار و پاکسازی! 🚮 چی دوست داری؟ 😎",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "word_filter":
            word_filter = GROUP_SETTINGS.get(chat_id, {}).get("word_filter", False)
            keyboard = [
                [InlineKeyboardButton(f"🚫 فیلتر کلمات {'✅' if word_filter else '❌'}", callback_data="toggle_word_filter")],
                [InlineKeyboardButton("➕ اضافه کردن کلمه", callback_data="add_word")],
                [InlineKeyboardButton("📜 لیست کلمات", callback_data="list_words")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")],
            ]
            await query.message.edit_text(
                "🚫 تنظیمات فیلتر کلمات! 😎 چیکار کنیم؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "main_menu":
            keyboard = [
                [InlineKeyboardButton("👮 مدیریت کاربران", callback_data="manage_users")],
                [InlineKeyboardButton("⚙ تنظیمات گروه", callback_data="settings")],
                [InlineKeyboardButton("📊 آمار و پاکسازی", callback_data="stats_clean")],
                [InlineKeyboardButton("🚫 فیلتر کلمات", callback_data="word_filter")],
            ]
            await query.message.edit_text(
                "🎛 دوباره تو پنل مدیریت! 😘 حالا چی؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data in ["ban", "unban", "mute", "unmute", "warn"]:
            await query.message.edit_text(
                f"📝 اوکی! حالا اینو بزن:\n"
                f"/{query.data} @username یا روی پیامش ریپلای کن! 😄"
            )

        elif query.data == "toggle_antilink":
            GROUP_SETTINGS.setdefault(chat_id, {})["antilink"] = not GROUP_SETTINGS.get(chat_id, {}).get("antilink", False)
            antilink = GROUP_SETTINGS[chat_id]["antilink"]
            keyboard = [
                [InlineKeyboardButton(f"🔗 ضد لینک {'✅' if antilink else '❌'}", callback_data="toggle_antilink")],
                [InlineKeyboardButton(f"🚫 فیلتر کلمات {'✅' if GROUP_SETTINGS.get(chat_id, {}).get('word_filter', False) else '❌'}", callback_data="toggle_word_filter")],
                [InlineKeyboardButton("📝 تنظیم خوشامد", callback_data="set_welcome")],
                [InlineKeyboardButton("📜 تنظیم قوانین", callback_data="set_rules")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")],
            ]
            await query.message.edit_text(
                "⚙ تنظیمات گروه! 🛠 چی رو درست کنیم؟ 😄",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "toggle_word_filter":
            GROUP_SETTINGS.setdefault(chat_id, {})["word_filter"] = not GROUP_SETTINGS.get(chat_id, {}).get("word_filter", False)
            word_filter = GROUP_SETTINGS[chat_id]["word_filter"]
            keyboard = [
                [InlineKeyboardButton(f"🚫 فیلتر کلمات {'✅' if word_filter else '❌'}", callback_data="toggle_word_filter")],
                [InlineKeyboardButton("➕ اضافه کردن کلمه", callback_data="add_word")],
                [InlineKeyboardButton("📜 لیست کلمات", callback_data="list_words")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")],
            ]
            await query.message.edit_text(
                "🚫 تنظیمات فیلتر کلمات! 😎 چیکار کنیم؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "add_word":
            await query.message.edit_text(
                "📝 یه کلمه ممنوعه بنویس که فیلترش کنم! 😎"
            )
            context.user_data["setting"] = {"type": "add_word", "chat_id": chat_id}

        elif query.data == "list_words":
            words = FILTERED_WORDS.get(chat_id, [])
            if not words:
                await query.message.edit_text("📜 هنوز کلمه ممنوعه‌ای نداریم! 😜")
            else:
                await query.message.edit_text(f"📜 کلمات ممنوعه:\n{', '.join(words)}")

        elif query.data == "set_welcome":
            await query.message.edit_text(
                "📝 یه پیام خوشامد باحال بنویس! 😍\nمثلا: خوش اومدی {mention} به گروه ما!"
            )
            context.user_data["setting"] = {"type": "welcome", "chat_id": chat_id}

        elif query.data == "set_rules":
            await query.message.edit_text(
                "📜 قوانین جدید گروه رو بنویس! ✍\nمثلا: 1. اسپم نکن\n2. حال کن!"
            )
            context.user_data["setting"] = {"type": "rules", "chat_id": chat_id}

        elif query.data == "show_stats":
            member_count = await query.message.chat.get_member_count()
            msg_count = MESSAGE_COUNT.get(chat_id, {}).get("total", 0)
            users = MESSAGE_COUNT.get(chat_id, {}).get("users", {})
            active_users = len(users)
            top_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:3]
            top_users_text = "\n".join(
                [f"🏅 @{context.bot.get_chat(user_id).username or 'کاربر'}: {count} پیام"
                 for user_id, count in top_users if context.bot.get_chat(user_id).username]
            ) if top_users else "هنوز کسی پیام نداده! 😴"
            stats_text = (
                f"📊 آمار خفن گروهمون! 🚀\n"
                f"👥 تعداد اعضا: {member_count} نفر\n"
                f"💬 کل پیام‌ها: {msg_count} تا\n"
                f"🌟 کاربران فعال: {active_users} نفر\n"
                f"🔥 فعال‌ترین اعضا:\n{top_users_text}\n"
                f"بیاین گروهو بترکونیم! 😎"
            )
            await query.message.edit_text(stats_text)
            await query.message.reply_text("🔙 برو به /panel برای کارهای بیشتر! 😄")

        elif query.data == "clean_messages":
            keyboard = [
                [InlineKeyboardButton("🗑 5 پیام", callback_data="clean_5")],
                [InlineKeyboardButton("🗑 10 پیام", callback_data="clean_10")],
                [InlineKeyboardButton("🗑 20 پیام", callback_data="clean_20")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="stats_clean")],
            ]
            await query.message.edit_text(
                "🗑 چند تا پیام پاک کنم؟ 😜",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data.startswith("clean_"):
            count = int(query.data.split("_")[1])
            message_id = query.message.message_id
            for i in range(count):
                try:
                    await query.message.chat.delete_message(message_id - i)
                except:
                    continue
            await query.message.reply_text(f"🗑 {count} تا پیام غیبشون زد! 😎")
            await panel(update, context)

        elif query.data == "game_tictactoe":
            GAME_STATE[(chat_id, user_id)] = {
                "game": "tictactoe",
                "board": [" " for _ in range(9)],
                "player": "X",
            }
            keyboard = [
                [InlineKeyboardButton("⬜" if GAME_STATE[(chat_id, user_id)]["board"][i] == " " else GAME_STATE[(chat_id, user_id)]["board"][i], callback_data=f"tictactoe_{i}") for i in range(j, j + 3)]
                for j in range(0, 9, 3)
            ]
            keyboard.append([InlineKeyboardButton("🔙 لغو بازی", callback_data="cancel_game")])
            board_str = "\n".join([" | ".join(GAME_STATE[(chat_id, user_id)]["board"][i:i+3]) for i in range(0, 9, 3)])
            await query.message.edit_text(
                f"❌ دوز! تو X هستی! 😎\n{board_str}\nیه خونه انتخاب کن!",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data.startswith("tictactoe_"):
            if (chat_id, user_id) not in GAME_STATE:
                await query.message.edit_text("🚫 اوپس! بازی تموم شده! دوباره /games بزن! 😜")
                return
            pos = int(query.data.split("_")[1])
            game_data = GAME_STATE[(chat_id, user_id)]
            if game_data["board"][pos] != " ":
                await query.message.edit_text("❓ این خونه پره! یه جای دیگه بزن! 😅")
                return
            game_data["board"][pos] = "X"
            wins = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
            winner = None
            for a, b, c in wins:
                if game_data["board"][a] == game_data["board"][b] == game_data["board"][c] != " ":
                    winner = game_data["board"][a]
                    break
            if winner:
                board_str = "\n".join([" | ".join(game_data["board"][i:i+3]) for i in range(0, 9, 3)])
                await query.message.edit_text(
                    f"{'🎉 تو بردی! 😍' if winner == 'X' else '😂 ربات برد! 😜'}\n{board_str}\nدوباره /games بزن!"
                )
                del GAME_STATE[(chat_id, user_id)]
                return
            if " " not in game_data["board"]:
                board_str = "\n".join([" | ".join(game_data["board"][i:i+3]) for i in range(0, 9, 3)])
                await query.message.edit_text(f"🟰 مساوی شد! 😎\n{board_str}\nدوباره /games بزن!")
                del GAME_STATE[(chat_id, user_id)]
                return
            # منطق ربات برای دوز
            for a, b, c in wins:
                if game_data["board"][a] == game_data["board"][b] == "O" and game_data["board"][c] == " ":
                    game_data["board"][c] = "O"
                    break
                elif game_data["board"][a] == game_data["board"][c] == "O" and game_data["board"][b] == " ":
                    game_data["board"][b] = "O"
                    break
                elif game_data["board"][b] == game_data["board"][c] == "O" and game_data["board"][a] == " ":
                    game_data["board"][a] = "O"
                    break
            else:
                for a, b, c in wins:
                    if game_data["board"][a] == game_data["board"][b] == "X" and game_data["board"][c] == " ":
                        game_data["board"][c] = "O"
                        break
                    elif game_data["board"][a] == game_data["board"][c] == "X" and game_data["board"][b] == " ":
                        game_data["board"][b] = "O"
                        break
                    elif game_data["board"][b] == game_data["board"][c] == "X" and game_data["board"][a] == " ":
                        game_data["board"][a] = "O"
                        break
                else:
                    if game_data["board"][4] == " ":
                        game_data["board"][4] = "O"
                    else:
                        empty = [i for i, x in enumerate(game_data["board"]) if x == " "]
                        if empty:
                            game_data["board"][random.choice(empty)] = "O"
            for a, b, c in wins:
                if game_data["board"][a] == game_data["board"][b] == game_data["board"][c] != " ":
                    winner = game_data["board"][a]
                    break
            if winner:
                board_str = "\n".join([" | ".join(game_data["board"][i:i+3]) for i in range(0, 9, 3)])
                await query.message.edit_text(
                    f"{'🎉 تو بردی! 😍' if winner == 'X' else '😂 ربات برد! 😜'}\n{board_str}\nدوباره /games بزن!"
                )
                del GAME_STATE[(chat_id, user_id)]
                return
            keyboard = [
                [InlineKeyboardButton("⬜" if game_data["board"][i] == " " else game_data["board"][i], callback_data=f"tictactoe_{i}") for i in range(j, j + 3)]
                for j in range(0, 9, 3)
            ]
            keyboard.append([InlineKeyboardButton("🔙 لغو بازی", callback_data="cancel_game")])
            board_str = "\n".join([" | ".join(game_data["board"][i:i+3]) for i in range(0, 9, 3)])
            await query.message.edit_text(
                f"❌ دوز! تو X هستی! 😎\n{board_str}\nیه خونه انتخاب کن!",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "game_twenty_questions":
            objects = ["کتاب", "صندلی", "تلفن", "درخت", "ماشین"]
            answer = random.choice(objects)
            GAME_STATE[(chat_id, user_id)] = {
                "game": "twenty_questions",
                "answer": answer,
                "questions": 0,
            }
            keyboard = [
                [InlineKeyboardButton("زنده‌ست؟", callback_data="tq_alive")],
                [InlineKeyboardButton("یه شیئه؟", callback_data="tq_object")],
                [InlineKeyboardButton("خوردنیه؟", callback_data="tq_edible")],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await query.message.edit_text(
                "⁉ بیست سؤالی! 😜 یه چیز تو ذهنمه، سؤال بپرس! (تا ۵ سؤال)\nسؤالت چیه؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data.startswith("tq_"):
            if (chat_id, user_id) not in GAME_STATE:
                await query.message.edit_text("🚫 اوپس! بازی تموم شده! دوباره /games بزن! 😜")
                return
            game_data = GAME_STATE[(chat_id, user_id)]
            game_data["questions"] += 1
            answer = game_data["answer"]
            response = ""
            if query.data == "tq_alive":
                response = "آره، زنده‌ست!" if answer in ["درخت"] else "نه، زنده نیست!"
            elif query.data == "tq_object":
                response = "آره، یه شیئه!" if answer in ["کتاب", "صندلی", "تلفن", "ماشین"] else "نه، شیء نیست!"
            elif query.data == "tq_edible":
                response = "نه، خوردنی نیست!"
            if game_data["questions"] >= 5:
                await query.message.edit_text(
                    f"❌ اوه! سؤالا تموم شد! 😜 جواب بود: {answer}\nدوباره /games بزن!"
                )
                del GAME_STATE[(chat_id, user_id)]
                return
            keyboard = [
                [InlineKeyboardButton("زنده‌ست؟", callback_data="tq_alive")],
                [InlineKeyboardButton("یه شیئه؟", callback_data="tq_object")],
                [InlineKeyboardButton("خوردنیه؟", callback_data="tq_edible")],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await query.message.edit_text(
                f"⁉ {response}\nسؤال بعدی چیه؟ ({game_data['questions']}/5)",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "game_rps":
            GAME_STATE[(chat_id, user_id)] = {"game": "rps"}
            keyboard = [
                [InlineKeyboardButton("✊ سنگ", callback_data="rps_rock")],
                [InlineKeyboardButton("📄 کاغذ", callback_data="rps_paper")],
                [InlineKeyboardButton("✂ قیچی", callback_data="rps_scissors")],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await query.message.edit_text(
                "✊ سنگ، کاغذ، قیچی! 😎 یکیو انتخاب کن!",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data.startswith("rps_"):
            if (chat_id, user_id) not in GAME_STATE:
                await query.message.edit_text("🚫 اوپس! بازی تموم شده! دوباره /games بزن! 😜")
                return
            user_choice = query.data.split("_")[1]
            choices = ["rock", "paper", "scissors"]
            bot_choice = random.choice(choices)
            result = ""
            if user_choice == bot_choice:
                result = "🟰 مساوی شد! 😎"
            elif (user_choice == "rock" and bot_choice == "scissors") or \
                 (user_choice == "paper" and bot_choice == "rock") or \
                 (user_choice == "scissors" and bot_choice == "paper"):
                result = "🎉 تو بردی! 😍"
            else:
                result = "😂 ربات برد! 😜"
            await query.message.edit_text(
                f"تو: {user_choice} | ربات: {bot_choice}\n{result}\nدوباره /games بزن!"
            )
            del GAME_STATE[(chat_id, user_id)]

        elif query.data == "game_word_guess":
            words = ["آفتاب", "ماه", "ستاره", "ابر", "دریا"]
            answer = random.choice(words)
            GAME_STATE[(chat_id, user_id)] = {
                "game": "word_guess",
                "answer": answer,
                "guesses": 0,
            }
            keyboard = [
                [InlineKeyboardButton(word, callback_data=f"wg_{word}") for word in words],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await query.message.edit_text(
                f"🔤 یه کلمه حدس بزن! 😜\nیکی از اینا رو انتخاب کن! (تا ۳ حدس)",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data.startswith("wg_"):
            if (chat_id, user_id) not in GAME_STATE:
                await query.message.edit_text("🚫 اوپس! بازی تموم شده! دوباره /games بزن! 😜")
                return
            game_data = GAME_STATE[(chat_id, user_id)]
            guess = query.data.split("_")[1]
            game_data["guesses"] += 1
            if guess == game_data["answer"]:
                await query.message.edit_text(
                    f"🎉 آفرین! تو {game_data['guesses']} حدس درست گفتی! 😍\nدوباره /games بزن!"
                )
                del GAME_STATE[(chat_id, user_id)]
                return
            if game_data["guesses"] >= 3:
                await query.message.edit_text(
                    f"❌ اوه! حدسات تموم شد! 😜 جواب بود: {game_data['answer']}\nدوباره /games بزن!"
                )
                del GAME_STATE[(chat_id, user_id)]
                return
            keyboard = [
                [InlineKeyboardButton(word, callback_data=f"wg_{word}") for word in words],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await query.message.edit_text(
                f"❌ نه! دوباره حدس بزن! 😜 ({game_data['guesses']}/3)",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "game_math":
            num1, num2 = random.randint(1, 20), random.randint(1, 20)
            ops = ["+", "-", "*"]
            op = random.choice(ops)
            if op == "+":
                answer = num1 + num2
            elif op == "-":
                answer = num1 - num2
            else:
                answer = num1 * num2
            options = [answer, answer + random.randint(-5, 5), answer + random.randint(-10, 10), answer + random.randint(5, 15)]
            random.shuffle(options)
            GAME_STATE[(chat_id, user_id)] = {
                "game": "math",
                "answer": answer,
            }
            keyboard = [
                [InlineKeyboardButton(str(opt), callback_data=f"math_{opt}") for opt in options],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await query.message.edit_text(
                f"➕ حل کن: {num1} {op} {num2} = ?\nجواب چیه؟ 😎",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data.startswith("math_"):
            if (chat_id, user_id) not in GAME_STATE:
                await query.message.edit_text("🚫 اوپس! بازی تموم شده! دوباره /games بزن! 😜")
                return
            guess = int(query.data.split("_")[1])
            game_data = GAME_STATE[(chat_id, user_id)]
            if guess == game_data["answer"]:
                await query.message.edit_text("🎉 درست حل کردی! 😍\nدوباره /games بزن!")
            else:
                await query.message.edit_text(f"❌ اوه! اشتباه بود! 😜 جواب: {game_data['answer']}\nدوباره /games بزن!")
            del GAME_STATE[(chat_id, user_id)]

        elif query.data == "game_memory":
            sequence = [random.randint(1, 5) for _ in range(4)]
            answer = "".join(map(str, sequence))
            GAME_STATE[(chat_id, user_id)] = {
                "game": "memory",
                "answer": answer,
                "shown": True,
            }
            await query.message.edit_text(
                f"🧠 اینو به خاطر بسپار: {answer}\nچند ثانیه دیگه می‌پرسم! 😎",
            )
            context.job_queue.run_once(
                lambda ctx: show_memory_options(ctx, chat_id, user_id, query.message.message_id),
                3,
                chat_id=chat_id,
                user_id=user_id,
            )

        elif query.data.startswith("mem_"):
            if (chat_id, user_id) not in GAME_STATE:
                await query.message.edit_text("🚫 اوپس! بازی تموم شده! دوباره /games بزن! 😜")
                return
            guess = query.data.split("_")[1]
            game_data = GAME_STATE[(chat_id, user_id)]
            if guess == game_data["answer"]:
                await query.message.edit_text("🎉 حافظه‌ت خفنه! 😍\nدوباره /games بزن!")
            else:
                await query.message.edit_text(f"❌ اوه! اشتباه بود! 😜 درستش: {game_data['answer']}\nدوباره /games بزن!")
            del GAME_STATE[(chat_id, user_id)]

        elif query.data == "game_story":
            GAME_STATE[(chat_id, user_id)] = {
                "game": "story",
                "sentence": "یه روز یه گربه تو جنگل...",
            }
            keyboard = [
                [InlineKeyboardButton("یه جمله اضافه کن", callback_data="story_add")],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await query.message.edit_text(
                f"📖 داستان‌ساز! 😜 اینو ادامه بده:\n{GAME_STATE[(chat_id, user_id)]['sentence']}\nچی می‌شه بعدش؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "story_add":
            if (chat_id, user_id) not in GAME_STATE:
                await query.message.edit_text("🚫 اوپس! بازی تموم شده! دوباره /games بزن! 😜")
                return
            await query.message.edit_text(
                "✍ یه جمله بنویس تا به داستان اضافه شه! 😎"
            )
            context.user_data["setting"] = {"type": "story", "chat_id": chat_id, "user_id": user_id}

        elif query.data == "game_poll":
            options = ["پیتزا 🍕", "ساندویچ 🌯", "سالاد 🥗", "کیک 🎂"]
            random.shuffle(options)
            GAME_STATE[(chat_id, user_id)] = {
                "game": "poll",
                "options": options,
            }
            keyboard = [
                [InlineKeyboardButton(opt, callback_data=f"poll_{i}") for i, opt in enumerate(options)],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await query.message.edit_text(
                "📊 نظرسنجی بامزه! 😜 کدومو بیشتر دوست داری؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data.startswith("poll_"):
            if (chat_id, user_id) not in GAME_STATE:
                await query.message.edit_text("🚫 اوپس! بازی تموم شده! دوباره /games بزن! 😜")
                return
            choice = int(query.data.split("_")[1])
            game_data = GAME_STATE[(chat_id, user_id)]
            await query.message.edit_text(
                f"🎉 اوه! تو {game_data['options'][choice]} رو انتخاب کردی! 😎\nدوباره /games بزن!"
            )
            del GAME_STATE[(chat_id, user_id)]

        elif query.data == "game_emoji":
            emojis = ["😺🐾", "🌞🏖", "🚀🌌", "🍕🎉"]
            answers = ["گربه بازیگوش", "روز آفتابی", "سفر فضایی", "مهمونی پیتزا"]
            idx = random.randint(0, len(emojis) - 1)
            GAME_STATE[(chat_id, user_id)] = {
                "game": "emoji",
                "answer": answers[idx],
            }
            keyboard = [
                [InlineKeyboardButton(ans, callback_data=f"emoji_{ans}") for ans in answers],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await query.message.edit_text(
                f"😀 این ایموجی‌ها چی می‌گن؟ {emojis[idx]}\nجواب چیه؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data.startswith("emoji_"):
            if (chat_id, user_id) not in GAME_STATE:
                await query.message.edit_text("🚫 اوپس! بازی تموم شده! دوباره /games بزن! 😜")
                return
            guess = query.data.split("_")[1]
            game_data = GAME_STATE[(chat_id, user_id)]
            if guess == game_data["answer"]:
                await query.message.edit_text("🎉 درست گفتی! 😍\nدوباره /games بزن!")
            else:
                await query.message.edit_text(f"❌ اوه! اشتباه بود! 😜 درستش: {game_data['answer']}\nدوباره /games بزن!")
            del GAME_STATE[(chat_id, user_id)]

        elif query.data == "game_speed":
            GAME_STATE[(chat_id, user_id)] = {
                "game": "speed",
                "start_time": time.time(),
            }
            keyboard = [
                [InlineKeyboardButton("⚡ بزن!", callback_data="speed_click")],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await query.message.edit_text(
                "⚡ مسابقه سرعت! 😎 سریع دکمه رو بزن!",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif query.data == "speed_click":
            if (chat_id, user_id) not in GAME_STATE:
                await query.message.edit_text("🚫 اوپس! بازی تموم شده! دوباره /games بزن! 😜")
                return
            game_data = GAME_STATE[(chat_id, user_id)]
            elapsed = time.time() - game_data["start_time"]
            await query.message.edit_text(
                f"🎉 وای! تو {elapsed:.2f} ثانیه زدی! 😍\nدوباره /games بزن!"
            )
            del GAME_STATE[(chat_id, user_id)]

        elif query.data == "cancel_game":
            if (chat_id, user_id) in GAME_STATE:
                del GAME_STATE[(chat_id, user_id)]
            await query.message.edit_text("🚫 بازی لغو شد! 😜\nدوباره /games بزن!")

    except Exception as e:
        logger.error(f"Error in button_callback: {str(e)}")
        traceback.print_exc(file=open("bot_debug.log", "a"))
        await query.message.edit_text("❌ اوه! یه مشکلی پیش اومد! دوباره امتحان کن! 😓")

async def show_memory_options(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, message_id: int) -> None:
    try:
        if (chat_id, user_id) not in GAME_STATE:
            return
        game_data = GAME_STATE[(chat_id, user_id)]
        if not game_data.get("shown", False):
            return
        answer = game_data["answer"]
        options = [answer, "".join([str(random.randint(1, 5)) for _ in range(4)])]
        random.shuffle(options)
        keyboard = [
            [InlineKeyboardButton(opt, callback_data=f"mem_{opt}") for opt in options],
            [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
        ]
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="🧠 حالا کدوم بود؟ 😎",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        game_data["shown"] = False
    except Exception as e:
        logger.error(f"Error in show_memory_options: {str(e)}")

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        setting = context.user_data.get("setting")
        if not setting or not update.message:
            return
        chat_id = setting["chat_id"]
        GROUP_SETTINGS.setdefault(chat_id, {})
        if setting["type"] == "welcome":
            GROUP_SETTINGS[chat_id]["welcome"] = update.message.text
            await update.message.reply_text("🎉 پیام خوشامد ذخیره شد! 😍\nبرگرد به /panel!")
        elif setting["type"] == "rules":
            GROUP_SETTINGS[chat_id]["rules"] = update.message.text
            await update.message.reply_text("📜 قوانین جدید ذخیره شد! 😎\nبرگرد به /panel!")
        elif setting["type"] == "add_word":
            word = update.message.text.strip().lower()
            FILTERED_WORDS.setdefault(chat_id, []).append(word)
            await update.message.reply_text(f"🚫 کلمه '{word}' به فیلتر اضافه شد! 😎\nبرگرد به /panel!")
        elif setting["type"] == "story":
            user_id = setting["user_id"]
            if (chat_id, user_id) not in GAME_STATE:
                await update.message.reply_text("🚫 اوپس! داستان تموم شده! 😜")
                return
            sentence = update.message.text.strip()
            GAME_STATE[(chat_id, user_id)]["sentence"] += f" {sentence}"
            keyboard = [
                [InlineKeyboardButton("یه جمله اضافه کن", callback_data="story_add")],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_game")],
            ]
            await update.message.reply_text(
                f"📖 داستان ادامه پیدا کرد! 😜\n{GAME_STATE[(chat_id, user_id)]['sentence']}\nبعدش چی؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        context.user_data.pop("setting", None)
    except Exception as e:
        logger.error(f"Error in handle_settings: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Ban command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        chat = update.effective_chat
        user = update.effective_user
        admins = await chat.get_administrators()
        if not any(admin.user.id == user.id for admin in admins):
            await update.message.reply_text("🚫 اوپس! فقط ادمین‌ها می‌تونن بن کنن! 😜")
            return
        target_user = None
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
        elif context.args:
            try:
                target_user = await context.bot.get_chat(context.args[0])
            except:
                pass
        if not target_user:
            await update.message.reply_text("❓ یه @username بده یا روی پیامش ریپلای کن! 😅")
            return
        await chat.ban_member(target_user.id)
        await update.message.reply_text(
            f"🔴 {target_user.mention_html()} بن شد! 😎 حالا چی؟",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error in ban_user: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Unban command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        chat = update.effective_chat
        user = update.effective_user
        admins = await chat.get_administrators()
        if not any(admin.user.id == user.id for admin in admins):
            await update.message.reply_text("🚫 فقط ادمین‌ها می‌تونن آنبن کنن! 😜")
            return
        if not context.args:
            await update.message.reply_text("❓ یه @username بده دیگه! 😅")
            return
        target = context.args[0]
        try:
            target_user = await context.bot.get_chat(target)
            await chat.unban_member(target_user.id, only_if_banned=True)
            await update.message.reply_text(
                f"🟢 {target_user.mention_html()} آزاد شد! 😊 خوش اومد!",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Unban failed for {target}: {str(e)}")
            await update.message.reply_text(
                f"❌ اوه! نمی‌تونم {target} رو آنبن کنم. شاید بن نیست یا یوزرنیم اشتباهه! 😓"
            )
    except Exception as e:
        logger.error(f"Error in unban_user: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Mute command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        chat = update.effective_chat
        user = update.effective_user
        admins = await chat.get_administrators()
        if not any(admin.user.id == user.id for admin in admins):
            await update.message.reply_text("🚫 فقط ادمین‌ها می‌تونن میوت کنن! 😜")
            return
        target_user = None
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
        elif context.args:
            try:
                target_user = await context.bot.get_chat(context.args[0])
            except:
                pass
        if not target_user:
            await update.message.reply_text("❓ یه @username بده یا روی پیامش ریپلای کن! 😅")
            return
        await chat.restrict_member(target_user.id, permissions={"can_send_messages": False})
        await update.message.reply_text(
            f"🔇 {target_user.mention_html()} ساکت شد! 😎",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error in mute_user: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Unmute command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        chat = update.effective_chat
        user = update.effective_user
        admins = await chat.get_administrators()
        if not any(admin.user.id == user.id for admin in admins):
            await update.message.reply_text("🚫 فقط ادمین‌ها می‌تونن آنمیوت کنن! 😜")
            return
        target_user = None
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
        elif context.args:
            try:
                target_user = await context.bot.get_chat(context.args[0])
            except:
                pass
        if not target_user:
            await update.message.reply_text("❓ یه @username بده یا روی پیامش ریپلای کن! 😅")
            return
        await chat.restrict_member(
            target_user.id,
            permissions={
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_polls": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True,
            },
        )
        await update.message.reply_text(
            f"🔊 {target_user.mention_html()} حالا می‌تونه گپ بزنه! 😊",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error in unmute_user: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Warn command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        chat = update.effective_chat
        user = update.effective_user
        admins = await chat.get_administrators()
        if not any(admin.user.id == user.id for admin in admins):
            await update.message.reply_text("🚫 فقط ادمین‌ها می‌تونن اخطار بدن! 😜")
            return
        target_user = None
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
        elif context.args:
            try:
                target_user = await context.bot.get_chat(context.args[0])
            except:
                pass
        if not target_user:
            await update.message.reply_text("❓ یه @username بده یا روی پیامش ریپلای کن! 😅")
            return
        user_id = target_user.id
        chat_id = chat.id
        WARNINGS.setdefault(chat_id, {}).setdefault(user_id, 0)
        WARNINGS[chat_id][user_id] += 1
        warn_count = WARNINGS[chat_id][user_id]
        if warn_count >= 3:
            await chat.ban_member(user_id)
            await update.message.reply_text(
                f"⚠ {target_user.mention_html()} ۳ تا اخطار گرفت و بن شد! 😱",
                parse_mode="HTML",
            )
            WARNINGS[chat_id].pop(user_id, None)
        else:
            await update.message.reply_text(
                f"⚠ {target_user.mention_html()} یه اخطار گرفت ({warn_count}/3)! 😳 مراقب باش!",
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error(f"Error in warn_user: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def clean_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Clean command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        chat = update.effective_chat
        user = update.effective_user
        admins = await chat.get_administrators()
        if not any(admin.user.id == user.id for admin in admins):
            await update.message.reply_text("🚫 فقط ادمین‌ها می‌تونن پاکسازی کنن! 😜")
            return
        keyboard = [
            [InlineKeyboardButton("🗑 5 پیام", callback_data="clean_5")],
            [InlineKeyboardButton("🗑 10 پیام", callback_data="clean_10")],
            [InlineKeyboardButton("🗑 20 پیام", callback_data="clean_20")],
        ]
        await update.message.reply_text(
            "🗑 چند تا پیام آخر رو پاک کنم؟ 😜",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        logger.error(f"Error in clean_messages: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"Pin command from user {update.effective_user.id}")
        if not await check_group_only(update, context):
            return
        chat = update.effective_chat
        user = update.effective_user
        admins = await chat.get_administrators()
        if not any(admin.user.id == user.id for admin in admins):
            await update.message.reply_text("🚫 فقط ادمین‌ها می‌تونن پیام پین کنن! 😜")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("❓ روی یه پیام ریپلای کن تا پینش کنم! 😅")
            return
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 پیام پین شد! حالا همه می‌بیننش! 😎")
    except Exception as e:
        logger.error(f"Error in pin_message: {str(e)}")
        await update.message.reply_text("❌ اوه! یه مشکلی پیش اومد! 😓")

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"New member in chat {update.effective_chat.id}")
        chat_id = update.effective_chat.id
        welcome = GROUP_SETTINGS.get(chat_id, {}).get("welcome", WELCOME_MESSAGE)
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                await update.message.reply_text(
                    "🎉 مرسی که منو به گروهتون دعوت کردین! 😎\nبرای شروع، منو ادمین کن تا بتونم گروهو بترکونم! 🚀\nدستوراتم رو با /help ببین!"
                )
                continue
            mention = f"<a href='tg://user?id={member.id}'>{member.full_name}</a>"
            await update.message.reply_text(
                welcome.format(mention=mention),
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error(f"Error in welcome_new_member: {str(e)}")

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        if not GROUP_SETTINGS.get(chat_id, {}).get("antilink", False):
            return
        message = update.message
        if message.text and re.search(r"http[s]?://", message.text, re.IGNORECASE):
            logger.debug(f"Link detected in chat {chat_id}")
            await message.delete()
            await message.reply_text("🚫 اوه اوه! لینک فرستادن ممنوعه، دوست من! 😜")
    except Exception as e:
        logger.error(f"Error in anti_link: {str(e)}")

async def word_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        if not GROUP_SETTINGS.get(chat_id, {}).get("word_filter", False):
            return
        message = update.message
        if message.text:
            text = message.text.lower()
            words = FILTERED_WORDS.get(chat_id, [])
            for word in words:
                if word in text:
                    logger.debug(f"Filtered word '{word}' detected in chat {chat_id}")
                    await message.delete()
                    await message.reply_text("🚫 اوه! کلمه ممنوعه زدی! 😜 مراقب باش!")
                    return
    except Exception as e:
        logger.error(f"Error in word_filter: {str(e)}")

async def chat_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.message.chat.type == "private":
            return
        text = update.message.text.lower()
        for pattern, responses in CHAT_RESPONSES.items():
            if re.search(pattern, text):
                logger.debug(f"Chat response triggered for pattern {pattern}")
                await update.message.reply_text(random.choice(responses))
                break
    except Exception as e:
        logger.error(f"Error in chat_response: {str(e)}")

async def count_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.message.chat.type == "private":
            return
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        if update.message.from_user.is_bot:
            return
        MESSAGE_COUNT.setdefault(chat_id, {"total": 0, "users": {}})
        MESSAGE_COUNT[chat_id]["total"] += 1
        MESSAGE_COUNT[chat_id]["users"].setdefault(user_id, 0)
        MESSAGE_COUNT[chat_id]["users"][user_id] += 1
        LAST_MESSAGE_TIME[chat_id] = time.time()
        logger.debug(f"Message counted in chat {chat_id}, total: {MESSAGE_COUNT[chat_id]['total']}")
    except Exception as e:
        logger.error(f"Error in count_messages: {str(e)}")

async def start_discussion(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    try:
        if chat_id not in LAST_MESSAGE_TIME:
            return
        last_time = LAST_MESSAGE_TIME.get(chat_id, 0)
        if time.time() - last_time >= 4 * 3600:  # ۴ ساعت
            discussion = random.choice(DISCUSSION_STARTERS)
            DISCUSSION_STARTERS.remove(discussion)  # جلوگیری از تکرار
            if not DISCUSSION_STARTERS:
                DISCUSSION_STARTERS.extend([
"🎬 اگه قرار بود یه فیلم درباره گروهمون بسازن، اسمش چی بود؟ 😎",
                    "🍕 آخرین غذایی که خوردی چی بود؟ تعریف کن ببینم! 😋",
                    "🦁 اگه یه حیوون بودی، چی بودی و چرا؟ 🤔",
                    "🚀 اگه یه ابرقدرت داشتی، چی دوست داشتی باشه؟ 😜",
                    "🎶 یه آهنگ بگو که الان تو سرته! 🎧",
                    "🏝 اگه می‌تونستی همین الان یه جا سفر کنی، کجا می‌رفتی؟ ✈",
                    "😂 بامزه‌ترین خاطره‌ت تو این گروه چیه؟ بگو بخندیم! 😄",
                    "🧙‍♂ اگه جادوگر بودی، چه جادویی رو گروه می‌کردی؟ 🪄",
                    "🍫 شکلات یا چیپس؟ نظرت چیه؟ 😋",
                    "🎮 آخرین بازی که کردی چی بود؟ حال دادی؟ 🕹",
                ])
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🌟 گروه چرا ساکته؟ بیا یه بحث باحال! 😜\n{discussion}",
            )
            logger.debug(f"Started discussion in chat {chat_id}: {discussion}")
    except Exception as e:
        logger.error(f"Error in start_discussion for chat {chat_id}: {str(e)}")

async def send_nightly_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        now = datetime.now().strftime("%H:%M")
        if now == "00:00":
            for chat_id in GROUP_SETTINGS.keys():
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="🌙 تایم فداتون! 😍 شب بخیر گروه خفن! ❤",
                    )
                    logger.debug(f"Sent nightly message to chat {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send nightly message to chat {chat_id}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in send_nightly_message: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.error(f"Update {update} caused error: {context.error}")
        traceback.print_exc(file=open("bot_debug.log", "a"))
    except Exception as e:
        logger.error(f"Error in error_handler: {str(e)}")

async def main() -> None:
    logger.info("Starting bot...")
    application = None
    try:
        logger.debug("Building application...")
        application = (
            Application.builder()
            .token(TOKEN)
            .get_updates_connect_timeout(10)
            .get_updates_read_timeout(10)
            .get_updates_write_timeout(10)
            .build()
        )
        logger.info("Application built successfully")
        logger.debug("Testing bot connection...")
        bot = application.bot
        me = await bot.get_me()
        logger.info(f"Bot connected: @{me.username}")

        logger.debug("Adding handlers...")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("games", games))
        application.add_handler(CommandHandler("panel", panel))
        application.add_handler(CommandHandler("tag", tag_user))
        application.add_handler(CommandHandler("rules", rules))
        application.add_handler(CommandHandler("stats", stats))
        application.add_handler(CommandHandler("ban", ban_user))
        application.add_handler(CommandHandler("unban", unban_user))
        application.add_handler(CommandHandler("mute", mute_user))
        application.add_handler(CommandHandler("unmute", unmute_user))
        application.add_handler(CommandHandler("warn", warn_user))
        application.add_handler(CommandHandler("clean", clean_messages))
        application.add_handler(CommandHandler("pin", pin_message))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_link))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, word_filter))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_response))
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, count_messages))
        application.add_error_handler(error_handler)

        logger.info("Handlers added successfully")
        logger.debug("Scheduling jobs...")
        application.job_queue.run_repeating(
            send_nightly_message,
            interval=60,
            first=0,
        )
        for chat_id in GROUP_SETTINGS.keys():
            application.job_queue.run_repeating(
                lambda ctx, cid=chat_id: start_discussion(ctx, cid),
                interval=300,
                first=300,
            )

        logger.debug("Initializing application...")
        await application.initialize()
        await application.start()
        logger.debug("Starting polling...")
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        logger.info("Bot is polling...")
        await application.bot.set_my_commands([
            ("start", "شروع ربات"),
            ("help", "راهنما"),
            ("games", "بازی‌ها"),
            ("panel", "پنل مدیریت"),
            ("tag", "صدا زدن"),
            ("rules", "قوانین"),
            ("stats", "آمار گروه"),
            ("ban", "بن کردن"),
            ("unban", "آزاد کردن"),
            ("mute", "میوت"),
            ("unmute", "آنمیوت"),
            ("warn", "اخطار"),
            ("clean", "پاکسازی"),
            ("pin", "پین کردن"),
        ])
        while True:
            await asyncio.sleep(3600)  # نگه داشتن حلقه
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        traceback.print_exc(file=open("bot_debug.log", "a"))
        raise
    finally:
        logger.debug("Shutting down application...")
        if application:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
        logger.info("Bot instance ended")

if __name__ == "__main__":
    logger.info("Script started")
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        traceback.print_exc(file=open("bot_debug.log", "a"))
    finally:
        logger.info("Bot instance ended")