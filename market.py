import json.decoder
import websockets
from objects import *
from dbWork import *


# слушатель сообщений
async def listen():
    async with websockets.connect(config.url) as exmo_socket:
        global socket, arr_sub
        socket = exmo_socket
        counter = 0  # счетчик апдейтов (чтоб не спамил слишком часто)
        rows = con.execute(f"SELECT DISTINCT pair_code FROM user_currency_pair")
        for x in rows.fetchall():
            arr_sub.add(x[0])
            await subscribe(x[0])
        while True:
            res = json.loads(await exmo_socket.recv())  # слушаем апдейты
            if res['event'] == 'update':
                counter = counter + 1
                if counter % 10 == 0:
                    await broadcast(res['topic'].replace("spot/ticker:", ""), res['data']['avg'])  # передаем в рассылку
                if counter > 1000:
                    counter = 0
            elif res['event'] == 'error':
                if res['id'] != 1 and res['message'].find('pair is not exists') != -1: # передана несуществующая пара
                    pair = res['message'].replace("pair is not exists, pair: ", "")[1:-1] # с помощью replace и среза выделяем валютную пару
                    result = del_sub(res['id'], pair)
                    await bot.send_message(res['id'], f"Пары {pair} нет на сайте" + f"\n{result}")
                    arr_sub.remove(pair)
                else:
                    print('\nНеизвестная ошибка')
                    print('\n' + res['message'] + ' id: ' + str(res['id']))
            elif res['event'] == 'info' and res['message'] == 'maintenance in progress':
                #  биржа на обслуживании, завершить работу
                await exmo_socket.close()
                db_close()
                return
            elif res['event'] == 'subscribed':
                print('\nsubscribed topic ' + res['topic'].replace("spot/ticker:", ""))
            elif res['event'] == 'unsubscribed':
                print('\nunsubscribed topic ' + res['topic'].replace("spot/ticker:", ""))
            else:
                await exmo_socket.pong()  # отправляем pong кадры, чтобы соединение не было прервано сервером


async def subscribe(pair_code, user_id=1):
    await socket.send(["""{"id":""" + str(user_id) + ""","method":"subscribe","topics":["spot/ticker:""" + pair_code + """"]}"""])


async def unsubscribe(pair_code):
    await socket.send(["""{"id":1,"method":"unsubscribe","topics":["spot/ticker:""" + pair_code + """"]}"""])


# рассылка сообщений пользователям
async def broadcast(pair_code, rate):
    users = con.execute(f"SELECT user_id, await_rate, trend FROM user_currency_pair WHERE pair_code = '{pair_code}'")
    count = 0
    for user in users.fetchall():  # для каждого пользователя отправляем сообщения если они подписан на валюту
        count += 1
        user_id = user[0]
        await_rate = user[1]
        trend = user[2]
        if trend == 1:
            if float(rate) > await_rate:
                await bot.send_message(user_id, f"Курс пары {pair_code} превысил {await_rate}\nТекущее значение: {rate}.\n\nПодписка удалена")
                del_sub(user_id, pair_code, trend)
                count -= 1
        else:
            if float(rate) < await_rate:
                await bot.send_message(user_id, f"Курс пары {pair_code} стал меньше чем {await_rate}\nТекущее значение: {rate}.\n\nПодписка удалена")
                del_sub(user_id, pair_code, trend)
                count -= 1
    if count == 0:
        await unsubscribe(pair_code)
        arr_sub.remove(pair_code)
