import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from app.bot import app as telegram_app

server = Flask(__name__)

@server.route('/')
def health_check():
    return "Bot is active!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    server.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    t = Thread(target=run_web_server)
    t.start()

    print("Starting Telegram Bot...")
    
    telegram_app.run_polling()