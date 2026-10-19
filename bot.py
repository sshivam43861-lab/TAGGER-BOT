import asyncio
import html
import logging
import random
import re
import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatType, ParseMode
from telegram.error import TelegramError, RetryAfter
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN,
    OWNER_ID,
    BOT_NAME,
    DEFAULT_TAG_MESSAGE,
    TAG_DELAY,
    UTAG_DELAY,
    BROADCAST_DELAY,
)

from database import (
    init_db,
    save_user,
    save_group,
    save_member,
    get_broadcast_users,
    get_group_members,
    get_stats,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ACTIVE_TASKS = {}
ACTIVE_CHATS = set()


# ==================================================
# 💗 STYLISH U TAG MESSAGES
# ==================================================

UTAG_MESSAGES = [
    "𓆩🥹💗𓆪 𝐀ʀᴇᴡ ɢᴄ ᴍᴇ ᴀᴀ ᴊᴀᴏ ɴᴀ 🎀",
    "𓆩😢🫶𓆪 𝐌ᴜᴊʜsᴇ ʙʜɪ ʙᴀᴀᴛ ᴋᴀʀ ʟᴏ",
    "𓆩🥹💞𓆪 𝐀ʀᴇ sᴜɴᴀ ɴᴀ, 𝐈 ᴍɪss ᴜ",
    "𓆩🙈❤️‍🔥𓆪 𝐀ʙ 𝐈 ʟᴏᴠᴇ ᴜ ʙᴏʟ ᴅᴏ ɴᴀ",
    "𓆩😂🔥𓆪 𝐀ɴᴜʀᴀɢ ᴄʜɪᴋɴᴀ ʜᴀɪ ɴᴀ?",
    "𓆩👑👀𓆪 𝐓ᴜᴍʜᴇ ᴘᴀᴛᴀ ʜᴀɪ ᴍᴇʀᴀ ᴏᴡɴᴇʀ ᴋᴏɴ ʜᴀɪ?",
    "𓆩🥹💌𓆪 𝐃ᴇᴋʜᴏ ᴍᴀɪ ᴛᴜᴍʜᴇ ʏᴀᴀᴅ ᴋɪʏᴀ",
    "𓆩🙈💞𓆪 𝐀ᴀᴘ sɪɴɢʟᴇ ʜᴏ ᴋʏᴀ?",
    "𓆩📱😂𓆪 𝐀ᴀᴘᴋᴀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴍɪʟᴇɢᴀ ᴋʏᴀ?",
    "𓆩🎉🥳𓆪 𝐒ᴜɴᴀ ɴᴀ, ᴄʜᴀʟᴏ ᴘᴀʀᴛʏ ᴋᴀʀᴛᴇ ʜᴀɪ",
    "𓆩🫶💗𓆪 𝐀ᴀᴘ ᴍᴇʀᴇ ᴅᴏsᴛ ʙᴀɴᴏɢᴇ ᴋʏᴀ?",
    "𓆩❤️‍🔥🙈𓆪 𝐈 ʟᴏᴠᴇ ᴜ ɴᴀ",
    "𓆩😂🙏🏻𓆪 𝐁ʜᴀʙʜɪ ᴋᴀɪsɪ ʜᴀɪ ʏʀ?",
    "𓆩👑💞𓆪 𝐀ᴀᴘ ᴍᴇʀᴇ ᴏᴡɴᴇʀ ᴋɪ ɢғ ʙᴀɴᴏɢᴇ ᴋʏᴀ?",
    "𓆩🤣💗𓆪 𝐀ᴀᴘ sɪɴɢʟᴇ sᴇ ᴍɪɴɢʟᴇ ᴋᴀʙ ʜᴏ ʀʜᴇ?",
    "𓆩🥹🎀𓆪 𝐒ᴜɴᴏ ɴᴀ, ɢᴄ ᴍᴇ ʙʜɪ ᴀᴀ ᴊᴀᴏ",
    "𓆩👀💞𓆪 𝐈 ᴡᴀɴɴᴀ sᴇᴇ ᴜ",
    "𓆩😂💗𓆪 𝐀ʀᴇ ʙᴀʙᴜ, ᴀᴀᴘ ᴊᴀɪsᴇ ɴᴀᴍᴏᴏɴᴇ ʀᴏᴢ ɴᴀʜɪ ᴍɪʟᴛᴇ… sʜᴜᴋʀ ʜᴀɪ ᴀᴀᴘ ᴇᴋ ʜɪ ʜᴏ 😂💗",
    "𓆩😂🙏🏻𓆪 𝐁ʜᴀʙʜɪ ᴋᴏ ᴍᴇʀᴀ ᴘʀᴀɴᴀᴍ ʙᴏʟɴᴀ",
    "𓆩🥹💌𓆪 𝐀ʀᴇ sᴜɴᴏ, ʏᴀᴀᴅ ᴛᴏʜ ᴋᴀʀ ʟɪʏᴀ ᴋᴀʀᴏ",
    "𓆩🎀🫶𓆪 𝐒ᴜɴᴀ ɴᴀ @rnmusicupdates ᴊᴏɪɴ ᴋᴀʀ ɴᴀ ᴘʟᴇᴀsᴇ",
    "𓆩👑💗𓆪 𝐀ᴀᴘᴋᴀ ᴘᴀᴛᴀ ʜᴀɪ ᴍᴇʀᴀ ᴏᴡɴᴇʀ ᴀᴀᴘᴋᴏ ʏᴀᴀᴅ ᴋɪʏᴇ",
    "𓆩😭🎀𓆪 𝐁ᴀʙᴜ, ɪᴛɴᴇ ᴄᴜᴛᴇ ᴋʏᴜɴ ʜᴏ?",
    "𓆩😭🎀𓆪 𝐁ᴀʙᴜ, ɪᴛɴᴇ ᴄᴜᴛᴇ ᴋʏᴜɴ ʜᴏ?",
    "𓆩😂🌷𓆪 𝐘ᴇ ᴋʏᴀ ʜᴀɪ ᴊɪ? 😂🌷",
    "𓆩🙈💗𓆪 𝐀ᴀᴘ ʙᴀᴅᴇ ᴄᴜᴛᴇ ʙᴇsʜᴀʀᴀᴍ ʜᴏ",
    "𓆩☕😭𓆪 𝐒ᴜɴᴏ ᴊɪ, ᴄʜᴀɪ ᴘɪʟᴀ ᴅᴏ ☕",
    "𓆩🎶🎀𓆪 𝐂ᴜᴛɪᴇ ᴘɪᴇ, sᴏɴɢ sᴜɴᴀ ᴅᴏ ɴᴀ",
    "𓆩🙈💗𓆪 𝐀ᴀᴘ ᴍᴇʀᴇ ɢғ ʙᴀɴᴏɢᴇ ᴋʏᴀ?",
    "𓆩🫶🌷𓆪 𝐀ᴀᴘ ᴍᴇʟᴇ sᴇ ᴅᴏsᴛɪ ᴋᴀʀᴏɢᴇ ᴋʏᴀ?",
    "𓆩💌🥹𓆪 𝐏ᴀᴛᴀ ɴᴀʜɪ ᴋʏᴜɴ, ᴀᴀᴊ ᴛᴜᴍʜᴀʀɪ ʏᴀᴀᴅ ᴀᴀʏɪ",
    "𓆩😂🙏🏻𓆪 𝐁ʜᴀʙʜɪ ᴋᴀɪsɪ ʜᴀɪ ʏʀ?",
    "𓆩💌🌷𓆪 𝐒ᴜɴᴏ ᴊɪ, ʙɪɴᴀ ᴡᴀᴊᴀʜ ʙʜɪ ʏᴀᴀᴅ ᴀᴀ ᴊᴀᴀᴛᴇ ʜᴏ",
    "𓆩🥹💌𓆪 𝐀ʀᴇ ʙᴀʙᴜ, ᴛᴜᴍ ʙʜɪ ᴋɪsɪ ᴋᴇ ʟɪʏᴇ sᴘᴇᴄɪᴀʟ ʜᴏ",
    "𓆩😂💘𓆪 𝐒ᴇᴛᴛɪɴɢ ᴋᴀʀᴀ ᴅᴏ ɴᴀ ᴀʙ",
    "𓆩😭😂💗𓆪 𝐘ᴀᴀᴅ ᴛᴏʜ ᴀᴀᴛɪ ʜᴀɪ ᴍᴇʀɪ ʏᴀ ʙᴀs ᴏɴʟɪɴᴇ ʀᴇʜɴᴀ ʜᴀɪ?",
    "𓆩🤧🙏🏻💞𓆪 𝐇ᴇʟʟᴏ ᴊɪ, ᴀᴀᴘᴋᴇ ᴅᴀʀsʜᴀɴ ᴋᴀʀɴᴇ ᴀᴀʏᴇ ᴛʜᴇ",
    "𓆩🫂💗𓆪 𝐒ᴜɴᴏ ᴊɪ, ᴇᴋ ᴊʜᴀᴘᴘɪ ᴜᴅʜᴀᴀʀ ᴍɪʟᴇɢɪ ᴋʏᴀ?",
    "𓆩😭☕💞𓆪 𝐓ᴜᴍʜᴀʀᴇ ʙɪɴᴀ ɢᴄ ᴄʜᴀɪ ʙɪɴᴀ ʙɪsᴄᴜɪᴛ ᴊᴀɪsᴀ ʜᴀɪ",
    "𓆩😂🫂❤️𓆪 𝐓ᴜᴍ ᴛʜᴏᴅᴇ ᴘᴀɢᴀʟ ʜᴏ, ᴘᴀʀ ᴀᴘɴᴇ ʜᴏ",
    "𓆩😭💌😂𓆪 𝐃ɪʟ ɴᴇ ᴍᴇssᴀɢᴇ ᴋᴀʀɴᴇ ᴋᴏ ᴋᴀʜᴀ, ᴅɪᴍᴀᴀɢ ɴᴇ ᴍᴀɴᴀ ᴋɪʏᴀ",
    "𓆩🕵🏻‍♀️🥹💗𓆪 𝐓ᴜᴍ ᴋʜᴜsʜ ʜᴏ ɴᴀ? sᴀᴄʜ ʙᴀᴛᴀɴᴀ",
    "𓆩🫂😂🥟𓆪 𝐄ᴋ ʜᴜɢ ᴀᴜʀ ᴅᴏ sᴀᴍᴏsᴇ ᴍɪʟ ᴊᴀᴀʏᴇɪɴ ᴛᴏʜ ᴢɪɴᴅᴀɢɪ sᴇᴛ",
    "𓆩😭🥟💞𓆪 𝐄ᴋ ᴅɪɴ sᴀʙᴋᴏ ᴄʜʜᴏᴅ ᴋᴇ ᴍᴏᴍᴏs ᴋʜᴀɴᴇ ᴄʜᴀʟᴇɴɢᴇ",
    "𓆩😭🤣💗𓆪 𝐇ᴀsᴏ, ɴᴀᴄʜᴏ, ᴋʜᴀᴏ ᴀᴜʀ ʜᴀᴍᴀʀᴇ ᴍᴇssᴀɢᴇ ᴋᴀ ʀᴇᴘʟʏ ᴋᴀʀᴏ",
    "𓆩😭🍫😂𓆪 𝐌ᴏᴏᴅ ᴛʜᴇᴇᴋ ᴋᴀʀɴᴀ ʜᴀɪ, ᴄʜᴏᴄᴏʟᴀᴛᴇ ᴋʜᴀᴏɢᴇ?",
    "𓆩🥹💗𓆪 𝐌ᴜᴊʜsᴇ ʙʜɪ ʙᴀᴀᴛ ᴋᴀʀ ʟᴏ ɴᴀ",
    "𓆩💌🌷𓆪 𝐒ᴜɴᴏ ᴊɪ, ᴀᴀᴘᴋᴏ ᴋᴏɪ ʏᴀᴀᴅ ᴋᴀʀ ʀᴀʜᴀ ʜᴀɪ",
    "𓆩🥹💞𓆪 𝐃ᴏ ᴍɪɴᴜᴛᴇ ᴍɪʟ sᴀᴋᴛᴇ ʜᴀɪɴ? ᴅɪʟ ʙᴏʀᴇ ʜᴀɪ",
    "𓆩😂🎀𓆪 𝐎ʏᴇ ɴᴀᴜᴛᴀɴᴋɪ, ᴛʜᴏᴅᴀ ɪᴅʜᴀʀ ʙʜɪ ᴀᴛᴛᴇɴᴛɪᴏɴ ᴅᴏ",
    "𓆩🥹💗𓆪 𝐊ᴀʙʜɪ ᴋʜᴜᴅ ʙʜɪ ᴍᴇssᴀɢᴇ ᴋᴀʀ ᴅɪʏᴀ ᴋᴀʀᴏ",
    "𓆩😂👀𓆪 𝐏ᴀᴘᴀ ᴀᴀ ɢʏᴇ ᴋʏᴀ? ᴏɴʟɪɴᴇ ᴀᴀ ᴊᴀᴏ",
    "𓆩🐼😂𓆪 𝐎ʏᴇ ᴄᴜᴛɪᴇ, ᴢɪɴᴅᴀ ʜᴏ ʏᴀ ᴄʜᴀʀɢɪɴɢ ᴘᴇ ʜᴏ?",
    "𓆩💗🎀𓆪 𝐀ᴀᴘᴋᴀ ɴᴀᴀᴍ ʟɪʏᴀ ᴀᴜʀ ᴅɪʟ ɴᴇ ᴀᴛᴛᴇɴᴅᴀɴᴄᴇ ʟᴀɢᴀ ᴅɪ",
    "𓆩🤣📩𓆪 𝐀ᴀᴘᴋᴏ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ɴᴀʜɪ, ɪɴᴠɪᴛᴀᴛɪᴏɴ ʙʜᴇᴊɴᴀ ʜᴏɢᴀ",
    "𓆩🙈💗𓆪 𝐎ʏᴇ ʙᴀʙᴜ, ɪᴅʜᴀʀ ʙʜɪ ᴅʜʏᴀᴀɴ ᴅᴏ",
    "𓆩😂💸𓆪 𝐎ɴʟɪɴᴇ ᴀᴀ ᴊᴀ, ᴋᴏɪ ᴘᴀɪsᴇ ɴᴀʜɪ ᴍᴀᴀɴɢ ʀᴀʜᴀ",
    "𓆩🫶🌷𓆪 𝐓ᴜ ᴋʜᴜsʜ ʀᴀʜᴀ ᴋᴀʀ, ʙᴀᴀᴋɪ sᴀʙ sᴀᴍʙʜᴀʟ ᴊᴀᴀʏᴇɢᴀ",
    "𓆩😂👥𓆪 𝐁ʜᴀɪ ᴛᴜ ɢʀᴏᴜᴘ ᴍᴇɪɴ ʜᴀɪ ʏᴀ ʙᴀs ʀᴇɴᴛ ᴘᴇ ɴᴀᴀᴍ ᴅɪʏᴀ ʜᴀɪ?",
    "𓆩🤣🫶𓆪 𝐃ᴏsᴛ ʜᴀɪ ᴛᴜ, ɪsʟɪʏᴇ ᴛᴇʀɪ ʙᴀᴋᴡᴀᴀs ʙʜɪ sᴇʜ ʟᴇᴛᴇ ʜᴀɪɴ",
    "𓆩🎶🎧𓆪 𝐎ʏᴇ ᴍᴜsɪᴄ ʟᴏᴠᴇʀ, ᴛʜᴏᴅᴀ ᴀᴘɴᴀ sᴜʀ ᴍɪʟᴀ",
    "𓆩😂💗𓆪 𝐀ʀᴇ sᴜɴᴏ ɴᴀ, ᴋᴀʜᴀ ʜᴏ ᴛᴜᴍ? 𝐑ᴏʙɪɴ ʙʜᴀʙʜɪ ᴋᴀɪsɪ ʜᴀɪɴ?",
    "𓆩🤣🔥𓆪 𝐂ʜᴜᴘ-ᴄʜᴀᴀᴘ ᴏɴʟɪɴᴇ ᴀᴀᴏ ᴀᴜʀ ʙᴀᴛᴀᴏ ᴀᴀᴊ ᴋɪsᴋɪ ʙᴀɴᴅ ʙᴀᴊᴀʏɪ",
    "𓆩🐸🌷𓆪 𝐎ʏᴇ ᴍᴇɴᴅʜᴀᴋ, ᴛᴀᴀʟᴀᴀʙ ᴄʜʜᴏᴅ ᴀᴜʀ ɢᴄ ᴍᴇɪɴ ᴀᴀ",
    "𓆩😂👀𓆪 𝐓ᴜ ɢᴄ ᴍᴇ ʙᴀᴀᴛ ᴋᴀʀɴᴇ ᴀᴀʏᴀ ʜᴀɪ ʏᴀ ʙᴀs ᴍᴇᴍʙᴇʀs ɢɪɴɴᴇ?",
    "𓆩🥹💗𓆪 𝐊ɪsɪ ɴᴇ ᴋᴀʜᴀ ᴛᴜᴍ ᴀᴄʜʜᴇ ʜᴏ? ɴᴀʜɪ? ᴄʜᴀʟᴏ, ʜᴜᴍ ᴋᴇʜ ᴅᴇᴛᴇ ʜᴀɪɴ",
    "𓆩🫶🌷𓆪 𝐊ᴀʙʜɪ ʙɪɴᴀ ᴋᴀᴀᴍ ᴋᴇ ʙʜɪ ʜᴇʟʟᴏ ʙᴏʟ ᴅɪʏᴀ ᴋᴀʀᴏ",
    "𓆩😭😂𓆪 𝐇ᴜᴍ ʏᴀᴀᴅ ɴᴀʜɪ ᴀᴀᴛᴇ ᴋʏᴀ? ʏᴀᴀᴅ ᴋᴀ ʀᴇᴄʜᴀʀɢᴇ ᴋʜᴀᴛᴀᴍ ʜᴏ ɢʏᴀ?",
    "𓆩🎀🤭𓆪 𝐀ᴀᴘᴋɪ sᴍɪʟᴇ ᴋᴀɪsɪ ʜᴀɪ? ᴜsᴋᴇ ᴍᴀᴀʟɪᴋ ᴋᴀʜᴀɴ ɢᴀʏᴀʙ ʜᴀɪɴ?",
    "𓆩🫶🤭𓆪 𝐊ʜᴀɴᴀ ᴋʜᴀ ʟɪʏᴀ? ᴘᴀᴀɴɪ ᴘɪ ʟɪʏᴀ? ᴀʙ ʀᴇᴘʟʏ ʙʜɪ ᴅᴇ ᴅᴏ",
    "𓆩💗🥹𓆪 𝐓ʜᴏᴅᴀ sᴀ ᴀᴛᴛᴇɴᴛɪᴏɴ ɪᴅʜᴀʀ ʙʜɪ ᴅᴇ ᴅᴇ",
    "𓆩🙈❤️𓆪 𝐒ᴜɴᴏ ɴᴀ, 𝐈 ʟᴏᴠᴇ ʏᴏᴜ",
    "𓆩😂💗𓆪 𝐀ʀᴇ ᴍᴇʀɪ ᴊᴀᴀɴ—ᴀʀʀᴇ ᴀʀʀᴇ, sᴀʙᴋᴏ ᴀɪsᴇ ʜɪ ʙᴜʟᴀᴀᴛᴀ ʜᴏᴏɴ",
    "𓆩🤣🎀𓆪 𝐈ᴛɴᴀ ʙʜɪ ᴋʏᴀ ʙʜᴀᴀᴠ ᴋʜᴀɴᴀ? ʀɪsʜᴛᴀ ʟᴇᴋᴀʀ ᴛʜᴏᴅɪ ᴀᴀʏᴇ ʜᴀɪɴ",
    "𓆩💗🌷𓆪 𝐌ᴜsᴋᴜʀᴀ ʙʜɪ ᴅᴏ, ɢᴜssᴀ ᴛᴜᴍ ᴘᴇ sᴜɪᴛ ɴᴀʜɪ ᴋᴀʀᴛᴀ",
    "𓆩🎀😂𓆪 𝐎ʏᴇ ᴄᴜᴛɪᴇ, ᴛᴜᴍʜᴀʀᴇ ʙɪɴᴀ ɢᴄ ᴋɪ ɴᴀᴜᴛᴀɴᴋɪ ᴀᴅʜᴜʀɪ ʜᴀɪ",
    "𓆩😂🔥𓆪 𝐉ᴅ ᴄʜɪᴋɴᴀ ᴋᴀʜᴀɴ ɢᴀʏᴀʙ ʜᴀɪ?",
    "𓆩👑💗𓆪 𝐌ᴇʀᴀ ᴘʏᴀʀᴀ ᴏᴡɴᴇʀ 𝐑ᴇʏᴠᴇɴ ᴋᴀʜᴀɴ ʜᴀɪ?",
    "𓆩🙈💞𓆪 𝐀ᴀᴘ ᴀᴀᴊ sɪɴɢʟᴇ sᴇ ᴍɪɴɢʟᴇ ʜᴏɢᴇ ᴋʏᴀ?",
    "𓆩😂💌𓆪 𝐄ᴋ ʙᴀᴀᴛ ᴘᴏᴏᴄʜɴɪ ᴛʜɪ… ᴘᴇʜʟᴇ ʙᴀᴛᴀᴏ ᴋʜᴀɴᴀ ᴋʜᴀʏᴀ?",
    "𓆩🫶🥹𓆪 𝐎ʏᴇ ᴍᴜᴊʜᴇ ʙʜɪ ʏᴀᴀᴅ ᴋᴀʀ ʟɪʏᴀ ᴋᴀʀᴏ",
    "𓆩💗😂𓆪 𝐓ᴜᴊʜsᴇ ʙᴀᴀᴛ ᴋᴀʀɴᴇ ᴋᴀ ᴍᴀɴɴ ᴛʜᴀ… ᴀʙ ᴋᴜᴄʜ ʙᴏʟ ʙʜɪ ᴅᴇ",
    "𓆩🤭✨𓆪 𝐂ʜᴇʜʀᴇ ᴘᴇ ᴍᴀᴀsᴏᴏᴍɪʏᴀᴛ, ᴅɪᴍᴀᴀɢ ᴍᴇɪɴ sʜᴀʀᴀʀᴀᴛ? ᴡᴀʜ!",
    "𓆩😂🙈𓆪 𝐄ᴋ ʙᴀᴀᴛ ᴋᴇʜɴɪ ᴛʜɪ… ᴛᴜ ᴘʜɪʀ ʜᴀᴡᴀ ᴍᴇɪɴ ᴜᴅɴᴇ ʟᴀɢᴇɢᴀ",
    "𓆩🤣🫶𓆪 𝐓ᴜ ᴀᴘɴᴀ ʜᴀɪ, ɪsʟɪʏᴇ ᴛᴇʀɪ ʙᴇɪᴢᴢᴀᴛɪ ʙʜɪ ᴘʏᴀᴀʀ sᴇ ᴋᴀʀᴛᴇ ʜᴀɪɴ",
    "𓆩📸🎀𓆪 𝐒ᴜɴᴀ ɴᴀ, ᴀᴘɴᴀ ɪɢ ᴅᴇ ᴅᴏ",
    "𓆩🫶🌷𓆪 𝐀ᴀᴘ ᴍᴇʟᴇ sᴇ ᴅᴏsᴛɪ ᴋᴀʀᴏɢᴇ ᴋʏᴀ?",
    "𓆩🙈👑𓆪 𝐌ᴇʀᴇ ᴏᴡɴᴇʀ 𝐑ᴇʏᴠᴇɴ ᴋᴀɪsᴇ ʜᴀɪ?",
    "𓆩🎶💗𓆪 𝐒ᴜɴᴏ ɴᴀ, ᴇᴋ ɢᴀᴀɴᴀ sᴜɴᴀ ᴅᴏ",
    "𓆩🥹💌𓆪 𝐊ᴏɪ ʏᴀᴀᴅ ɴᴏɪ ᴋᴀʀᴛᴀ ᴍᴇʟᴇ ᴋᴏ",
    "𓆩🎀💞𓆪 𝐀ᴀᴘ ᴛᴏ ᴄᴜᴛɪᴇ ʜᴏ ʏʀ",
    "𓆩🥹🌷𓆪 𝐀ᴀᴘᴋᴇ ʙɪɴᴀ ɢᴄ sᴜɴᴀ ʜᴀɪ",
    "𓆩🫶💗𓆪 𝐀ᴀᴘᴋᴏ sᴀʙ ʏᴀᴀᴅ ᴋᴀʀ ʀᴀʜᴇ, ᴀᴀᴏ ɴᴀ",
    "𓆩💌🌷𓆪 𝐀ᴀᴘᴋɪ ʏᴀᴀᴅ ᴀᴀʏɪ ᴛᴏʜ ᴛᴀɢ ᴋᴀʀ ᴅɪʏᴀ… ᴀʙ ɪᴛɴᴀ ʙʜᴀᴀᴠ ᴍᴀᴛ ᴋʜᴀɪʏᴇ",
    "𓆩🥹💗𓆪 𝐁ʜᴀɪ, ᴋʜᴜsʜɪ ᴋᴀʜᴀɴ ᴍɪʟᴇɢɪ ᴡᴏ ᴡᴀᴀʟɪ?"
]


# ==================================================
# DATABASE HELPERS
# ==================================================

async def remember(update):
    user = update.effective_user
    chat = update.effective_chat

    if user:
        await asyncio.to_thread(save_user, user)

    if chat and chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        await asyncio.to_thread(save_group, chat)
        if user:
            await asyncio.to_thread(save_member, chat.id, user)


async def admin_only(update, context):
    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return False

    if user.id == OWNER_ID:
        return True

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator", "owner")
    except TelegramError:
        return False


# ==================================================
# START / HELP / PING
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await remember(update)

    user = update.effective_user
    if not user or not update.message:
        return

    me = await context.bot.get_me()

    keyboard = [
        [
            InlineKeyboardButton("❔ 𝐇ᴇʟᴘ", callback_data="help"),
            InlineKeyboardButton("👤 𝐏ʀᴏғɪʟᴇ", callback_data="profile"),
        ],
        [
            InlineKeyboardButton(
                "➕ 𝐀ᴅᴅ ᴛᴏ ɢʀᴏᴜᴘ",
                url=f"https://t.me/{me.username}?startgroup=true",
            ),
            InlineKeyboardButton(
                "👑 𝐎ᴡɴᴇʀ",
                url=f"tg://user?id={OWNER_ID}",
            ),
        ],
    ]

    text = (
        f"╭━━━〔 🏷️ 〕━━━╮\n"
        f"   <b>{BOT_NAME}</b>\n"
        f"╰━━━━━━━━━━━━╯\n\n"
        f"╭─❖ 𝐇ᴇʟʟᴏ {html.escape(user.first_name)}! 🪽\n"
        f"│\n"
        f"├ 🆔 <b>𝐔sᴇʀ 𝐈ᴅ:</b> <code>{user.id}</code>\n"
        f"├ ✨ <b>𝐅ᴇᴀᴛᴜʀᴇs:</b> 𝐓ᴀɢᴀʟʟ • 𝐔ᴛᴀɢ\n"
        f"├ 📣 <b>𝐁ʀᴏᴀᴅᴄᴀsᴛ:</b> 𝐎ᴡɴᴇʀ 𝐎ɴʟʏ\n"
        f"│\n"
        f"╰─ 🪄 /help ᴛʏᴘᴇ ᴋᴀʀᴏ ᴄᴏᴍᴍᴀɴᴅs ᴋᴇ ʟɪʏᴇ!"
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await remember(update)

    text = (
        f"╭━━━〔 🏷️ 〕━━━╮\n"
        f"   <b>{BOT_NAME} — 𝐇ᴇʟᴘ</b>\n"
        f"╰━━━━━━━━━━━━╯\n\n"
        "👥 <b>𝐆ʀᴏᴜᴘ 𝐂ᴏᴍᴍᴀɴᴅs</b>\n"
        "├ /tagall [message] — 𝐓ᴀɢ 𝐌ᴇᴍʙᴇʀs\n"
        "├ @all [message] — 𝐐ᴜɪᴄᴋ 𝐓ᴀɢ\n"
        "├ /utag — 𝐅ᴜɴɴʏ 𝐔ᴛᴀɢ\n"
        "└ /stop — 𝐒ᴛᴏᴘ 𝐓ᴀɢɢɪɴɢ\n\n"
        "🤖 <b>𝐆ᴇɴᴇʀᴀʟ</b>\n"
        "├ /start — 𝐒ᴛᴀʀᴛ 𝐁ᴏᴛ\n"
        "├ /ping — 𝐂ʜᴇᴄᴋ 𝐑ᴇsᴘᴏɴsᴇ\n"
        "└ /stats — 𝐁ᴏᴛ 𝐒ᴛᴀᴛs\n\n"
        "👑 <b>𝐎ᴡɴᴇʀ 𝐂ᴏᴍᴍᴀɴᴅ</b>\n"
        "└ /broadcast [message]\n\n"
        "⚠️ 𝐍ᴏᴛᴇ: 𝐁ᴏᴛ ᴛᴀɢs ᴏɴʟʏ ᴍᴇᴍʙᴇʀs ɪᴛ ʜᴀs sᴇᴇɴ."
    )

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await remember(update)

    if update.message:
        await update.message.reply_text(
            "🏓 𝐏ᴏɴɢ! 𝐓ᴀɢɢᴇʀ 𝐁ᴏᴛ ɪs ᴀʟɪᴠᴇ 🪽"
        )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await remember(update)

    if not update.message or update.effective_user.id != OWNER_ID:
        if update.message:
            await update.message.reply_text("⛔ 𝐎ᴡɴᴇʀ 𝐎ɴʟʏ!")
        return

    users, groups = await asyncio.to_thread(get_stats)

    await update.message.reply_text(
        f"📊 <b>𝐁ᴏᴛ 𝐒ᴛᴀᴛs</b>\n\n"
        f"👤 𝐔sᴇʀs: {users}\n"
        f"👥 𝐆ʀᴏᴜᴘs: {groups}",
        parse_mode=ParseMode.HTML,
    )


# ==================================================
# BUTTONS
# ==================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await query.message.reply_text(
            "🏷️ /tagall [message]\n"
            "🎭 /utag\n"
            "🛑 /stop\n"
            "🏓 /ping\n"
            "📊 /stats"
        )

    elif query.data == "profile":
        user = query.from_user
        await query.message.reply_text(
            f"╭━━〔 👤 〕━━╮\n"
            f"𝐍ᴀᴍᴇ: {html.escape(user.full_name)}\n"
            f"𝐈ᴅ: <code>{user.id}</code>\n"
            f"𝐔sᴇʀɴᴀᴍᴇ: @{html.escape(user.username or 'not set')}\n"
            f"╰━━━━━━━━━━╯",
            parse_mode=ParseMode.HTML,
        )


# ==================================================
# TAGGING ENGINE
# ==================================================

async def run_tagging(chat_id, context, members, mode, message=""):
    try:
        for index, member in enumerate(members):
            if chat_id not in ACTIVE_CHATS:
                break

            user_id = member["user_id"]
            name = html.escape(member.get("first_name") or "Member")

            if mode == "utag":
                line = random.choice(UTAG_MESSAGES)
                delay = UTAG_DELAY
            else:
                line = message or DEFAULT_TAG_MESSAGE
                delay = TAG_DELAY

            text = (
                f"{line}\n"
                f"╰➤ <a href=\"tg://user?id={user_id}\">{name}</a>"
            )

            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )

            except RetryAfter as exc:
                wait_time = getattr(exc, "retry_after", 3)
                await asyncio.sleep(float(wait_time) + 1)

                if chat_id not in ACTIVE_CHATS:
                    break

                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        parse_mode=ParseMode.HTML,
                    )
                except TelegramError:
                    logger.warning("Tag failed for chat %s", chat_id)

            except TelegramError:
                logger.warning("Tag failed for chat %s", chat_id)

            await asyncio.sleep(delay)

    except asyncio.CancelledError:
        pass

    finally:
        ACTIVE_CHATS.discard(chat_id)
        ACTIVE_TASKS.pop(chat_id, None)


