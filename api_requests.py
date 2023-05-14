import requests
import constants

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

def get_exchangers():
    response = requests.get(url = constants.EXCHANGE_RATE_API)
    data = response.json()['pageProps']['exchangesStaticProps']['usd']
    return data