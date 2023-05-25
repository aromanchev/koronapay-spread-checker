import logging
import constants
import os
import requests
import constants
import prettytable
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# ---------------------------- B0T CONFIG ------------------------------
TOKEN = os.environ["TOKEN"]
application = Application.builder().token(TOKEN).read_timeout(30).get_updates_read_timeout(42).build()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------- API REQUESTS ------------------------------
def get_koronapay():
    response = requests.get(url = constants.KORONA_API, params=constants.KORONA_API_QUERY, headers=constants.KORONA_API_HEADERS)
    data = response.json()
    return data

def get_binance_p2p_rate():
    response = requests.post(url = constants.BINANCE_API, json = constants.BINANCE_API_PAYLOAD)
    data = response.json()
    for slot in data['data']:
        seller_rate = int(slot['advertiser']['monthFinishRate'] * 100)
        if seller_rate > 95:
            binance_p2p_rate = slot['adv']['price']
            break
    return binance_p2p_rate

def get_exchangers() -> list[object]:
    response = requests.get(url = constants.EXCHANGE_RATE_API)
    data = response.json()['pageProps']['exchangesStaticProps']['usd']
    return data

# ---------------------------- UTILITY ------------------------------
def calculate_spread(sending_amount: int, rate: int, binance_rate: int):
    receiving_amount = constants.KORONA_RECEIVING_AMOUNT / 100
    total_usd = receiving_amount / rate
    binance_total_amount = total_usd * binance_rate
    spread = 100 - (sending_amount / binance_total_amount * 100)
    return round(spread, 2)


def create_table():
    exchangers = get_exchangers()

    binance_p2p_rate = float(get_binance_p2p_rate())
    korona_pay = get_koronapay()
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
        spread = calculate_spread(korona_pay_sending_amount, rate, binance_p2p_rate)
        table.add_row([company, f'{rate:.3f}', f'{spread}%'])

    table.add_row(['------------', '', ''])
    table.add_row([f'\nKoronaPay GEL: ', f'\n{korona_pay_exchange_rate:.3f}', ''])

    content = f'<pre>{table}</pre>'
    return content

# ---------------------------- BOT ACTIONS ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    table = create_table()
    context.job_queue.run_repeating(spread_auto_messaging, 300, chat_id=chat_id, job_kwargs={'max_instances': 10})
    await context.bot.send_message(chat_id=chat_id, text=f'Добро пожаловать @{update.message.from_user.username}!')
    await context.bot.send_message(chat_id=chat_id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)

async def spread_auto_messaging(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    table = create_table()
    await context.bot.send_message(chat_id=job.chat_id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)

if __name__ == '__main__':
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler(["start"], start))
    application.run_polling()
