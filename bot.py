import logging
import prettytable
from telegram.ext import Application, CommandHandler
from telegram.constants import ParseMode
import constants
import os
import api_requests

TOKEN = os.environ["TOKEN"]
application = Application.builder().token(TOKEN).build()
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

async def start_bot(update, context):
    table = create_table()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Добро пожаловать @{update.message.from_user.username}!')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
    context.job_queue.run_repeating(spread_auto_messaging, 300, chat_id=update.message.chat_id)

async def spread_auto_messaging(context):
    job = context.job
    table = create_table()
    await context.bot.send_message(chat_id=job.chat_id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)


application.add_handler(CommandHandler("start", start_bot))

application.run_polling(drop_pending_updates=True)