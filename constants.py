EXCHANGE_RATE_API = 'https://mapi.ge/_next/data/Id9M_PzvWg56xBII11XLF/index.json'

KORONA_RECEIVING_AMOUNT = 400000
KORONA_API = 'https://koronapay.com/transfers/online/api/transfers/tariffs'
KORONA_API_QUERY = {
    'sendingCountryId': 'RUS',
    'sendingCurrencyId': '810',
    'receivingCountryId': 'GEO',
    'receivingCurrencyId': 981,
    'paymentMethod': 'debitCard',
    'receivingAmount': 400000,
    'receivingMethod': 'cash',
    'paidNotificationEnabled': 'False'
}
KORONA_API_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'}

BINANCE_API = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
BINANCE_API_PAYLOAD = {
  'asset': 'USDT',
  'fiat': 'RUB',
  'countries': ['RU'],
  'merchantCheck': 'False',
  'page': 1,
  'payTypes': ['TinkoffNew', 'RaiffeisenBank'],
  'publisherType': None,
  'rows': 10,
  'tradeType': 'sell'
}

BOT_INTERVAL = 2
BOT_TIMEOUT = 10
