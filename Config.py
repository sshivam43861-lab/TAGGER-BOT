import os

# ==============================
# BOT CONFIGURATION
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

OWNER_ID = int(os.getenv("OWNER_ID", "0"))

BOT_NAME = "𝐓ᴀɢɢᴇʀ 𝐁ᴏᴛ"


# ==============================
# MONGODB CONFIGURATION
# ==============================

MONGO_DB_URI = os.getenv("MONGO_DB_URI", "").strip()

MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "tagger_bot").strip()


# ==============================
# TAGGING CONFIGURATION
# ==============================

DEFAULT_TAG_MESSAGE = os.getenv(
    "DEFAULT_TAG_MESSAGE",
    "𝐇ᴇʏ ᴇᴠᴇʀʏᴏɴᴇ! 🪽 ᴡʜᴇʀᴇ ᴀʀᴇ ʏᴏᴜ ᴀʟʟ? 👀✨"
)

TAG_DELAY = float(os.getenv("TAG_DELAY", "2.5"))

UTAG_DELAY = float(os.getenv("UTAG_DELAY", "3.0"))

BROADCAST_DELAY = float(os.getenv("BROADCAST_DELAY", "0.1"))


# ==============================
# RENDER CONFIGURATION
# ==============================

PORT = int(os.getenv("PORT", "10000"))


# ==============================
# VALIDATION
# ==============================

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN missing! Set it in Render Environment Variables."
    )

if OWNER_ID <= 0:
    raise RuntimeError(
        "OWNER_ID missing! Set your numeric Telegram ID in Render."
    )

if not MONGO_DB_URI:
    raise RuntimeError(
        "MONGO_DB_URI missing! Set it in Render Environment Variables."
    )

if not MONGO_DB_NAME:
    raise RuntimeError(
        "MONGO_DB_NAME cannot be empty."
    )
