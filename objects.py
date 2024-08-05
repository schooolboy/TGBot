import config
import sqlite3
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Dispatcher
from aiogram import Bot

# подключение к СУБД
con = sqlite3.connect('bot_users.db')

# Объект бота
bot = Bot(config.token)
# Диспетчер
dp = Dispatcher()
# роутер
router = Router()
# Распределяем роутеры
dp.include_routers(router)

arr_sub = set()  # множество подписок EXMO

socket = None
