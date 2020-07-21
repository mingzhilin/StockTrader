#import os
#import sys
#import pickle
#import requests
from datetime import date
from datetime import datetime
from threading import Thread
from threading import Timer
#from multiprocessing import Process

import CompanyInfo
import StockComprehensiveReport
import StockDailyQuote
import StockDividendQuote
import StockEpsQuote
import StockMarginQuote
import StockProfitQuote
import StockRevenueQuote
import StockRealTimeReport
import StockLegalTrader

from StockDailyQuote import DailyQuote
from StockDividendQuote import DividendQuote
from StockEpsQuote import EpsQuote
from StockMarginQuote import MarginQuote
from StockProfitQuote import ProfitQuote
from StockRevenueQuote import RevenueQuote
from StockRealTimeReport import RealTimeReport
from StockLegalTrader import LegalTrader


TIME = {
    'RetriveAllQuotes': {'hour': 19, 'minute': 0, 'second': 0},
    'startRealTimeReport': {'hour': 9, 'minute': 5, 'second': 0},
    'stopRealTimeReport': {'hour': 13, 'minute': 20, 'second': 0}
}


def displayMainMenu():
    print('\n')
    print(' 0. 產出綜合報表 (StockComprehensiveReport)')
    print(' 1. 擷取即時量價資料、並產出報表 (StockRealTimeReport)')
    print(' 2. 擷取每日資料 (StockDailyQuote)')
    print(' 3. 擷取融資、融券資料 (StockMarginQuote)')
    print(' 4. 擷取法人買賣超資料 (StockLegalTrader)')
    print(' 5. 擷取營收資料 (StockRevenueQuote)')
    print(' 6. 擷取EPS資料 (StockEpsQuote)')
    print(' 7. 擷取營利資料 (StockProfitQuote)')
    print(' 8. 擷取股息、股利資料 (StockDividendQuote)')
    print(' 9. 擷取全部資料 (RetriveAllQuotes)')
    print('10. 擷取公司資料 (CompanyInfo)')
    print('11. 結束')
    print('>> 選擇指令 (數字、ENTER)：', end='')


def calculateStartExecTime(startTime):
    now = datetime.now()

    hour = startTime['hour']
    minute = startTime['minute']
    second = startTime['second']

    second -= now.second
    if second < 0:
        second += 60
        minute -= 1

    minute -= now.minute
    if minute < 0:
        minute += 60
        hour -= 1

    hour -= now.hour
    if hour < 0:
        hour += 24

    startExecTime = hour * 60 * 60 + minute * 60 + second
    #print('startExecTime =', startExecTime)

    return startExecTime


def setupAutoExecution():
    # 自動擷取全部資料
    startExecTime = calculateStartExecTime(TIME['RetriveAllQuotes'])
    thread = Timer(startExecTime, retriveAllQuotes)
    thread.daemon = True
    thread.start()

    # 自動擷取即時量價資料
    startExecTime = calculateStartExecTime(TIME['startRealTimeReport'])
    thread = Timer(startExecTime, retriveRealTimeQuotes)
    thread.daemon = True
    thread.start()


def retriveAllQuotes():
    print('\n')

    # 開始時間
    startTime = datetime.now()

    threads = {
        0: Thread(target=StockDailyQuote.retriveAllStocksMultiThread),
        1: Thread(target=StockDividendQuote.retriveAllStocksMultiThread),
        2: Thread(target=StockEpsQuote.retriveAllStocksMultiThread),
        3: Thread(target=StockMarginQuote.retriveAllStocksMultiThread),
        4: Thread(target=StockLegalTrader.retriveAllStocks),
        5: Thread(target=StockProfitQuote.retriveAllStocksMultiThread),
        6: Thread(target=StockRevenueQuote.retriveAllStocksMultiThread),
        7: Thread(target=StockRealTimeReport.retriveAllStocksMultiThread)
    }

    for i in range(len(threads)):
        threads[i].daemon = True
        threads[i].start()
        threads[i].join()

    # 輸出報表
    StockComprehensiveReport.retriveAllStocks()

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[Autorun]')
    print('執行時間 (時：分：秒)：', stopTime - startTime)

    print('\n按ENTER完成')
    #displayMainMenu()


def retriveRealTimeQuotes():
    if isMarketOpen():
        thread = Thread(target=StockRealTimeReport.retriveAllStocksMultiThread)
        thread.daemon = True
        thread.start()
        thread.join()

        now = datetime.now()
        currTime = now.hour * 60 * 60 + now.minute * 60 + now.second

        stopTime = TIME['stopRealTimeReport']['hour'] * 60 * 60 +  \
                   TIME['stopRealTimeReport']['minute'] * 60 +     \
                   TIME['stopRealTimeReport']['second']

        #print('currTime =', currTime)
        #print('stopTime =', stopTime)

        if currTime > stopTime:
            startExecTime = calculateStartExecTime(TIME['startRealTimeReport'])
        else:
            startExecTime = 5

        thread = Timer(startExecTime, retriveRealTimeQuotes)
        thread.daemon = True
        thread.start()
    else:
        startExecTime = calculateStartExecTime(TIME['startRealTimeReport'])
        thread = Timer(startExecTime, retriveRealTimeQuotes)
        thread.daemon = True
        thread.start()


def isMarketOpen():
    stockNos = [1301, 1326, 2317, 2330, 2882]

    prevDailyQuote = StockDailyQuote.loadQuotes(0, 1)[0]

    for i in stockNos:
        try:
            quote = DailyQuote(i)
            quote.retriveQuote()
            if quote.volume != prevDailyQuote[i].volume:
                return True
        except:
            continue

    return False


if __name__ == '__main__':
    FUNCTIONS = {
        '0': StockComprehensiveReport.retriveAllStocks,
        '1': StockRealTimeReport.retriveAllStocksMultiThread,
        '2': StockDailyQuote.retriveAllStocksMultiThread,
        '3': StockMarginQuote.retriveAllStocksMultiThread,
        '4': StockLegalTrader.retriveAllStocksMultiThread,
        '5': StockRevenueQuote.retriveAllStocksMultiThread,
        '6': StockEpsQuote.retriveAllStocksMultiThread,
        '7': StockProfitQuote.retriveAllStocksMultiThread,
        '8': StockDividendQuote.retriveAllStocksMultiThread,
        '9': retriveAllQuotes,
        '10': CompanyInfo.search_whole_market,
        '11': exit
    }

    while True:
        #setupAutoExecution()
        displayMainMenu()
        commands = input()
        commands = commands.split()
        for command in commands:
            if FUNCTIONS.get(command):
                FUNCTIONS[command]()
