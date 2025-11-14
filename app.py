# app.py
import os
import asyncio
from fastapi import FastAPI
from main import bot  # Import your existing Bot instance

import uvicorn

app = FastAPI()

# Simple health check endpoint
@app.get("/")
async def root():
    return {"status": "Bot is running"}

# Start the bot in the background on startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(bot.start())

# Stop the bot gracefully on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await bot.stop()

# Run Uvicorn server if executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
