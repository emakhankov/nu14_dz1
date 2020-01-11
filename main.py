import purchasesVGTRK
import telebot
from telebot import apihelper
import json
import time
import os
import pandas as pd
from collections import defaultdict

TEXT_WAIT_FOR = 'Подождите до формирования сведений'

STAGE_0, STAGE_SEND_BY_NOMER = range(0, 2)
USER_STATE = defaultdict(lambda: STAGE_0)
USER_DATA = defaultdict(lambda: {})


def get_settings():

    with open("settings.json", "r") as read_file:
        data = json.load(read_file)
        return data


SETTINGS = get_settings()
TOKEN = SETTINGS['TOKEN']
OUTPUT_EXCEL = SETTINGS['OUTPUT_EXCEL']

if 'PROXIES' in SETTINGS:
    PROXIES = SETTINGS['PROXIES']
    apihelper.proxy = PROXIES
bot = telebot.TeleBot(TOKEN)


def get_state(message):
    return USER_STATE[message.chat.id]


def update_state(message, newstate):
    USER_STATE[message.chat.id] = newstate


def read_from_excel():

    df = pd.read_excel(OUTPUT_EXCEL, sheet_name='Sheet1', index_col=0)
    return df

def verify_up_to_date(message):

    if not os.path.isfile(OUTPUT_EXCEL):
        bot.send_message(message.chat.id, TEXT_WAIT_FOR)
        purchasesVGTRK.get_excel()
    else:
        time_creation = os.path.getctime(OUTPUT_EXCEL)
        time_now = time.time()
        diff_sec = time_now - time_creation
        if diff_sec > 3600.0:
            bot.send_message(message.chat.id, TEXT_WAIT_FOR)
            purchasesVGTRK.get_excel()

# Обработчик 1
@bot.message_handler(commands=['start'])
def send_welcome(message):

    text = '''Добрый день! Я телебот созданный как домашнее задание. Я умею искать закупки ВГТРК на сайте закупок.
    Для получения списка команд введите команда /help'''

    bot.send_message(message.chat.id, text)
    update_state(message, STAGE_0)

# Обработчик 2
@bot.message_handler(commands=['help'])
def send_welcome(message):

    text = '''
    Доступные команды:
    /getexcel - Получить последную полную выгрузку в формате EXCEL
    /getlast n - Получить информацию о последних n закупках (если n не задано 10)
    /getbynomer nomer - Получить информацию закупке по номеру'''

    bot.send_message(message.chat.id, text)
    update_state(message, STAGE_0)

# Обработчик 3
@bot.message_handler(commands=['getexcel'])
def send_excel(message):

    verify_up_to_date(message)
    doc = open(OUTPUT_EXCEL, 'rb')
    bot.send_document(message.chat.id, doc, caption='Данные в формате EXCEL')
    update_state(message, STAGE_0)


# Обработчик 4
@bot.message_handler(commands=['getlast'])
def send_last(message):

    param = message.text.split()
    if len(param) == 1:
        count = 10
    else:
        count_t = param[1]
        if count_t.isdigit():
            count = int(count_t)
        else:
            bot.reply_to(message, 'Ошибка параметра')
            return

    verify_up_to_date(message)
    df = read_from_excel()
    count = min(len(df), count)
    text = []
    for index, row in df.head(count).iterrows():
        if index != 0:
            text.append('')
            text.append('')
        text.append(f'Закупка: {index+1}')
        text.append(f'Номер: {row["num"]}')
        text.append(f'ссылка: {row["href"]}')
        text.append(f'Описание: {row["description"]}')

    bot.send_message(message.chat.id, '\n'.join(text))
    update_state(message, STAGE_0)



def send_byNomer_finish(message, num):

    verify_up_to_date(message)
    df = read_from_excel()

    row = df.loc[df['num'] == num]
    if len(row) != 0:
        row = row.iloc[0]
    else:
        bot.reply_to(message, 'нет такой закупки')
    text = []
    text.append(f'Номер: {row["num"]}')
    text.append(f'Ссылка: {row["href"]}')
    text.append(f'Описание: {row["description"]}')
    text.append(f'Стоимость: {row["price"]}')
    text.append(f'Состояние: {row["state"]}')
    bot.send_message(message.chat.id, '\n'.join(text))

# Обработчик 5
@bot.message_handler(commands=['getbynomer'])
def send_byNomer(message):

    param = message.text.split()
    if len(param) < 2:
        bot.reply_to(message, 'Введите номер закупки')
        update_state(message, STAGE_SEND_BY_NOMER)
        return

    num = param[1]
    send_byNomer_finish(message, num)


# Обработчик 6
@bot.message_handler(func=lambda message: get_state(message) == STAGE_SEND_BY_NOMER)
def send_byNomer_num(message):
    num = message.text
    send_byNomer_finish(message, num)
    update_state(message, STAGE_0)

# Обработчик 7
@bot.message_handler(commands=['about'])
def test_send_message_with_markdown(message):
    bot.send_message(message.chat.id, "Университет искуственного интеллекта \n Evgeny Makhankov (C)")
    update_state(message, STAGE_0)

bot.polling()


