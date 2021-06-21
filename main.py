from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

import logging
import config
import re
import os
# from icecream import ic
import requests
from tables import *
from random import randint


email_regex = "\S+@\S+\.\S+"
url = 'https://front.koshelek.ru/api/'
path_to_images = os.getcwd() + '/images/'

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(config.token)
dp = Dispatcher(bot, storage=storage)


class Form(StatesGroup):
    login = State()
    email = State()
    password = State()
    capcha = State()


class SignIn(StatesGroup):
    email = State()
    password = State()


class Change(StatesGroup):
    password1 = State()
    password2 = State()


class Keyboards:
    def __init__(self):
        self.fin_yes = "Всё верно ✅"
        self.fin_no = "Нет! Давай заново ❌"
        self.start_reg = "Зарегистрироваться"
        self.start_sign_in = "Войти"
        self.profile = "Мой профиль"
        self.change_pass = "Сменить пароль"
        self.sign_out = "Выйти"

    def get_fin_keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(self.fin_yes)
        markup.add(self.fin_no)
        return markup

    def get_start_keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(self.start_reg)
        markup.add(self.start_sign_in)
        return markup

    def get_in_keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(self.profile, self.sign_out)
        markup.add(self.change_pass)
        return markup


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):

    if not is_signed_in(message.from_user.id):
        await bot.send_message(message.chat.id, f"Добро пожаловать, {message.from_user.first_name}\n",
                               reply_markup=Keyboards().get_start_keyboard())
    else:
        await bot.send_message(message.chat.id, f"Добро пожаловать, {message.from_user.first_name}\n",
                               reply_markup=Keyboards().get_in_keyboard())


