import asyncio
import prettytable
from telebot.async_telebot import AsyncTeleBot
import constants
import os
import api_requests

TOKEN = os.environ["TOKEN"]

def calculate_spread(sending_amount, rate, binance_rate):
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

async def bot_polling():
    print("Starting bot polling now")
    while True:
        try:
            bot = AsyncTeleBot(TOKEN, parse_mode="HTML")
            bot_actions(bot)
            asyncio.run(bot.polling(none_stop=True, interval=constants.BOT_INTERVAL, timeout=constants.BOT_TIMEOUT))
        except Exception as ex: #Error in polling
            asyncio.run(bot.stop_polling())
            await asyncio.sleep(constants.BOT_TIMEOUT)
        else:
            asyncio.run(bot.stop_polling())
            break

def bot_actions(bot):
    @bot.message_handler(commands=["start"])
    async def start_bot(message):
        await bot.send_message(message.chat.id, f'Добро пожаловать @{message.from_user.username}!')
        while (True):
            table_updated = create_table()
            await bot.send_message(message.chat.id, table_updated)
            await asyncio.sleep(60)

bot_polling()
