import os
import threading
from flask import Flask
from main import bot  # your Bot instance

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <body style="background-color:black; color:#39FF14; display:flex; justify-content:center; align-items:flex-start; height:100vh; margin:0; font-family:sans-serif; padding-top:20vh; font-size:4rem;">
        Coded By @MyselfNeon
    </body>
    """

# Function to start the Pyrogram bot
def run_bot():
    bot.run()  # this blocks and keeps bot running

if __name__ == "__main__":
    # Start the bot in a background daemon thread
    threading.Thread(target=run_bot, daemon=True).start()

    # Start Flask web server (Render needs port binding)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
