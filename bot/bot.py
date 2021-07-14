import os
from aiogram import Bot

API_TOKEN = os.environ.get('BOT_TOKEN', '')

bot = Bot(token=API_TOKEN, parse_mode='HTML')
