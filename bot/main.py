from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext,
)
from bot.config.settings import (
    TOKEN,
    CLIENT_NAME,
    COURSE,
    CONTRACT_AMOUNT,
    PAYMENT_STATUS,
    PLAN,
    LLM_ADD,
)
from bot.handlers.basic_handlers import (
    start,
    help_command,
    myid,
    end_of_day_reminder,
    start_work_day,
    process_new_tasks,
    finish_work_day,
    process_feedback,
    cancel_feedback,
)
from bot.handlers.add_handlers import (
    add,
    get_client_name,
    get_course,
    get_contract_amount,
    get_payment_status,
    get_plan,
    cancel,
)
from bot.handlers.llm_handlers import llm_add, process_llm_instruction
from bot.handlers.admin_handlers import setup_handlers as setup_admin_handlers
from bot.handlers.reminder_handlers import setup_reminder_handlers, start_scheduler
from bot.utils.role_manager import role_manager
import sqlite3
import logging

ADD_TASKS = 2
FEEDBACK = 1


async def error_handler(update: Update, context: CallbackContext) -> None:
    logging.error(f"Произошла ошибка: {context.error}", exc_info=True)
    if update and update.message:
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")


async def post_init(application):
    start_scheduler(application)


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_error_handler(error_handler)

    def check_first_director(update, context):
        user_id = update.effective_user.id
        if role_manager.get_role(user_id) is None:
            with sqlite3.connect("users.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                if user_count == 0:
                    role_manager.add_user(user_id, "director")
                    update.message.reply_text(
                        f"Вы первый пользователь и автоматически назначены директором!\n"
                        f"Ваш Telegram ID: {user_id}"
                    )
        return start(update, context)

    app.add_handler(CommandHandler("start", check_first_director))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("myid", myid))

    start_work_handler = ConversationHandler(
        entry_points=[CommandHandler("start_work_day", start_work_day)],
        states={
            ADD_TASKS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_new_tasks)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_feedback)],
    )
    app.add_handler(start_work_handler)

    finish_handler = ConversationHandler(
        entry_points=[CommandHandler("finish_work_day", finish_work_day)],
        states={
            FEEDBACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_feedback)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_feedback)],
    )
    app.add_handler(finish_handler)

    setup_admin_handlers(app)
    setup_reminder_handlers(app)

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add", add),
            CommandHandler("ai_assistent", llm_add),
        ],
        states={
            CLIENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_name)
            ],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_course)],
            CONTRACT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_contract_amount)
            ],
            PAYMENT_STATUS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment_status)
            ],
            PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_plan)],
            LLM_ADD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_llm_instruction)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)

    print("🤖 Бот запущен!")
    app.run_polling(timeout=10)


if __name__ == "__main__":
    main()
