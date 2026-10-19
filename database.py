from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from config import MONGO_DB_URI, MONGO_DB_NAME


# ==============================
# MONGODB CONNECTION
# ==============================

client = MongoClient(
    MONGO_DB_URI,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
)

db = client[MONGO_DB_NAME]

# Collections
users_collection = db["users"]
groups_collection = db["groups"]
members_collection = db["members"]


# ==============================
# DATABASE INITIALIZATION
# ==============================

def init_db():
    """Check MongoDB connection and create indexes."""

    try:
        client.admin.command("ping")

        users_collection.create_index("user_id", unique=True)
        groups_collection.create_index("chat_id", unique=True)

        members_collection.create_index(
            [("chat_id", 1), ("user_id", 1)],
            unique=True,
        )

        users_collection.create_index("opted_out")
        members_collection.create_index("chat_id")

        print("✅ MongoDB connected successfully!")
        print(f"📁 Database: {MONGO_DB_NAME}")

    except PyMongoError as exc:
        raise RuntimeError(
            f"MongoDB connection failed: {exc}"
        ) from exc


# ==============================
# SAVE USERS
# ==============================

def save_user(user):
    """Save a user who starts or interacts with the bot."""

    if not user or getattr(user, "is_bot", False):
        return

    users_collection.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "first_name": getattr(user, "first_name", "") or "",
                "username": getattr(user, "username", None),
                "last_seen": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "user_id": user.id,
                "started_at": datetime.now(timezone.utc),
                "opted_out": False,
            },
        },
        upsert=True,
    )


# ==============================
# SAVE GROUPS
# ==============================

def save_group(chat):
    """Save a group or supergroup."""

    if not chat or getattr(chat, "type", None) not in (
        "group",
        "supergroup",
    ):
        return

    groups_collection.update_one(
        {"chat_id": chat.id},
        {
            "$set": {
                "title": getattr(chat, "title", "") or "",
                "chat_type": str(chat.type),
                "last_seen": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "chat_id": chat.id,
                "added_at": datetime.now(timezone.utc),
            },
        },
        upsert=True,
    )


# ==============================
# SAVE GROUP MEMBERS
# ==============================

def save_member(chat_id, user):
    """Save a member the bot has actually observed."""

    if not user or getattr(user, "is_bot", False):
        return

    members_collection.update_one(
        {
            "chat_id": chat_id,
            "user_id": user.id,
        },
        {
            "$set": {
                "first_name": getattr(user, "first_name", "") or "",
                "username": getattr(user, "username", None),
                "last_seen": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "chat_id": chat_id,
                "user_id": user.id,
                "added_at": datetime.now(timezone.utc),
            },
        },
        upsert=True,
    )


# ==============================
# BROADCAST USERS
# ==============================

def get_broadcast_users():
    """Return users who have not opted out."""

    cursor = users_collection.find(
        {"opted_out": {"$ne": True}},
        {"_id": 0, "user_id": 1},
    )

    return [document["user_id"] for document in cursor]


# ==============================
# GROUP MEMBERS
# ==============================

def get_group_members(chat_id):
    """Return members known to this bot for a group."""

    cursor = members_collection.find(
        {"chat_id": chat_id},
        {
            "_id": 0,
            "user_id": 1,
            "first_name": 1,
            "username": 1,
        },
    )

    return list(cursor)


# ==============================
# STATISTICS
# ==============================

def get_stats():
    """Return total saved users and groups."""

    total_users = users_collection.count_documents(
        {"opted_out": {"$ne": True}}
    )

    total_groups = groups_collection.count_documents({})

    return total_users, total_groups


# ==============================
# USER OPT-OUT
# ==============================

def opt_out_user(user_id):
    """Allow a user to stop receiving broadcasts."""

    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"opted_out": True}},
    )


def opt_in_user(user_id):
    """Allow a user to receive broadcasts again."""

    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"opted_out": False}},
    )
