# (c) EDM115 - 2022

import os
import logging
from asyncio import sleep
from datetime import datetime, timedelta

from pyrogram import Client, enums, filters
from pyrogram.types import BotCommand, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait, RPCError

from config import *

banbot = Client(
        "banbot",
        api_id = Config.API_ID,
        api_hash = Config.API_HASH,
        bot_token = Config.BOT_TOKEN,
        sleep_threshold = 10
    )

"""
async def setCommands():
    banbot.set_bot_commands([
        BotCommand("start", "Useless"),
        BotCommand("help", "Useful"),
        BotCommand("fusrodah", "Actually what you need"),
        BotCommand("log", "For pro users only")])
"""

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
            await sleep(e.x)
        except RPCError as e:
            message.reply_text(e, quote=True)
            LOGGER.warn(f"Error in /log : {e}")

@banbot.on_message(filters.command("help"))
async def help_me(_, message: Message):
    await message.reply_text(text="""
Here is the help :

--Preconditions :--
    • Be an admin
    • Have "Ban members" rights
    • Same conditions for me, the bot

--Usage :--
    • Send `/fusrodah`
    • Choose if you want to **Ban** or **Kick all** the members excepting the admins
    • Let the bot do its job
    • If some errors happened, check the errors text file to manually ban/kick those users ID's

--Help :--
    You can contact the support here : **@EDM115_chat**
    Subscribe for more : **@EDM115bots**
    Source code : https://github.com/EDM115/ban-all-except-admins
    """)

class Buttons:
    CONFIRMATION = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Kick 🚪", callback_data="kick"),
                InlineKeyboardButton("Ban 🕳", callback_data="ban")
            ],
            [
                InlineKeyboardButton("Cancel ❌", callback_data="nope")
            ]
        ])

class Text:
    PROCESSING = """
Retrieving members of the chat… {}
Comparing with the admins of the chat… {}
{} members… {}/{} ({} errors)
    """

@banbot.on_callback_query()
async def callbacks(banbot: Client, query: CallbackQuery):
    cid = query.message.chat.id
    uid = query.from_user.id
    qid = query.message.id
    if query.data == "nope":
        return await query.edit_message_text("❌ Successfully canceled your task ✅")
    elif query.data == "kick":
        await justdoit("Kicking", 0, cid, uid, qid)
    elif query.data == "ban":
        await justdoit("Banning", 1, cid, uid, qid)

async def justdoit(text, mode, chat, user, query):
    await banbot.delete_messages(chat_id=chat, message_ids=query)
    memberslist = []
    action = banbot.send_message(chat_id=chat, text="`Processing… ⏳`")
    await action.edit(Text.PROCESSING.format("⏳", "⏳", text, 0, 0, 0))
    async for member in banbot.get_chat_members(chat_id=chat):
        memberslist.append(member)
        await action.edit(Text.PROCESSING.format(len(memberslist) + " members found", "⏳", text, 0, 0, 0))
    memberscount = len(memberslist)
    adminscount = len(adminlist)
    for member in range(memberscount):
        if memberslist[member] in adminlist:
            memberslist.pop(member)
    actioncount = memberscount - adminscount
    donecount = 0
    errorcount = 0
    errorlist = []
    await action.edit(Text.PROCESSING.format(memberscount + " members found", "Done ✅", text, donecount, actioncount, errorcount))
    for member in range(actioncount):
        try:
            useraction = memberslist[member].user.id
            if mode == 0:
                await banbot.ban_chat_member(chat_id=chat, user_id=useraction, until_date=datetime.now() + timedelta(seconds=31))
            elif mode == 1:
                await banbot.ban_chat_member(chat_id=chat, user_id=useraction)
            donecount+=1
        except FloodWait as f:
            await sleep(f.x)
            member-=1
        except Exception as e:
            LOGGER.warning(e)
            donecount+=1
            errorcount+=1
            errrorlist.append(useraction)
        await action.edit(Text.PROCESSING.format(memberscount + " members found", "Done ✅", text, donecount, actioncount, errorcount))
    if len(errorlist) > 0:
        errorfile = open(f"errors_{chat}.txt", "w")
        for item in errorlist:
            errorfile.write(item + "\n")
        errorfile.close()
        with open(f"errors_{chat}.txt", "rb") as doc_f:
            try:
                await banbot.send_document(
                    chat_id=chat,
                    document=doc_f,
                    file_name=doc_f.name
                )
                LOGGER.info(f"Log file sent to {chat}")
            except FloodWait as e:
                await sleep(e.x)
            except RPCError as e:
                message.reply_text(e, quote=True)
                LOGGER.warn(f"Error in /log : {e}")
        return await action.edit(f"Done ✅\nBanned {donecount} users, with {errorcount} errors. Check the file above to know which User ID's we failed to process")
    return await action.edit(f"Done ✅\nBanned {donecount} users")

@banbot.on_message(filters.command("fusrodah")) # & filters.group
async def being_devil(_, message: Message):
    if message.chat.type == enums.ChatType.GROUP or message.chat.type == enums.ChatType.SUPERGROUP:
        starter = message.from_user.id
        cid = message.chat.id
        LOGGER.info(f"{starter} started a task in {cid}")
        adminlist = []
        async for admin in banbot.get_chat_members(chat_id=cid, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            adminlist.append(admin)
        global adminlist2
        adminlist2 = adminlist.copy()
        for admin2 in adminlist:
            userinfo = adminlist[admin2]
            if userinfo.id != starter:
                adminlist.remove(userinfo) # or adminlist.pop(admin2)
            else:
                adminlist.append(starter)
        if starter in adminlist:
            admin3 = adminlist[0]
            if admin3.privileges.can_restrict_members == True:
                botid = Config.BOT_TOKEN.split(":")[0]
                selfuser = await banbot.get_chat_member(chat_id=cid, user_id=botid)
                if selfuser.privileges.can_restrict_members == True:
                    await message.reply("Confirm your action bro\nChoose either :\n• Kick all members except the admins\n• **Ban** all members except the admins\n• Cancel your task", reply_markup=Buttons.CONFIRMATION)
                else:
                    LOGGER.warning("Bot cannot ban members")
                    return message.reply("You need to add me as admin with the following scope : `can_restrict_members`\n__(Turn on \"Ban members\")__")
            else:
                LOGGER.warning("User cannot ban members")
                return message.reply("You are admin, but… You're missing the following scope : `can_restrict_members`\nAsk to a higher admin to give you the ability to ban members")
        else:
            LOGGER.warning("Not admin")
            return message.reply("You aren't admin 😐 Don't mess around with me")
    else:
        LOGGER.warning("Not in group")
        return message.reply("Bruh, do it in a group 😐\nI might be able to do it in channels soon, however I don't see any interest in it. PM **@EDM115** for requesting that feature")

# check if admin performed it
# check admin rights
# confirm by buttons
# start doing it
# note banned user ID’s in a log txt file
# retry on FloodWait
# send the log file to initiator (private)
# send message with stats

LOGGER.info("Bot started")
banbot.run()
