"""
Telegraph Uploader Bot

This module defines a Telegram bot that can upload photos to imgBB / envs.sh and
create instant view links for text messages.
"""

import logging
import logging.config
import os
import re
import time
import asyncio
import requests
import aiohttp
from telegraph import Telegraph
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

from config import Config, KEEP_ALIVE_URL
from utils import progress

# Logging setup
logging.config.fileConfig("logging.conf")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Optional speedup
try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

# Regex patterns
EMOJI_PATTERN = re.compile(r'<emoji id="\d+">')
TITLE_PATTERN = re.compile(r"title:? (.*)", re.IGNORECASE)

# ---------------- Bot Class ----------------
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

# ---------------- Handlers ----------------
@bot.on_message(filters.command("start") & filters.incoming & filters.private)
async def start_handlers(_: Bot, message: Message) -> None:
    logger.debug("Received /start from %s", message.from_user.first_name)
    await message.reply(
        text=(
            f"👋 **Hello {message.from_user.mention}!**\n\n"
            "✨ Welcome to the **Telegraph Uploader Bot!**\n\n"
            "📸 Upload Photos → ImgBB / Envs.sh\n"
            "📝 Create Graph.org posts from text.\n"
        ),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👨‍💻 My Creator", url="https://t.me/The_proGrammerr"),
                    InlineKeyboardButton("🛠 Source Code", url="https://github.com/Ns-AnoNymouS/Telegraph-Uploader"),
                ],
                [
                    InlineKeyboardButton("📌 Updates", url="https://t.me/NsBotsOfficial"),
                    InlineKeyboardButton("❤️ Support", url="https://t.me/amcDevSupport"),
                ],
            ]
        ),
        quote=True,
    )

def upload_file(file_path):
    """Uploads a file to ImgBB (if API key) or falls back to envs.sh."""
    imgbb_key = getattr(Config, "IMGBB_API_KEY", None)
    logger.debug("Uploading file: %s", file_path)

    # Try ImgBB
    if imgbb_key:
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    "https://api.imgbb.com/1/upload",
                    params={"key": imgbb_key},
                    files={"image": f},
                    timeout=15,
                )
            if response.ok:
                data = response.json()["data"]
                return {"provider": "imgbb", "url": data["url"], "delete_url": data.get("delete_url")}
            else:
                logger.warning("ImgBB upload failed: %s", response.text)
        except Exception as e:
            logger.error("ImgBB upload error: %s", e, exc_info=True)

    # Fallback: envs.sh
    try:
        with open(file_path, "rb") as f:
            response = requests.post("https://envs.sh", files={"file": f}, timeout=15)
        if response.ok:
            url = response.text.strip()
            logger.info("File uploaded to envs.sh: %s", url)
            return {"provider": "envs.sh", "url": url}
        else:
            logger.error("envs.sh upload failed: %s", response.text)
    except Exception as e:
        logger.critical("All upload methods failed: %s", e, exc_info=True)

@bot.on_message(filters.photo & filters.incoming & filters.private)
async def photo_handler(_: Bot, message: Message):
    try:
        msg = await message.reply_text("Processing....⏳", quote=True)
        location = f"./{message.from_user.id}{time.time()}/"
        file = await message.download(location, progress=progress, progress_args=(msg, time.time()))
        await msg.edit("📥 Download complete! Uploading to cloud...")
        media_data = upload_file(file)
        if not media_data:
            await msg.edit("⚠️ Upload failed.")
            return
        buttons = [[InlineKeyboardButton("🌐 View Image", url=media_data["url"])]]
        if media_data.get("delete_url"):
            buttons.append([InlineKeyboardButton("🗑️ Delete Image", url=media_data["delete_url"])])
        text = f"✅ Upload Successful!\n📡 Provider: {media_data['provider']}\n🔗 Link: {media_data['url']}"
        await msg.edit(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        logger.error(e)
        await msg.edit(f"**Error:** {e}")
    finally:
        if os.path.exists(file):
            os.remove(file)
            os.rmdir(location)

@bot.on_message(filters.text & filters.incoming & filters.private)
async def text_handler(_: Bot, message: Message):
    try:
        msg = await message.reply_text("Processing....⏳", quote=True)
        short_name = "Ns Bots"
        user = Telegraph(domain=Config.DOMAIN).create_account(short_name=short_name)
        access_token = user.get("access_token")
        content = re.sub(EMOJI_PATTERN, "", message.text.html).replace("</emoji>", "")
        title = re.findall(TITLE_PATTERN, content)
        title = title[0] if title else message.from_user.first_name
        if title and "\n" in content:
            content = "\n".join(content.splitlines()[1:])
        content = content.replace("\n", "<br>")
        author_url = f"https://telegram.dog/{message.from_user.username}" if message.from_user.username else None
        path = Telegraph(domain=Config.DOMAIN, access_token=access_token).create_page(
            title=title,
            html_content=content,
            author_name=str(message.from_user.first_name),
            author_url=author_url,
        )["path"]
        await msg.edit(f"https://{Config.DOMAIN}/{path}")
    except Exception as e:
        logger.error(e)
        await msg.edit(f"**Error:** {e}")

# ---------------- Keep-Alive ----------------
async def keep_alive():
    if not KEEP_ALIVE_URL:
        logger.warning("KEEP_ALIVE_URL not set.")
        return
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(KEEP_ALIVE_URL) as resp:
                    if resp.status == 200:
                        logger.info("✅ Keep-alive successful")
                    else:
                        logger.warning(f"⚠️ Keep-alive returned {resp.status}")
            except Exception as e:
                logger.error(f"❌ Keep-alive failed: {e}")
            await asyncio.sleep(300)

# ---------------- Web Server ----------------
async def handle_root(request):
    return web.Response(
        text='<body style="background:black;color:#39FF14;display:flex;justify-content:center;align-items:flex-start;height:100vh;margin:0;font-family:sans-serif;padding-top:20vh;font-size:4rem;">Coded By @MyselfNeon</body>',
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
    logger.info("Web server running on port %s", port)

# ---------------- Main ----------------
async def main():
    # Start keep-alive and web server
    if KEEP_ALIVE_URL:
        asyncio.create_task(keep_alive())
        logger.info("🌐 Keep-alive task started.")
    asyncio.create_task(start_web_server())

    # Start bot
    await bot.start()
    logger.info("Bot started successfully")

    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
