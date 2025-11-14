"""
Telegraph Uploader Bot

This module defines a Telegram bot that can upload photos to imgBB / envs.sh and
create instant view links for text messages.
The bot is built using the Pyrogram library and the Telegraph API.

Features:
- Upload photos to imgBB / envs.sh and return the URL.
- Create graph.org posts from text messages, with support for custom titles and emoji removal.

Classes:
- Bot: A subclass of Pyrogram's Client, representing the Telegram bot.

Functions:
- start_handlers: Handles the /start command to provide a welcome message.
- photo_handler: Handles incoming photo messages, uploads them to imgBB / envs.sh,
                 and sends the URL to the user.
- text_handler: Handles incoming text messages, creates graph.org posts,
                and sends the URL to the user.

Patterns:
- EMOJI_PATTERN: Regular expression to match <emoji> tags in the text.
- TITLE_PATTERN: Regular expression to match title lines in the text.

Usage:
1. Send a /start command to receive a welcome message.
2. Send a photo to upload it to imgBB / envs.sh and get the link.
3. Send a text message in the format
        Title: {title}
        {content}
    to create a Telegra.ph post.
"""

import logging
import logging.config

# ----------------------
# Logging configuration
# ----------------------
logging.config.fileConfig("logging.conf")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

import os
import re
import time

import requests
from telegraph import Telegraph
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from utils import progress

try:
    import uvloop  # optional speedup
    uvloop.install()
except ImportError:
    pass


# ----------------------
# Bot class
# ----------------------
class Bot(Client):
    """Telegram bot client for uploading photos and creating posts on Telegra.ph."""

    def __init__(self):
        super().__init__(
            "telegraph",
            bot_token=Config.BOT_TOKEN,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
        )

    async def start(self):
        Config.validate()
        await super().start()
        logger.info("Bot started successfully at @%s", self.me.username)
        logger.debug("Full bot info: %s", self.me)

    async def stop(self, *args, **kwargs):
        await super().stop(*args, **kwargs)
        logger.info("Bot session stopped gracefully.")


bot = Bot()
EMOJI_PATTERN = re.compile(r'<emoji id="\d+">')
TITLE_PATTERN = re.compile(r"title:? (.*)", re.IGNORECASE)


# ----------------------
# Handlers
# ----------------------
@bot.on_message(filters.command("start") & filters.incoming & filters.private)
async def start_handlers(_: Bot, message: Message) -> None:
    await message.reply(
        text=(
            f"👋 **Hello {message.from_user.mention}!**\n\n"
            "✨ Welcome to the **Telegraph Uploader Bot!**\n\n"
            "With me, you can:\n"
            "📸 **Upload Photos** → Send me any photo, and I'll upload it to **ImgBB** or **Envs.sh** with a direct shareable link.\n"
            "📝 **Create Instant View Posts** → Send me text in a simple format, and I’ll create a stylish post on **Graph.org** (Telegraph alternative).\n\n"
            "📌 **Usage**:\n"
            "• Send a **photo** directly → Get ImgBB/Envs.sh link.\n"
            "• Send a **text** in the following format → Get Graph.org post.\n\n"
            "📝 **Custom Title**:\n"
            "```txt\n"
            "Title: {title}\n{content}\n"
            "```\n\n"
            "✅ **Example**:\n"
            "```txt\n"
            "Title: My First Graph.org Post\n"
            "This is the content of my first post!\n\n"
            "Here's a list of what I like:\n"
            "- Programming 💻\n"
            "- Reading 📚\n"
            "- Traveling ✈️\n"
            "- Music 🎵\n"
            "```\n\n"
            "🌟 **Get Started Now!** Just send a photo or formatted text message and let me handle the rest 🚀"
        ),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "👨‍💻 My Creator", url="https://t.me/The_proGrammerr"
                    ),
                    InlineKeyboardButton(
                        "🛠 Source Code",
                        url="https://github.com/Ns-AnoNymouS/Telegraph-Uploader",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "📌 Updates", url="https://t.me/NsBotsOfficial"
                    ),
                    InlineKeyboardButton("❤️ Support", url="https://t.me/amcDevSupport"),
                ],
            ]
        ),
        quote=True,
    )


def upload_file(file_path):
    imgbb_key = getattr(Config, "IMGBB_API_KEY", None)
    # Try ImgBB first
    if imgbb_key:
        try:
            with open(file_path, "rb") as f:
                files = {"image": f}
                response = requests.post(
                    "https://api.imgbb.com/1/upload",
                    params={"key": imgbb_key},
                    files=files,
                    timeout=15,
                )
            if response.ok:
                data = response.json()["data"]
                return {"provider": "imgbb", "url": data["url"], "delete_url": data.get("delete_url")}
        except Exception:
            pass
    # Fallback: envs.sh
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post("https://envs.sh", files=files, timeout=15)
        if response.ok:
            url = response.text.strip()
            return {"provider": "envs.sh", "url": url}
    except Exception:
        pass
    return None


@bot.on_message(filters.photo & filters.incoming & filters.private)
async def photo_handler(_: Bot, message: Message) -> None:
    msg = await message.reply_text("Processing....⏳", quote=True)
    location = f"./{message.from_user.id}{time.time()}/"
    os.makedirs(location, exist_ok=True)
    file = await message.download(location, progress=progress, progress_args=(msg, time.time()))
    media_data = upload_file(file)
    if media_data:
        await msg.edit(f"✅ Upload Successful!\n{media_data['url']}")
    else:
        await msg.edit("⚠️ Upload failed.")
    os.remove(file)
    os.rmdir(location)


@bot.on_message(filters.text & filters.incoming & filters.private)
async def text_handler(_: Bot, message: Message) -> None:
    msg = await message.reply_text("Processing....⏳", quote=True)
    try:
        user = Telegraph(domain=Config.DOMAIN).create_account(short_name="Ns Bots")
        access_token = user.get("access_token")
        content = message.text.html
        content = re.sub(EMOJI_PATTERN, "", content).replace("</emoji>", "")
        title = re.findall(TITLE_PATTERN, content)
        title = title[0] if title else message.from_user.first_name
        content = "\n".join(content.splitlines()[1:]).replace("\n", "<br>")
        response = Telegraph(domain=Config.DOMAIN, access_token=access_token).create_page(
            title=title,
            html_content=content,
            author_name=str(message.from_user.first_name),
        )
        path = response["path"]
        await msg.edit(f"https://{Config.DOMAIN}/{path}")
    except Exception:
        await msg.edit("Unable to generate instant view link.")


# ----------------------
# Start bot + web server
# ----------------------
if __name__ == "__main__":
    import asyncio
    from aiohttp import web

    async def handle_root(request):
        return web.Response(
            text="""
            <body style="background-color:black; color:#39FF14; display:flex; 
            justify-content:center; align-items:flex-start; height:100vh; 
            margin:0; font-family:sans-serif; padding-top:20vh; font-size:4rem;">
                Coded By @MyselfNeon
            </body>
            """,
            content_type="text/html"
        )

    async def start_web_server():
        app = web.Application()
        app.add_routes([web.get("/", handle_root)])
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get("PORT", 8080))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        print(f"Web server running on port {port}")

    async def main_async():
        # Start web server and bot concurrently
        await asyncio.gather(
            start_web_server(),
            bot.start(),  # keeps your bot running
        )
        print(f"Bot started successfully at @{bot.me.username}")

        # Keep bot alive
        while True:
            await asyncio.sleep(3600)

    asyncio.run(main_async())
