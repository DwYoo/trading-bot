#텔레그램 봇
from aiogram import Bot
from pubsub import pub
import asyncio


#다 바꿀 예정
class TelegramBot:
    def __init__(self, token, chat_ids):
        self.bot = Bot(token)
        self.chat_ids = chat_ids

    async def send_message(self, text):
        for chat_id in self.chat_ids:
            try:
                await self.bot.send_message(chat_id, text)
            except Exception as e:
                print(f"Failed to send message: {e}")

    def on_balance_book_data(self, message):
        asyncio.create_task(self.send_message(message))

    def on_trade(self, message):
        asyncio.create_task(self.send_message(message))



