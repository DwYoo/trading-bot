#텔레그램 봇
from aiogram import Bot
from pubsub import pub
import asyncio

import os
from dotenv import load_dotenv
load_dotenv()
bot_token= os.getenv("TELEGRAM_BOT_TOKEN")


bot = Bot(token='token')

class TelegramAlert:
    # 특정 이벤트 발생 시 텔레그램으로 메시지 보냄
    def __init__(self, chat_ids):
        self.bot = bot
        self.chat_ids = chat_ids
        # pub.subscribe(self.on_balance_book_data, 'balance_data')

    def subscribe_to_singal(self, signal_name:str):
        pub.subscribe(self.on_signal, f"{signal_name} signal")

    async def send_message(self, text):
        for chat_id in self.chat_ids:
            try:
                await self.bot.send_message(chat_id, text)
            except Exception as e:
                print(f"Failed to send message: {e}")

    def on_signal(self, message):
        asyncio.create_task(self.send_message(message))

    # def on_balance_book_data(self, message):
    #     asyncio.create_task(self.send_message(message))

    # def on_trade(self, message):
    #     asyncio.create_task(self.send_message(message))



