from bitkub import Bitkub
import pandas as pd
from datetime import datetime
import pytz
from songline import Sendline

API_KEY = '...................................'
API_SECRET = '................................'

token = '.....................................'

messenger = Sendline(token)

bitkub = Bitkub(api_key=API_KEY, api_secret=API_SECRET)
bitkub.servertime()
pd.to_datetime(bitkub.servertime(), unit='s')

posframe = pd.read_csv('config_.csv')
# df = pd.DataFrame(posframe)
# print(posframe)
ticker = pd.DataFrame(bitkub.ticker()) #sym='THB_BTC')

lim_pct = 0.02
lim_value = 10
period =    5*300*5   #5*60*300 #

Sma_W = 5*60*24*7

def changpos(curr, buy=True):
    if buy:
        posframe.loc[posframe.Currency == curr, 'position'] = 0      #1
    # else:
    #     posframe.loc[posframe.Currency == curr, 'position'] = 0
    # posframe.to_csv('position', index=False)

def gethourldata(symbol):
    data = bitkub.tradingview(sym= symbol, int=5, 
                                        frm=(bitkub.servertime()-period), 
                                        to=bitkub.servertime())

    frame = pd.DataFrame(data)
    # frame = frame.iloc[:,:6]
    frame = frame[['t','o','h','l','c','v','s']]
    frame.columns = ['Timestamp','Open','High','Low','Close','Volume','status']
    frame['Timestamp'] = pd.to_datetime(frame['Timestamp'], unit='s').dt.tz_localize('Asia/Bangkok')
    return frame
df = gethourldata('BTC_THB')

def applytechnicals(df):
    df['FastEMA'] = df.Close.ewm(7).mean()
    df['SlowEMA'] = df.Close.ewm(25).mean()
    df['SMA_'] = df.Close.rolling(20).mean()  
    df['stddev'] = df.Close.rolling(20).std()
    df['Upper'] = df.SMA_ + 2 * df.stddev
    df['Lower'] = df.SMA_ - 2 * df.stddev    
    df['SMA_W'] = df.Close.rolling(Sma_W).mean()  
applytechnicals(df)    

def balance(coin_):
    bal = pd.DataFrame(bitkub.wallet())
    balance = bal['result'][coin_] 
    return balance

def orderhistory(crr):
    hisframe = bitkub.my_open_history(sym=crr, p=1, lmt=1)
    hisframe = pd.DataFrame(hisframe['result']) 
    orderhis = hisframe[['date','side','amount','rate','fee','credit','txn_id']]
    orderhis.to_csv('order_record.csv', mode='a', header=False, index=False)    
    order    = hisframe[['side','amount','rate']][0:1]
    amnt = order.amount
    rat  = order.rate
    order['value'] = float(amnt) * float(rat)
    print(f'{crr}',  order.set_index('side'))

def report(curr,qty,price,amts,value,re_sell):
    print(f' Rebalancing: Fix {curr} {qty}')
    print(f' Price: {price}, amt: {amts}')    
    print(f' Lastvalue: {value}, P/L: {re_sell}')
    print('-----------------------------------')


def trader(curr):
    qty = posframe[posframe.Currency == curr].quantity.values[0]
    coins  = posframe[posframe.Currency == curr].coins.values[0]
    crr    = posframe[posframe.Currency == curr].crr.values[0]
    pct_   = posframe[posframe.Currency == curr].pct.values[0]
    df = gethourldata(curr)   
    applytechnicals(df)   
    amts = balance(coins)
    lastrow = df.iloc[-1]
    price = lastrow.Close
    value  = '%.2f'%(float(amts) * float(price))
    re_buy  = '%.2f'%(float(qty) - float(value))
    re_sell = '%.2f'%(float(value) - float(qty))
    pct = float(qty) * pct_ #lim_pct


    if posframe[posframe.Currency == curr].quantity.values[0]:
        report(curr,qty,price,amts,value,re_sell)        

        if price < lastrow.Lower or price > lastrow.SMA_ and float(re_sell) <= lim_value:

            if  float(re_buy) <= lim_value:
                pass

            elif float(re_buy) >= lim_value and float(re_buy) >= pct:

                bitkub.place_bid(sym= crr, 
                                 amt= re_buy, 
                                 typ='market')
                time.sleep(3)
                orderhistory(crr)    
                print('______________________________________________')
                # changpos(curr, buy=True)

                messenger.sendtext(f' Buy {curr} : {price} : values {re_buy} ')
          

        elif  price > lastrow.Upper or price < lastrow.SMA_ and float(re_buy) <= lim_value:

            if  float(re_sell) <= lim_value:
                pass

            elif float(re_sell) >= lim_value and float(re_sell) >= pct:

                    sell = '%.4f'%(float(re_sell) / price)

                    bitkub.place_ask(sym= crr, 
                                     amt= sell,  
                                     typ='market') 
                    time.sleep(3)
                    orderhistory(crr)                 
                    print('______________________________________________')
                    # changpos(curr, buy=True)

                    messenger.sendtext(f' Sell {curr} : {price} : values {re_sell} ')

    else:
        print('Nothing')


import time

while True:
    time.sleep(60)
    for coin in posframe.Currency:
        try:
            trader(coin)
        except KeyboardInterrupt:
            print(f' error: {KeyboardInterrupt}')
            pass
        except:
            continue






#==========================================================================================================#






# symbols = ['THB_BTC','THB_ETH','THB_KUB','THB_XRP']
