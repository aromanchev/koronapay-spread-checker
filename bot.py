import prettytable
import telebot
import constants
import os
import time
import api_requests

TOKEN = os.environ["TOKEN"]
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

def calculate_spread(sending_amount, rate, binance_rate):
    receiving_amount = constants.KORONA_RECEIVING_AMOUNT / 100
    total_usd = receiving_amount / rate
    binance_total_amount = total_usd * binance_rate
    print(binance_total_amount)
    spread = 100 - (sending_amount / binance_total_amount * 100)
    return round(spread, 2)

def create_table():
    exchangers = api_requests.get_exchangers()

    binance_p2p_rate = float(api_requests.get_binance_p2p_rate())
    korona_pay = api_requests.get_koronapay()
    korona_pay_exchange_rate = korona_pay[0]['exchangeRate']
    korona_pay_sending_amount = korona_pay[0]['sendingAmount'] / 100

    table = prettytable.PrettyTable(['Обменник', 'USD' ,'Спред'])
    table.align['Обменник'] = 'l'
    table.align['USD'] = 'l'
    table.align['Спред'] = 'l'
    table.border = False

    for exchanger in exchangers:
        rate = exchanger['rates']['sellRate']
        company = exchanger['company']
        spread =  calculate_spread(korona_pay_sending_amount, rate, binance_p2p_rate)
        table.add_row([company, f'{rate:.3f}', f'{spread}%'])

    table.add_row(['------------', '', ''])
    table.add_row([f'\nKoronaPay GEL: ', f'\n{korona_pay_exchange_rate:.3f}', ''])
    
    content = f'<pre>{table}</pre>'
    return content

@bot.message_handler(commands=['start'])
def start_bot(message):
    bot.send_message(message.chat.id, f'Добро пожаловать @{message.from_user.username}!')

    table = create_table()
    bot.send_message(message.chat.id, table)
    
    while(True):
        bot.send_message(message.chat.id, table, time.sleep(60))
	
bot.infinity_polling()