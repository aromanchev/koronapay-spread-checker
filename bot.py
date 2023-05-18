import logging
import prettytable
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode
import constants
import os
import api_requests

TOKEN = os.environ['TOKEN']
PORT = int(os.environ.get('PORT', '8443'))
APP_NAME = os.environ['APP_NAME']

updater = Updater(TOKEN, use_context=True)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_spread(sending_amount: int, rate: int, binance_rate: int):
    receiving_amount = constants.KORONA_RECEIVING_AMOUNT / 100
    total_usd = receiving_amount / rate
    binance_total_amount = total_usd * binance_rate
    spread = 100 - (sending_amount / binance_total_amount * 100)
    return round(spread, 2)


def create_table():
    exchangers = api_requests.get_exchangers()

    binance_p2p_rate = float(api_requests.get_binance_p2p_rate())
    korona_pay = api_requests.get_koronapay()
    korona_pay_exchange_rate = korona_pay[0]['exchangeRate']
    korona_pay_sending_amount = korona_pay[0]['sendingAmount'] / 100

    table = prettytable.PrettyTable(['Обменник', 'USD', 'Спред'])
    table.align['Обменник'] = 'l'
    table.align['USD'] = 'l'
    table.align['Спред'] = 'l'
    table.border = False

    for exchanger in exchangers:
        rate = exchanger['rates']['sellRate']
        company = exchanger['company']
        spread = calculate_spread(
            korona_pay_sending_amount, rate, binance_p2p_rate)
        table.add_row([company, f'{rate:.3f}', f'{spread}%'])

    table.add_row(['------------', '', ''])
    table.add_row(
        [f'\nKoronaPay GEL: ', f'\n{korona_pay_exchange_rate:.3f}', ''])

    content = f'<pre>{table}</pre>'
    return content

def start_bot(update, context):
    table = create_table()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Добро пожаловать @{update.message.from_user.username}!')
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
    context.job_queue.run_repeating(spread_auto_messaging, 180, context=update.message.chat_id)


def spread_auto_messaging(context):
    table = create_table()
    context.bot.send_message(chat_id=context.job.context, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)


dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler("start", start_bot))
updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=APP_NAME + TOKEN)


updater.start_polling()
updater.idle()