async def start_tagging(update, context, mode):
    await remember(update)

    if not update.message or not update.effective_chat:
        return

    if update.effective_chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await update.message.reply_text("❌ 𝐘ᴇ ᴄᴏᴍᴍᴀɴᴅ ɢʀᴏᴜᴘ ᴍᴇɪɴ ᴄʜᴀʟᴛᴀ ʜᴀɪ.")
        return

    if not await admin_only(update, context):
        await update.message.reply_text("⛔ 𝐀ᴅᴍɪɴ 𝐎ɴʟʏ!")
        return

    chat_id = update.effective_chat.id

    if chat_id in ACTIVE_CHATS:
        await update.message.reply_text("⚠️ 𝐓ᴀɢɢɪɴɢ ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ! /stop")
        return

    members = await asyncio.to_thread(get_group_members, chat_id)

    if not members:
        await update.message.reply_text(
            "🥹 𝐀ʙʜɪ ᴋᴏɪ ᴍᴇᴍʙᴇʀ ʀᴇᴄᴏʀᴅ ɴᴀʜɪ ʜᴀɪ.\n"
            "𝐁ᴏᴛ ᴋᴏ ɢʀᴏᴜᴘ ᴍᴇɪɴ ᴀᴅᴅ ᴋᴀʀᴏ ᴀᴜʀ ᴜsᴋᴇ ᴘᴀᴀs ᴍᴇᴍʙᴇʀs ᴋᴇ ᴍᴇssᴀɢᴇs ᴀᴀɴᴇ ᴅᴏ."
        )
        return

    custom_message = " ".join(context.args).strip()

    ACTIVE_CHATS.add(chat_id)

    task = asyncio.create_task(
        run_tagging(
            chat_id,
            context,
            members,
            mode,
            custom_message or DEFAULT_TAG_MESSAGE,
        )
    )

    ACTIVE_TASKS[chat_id] = task

    label = "𝐔ᴛᴀɢ 🎭" if mode == "utag" else "𝐓ᴀɢᴀʟʟ 🏷️"

    await update.message.reply_text(
        f"╭━━〔 {label} 〕━━╮\n"
        f"👥 𝐌ᴇᴍʙᴇʀs: {len(members)}\n"
        f"⏳ 𝐒ᴛᴀᴛᴜs: 𝐒ᴛᴀʀᴛᴇᴅ\n"
        f"🛑 𝐒ᴛᴏᴘ: /stop\n"
        f"╰━━━━━━━━━━╯"
    )


