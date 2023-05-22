import logging
import constants
import os
import api_requests
import prettytable
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode


TOKEN = os.environ["TOKEN"]
SECRET_KEY = os.environ["SECRET_KEY"]
PORT = int(os.environ.get('PORT', '8443'))
application = Application.builder().token(TOKEN).read_timeout(60).get_updates_read_timeout(60).build()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
aps_logger = logging.getLogger('apscheduler')
aps_logger.setLevel(logging.WARNING)

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

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

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    table = create_table()
    await context.bot.send_message(chat_id=chat_id, text=f'Добро пожаловать @{update.message.from_user.username}!')
    await context.bot.send_message(chat_id=chat_id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
    remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_repeating(spread_auto_messaging, 300, chat_id=chat_id)

async def spread_auto_messaging(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    table = create_table()
    await context.bot.send_message(chat_id=job.chat_id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)


application.add_handler(CommandHandler("start", start_bot))

application.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    secret_token='koronapay_spread',
    webhook_url="https://koronapay-spread.herokuapp.com/"
)
