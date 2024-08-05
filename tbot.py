from dbWork import add_upd_sub, del_sub, get_sub
from objects import *
from market import *


bt1 = KeyboardButton(text="Добавить подписку")
bt2 = KeyboardButton(text="Удалить подписку")
bt3 = KeyboardButton(text="Мои подписки")
placeholder1 = "Выберите действие"
btns1 = list([list([bt1, bt2, bt3])])
keyboard_main = types.ReplyKeyboardMarkup(keyboard=btns1, resize_keyboard=True, input_field_placeholder=placeholder1)


bt4 = KeyboardButton(text="Больше")
bt5 = KeyboardButton(text="Меньше")
placeholder2 = "Выберите тип сравнения"
btns2 = list([list([bt4, bt5])])
keyboard_add = types.ReplyKeyboardMarkup(keyboard=btns2, resize_keyboard=True, input_field_placeholder=placeholder2)


class FSMadd(StatesGroup):
    pair = State()
    trend = State()
    await_rate = State()


# машина состояний удаления подписки
class FSMdel(StatesGroup):
    pair = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Добро пожаловать в бот EXMO оповощений", reply_markup=keyboard_main)


@router.message(F.text == 'Добавить подписку', StateFilter(None))
async def message_add(message: Message, state: FSMContext):
    await state.set_state(FSMadd.pair)
    await state.set_data({'pair': '', 'trend': 0, 'await_rate': 0})
    await message.answer('Введите валютную пару в формате xxx(x)-xxx(x)', reply_markup=keyboard_main)


@router.message(StateFilter(FSMadd.pair))
async def message_add_pair(message: Message, state: FSMContext):
    await state.update_data({'pair': message.text.upper().replace('-', '_').replace(' ', '')})
    await state.set_state(FSMadd.trend)
    await message.answer('Уведомить когда курс пары (больше или меньше)', reply_markup=keyboard_add)


@router.message(StateFilter(FSMadd.trend))
async def message_add_trend(message: Message, state: FSMContext):
    trend = 0
    if message.text.lower() == 'больше':
        trend = 1
    elif message.text.lower() == 'меньше':
        trend = -1
    else:
        await message.answer('Неправильный ввод', reply_markup=keyboard_add)
        return
    await state.update_data({'trend': trend})
    await state.set_state(FSMadd.await_rate)
    await message.answer('Больше или меньше чем (введите число)', reply_markup=keyboard_main)


# конечный этап добавления/обновления подписки
@router.message(StateFilter(FSMadd.await_rate))
async def message_add_rate(message: Message, state: FSMContext):
    try:
        await_rate = float(message.text)
        if await_rate <= 0:
            await message.answer('Неправильный ввод', reply_markup=keyboard_main)
            return
    except:
        await message.answer('Неправильный ввод', reply_markup=keyboard_main)
        return
    await state.update_data({'await_rate': await_rate})
    data = await state.get_data()
    # rows = con.execute(f"SELECT DISTINCT pair_code FROM user_currency_pair WHERE pair_code = '{data['pair']}'")
    if data['pair'] not in arr_sub:
        await subscribe(data['pair'], message.from_user.id)  # если таких подписок еще не было, то подписываемся в exmo
        arr_sub.add(data['pair'])
    res = add_upd_sub(message.from_user.id, data['pair'], await_rate, data['trend'])
    await state.clear()
    await message.answer(res, reply_markup=keyboard_main)


@router.message(F.text == 'Удалить подписку', StateFilter(None))
async def message_del(message: Message, state: FSMContext):
    rows = con.execute(f'SELECT pair_code, trend, await_rate FROM user_currency_pair WHERE user_id = {message.from_user.id}')
    count = 0
    trend = 'меньше'
    keyboard_del = InlineKeyboardBuilder()
    for row in rows.fetchall():
        count += 1
        if str(row[1]) == '1':
            trend = 'больше'
        keyboard_del.button(text=f'Пара {row[0]} {trend} {row[2]}', callback_data=row[0]+trend)
        trend = 'меньше'
    keyboard_del.button(text='Отмена', callback_data='ОтменаОтмена')
    keyboard_del.adjust(1)
    if count > 0:
        await state.set_state(FSMdel.pair)
        await message.answer('Выберите подписку', reply_markup=keyboard_del.as_markup())
    else:
        await message.answer('У вас нет подписок', reply_markup=keyboard_main)


@dp.callback_query(StateFilter(FSMdel.pair))
async def message_del_pair(callback: CallbackQuery, state: FSMContext):
    pair = callback.data[:-6]
    trend = callback.data[len(callback.data) - 6:]
    if trend == 'больше':
        trend = '1'
    elif trend == 'меньше':
        trend = '-1'
    else:  # значит отмена
        await callback.answer('Операция отменена', reply_markup=keyboard_main, show_alert=True)
        await state.clear()
        return
    await state.clear()
    rows = con.execute(f"SELECT * FROM user_currency_pair WHERE user_id = '{callback.from_user.id}' AND pair_code = '{pair}' AND trend = {trend}")
    res = ''
    if rows.fetchone() is None:  # если нет такой подписки у пользователя
        res = 'У вас нет такой подписки'
    else:
        res = del_sub(callback.from_user.id, pair, trend)  # удалим подписку в базе
        rows = con.execute(f"SELECT DISTINCT pair_code FROM user_currency_pair WHERE pair_code = '{pair}'")
        if rows.fetchone() is None: # если больше нет таких подписок у пользователей то отписываемся и удаляем из arr_sub
            await unsubscribe(pair)
            arr_sub.remove(pair)
    await callback.answer('',reply_markup=keyboard_main) # чтобы у клиента не отображался процесс
    await callback.message.answer(res, reply_markup=keyboard_main)
    await state.clear()


@router.message(StateFilter(FSMdel.pair))
async def message_del_pair(message: Message, state: FSMContext):
    await message.answer("Выберите операцию из предложенных", reply_markup=keyboard_main)


@dp.callback_query(StateFilter(None))
async def message_del_pair(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Выберите пункт 'Удалить подписку'", reply_markup=keyboard_main, show_alert=True)


@router.message(F.text == 'Мои подписки', StateFilter(None))
async def message_with_text(message: Message):
    res = get_sub(message.from_user.id)
    if res.find('Пара') != -1:
        await message.answer("Список ваших подписок: " + res, reply_markup=keyboard_main)
    else:
        await message.answer('У вас нет подписок', reply_markup=keyboard_main)


@router.message(StateFilter(None))
async def message_del_pair(message: Message, state: FSMContext):
    await message.answer("Неизвестная операция", reply_markup=keyboard_main, show_alert=True)