async def tagall(update, context):
    await start_tagging(update, context, "tagall")


async def utag(update, context):
    await start_tagging(update, context, "utag")


async def stop(update, context):
    await remember(update)

    if not update.message or not update.effective_chat:
        return

    if not await admin_only(update, context):
        await update.message.reply_text("⛔ 𝐀ᴅᴍɪɴ 𝐎ɴʟʏ!")
        return

    chat_id = update.effective_chat.id

    if chat_id not in ACTIVE_CHATS:
        await update.message.reply_text("ℹ️ 𝐊ᴏɪ ᴛᴀɢɢɪɴɢ ʀᴜɴ ɴᴀʜɪ ʜᴏ ʀᴀʜɪ.")
        return

    ACTIVE_CHATS.discard(chat_id)
    task = ACTIVE_TASKS.get(chat_id)

    if task:
        task.cancel()

    await update.message.reply_text("🛑 𝐓ᴀɢɢɪɴɢ sᴛᴏᴘᴘᴇᴅ!")


async def all_alias(update, context):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if not re.match(r"^@all(?:\s|$)", text, re.IGNORECASE):
        return

    await remember(update)

    if not await admin_only(update, context):
        await update.message.reply_text("⛔ 𝐀ᴅᴍɪɴ 𝐎ɴʟʏ!")
        return

    # Create a temporary argument list without modifying context.args.
    class AliasContext:
        args = text.split()[1:]

    await start_tagging_with_args(update, context, AliasContext.args)


