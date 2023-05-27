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
PORT = int(os.environ.get('PORT', '8443'))
application = Application.builder().token(TOKEN).read_timeout(30).get_updates_read_timeout(60).build()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------- API REQUESTS ------------------------------
def get_koronapay() -> list[object]:
    response = requests.get(url = constants.KORONA_API, params=constants.KORONA_API_QUERY, headers=constants.KORONA_API_HEADERS)
    data = response.json()
    return data

def get_binance_p2p_rate() -> int:
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

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

# ---------------------------- BOT ACTIONS ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=f'Добро пожаловать @{update.message.from_user.username}!\n\n' +
                                   '/spread - Получение информации по спреду\n' + 
                                   '/auto_messaging - Рассылка информации по спреду\n' +
                                   '/stop_messaging - Остановка рассылки')

async def get_spread(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    table = create_table()
    await context.bot.send_message(chat_id=chat_id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)

async def start_auto_messaging(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_repeating(spread_auto_messaging, 300, chat_id=chat_id, name=str(chat_id))
    await context.bot.send_message(chat_id=chat_id, text=f'Вы будете получать актуальную информацию по спреду каждые 5 минут!', parse_mode=ParseMode.HTML)

async def stop_messaging(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    remove_job_if_exists(str(chat_id), context)
    await context.bot.send_message(chat_id=chat_id, text='Остановка рассылки!')

async def spread_auto_messaging(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    table = create_table()
    await context.bot.send_message(chat_id=job.chat_id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)

# ---------------------------- SETUP ------------------------------
application.add_error_handler(error_handler)
application.add_handler(CommandHandler(["start", "help"], start))
application.add_handler(CommandHandler("spread", get_spread))
application.add_handler(CommandHandler("auto_messaging", start_auto_messaging))
application.add_handler(CommandHandler("stop_messaging", stop_messaging))
application.run_webhook(
        listen="0.0.0.0",
        port=int(PORT),
        secret_token="koronaPAY"
        webhook_url='https://koronapay-spread.herokuapp.com/'
    )
