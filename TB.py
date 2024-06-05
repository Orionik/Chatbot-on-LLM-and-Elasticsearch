import telebot

from telebot import types

import requests
import datetime





bot = telebot.TeleBot('6941708453:AAGqkMugHASFxXEALGDfVw35fjvfkLd97cM')
status = 0
new_id = ""
new_tags = ""




@bot.message_handler(commands=['start'])
def start_message(message):
    """
    Обрабатывает команду /start. 
    Отправляет приветственное сообщение и клавиатуру с кнопкой "Добавить документ в БЗ".
    """
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1=types.KeyboardButton("Добавить документ в БЗ")
    markup.add(item1)
    bot.send_message(message.chat.id, "content", reply_markup=markup)


@bot.message_handler(commands=['stop'])
def end_message(message):
    """
    Обрабатывает команду /stop. 
    Отправляет сообщение "Пока" и останавливает работу бота.
    """
    bot.send_message(message.chat.id,"Пока")
    bot.stop_bot() 


@bot.message_handler(content_types='text')
def message_reply(message):
    """
    Обработчик любых текстовых сообщений.
    В зависимости от текущего статуса (глобальная переменная) выполняет разные действия:

    - status == 1: Сохраняет введённый id документа в переменную new_id,
                   запрашивает теги и переходит в status 2.

    - status == 2: Сохраняет введённые теги в переменную new_tags,
                   запрашивает документ и переходит в status 3.

    - status == 3: Формирует JSON-объект с id, тегами и текстом документа,
                   отправляет POST-запрос на сервер http://127.0.0.1:8000/add_doc,
                   сообщает о сохранении документа и переходит в status 0.

    - message.text == "Добавить документ в БЗ": Устанавливает статус в 1 
                                                  и запрашивает id документа.

    - message.text == "Отмена": Сбрасывает статус в 0 
                                 и сообщает о готовности принимать вопросы.

    - status == 0: Отправляет GET-запрос на сервер http://127.0.0.1:8000/find_doc
                    с текстом сообщения,
                    получает ответ и отправляет его пользователю.
    """
    global status
    global new_id
    global new_tags
    if status == 1:
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1=types.KeyboardButton("Отмена")
        markup.add(item1)
        new_id = message.text
        bot.send_message(message.chat.id,'Введите теги для документа',reply_markup=markup)
        status = 2

    elif status == 2:
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1=types.KeyboardButton("Отмена")
        markup.add(item1)
        new_tags = message.text
        bot.send_message(message.chat.id,'Введите документ',reply_markup=markup)
        status = 3

    elif status==3:
        requests.post('http://127.0.0.1:8000/add_doc', 
                json={
                   "id": new_id + "_" + datetime.datetime.today().strftime("%Y%m%d%H%M%S") + str(datetime.datetime.today().microsecond),
                   "text": f"Tags: {new_tags}\n{message.text}"})
        bot.send_message(message.chat.id,'Документ сохранён')
        status = 0
    
    elif message.text == "Добавить документ в БЗ":
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1=types.KeyboardButton("Отмена")
        markup.add(item1)
        status = 1
        print(status)
        bot.send_message(message.chat.id,'Введите id документа')

    elif message.text == "Отмена":
        bot.send_message(message.chat.id, "Задавайте вопрос")
        status = 0   

    elif status==0:
        response = requests.get('http://127.0.0.1:8000/find_doc', 
                  json={"text": message.text})
        print(message.text)
        bot.send_message(message.chat.id, response.text)




bot.infinity_polling()