async def start_tagging_with_args(update, context, args):
    # Use a separate helper so @all works without changing Telegram context.
    original_args = context.args
    try:
        # CallbackContext.args may be read-only; pass args directly instead.
        await start_tagging_args(update, context, "tagall", args)
    finally:
        pass


async def start_tagging_args(update, context, mode, args):
    await remember(update)

    if not update.message or not update.effective_chat:
        return

    if update.effective_chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    if not await admin_only(update, context):
        return

    chat_id = update.effective_chat.id

    if chat_id in ACTIVE_CHATS:
        await update.message.reply_text("⚠️ 𝐓ᴀɢɢɪɴɢ ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ!")
        return

    members = await asyncio.to_thread(get_group_members, chat_id)

    if not members:
        await update.message.reply_text("🥹 𝐀ʙʜɪ ᴍᴇᴍʙᴇʀ ʀᴇᴄᴏʀᴅ ɴᴀʜɪ ʜᴀɪ.")
        return

    custom_message = " ".join(args).strip() or DEFAULT_TAG_MESSAGE

    ACTIVE_CHATS.add(chat_id)
    task = asyncio.create_task(
        run_tagging(chat_id, context, members, mode, custom_message)
    )
    ACTIVE_TASKS[chat_id] = task

    await update.message.reply_text(
        f"🏷️ 𝐓ᴀɢᴀʟʟ sᴛᴀʀᴛᴇᴅ!\n"
        f"👥 𝐒ᴀᴠᴇᴅ 𝐌ᴇᴍʙᴇʀs: {len(members)}\n"
        f"🛑 /stop"
    )


