from telegram import Update
from telegram.ext import CallbackContext
from bot.utils.role_manager import role_manager


async def help_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not role_manager.is_active(user_id):
        await update.message.reply_text(
            "⚠️ *Бот отключён для вас\\. Включите его командой* `/start_work_day`\\.",
            parse_mode="MarkdownV2",
        )
        return

    role = role_manager.get_role(user_id)
    if role_manager.is_director(user_id):
        help_text = (
            "👑 *Команды для директора*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📋 *Основные команды:*\n"
            "• `/start` — Начать работу с ботом\n"
            "• `/help` — Показать список команд\n"
            "• `/myid` — Узнать свой Telegram ID\n"
            "• `/start_work_day` — Включить бота\n"
            "• `/finish_work_day` — Отключить бота\n"
            "• `/remindme` — Установить напоминание — например, 12\\.\\03 Напомни о встрече с Компанией Самолёт по поводу Курса такого\\-\\то\n"
            "• `/cancel` — Отменить текущую операцию\n"
            "\n📝 *Добавление записей:*\n"
            "• `/add` — Пошаговое добавление записи\n"
            "• `/ai_assistent` — Добавление через текстовую инструкцию\n"
            "\n📊 *Управление и статистика:*\n"
            "• `/manage_users` — Управление пользователями\n"
            "• `/stats` — Посмотреть статистику менеджера\n"
            "• `/today_revenue` — Статистика всех менеджеров\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Используйте команды для эффективной работы\\!"
        )
    elif role_manager.is_manager(user_id):
        help_text = (
            "🧑‍💼 *Команды для менеджера*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📋 *Основные команды:*\n"
            "• `/start` — Начать работу с ботом\n"
            "• `/help` — Показать список команд\n"
            "• `/myid` — Узнать свой Telegram ID\n"
            "• `/start_work_day` — Включить бота\n"
            "• `/finish_work_day` — Отключить бота\n"
            "• `/remindme` — Установить напоминание — например, 12\\.\\03 Напомни о встрече с Компанией Самолёт по поводу Курса такого\\-\\то\n"
            "• `/cancel` — Отменить текущую операцию\n"
            "\n📝 *Добавление записей:*\n"
            "• `/add` — Пошаговое добавление записи\n"
            "• `/ai_assistent` — Добавление через текстовую инструкцию\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Выполняйте задачи и закрывайте заказы\\!"
        )
    else:
        help_text = (
            "🚫 *Вы не зарегистрированы*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Обратитесь к директору для регистрации\\.\n"
            "📋 *Доступные команды:*\n"
            "• `/myid` — Узнать свой Telegram ID\n"
            "• `/start_work_day` — Включить бота \\после регистрации\\\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📞 Свяжитесь с директором для доступа\\!"
        )

    await update.message.reply_text(help_text, parse_mode="MarkdownV2")


__all__ = ["help_command"]
