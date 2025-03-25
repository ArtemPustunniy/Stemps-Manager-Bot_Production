from telegram import Update, BotCommand, BotCommandScopeChat
from telegram.ext import CallbackContext
from bot.utils.role_manager import role_manager


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)

    if role:
        if role_manager.is_director(user_id):
            commands = [
                BotCommand("start", "Начать работу с ботом"),
                BotCommand("help", "Показать список команд"),
                BotCommand("myid", "Узнать свой Telegram ID"),
                BotCommand("start_work_day", "Включить бота"),
                BotCommand("finish_work_day", "Отключить бота"),
                BotCommand("cancel", "Отменить текущую операцию"),
                BotCommand("add", "Пошаговое добавление записи"),
                BotCommand("ai_assistent", "Добавление через текстовую инструкцию"),
                BotCommand("manage_users", "Управление пользователями"),
                BotCommand("stats", "Посмотреть статистику менеджера"),
                BotCommand("today_revenue", "Статистика всех менеджеров"),
                BotCommand("remindme", "Установить напоминание"),
                BotCommand("listreminders", "Показать все запланированные напоминания"),
            ]

        elif role_manager.is_manager(user_id):
            commands = [
                BotCommand("start", "Начать работу с ботом"),
                BotCommand("help", "Показать список команд"),
                BotCommand("myid", "Узнать свой Telegram ID"),
                BotCommand("start_work_day", "Включить бота"),
                BotCommand("finish_work_day", "Отключить бота"),
                BotCommand("cancel", "Отменить текущую операцию"),
                BotCommand("add", "Пошаговое добавление записи"),
                BotCommand("ai_assistent", "Добавление через текстовую инструкцию"),
                BotCommand("remindme", "Установить напоминание"),
                BotCommand("listreminders", "Показать все запланированные напоминания"),
            ]
        else:
            commands = [
                BotCommand("myid", "Узнать свой Telegram ID"),
                BotCommand("start_work_day", "Включить бота (после регистрации)"),
            ]

        await context.bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
        )

        if role_manager.is_active(user_id):
            await update.message.reply_text(
                f"Привет! Ваша роль: {role}\nДля списка команд используй /help."
            )
        else:
            await update.message.reply_text(
                "Бот отключён для вас. Включите его командой /start_work_day."
            )
    else:
        await update.message.reply_text(
            "Привет! Вы не зарегистрированы в системе. Обратитесь к директору для получения роли.\n"
            "Узнайте свой ID с помощью /myid."
        )


__all__ = ["start"]

