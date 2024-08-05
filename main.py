import json.decoder
import asyncio
import websockets
import logging
import tbot
import time
from dbWork import db_start
from market import listen
from objects import *

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)


async def main():
    task1 = asyncio.create_task(listen())
    task2 = asyncio.create_task(dp.start_polling(bot, none_stope=True))
    while True:
        try:
            await task1
        except websockets.exceptions.ConnectionClosed as ex:
            print("connection closed" + str(ex))
            await bot.stop_polling
            arr_sub.clear()
            time.sleep(3)
        try:
            await task2
        except Exception as ex:
            print("Bot exception" + str(ex))
            arr_sub.clear()
            await socket.close()
            arr_sub.clear()
            time.sleep(3)


if __name__ == "__main__":
    db_start()
    asyncio.run(main())
