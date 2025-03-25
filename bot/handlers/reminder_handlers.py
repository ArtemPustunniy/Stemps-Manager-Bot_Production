import sqlite3
from datetime import datetime, timedelta
import json
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.utils.role_manager import role_manager
from openai import AsyncOpenAI
from bot.config.settings import OPENAI_API_KEY
import logging

# Инициализация планировщика
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# Инициализация клиента OpenAI
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def parse_reminder_message(user_input: str) -> dict:
    """
    Парсит пользовательский ввод с помощью LLM и возвращает структурированные данные в формате JSON.
    """
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt = (
        "Ты — помощник, который извлекает структурированные данные из текста напоминания. "
        "Пользователь написал напоминание в свободной форме, например: '12-го числа о том, что я должен написать компании самолёт по Курсу1' "
        "или 'завтра в 14:00 позвонить клиенту по поводу проекта'. "
        "Твоя задача: "
        "1. Извлечь дату и время напоминания. Если дата относительная (например, 'завтра', 'через 3 дня'), "
        f"используй текущую дату и время ({current_date}) для расчёта. Если время не указано, используй 00:00. "
        "2. Извлечь следующие поля: "
        "- action: действие, которое нужно выполнить (например, 'написать', 'позвонить'). "
        "- company: название компании или кому нужно выполнить действие (например, 'компании Самолёт'). "
        "- topic: тема или курс, по поводу которого нужно выполнить действие (например, 'курса Курс1'). "
        "3. Сформировать красивое напоминание в формате: 'Не забудь, ты должен [действие] [кому] по поводу [тема/курс].' "
        "Верни результат в формате JSON: "
        "{"
        "  'remind_date': 'YYYY-MM-DD HH:MM:SS',"
        "  'action': '<действие>',"
        "  'company': '<кому>',"
        "  'topic': '<тема>',"
        "  'formatted_message': '<красивое напоминание>'"
        "}"
        "Сохраняй ключевые детали (даты, имена, курсы и т.д.), но делай текст более формальным и приятным. "
        "Если дата не указана или не распознана, используй текущую дату + 1 день. "
        "Не добавляй лишних деталей, не меняй смысл. "
        f"Пользователь написал: '{user_input}'"
    )

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=200,
            temperature=0.3,
        )
        result = response.choices[0].message.content.strip()
        # Парсим JSON из ответа
        parsed_data = json.loads(result)

        # Валидация полей
        required_fields = ["remind_date", "action", "company", "topic", "formatted_message"]
        if not all(field in parsed_data for field in required_fields):
            raise ValueError("Отсутствуют обязательные поля в JSON")

        # Проверяем формат даты
        try:
            remind_date = datetime.strptime(parsed_data["remind_date"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(f"Неверный формат даты: {parsed_data['remind_date']}")

        return parsed_data
    except Exception as e:
        logging.error(f"Ошибка при парсинге напоминания через LLM: {str(e)}")
        # Если LLM не сработал, возвращаем заглушку
        tomorrow = (datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1))
        return {
            "remind_date": tomorrow.strftime("%Y-%m-%d %H:%M:%S"),
            "action": "написать",
            "company": "неизвестной компании",
            "topic": "неизвестной темы",
            "formatted_message": f"Напоминание: {user_input}"
        }

async def remindme(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Проверяем, что пользователь зарегистрирован
    if not role_manager.get_role(user_id):
        await update.message.reply_text("Вы не зарегистрированы. Обратитесь к директору.")
        return

    # Проверяем, что бот активен для пользователя
    if not role_manager.is_active(user_id):
        await update.message.reply_text("Бот отключён. Включите его с помощью /start_work_day.")
        return

    # Проверяем, что текст команды содержит аргументы
    if not context.args:
        await update.message.reply_text(
            "Использование: /remindme <дата> <сообщение>\n"
            "Пример: /remindme 12-го числа о том, что я должен написать компании самолёт по Курсу1\n"
            "Или: /remindme завтра в 14:00 позвонить клиенту по поводу проекта"
        )
        return

    # Объединяем аргументы в строку
    reminder_text = " ".join(context.args)

    # Парсим сообщение через LLM
    reminder_data = await parse_reminder_message(reminder_text)

    # Извлекаем данные из JSON
    remind_date = datetime.strptime(reminder_data["remind_date"], "%Y-%m-%d %H:%M:%S")
    action = reminder_data.get("action", "написать")
    company = reminder_data.get("company", "неизвестной компании")
    topic = reminder_data.get("topic", "неизвестной темы")
    formatted_message = reminder_data.get("formatted_message", f"Напоминание: {reminder_text}")

    # Сохраняем напоминание в базу данных
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (telegram_id, remind_date, action, company, topic, formatted_message, is_sent) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, remind_date.strftime("%Y-%m-%d %H:%M:%S"), action, company, topic, formatted_message, 0)
        )
        reminder_id = cursor.lastrowid
        conn.commit()

    # Планируем отправку напоминания
    async def send_reminder():
        await context.bot.send_message(chat_id=user_id, text=formatted_message)
        # Помечаем напоминание как отправленное
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,))
            conn.commit()

    scheduler.add_job(
        send_reminder,
        "date",
        run_date=remind_date,
        args=[],
        id=f"reminder_{reminder_id}"
    )

    await update.message.reply_text(f"Напоминание установлено на {remind_date.strftime('%d.%m.%Y %H:%M')}: {formatted_message}")


async def listreminders(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Проверяем, что пользователь зарегистрирован
    if not role_manager.get_role(user_id):
        await update.message.reply_text("Вы не зарегистрированы. Обратитесь к директору.")
        return

    # Извлекаем все напоминания пользователя из базы данных
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, remind_date, formatted_message FROM reminders WHERE telegram_id = ? AND is_sent = 0",
            (user_id,)
        )
        reminders = cursor.fetchall()

    if not reminders:
        await update.message.reply_text("У вас нет запланированных напоминаний.")
        return

    # Формируем список напоминаний
    response_text = "📅 *Ваши запланированные напоминания*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for reminder in reminders:
        reminder_id, remind_date, formatted_message = reminder
        remind_date = datetime.strptime(remind_date, "%Y-%m-%d %H:%M:%S")
        response_text += (
            f"ID: {reminder_id}\n"
            f"Дата: {remind_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Сообщение: {formatted_message}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

    await update.message.reply_text(response_text, parse_mode="MarkdownV2")

def load_existing_reminders(app):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, telegram_id, remind_date, formatted_message FROM reminders WHERE is_sent = 0")
        reminders = cursor.fetchall()

    for reminder in reminders:
        reminder_id, telegram_id, remind_date, formatted_message = reminder
        remind_date = datetime.strptime(remind_date, "%Y-%m-%d %H:%M:%S")

        if remind_date < datetime.now():
            with sqlite3.connect("users.db") as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,))
                conn.commit()
            continue

        async def send_reminder():
            await app.bot.send_message(chat_id=telegram_id, text=formatted_message)
            with sqlite3.connect("users.db") as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,))
                conn.commit()

        scheduler.add_job(
            send_reminder,
            "date",
            run_date=remind_date,
            args=[],
            id=f"reminder_{reminder_id}"
        )

def setup_reminder_handlers(app):
    app.add_handler(CommandHandler("remindme", remindme))

def start_scheduler(app):
    load_existing_reminders(app)
    logging.info("Планировщик запущен")
    scheduler.start()

__all__ = ["setup_reminder_handlers", "start_scheduler"]