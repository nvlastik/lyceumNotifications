import logging
import os

from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)
from _helpers import join_notifications, get_notification_by_id, get_user_by_id, add_notifications_to_user

from main import YLNotifications

from db import db_session
from models.notification import Notification
from models.user import User

load_dotenv()

db_session.global_init("db/database.db")

INTERVAL = 10

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

notifier = YLNotifications(os.environ.get('YANDEX_LOGIN'),
                           os.environ.get('YANDEX_PASSWORD'))

users_notifications = {}


def check_notifications(context: CallbackContext):
    job = context.job
    notifications = notifier.get_all_notifications()
    user_id = job.context[1]

    try:
        user_notifications = set(get_user_by_id(
            user_id, db_session).notifications)
        user_notifications_id = set(
            map(notif.id for notif in user_notifications))
        notifications_to_add = set()

        for notification_id, notification in notifications.items():
            if notification_id not in user_notifications_id:
                context.bot.send_message(
                    user_id, text=notification, parse_mode='HTML')
                notifications_to_add.add(notification_id)
        add_notifications_to_user(notifications_to_add, user_id, db_session)

    except AttributeError:
        context.bot.send_message(
            user_id, text="<b>Вы не зарегистрированы!</b>", parse_mode='HTML')


def remove_job_if_exists(name: str, context: CallbackContext):
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def enable_notifications_checker(update: Update, context: CallbackContext):
    """Add a job to the queue."""

    chat_id = update.message.chat_id
    try:
        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(
            check_notifications, INTERVAL, context=(chat_id, update.message.from_user['id']), name=str(chat_id))

        text = 'Отслеживание уведомлений включено!'
        if job_removed:
            text = 'Уведомления уже отслеживаются!'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Использование: /enable')


def disable_notifications_checker(update: Update, context: CallbackContext):
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Отслеживание уведомлений отключено!' if job_removed else 'Отслеживание не включено.'
    update.message.reply_text(text)


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(fr'Привет {user.mention_markdown_v2()}\! Я Yandex Lyceum Notifier Bot\.\
 Буду отсылать тебе все уведомления из LMS :\)')


def help_command(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        '/enable - включить отслеживание уведомлений \n/disable - выключить\n/last - получить последнее уведомление\n/all - получить все уведомления\n')


def send_last_notification(update: Update, context: CallbackContext):
    """Send Yandex Lyceum notifications"""
    update.message.reply_html(notifier.get_last_notification())


def send_all_notifications(update: Update, context: CallbackContext):
    """Send Yandex Lyceum notifications"""
    update.message.reply_html(join_notifications(
        notifier.get_all_notifications()))

def begin_register(update: Update, context: CallbackContext):
    update.message.reply_html("<b>Через пробел введите команду <code>/enter</code> , почту, а затем пароль от LMS (кликните, чтобы скопировать шаблон):\n\n</b><code>/enter [почта] [пароль]</code>")


def finish_register(update: Update, context: CallbackContext):
    email, password = context.args[0], context.args[1] 
    #todo проверить корректность, добавить пользователя в бд
    
def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.environ.get('TELEGRAM_TOKEN'))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(CommandHandler("last", send_last_notification))
    dispatcher.add_handler(CommandHandler("all", send_all_notifications))

    dispatcher.add_handler(CommandHandler(
        "enable", enable_notifications_checker))
    dispatcher.add_handler(CommandHandler(
        "disable", disable_notifications_checker))
    
    dispatcher.add_handler(CommandHandler("register", begin_register))
    dispatcher.add_handler(CommandHandler("enter", finish_register))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
