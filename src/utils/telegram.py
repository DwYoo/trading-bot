#텔레그램 봇
from aiogram import Bot
from pubsub import pub
import asyncio

import os
from dotenv import load_dotenv

from base.Events import Events

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

class TelegramAlert:
    # 특정 이벤트 발생 시 텔레그램으로 메시지 보냄
    def __init__(self, chat_ids):
        self.bot = bot
        self.chat_ids = chat_ids
        pub.subscribe(self._on_event, Events.BALANCE_UPDATED.value)
        pub.subscribe(self._on_event, Events.ORDER_CREATED.value)
    async def send_message(self, text):
        for chat_id in self.chat_ids:
            try:
                await self.bot.send_message(chat_id, text)
            except Exception as e:
                print(f"Failed to send message: {e}")

    def subscribe_to_singal(self, signal_name:str):
        pub.subscribe(self._on_event, signal_name)

    def _on_event(self, message):
        asyncio.create_task(self.send_message(message))

telegram_alert = TelegramAlert(chat_ids=[os.getenv("TELEGRAM_CHAT_ID_1")])



