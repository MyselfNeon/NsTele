import os
import threading
from flask import Flask
from main import bot  # Your Pyrogram Bot instance

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <body style="background-color:black; color:#39FF14; display:flex; justify-content:center; align-items:flex-start; height:100vh; margin:0; font-family:sans-serif; padding-top:20vh; font-size:4rem;">
        Coded By @MyselfNeon
    </body>
    """

def run_bot():
    bot.run()  # Starts your Pyrogram bot and blocks

if __name__ == "__main__":
    # Start the bot in a daemon thread so Flask can run in main thread
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Start Flask server on the Render-required port
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
