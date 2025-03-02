import os
import math
import logging
import datetime
import pytz
import logging.config
import asyncio
from aiohttp import web, ClientSession
from pyrogram import Client, types
from database.users_chats_db import db
from database.ia_filterdb import Media
from typing import Union, Optional, AsyncGenerator
from utils import temp, __repo__, __license__, __copyright__, __version__
from info import API_ID, API_HASH, BOT_TOKEN, LOG_CHANNEL, UPTIME, WEB_SUPPORT, LOG_MSG

# Get logging configurations
logging.config.fileConfig("logging.conf")
logging.getLogger(__name__).setLevel(logging.INFO)
logging.getLogger("cinemagoer").setLevel(logging.ERROR)


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Professor-Bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats

        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.id = me.id
        self.name = me.first_name
        self.mention = me.mention
        self.username = me.username
        self.log_channel = LOG_CHANNEL
        self.uptime = UPTIME
        curr = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        date = curr.strftime("%d %B, %Y")
        time = curr.strftime("%I:%M:%S %p")
        logging.info(
            LOG_MSG.format(me.first_name, date, time, __repo__, __version__, __license__, __copyright__)
        )

        try:
            await self.send_message(
                LOG_CHANNEL,
                text=LOG_MSG.format(me.first_name, date, time, __repo__, __version__, __license__, __copyright__),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logging.warning(f"Bot Isn't Able To Send Message To LOG_CHANNEL \n{e}")

        if bool(WEB_SUPPORT) is True:
            app = web.Application(client_max_size=30000000)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", 8080)
            await site.start()
            logging.info("Web Response Is Running......🕸️")

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot Is Restarting ⟳...")

    async def iter_messages(
        self, chat_id: Union[int, str], limit: int, offset: int = 0
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current + new_diff + 1)))
            for message in messages:
                yield message
                current += 1


URL = "https://scattered-catlaina-unknownr-5093cdff.koyeb.app/"  # Replace with your koyeb app link...


async def ping():
    async with ClientSession() as session:
        while True:
            try:
                async with session.get(URL) as response:
                    print(f"Pinged server, status: {response.status}")
            except Exception as e:
                print(f"{e}")
            await asyncio.sleep(600)


loop = asyncio.get_event_loop()
loop.create_task(ping())

Bot().run()