@dp.message_handler(state=Form.login)
async def process_login(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['login'] = message.text.strip()

    await Form.next()

    await bot.send_message(message.chat.id, f"Теперь отправь свой адрес электронной почты")


@dp.message_handler(state=SignIn.email)
async def process_login(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['email'] = message.text.strip()

    await SignIn.next()

    await bot.send_message(message.chat.id, f"Теперь отправь свой пароль")


@dp.message_handler(state=Change.password1)
async def process_login(message: types.Message, state: FSMContext):

    if len(message.text.strip()) < 8 or len(message.text.strip()) > 128:
        await bot.send_message(message.chat.id, f"Длина пароля должна быть не меньше восьми символов\n"
                                                f"Давай попробуем ещё раз.\n"
                                                f"Отправьте новый пароль")
    else:
        async with state.proxy() as data:
            data['password1'] = message.text.strip()

        await Change.next()

        await bot.send_message(message.chat.id, f"Теперь снова отправьте новый пароль")


@dp.message_handler(state=Change.password2)
async def process_login(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['password2'] = message.text.strip()

        if data['password2'] != data['password1']:
            await Change.password1.set()
            await bot.send_message(message.chat.id, f"Пароли должны совпадать!\n"
                                                    f"Смена пароля отменена",
                                   reply_markup=Keyboards().get_in_keyboard())
        else:
            await bot.send_message(message.chat.id, f"Пароль успешно изменён")
            sql.update('users', 'password = %s where user_id = %s', values=(data['password1'],
                                                                            message.from_user.id))
        await state.finish()


@dp.message_handler(state=SignIn.password)
async def process_login(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['password'] = message.text.strip()
        await state.finish()
        res = sql.select('users', '*', 'email = %s and password = %s', values=(data['email'], data['password']),
                         one=True)
        # ic(res)
        if res is not None:
            await bot.send_message(message.chat.id, f"Вход выполнен успешно!",
                                   reply_markup=Keyboards().get_in_keyboard())
            sql.update('users', 'logined = 1 where user_id = %s', values=(message.from_user.id,))
        else:
            await bot.send_message(message.chat.id, f"Неверная почта или пароль",
                                   reply_markup=Keyboards().get_start_keyboard())


@dp.message_handler(types.Message, state=Form.email)
async def process_email(message: types.Message, state: FSMContext):
    email = re.findall(email_regex, message.text)
    if len(email) == 0:
        await bot.send_message(message.chat.id, f"Требуется ввести настоящий адрес электронной почты\n"
                                                f"Давай попробуем ещё раз.\n"
                                                f"Отправь свой адрес электронной почты")

    else:
        email = email[0]

        await Form.next()

        async with state.proxy() as data:
            data['email'] = email

        await bot.send_message(message.chat.id, f"Теперь введи свой пароль\n"
                                                f"Длина пароля должна быть не меньше восьми символов")


@dp.message_handler(state=Form.password)
async def process_password(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 8 or len(message.text.strip()) > 128:
        await bot.send_message(message.chat.id, f"Длина пароля должна быть не меньше восьми символов\n"
                                                f"Давай попробуем ещё раз.\n"
                                                f"Отправь свой пароль")
    else:
        async with state.proxy() as data:

            await Form.next()
            data['password'] = message.text.strip()

            await bot.send_photo(message.chat.id, caption="Теперь введите капчу",
                                 photo=open(path_to_images + 'capcha.png', 'rb'))


def get_random_float():
    return str(float(randint(10000, 99999)/10000))


def is_signed_in(user_id):
    res = sql.select('users', 'logined', 'user_id = %s', values=(user_id,), one=True)
    # ic(res)
    if res is None:
        return False
    elif res[0] != 0:
        return True
    else:
        return False


@dp.message_handler(state=Form.capcha)
async def process_password(message: types.Message, state: FSMContext):
    if message.text.strip().lower() == 'smwm':
        async with state.proxy() as data:
            await state.finish()
            sql.insert('users', values=(message.from_user.id, data['login'], data['email'],
                                        data['password'], f"BTC: {get_random_float()}|LiteCoin: {get_random_float()}|"
                                                          f"Ethereum: {get_random_float()}", 1))
            show_pass = '*' * (len(data['password']) - 2) + data['password'][-2:]
            await bot.send_message(message.chat.id, f"Всё верно?\n"
                                                    f"Логин: {data['login']}\n"
                                                    f"Почта: {data['email']}\n"
                                                    f"Пароль: {show_pass}",
                                   reply_markup=Keyboards().get_fin_keyboard())

    else:
        await bot.send_message(message.chat.id, 'Вы ввели неверный текст капчи. Попробуйте ещё раз')


@dp.message_handler(content_types=['text'])
async def send_welcome(message: types.Message):

    fk = Keyboards()
    sign = is_signed_in(message.from_user.id)
    # ic(sign)

    if message.text == fk.start_reg and not sign:
        await bot.send_message(message.chat.id, f"Чтобы зарегистрироваться вам потребуется ввести свои логин,"
                                                f" почту и пароль.\n"
                                                f"Отправьте свой логин")

        await Form.login.set()

    if message.text == fk.start_sign_in and not sign:
        await SignIn.email.set()
        await bot.send_message(message.chat.id, f"Введите почту",
                               reply_markup=types.ReplyKeyboardRemove())

    if message.text == fk.fin_yes:
        await bot.send_message(message.chat.id, f"Поздравляю! Вы прошли регистрацию",
                               reply_markup=Keyboards().get_in_keyboard())

    if message.text == fk.fin_no:
        sql.delete('users', 'user_id = %s', values=(message.from_user.id,))
        await bot.send_message(message.chat.id, f"Хорошо, давай начнём с начала.\n"
                                                f"Чтобы зарегистрироваться вам потребуется ввести свои логин,"
                                                f" почту и пароль.\n"
                                                f"Отправьте свой логин")

        await Form.login.set()

    if message.text == fk.sign_out and sign:
        sql.update('users', 'logined = 0 where user_id = %s', values=(message.from_user.id,))
        await bot.send_message(message.chat.id, 'Вы вышли из аккаунта', reply_markup=Keyboards().get_start_keyboard())

    if message.text == fk.profile and sign:
        login, balance = sql.select('users', 'login, currencies', 'user_id = %s', values=(message.from_user.id,),
                                    one=True)

        balance = balance.replace('|', '\n')
        await bot.send_message(message.chat.id, f'Логин: {login}\n'
                                                f'Балансы:\n'
                                                f'{balance}',
                               reply_markup=Keyboards().get_in_keyboard())

    if message.text == fk.change_pass and sign:
        await bot.send_message(message.chat.id, 'Введите новый пароль')
        await Change.password1.set()


executor.start_polling(dp, skip_updates=True)
