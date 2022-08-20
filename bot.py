# (c) EDM115 - 2022

import os
import logging
from pyrogram import Client, enums, filters
from pyrogram.types import BotCommand, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait, RPCError
# import pyromod.listen
from config import *

banbot = Client(
        "banbot",
        api_id = Config.API_ID,
        api_hash = Config.API_HASH,
        bot_token = Config.BOT_TOKEN,
        sleep_threshold = 10
    )

async def setCommands():
    banbot.set_bot_commands([
        BotCommand("start", "Useless"),
        BotCommand("log", "Send you the logs, in case it's needed")])

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler('logs.txt'), logging.StreamHandler()],
    format="%(asctime)s - %(levelname)s - %(name)s - %(threadName)s - %(message)s"
)
LOGGER = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARN)

@banbot.on_message(filters.command("start"))
async def start_bot(_, message: Message):
    await message.reply_text(text="**Hello {} 👋**".format(message.from_user.mention), disable_web_page_preview=True)

@banbot.on_message(filters.command("log"))
async def send_logs(_, message: Message):
    with open('logs.txt', 'rb') as doc_f:
        try:
            await banbot.send_document(
                chat_id=message.chat.id,
                document=doc_f,
                file_name=doc_f.name,
                reply_to_message_id=message.id
            )
            LOGGER.info(f"Log file sent to {message.from_user.id}")
        except FloodWait as e:
            sleep(e.x)
        except RPCError as e:
            message.reply_text(e, quote=True)
            LOGGER.warn(f"Error in /log : {e}")

@banbot.on_message(filters.command("help"))
async def help_me(_, message: Message):
    await message.reply_text(text="This is help text")

class Buttons:
    CONFIRMATION = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅", callback_data="yessir"),
                InlineKeyboardButton("❌", callback_data="nope")
            ]
        ])

@banbot.on_callback_query()
async def callbacks(banbot: Client, query: CallbackQuery):
    cid = query.chat.id
    if query.data == "nope":
        await query.edit_message_text(text="yes")

@banbot.on_message(filters.command("ban"))
async def help_me(_, message: Message):
    await message.reply_text(text="🚧")
    if message.chat.type == enums.GROUP or message.chat.type == enums.SUPERGROUP:
        starter = message.from_user.id
        cid = message.chat.id
        adminlist = []
        async for admin in banbot.get_chat_members(chat_id=cid, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            adminlist.append(admin)
        for admin2 in adminlist:
            userinfo = adminlist[admin2]
            if userinfo.id != starter:
                adminlist.remove(userinfo) # or adminlist.pop(admin2)
            else:
                adminlist.append(starter)
        if starter in adminlist:
            admin3 = adminlist[0]
            if admin3.privileges.can_restrict_members == True:
                await message.reply("Are you sure you wanna ban everyone excepting the admins ?", reply_markup=Buttons.CONFIRMATION)

# check if admin performed it
# check admin rights
# confirm by buttons
# start doing it
# note banned user ID’s in a log txt file
# retry on FloodWait
# send the log file to initiator (private)
# send message with stats

LOGGER.info("Bot started")
await setCommands()
banbot.run()
