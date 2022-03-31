import logging
import os

from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)
from _helpers import join_notifications

from main import YLNotifications


load_dotenv()


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

notifier = YLNotifications(os.environ.get('YANDEX_LOGIN'),
                           os.environ.get('YANDEX_PASSWORD'))


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(fr'Привет {user.mention_markdown_v2()}\! Я Yandex Lyceum Notifier Bot\. Буду отсылать тебе все уведомления из твоего LMS :\)',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text('/last - получить последнее уведомление\n/all - получить все уведомления')


def send_last_notification(update: Update, context: CallbackContext):
    """Send Yandex Lyceum notifications"""
    update.message.reply_html(notifier.get_last_notification())


def send_all_notifications(update: Update, context: CallbackContext):
    """Send Yandex Lyceum notifications"""
    update.message.reply_html(join_notifications(notifier.get_all_notifications()))

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.environ.get('TELEGRAM_TOKEN'))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))


    # dispatcher.add_handler(MessageHandler(
    #     Filters.text & ~Filters.command, send_notifications))
    
    dispatcher.add_handler(CommandHandler("last", send_last_notification))
    dispatcher.add_handler(CommandHandler("all", send_all_notifications))
    
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    
    


if __name__ == '__main__':
    main()
