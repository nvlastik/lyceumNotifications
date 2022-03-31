import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater

from _helpers import (add_notifications_to_user, add_user, get_user_by_id,
                      join_notifications)
from db import db_session
from main import YLNotifications

load_dotenv()

db_session.global_init("db/database.db")

CHECK_INTERVAL = 60  # in seconds

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def check_notifications(context: CallbackContext):
    job = context.job
    notifier = job.context[2]
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
        context.bot.send_message(user_id,
                                 text="<b>Вы не зарегистрированы!</b>", parse_mode='HTML')


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
            check_notifications, CHECK_INTERVAL, context=(chat_id, update.message.from_user['id'],
                                                          context.user_data['notifier']), name=str(chat_id))

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
    notifier = context.user_data['notifier']
    update.message.reply_html(notifier.get_last_notification())


def send_all_notifications(update: Update, context: CallbackContext):
    """Send Yandex Lyceum notifications"""
    notifier = context.user_data['notifier']
    update.message.reply_html(join_notifications(
        notifier.get_all_notifications()))


def begin_register(update: Update, context: CallbackContext):
    update.message.reply_html(
        "<b>Через пробел введите команду <code>/enter</code> , почту, а затем пароль от LMS (кликните, чтобы скопировать шаблон):\n\n</b><code>/enter [почта] [пароль]</code>")


def finish_register(update: Update, context: CallbackContext):
    email, password = context.args[0], context.args[1]
    try:

        notifier = YLNotifications(email, password)
        context.user_data['notifier'] = notifier

        if not add_user({'email': email, 'password': password, 'id': update.message.chat_id}, db_session):
            update.message.reply_text(
                'Вы уже зарегистрированы! Введите /help чтобы узнать подробнее обо всех командах')
        else:
            update.message.reply_text(
                'Регистрация прошла успешно! Введите /help чтобы узнать подробнее обо всех командах')

        context.bot.delete_message(chat_id=update.message.chat_id,
                                   message_id=update.message.message_id)

    except Exception as e:
        print(e)
        update.message.reply_text(
            'Введены некорректные данные! Пожалуйста введите команду /enter повторно.')


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
