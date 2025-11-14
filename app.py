import os
import asyncio
from aiohttp import web
from main import bot  # Your Pyrogram Bot instance

# ---------- Web server ----------
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root(request):
    return web.Response(
        text="""
        <body style="background-color:black; color:#39FF14; display:flex; justify-content:center; align-items:flex-start; height:100vh; margin:0; font-family:sans-serif; padding-top:20vh; font-size:4rem;">
            Coded By @MyselfNeon
        </body>
        """,
        content_type="text/html"
    )

async def start_web():
    app = web.Application()
    app.add_routes(routes)
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server running on port {port}")

# ---------- Main ----------
async def main():
    # Start the web server
    await start_web()
    # Start the bot
    await bot.start()
    print(f"Bot started successfully at @{bot.me.username}")
    # Keep the loop alive indefinitely
    while True:
        await asyncio.sleep(3600)  # sleep 1h, repeat

if __name__ == "__main__":
    asyncio.run(main())
