import asyncio
import os
from io import BytesIO
from uuid import uuid4
from typing import Callable

from aiogram import Dispatcher
from aiogram.types import ContentType, Message

from telethon.client import TelegramClient
from telethon.sessions.string import StringSession

API_ID = os.environ.get('API_ID', '')
API_HASH = os.environ.get('API_HASH', '')

CLIENT_SESSION = os.environ.get('CLIENT_SESSION', '')


class Sender:

    def __init__(self, dp: Dispatcher) -> None:
        self.dp: Dispatcher = dp
        self.responses = {}

        self.dp.message_handler(
            content_types=[ContentType.DOCUMENT])(self.on_file)

    async def on_file(self, message: Message):
        response = self.responses.pop(message.caption)
        if response:
            response.set_result(message.document.file_id)

    async def send_file(self, file: BytesIO, progress_callback: Callable = None) -> str:
        async with TelegramClient(StringSession(CLIENT_SESSION), API_ID, API_HASH, timeout=1000) as client:

            client: TelegramClient

            bot = await self.dp.bot.get_me()

            file_id = str(uuid4())

            await client.send_file(f'@{bot.username}', file=file, caption=file_id, progress_callback=progress_callback)

            future = asyncio.Future()
            self.responses[file_id] = future
            return await future
