import sqlite3
from objects import *


def db_start():
    if con:
        print('SQLite Connected')
        res = con.execute("SELECT * FROM sqlite_master where name='user_currency_pair'")
        if res.fetchone() is None:  # если не найдено
            con.execute('CREATE TABLE user_currency_pair(user_id TEXT NOT NULL, pair_code TEXT NOT NULL,' +
                        'await_rate REAL NOT NULL, trend INTEGER NOT NULL, PRIMARY KEY (user_id, pair_code, trend))')
            con.commit()
    else:
        print('Error: SQLite not connected')


def db_close():
    con.close()


# добавить или изменить подписку пользователя
def add_upd_sub(user_id, pair_code, await_rate, trend):
    res = con.execute(f"SELECT * FROM user_currency_pair WHERE user_id = '{user_id}' AND pair_code = '{pair_code}' AND trend = {trend}")
    try:
        if res.fetchone() is None:  # если записей нету то добавляем
            con.execute(f"INSERT INTO user_currency_pair VALUES('{user_id}','{pair_code}', {await_rate}, {trend})")
            con.commit()
            return "Подписка добавлена"
        else:  # если запись есть то обновляем
            con.execute(f"UPDATE user_currency_pair SET await_rate = {await_rate} WHERE user_id = '{user_id}' and pair_code = '{pair_code}' AND trend = {trend}")
            con.commit()
            return 'Подписка обновлена'
    except sqlite3.Error:
        print(sqlite3.Error)
        return 'Ошибка во время добавления/обновления подписки'


# удалить подписку пользователя
def del_sub(user_id, pair_code, trend='0'):
    try:
        if trend == '0':
            con.execute(f"DELETE FROM user_currency_pair WHERE user_id = '{user_id}' AND pair_code = '{pair_code}'")
        else:
            con.execute(
                f"DELETE FROM user_currency_pair WHERE user_id = '{user_id}' AND pair_code = '{pair_code}' AND trend = {trend}")
        con.commit()
        return 'Подписка удалена'
    except sqlite3.Error:
        print(sqlite3.Error)
        return 'Ошибка при удалении подписки'


def get_sub(user_id):
    rows = con.execute(f'SELECT pair_code, trend, await_rate FROM user_currency_pair WHERE user_id = {user_id}')
    strres = '\n'
    trend = 'меньше'
    for row in rows.fetchall():
        if str(row[1]) == '1':
            trend = 'больше'
        strres += f'\nПара {row[0]} {trend} {row[2]}\n'
        trend = 'меньше'
    return strres