# ==================================================
# BROADCAST — OWNER ONLY
# ==================================================

async def broadcast(update, context):
    await remember(update)

    user = update.effective_user

    if not update.message or not user or user.id != OWNER_ID:
        if update.message:
            await update.message.reply_text("⛔ 𝐎ᴡɴᴇʀ 𝐎ɴʟʏ!")
        return

    message = " ".join(context.args).strip()

    if not message:
        await update.message.reply_text(
            "📣 𝐔sᴀɢᴇ:\n/broadcast Your message here"
        )
        return

    user_ids = await asyncio.to_thread(get_broadcast_users)

    status = await update.message.reply_text(
        f"📣 𝐁ʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ!\n👥 𝐔sᴇʀs: {len(user_ids)}"
    )

    sent = 0
    failed = 0

    for user_id in user_ids:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
            )
            sent += 1

        except TelegramError:
            failed += 1

        await asyncio.sleep(BROADCAST_DELAY)

    await status.edit_text(
        f"╭━━〔 📣 〕━━╮\n"
        f"𝐁ʀᴏᴀᴅᴄᴀsᴛ 𝐃ᴏɴᴇ!\n\n"
        f"✅ 𝐒ᴇɴᴛ: {sent}\n"
        f"❌ 𝐅ᴀɪʟᴇᴅ: {failed}\n"
        f"╰━━━━━━━━━━╯"
    )


# ==================================================
# TRACK GROUP MEMBERS
# ==================================================

async def track_message(update, context):
    try:
        await remember(update)
    except Exception:
        logger.exception("Failed to record update")


# ==================================================
# STARTUP
# ==================================================

async def post_init(application):
    await asyncio.to_thread(init_db)
    logger.info("%s started successfully", BOT_NAME)


def main():
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("tagall", tagall))
    application.add_handler(CommandHandler("utag", utag))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("stats", stats))

    application.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern="^(help|profile)$",
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            all_alias,
        ),
        group=0,
    )

    application.add_handler(
        MessageHandler(
            filters.ALL,
            track_message,
        ),
        group=1,
    )

    logger.info("Starting %s...", BOT_NAME)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
