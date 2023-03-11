#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import config
import telebot
import random
import sys
from telebot import types
from emoji import emojize
import sqlite3
from loguru import logger

logger.remove()
logger.add(
    sink=sys.stdout,  # вывод в stdout
    colorize=True,    # цветной вывод
    format="<green>{time}</green> <level>{message}</level>",  # формат логов
)


bot = telebot.TeleBot(config.token)

smiley = emojize(":smiley:", language='alias')
imp = emojize(":imp:", language='alias')
pensive = emojize(":pensive:", language='alias')
heart_eyes = emojize(":heart_eyes:", language='alias')
crown = emojize(":crown:", language='alias')

user_dict = {}


class User:
    def __init__(self, name):
        self.name = name
        self.chat_id = None
        self.bot_num = None
        self.user_num = None
        self.user_attempts = 0
        self.user_score = 0
        self.user_options = []


class Responser():
    delimiter = ' '

    def __init__(self, config, default):
        self.config = config
        self.default = default
        self.cache = {}
        self._load_config(config)

    def _load_config(self, config):
        # CACHE tuple with all the words
        for section, data in self.config.items():
            for w in data.get('markers', []):
                if w not in self.cache:
                    self.cache[w] = section

    def get_message(self, input):
        # IN Cache?
        index = self.default
        for word in input.split(self.delimiter):
            if self.cache.get(word):
                index = self.cache[word]
                break
        return self.config[index]['message']


def get_puzzled_number():
    random_set = set()
    while len(random_set) != 4:
        new_number = random.randint(0, 9)
        random_set.add(new_number)
    return random_set


def check(nums, true_nums):
    bulls, cows = 0, 0
    for i, num in enumerate(nums):
        if num in true_nums:
            if nums[i] == true_nums[i]:
                bulls += 1
            else:
                cows += 1
    return bulls, cows


def get_top10_gamers():
    db = sqlite3.connect('bot_stat.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT name, score FROM users ORDER BY score DESC LIMIT 10')
    top_10_gamers = "\n".join(f'{k} - {v} pts' for k, v in cursor.fetchall())
    db.close()
    return top_10_gamers


@bot.message_handler(commands=['start'])
def send_welcome(message):
    db = sqlite3.connect('bot_stat.sqlite')
    cursor = db.cursor()
    cursor.execute('select name,score from users where chat_id=?', (message.chat.id,))
    data = cursor.fetchone()
    if data is None:
        cursor.executemany('insert into users values (?, ? , ?)', [(message.from_user.first_name, message.chat.id, 0)])
        db.commit()
        db.close()
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}')
    start_keyboard(message)


def start_keyboard(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row("Начать игру", "Остановить игру")
    markup.add("Показать введенные варианты")
    markup.add("Показать топ-10 игроков")
    markup.add("Правила игры")
    bot.send_message(message.chat.id,
                     f'Вот какие у меня есть кнопки для игры {smiley}',
                     reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Начать игру")
def start_game(message):
    if message.text == "Начать игру":
        name = message.from_user.first_name
        user = User(name)
        user_dict[message.chat.id] = user
        bot_num = (get_puzzled_number())
        user = user_dict[message.chat.id]
        user.chat_id = message.chat.id
        user.bot_num = bot_num
        msg = bot.reply_to(message, f'Попробуй угадать число, которое я загадал')
        bot.register_next_step_handler(msg, process_game)


def process_game(message):
    user_num = message.text
    user = user_dict[message.chat.id]
    if message.text == "Остановить игру":
        return
    elif message.text == "Показать введенные варианты":
        user_options_output = '\n'.join(user.user_options)
        msg = bot.reply_to(message, f'Ты уже пробовал следующие варианты:\n{user_options_output}')
        bot.register_next_step_handler(msg, process_game)
        return
    elif message.text == "Показать топ-10 игроков":
        top_10_gamers_output = get_top10_gamers()
        msg = bot.reply_to(message, f'\nТоп-10 {crown} игроков:\n{top_10_gamers_output}')
        bot.register_next_step_handler(msg, process_game)
        return
    elif message.text == "Правила игры":
        msg = bot.reply_to(message, config.rules)
        bot.register_next_step_handler(msg, process_game)
        return
    else:
        user.user_num = user_num
        logger.debug("User dictionary: {}", user.__dict__)
        # print(user.__dict__)
        bot_num = list(user.bot_num)
        bot_num_output = ''.join(map(str, user.bot_num))
        if len(user_num) != 4 or not user_num.isdigit():
            msg = bot.reply_to(message, 'Число! И число должно состоять из четырёх неповторяющихся цифр')
            bot.register_next_step_handler(msg, process_game)
            return
        user_num = list(map(int, user.user_num))
        if len(set(user_num)) == 4:
            user.user_options.append(user.user_num)
            bulls, cows = check(user_num, bot_num)
            bot.send_message(message.chat.id, f'Быков: {bulls}, Коров: {cows}')
            if bulls == 4:
                db = sqlite3.connect('bot_stat.sqlite')
                cursor = db.cursor()
                [name, score], = cursor.execute('select name, score from users where chat_id=?', (message.chat.id,))
                user_stat = [name, score]
                if user.user_attempts <= 5:
                    user.user_score += 3
                elif 5 < user.user_attempts <= 10:
                    user.user_score += 2
                else:
                    user.user_score += 1
                user_stat[1] = user_stat[1] + user.user_score
                cursor.execute("update users set score=? where chat_id=?", (user_stat[1], message.chat.id))
                db.commit()
                db.close()
                bot.send_message(message.chat.id, f'Ура! Ты победил! {heart_eyes} Я, действительно,'
                                                  f' загадал число {bot_num_output}\n'
                                                  f'Всего понадобилось попыток: {user.user_attempts}. Сможешь лучше?\n'
                                                  f'\nНажми \"Начать игру\" для новой игры')
                return
            else:
                msg = bot.reply_to(message, 'На один шаг ближе к победе, но пока нет. Итак, я загадал...')
                user.user_attempts += 1
                bot.register_next_step_handler(msg, process_game)
                return
        else:
            msg = bot.reply_to(message, 'Неповторяющихся цифр!')
            bot.register_next_step_handler(msg, process_game)
            return


@bot.message_handler(func=lambda message: message.text == "Остановить игру")
def stop_game(message):
    bot.send_message(message.chat.id, f'Чтобы остановить игру, ее для начала надо запустить')


@bot.message_handler(commands=['help'])
def command_help(message):
    bot.send_message(message.chat.id, config.rules)


@bot.message_handler(func=lambda message: message.text == "Правила игры")
def send_help(message):
    bot.send_message(message.chat.id, config.rules)


@bot.message_handler(func=lambda message: message.text == "Показать введенные варианты")
def get_statistic(message):
    bot.send_message(message.chat.id, f'Йо! Мы сейчас не в режиме игры')


@bot.message_handler(func=lambda message: message.text == "Показать топ-10 игроков")
def get_winners(message):
    top_10_gamers_output = get_top10_gamers()
    bot.send_message(message.chat.id, f'\nТоп-10 {crown} игроков:\n{top_10_gamers_output}')


# default handler for every other text
@bot.message_handler(func=lambda message: True, content_types=['text'])
def command_default(m):
   # this is the standard reply to a normal message
   i = m.text.lower()
   r = Responser(config.RESPONSES, config.DEFAULT)
   bot.send_message(m.chat.id, r.get_message(i))


bot.polling(none_stop=True)
