import datetime
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import telebot
from telebot import types

BOT_TOKEN = "7906758051:AAEbLOa67qZa4bZYoHlNLnZtsx3ZJbffpf8"

# Создание Flask-приложения
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"  # Настройка URI для базы данных SQLite
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Отключение отслеживания модификаций

# Инициализация SQLAlchemy для работы с базой данных
db = SQLAlchemy(app)

# Инициализация TeleBot с использованием токена бота
bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(level=logging.INFO)

# -----------------------------------
# Модели базы данных
# -----------------------------------
class MessageLog(db.Model):
    """
    Хранит все сообщения пользователей (для логирования).
    """
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор записи
    user_id = db.Column(db.String(50), nullable=False)  # Идентификатор пользователя
    message_text = db.Column(db.String(255), nullable=False)  # Текст сообщения
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)  # Время отправки сообщения

    def __repr__(self):
        return f"<MessageLog {self.id} - {self.user_id} - {self.message_text}>"

class Habit(db.Model):
    """
    Простая таблица для отслеживания привычек пользователей.
    """
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор записи
    user_id = db.Column(db.String(50), nullable=False)  # Идентификатор пользователя
    habit_name = db.Column(db.String(100), nullable=False)  # Название привычки
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)  # Дата и время создания записи

    def __repr__(self):
        return f"<Habit {self.id} - {self.user_id} - {self.habit_name}>"

# -----------------------------------
# Вспомогательные функции
# -----------------------------------
def log_message(user_id, text):
    """
    Логирует сообщения пользователей в таблицу MessageLog.
    """
    with app.app_context():
        new_log = MessageLog(user_id=str(user_id), message_text=text)
        db.session.add(new_log)
        db.session.commit()

def add_new_habit(user_id, habit_name):
    """
    Добавляет новую привычку в таблицу Habit.
    """
    with app.app_context():
        habit = Habit(user_id=str(user_id), habit_name=habit_name)
        db.session.add(habit)
        db.session.commit()

def get_user_habits(user_id):
    """
    Извлекает привычки пользователя из базы данных.
    """
    with app.app_context():
        return Habit.query.filter_by(user_id=str(user_id)).all()

# -----------------------------------
# Обработчики бота
# -----------------------------------

@bot.message_handler(commands=["start"])
def send_welcome(message):
    """
    Обработчик команды /start – приветствует пользователя и предоставляет простое меню с кнопками.
    """
    user_id = message.from_user.id  # Получаем ID пользователя
    text = f"Здравствуйте, {message.from_user.first_name}!\nЯ ваш бот для отслеживания привычек.\nВыберите опцию ниже:"

    # Логируем это сообщение
    log_message(user_id, message.text)

    # Создаем клавиатуру с двумя кнопками
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_add = types.KeyboardButton("Добавить Привычку")
    btn_view = types.KeyboardButton("Просмотреть Мои Привычки")
    markup.add(btn_add, btn_view)

    # Отправляем приветственное сообщение с клавиатурой
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Добавить Привычку")
def on_add_habit_clicked(message):
    """
    Обработчик нажатия кнопки "Добавить Привычку". Запрашивает у пользователя название привычки.
    """
    user_id = message.from_user.id  # Получаем ID пользователя
    log_message(user_id, message.text)  # Логируем сообщение

    # Запрашиваем у пользователя название новой привычки
    bot.send_message(
        chat_id=message.chat.id,
        text="Какую привычку вы хотели бы добавить? Пожалуйста, введите ее сейчас."
    )

@bot.message_handler(func=lambda m: m.text == "Просмотреть Мои Привычки")
def on_view_habits_clicked(message):
    """
    Обработчик нажатия кнопки "Просмотреть Мои Привычки". Отображает список привычек пользователя.
    """
    user_id = message.from_user.id  # Получаем ID пользователя
    log_message(user_id, message.text)  # Логируем сообщение

    habits = get_user_habits(user_id)  # Получаем привычки пользователя из базы данных
    if habits:
        # Формируем список привычек для отображения
        habit_list = "\n".join(f"- {h.habit_name}" for h in habits)
        bot.send_message(
            chat_id=message.chat.id,
            text=f"Ваши привычки:\n{habit_list}"
        )
    else:
        # Если у пользователя нет привычек, предлагаем добавить новую
        bot.send_message(
            chat_id=message.chat.id,
            text="У вас пока нет привычек. Попробуйте добавить новую с помощью кнопки 'Добавить Привычку'!"
        )

@bot.message_handler(func=lambda m: True, content_types=["text"])
def on_any_text_message(message):
    """
    Общий обработчик для любых текстовых сообщений.
    - Если пользователь нажал 'Добавить Привычку', обработано выше.
    - Если пользователь нажал 'Просмотреть Мои Привычки', обработано выше.
    - В противном случае предполагается, что пользователь вводит название новой привычки.
    """
    user_id = message.from_user.id  # Получаем ID пользователя
    text = message.text.strip()  # Получаем и очищаем текст сообщения

    # Логируем сообщение
    log_message(user_id, text)

    # Если сообщение не является одной из специальных команд, рассматриваем его как название привычки
    if text not in ["Добавить Привычку", "Просмотреть Мои Привычки", "/start"]:
        add_new_habit(user_id, text)  # Добавляем новую привычку в базу данных
        bot.send_message(
            chat_id=message.chat.id,
            text=f"Привычка '{text}' добавлена!\nВведите /start, чтобы снова увидеть опции."
        )

# -----------------------------------
# Основная точка входа
# -----------------------------------
if __name__ == "__main__":
    # Создаем все таблицы базы данных, если их еще нет
    with app.app_context():
        db.create_all()

    # Запускаем опрос бота (без необходимости запускать Flask веб-сервер для базового локального использования)
    print("Бот запущен и работает...")
    bot.infinity_polling()
