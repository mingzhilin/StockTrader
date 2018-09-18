import os
import sys
import pickle
import requests
from datetime import date
from datetime import datetime
from lxml.html import fromstring
from threading import Thread

import StockDailyQuote


class MarginQuote():
    def __init__(self, stockNo):
        self.stockNo = stockNo          # 股票代號
        self.marginLong = {             # 融資
            'increase': 0,              # 淨增減
            'ratio': 0                  # 使用率
        }
        self.marginShort = {            # 融券
            'increase': 0,              # 淨增減
            'ratio': 0                  # 券資比
        }

    def display(self):
        print('stockNo =', self.stockNo)
        print('marginLong =', self.marginLong)
        print('marginShort =', self.marginShort)

    def retriveHtml(self, url, payload=''):
        #retryCount = 0
        while True:
            try:
                response = requests.post(url, data=payload, timeout=5)
            except:
                #retryCount += 1
                #if retryCount >= 10:
                #    return None
                continue
            break
        try:
            html = fromstring(response.content)
        except:
            html = None
        return html

    def retriveQuote(self):
        stockNo = '{n:04d}'.format(n=self.stockNo)
        url = 'http://pchome.megatime.com.tw/stock/sto1/ock1/sid' + stockNo + '.html'
        payload = {'is_check': 1}
        html = self.retriveHtml(url, payload)
        if html is None:
            return False

        nodes = html.xpath('//tr/th/text() | //tr/td/text()')
        if not nodes:
            return False

        # 融資
        index = nodes.index('日期')
        nodes = nodes[index:]
        try:
            self.marginLong['increase'] = int(nodes[13].replace(',', ''))
            self.marginLong['ratio'] = float(nodes[15][:-1]) / 100
        except:
            return False

        # 融券
        nodes = nodes[7:]
        index = nodes.index('日期')
        nodes = nodes[index:]
        try:
            self.marginShort['increase'] = int(nodes[13].replace(',', ''))
            self.marginShort['ratio'] = float(nodes[15]) / 100
        except:
            return False

        return True


def retriveOneStock(stockNo):
    quote = MarginQuote(stockNo)
    quote.retriveQuote()
    quote.display()


def retriveStocks(division, prevDailyQuotes):
    for stockNo in range(division['start'], division['stop']):
        print('股票代號：', stockNo, end='\r')
        if prevDailyQuotes.get(stockNo) is None:
            continue
        quote = MarginQuote(stockNo)
        if quote.retriveQuote() is True:
            division['quotes'][stockNo] = quote


def retriveAllStocksMultiThread():
    START_STOCK_NO = 1000       # 啟始代號
    STOP_STOCK_NO = 10000       # 結束代號
    DIVISION_COUNT = 30         # 分割太多會掉資料
    STOCK_COUNT_PER_DIVISION = (STOP_STOCK_NO - START_STOCK_NO) // DIVISION_COUNT

    # 開始時間
    startTime = datetime.now()

    # 分割區間
    divisions = {}
    for i in range(DIVISION_COUNT):
        divisions[i] = {}
        divisions[i]['quotes'] = {}
        divisions[i]['start'] = i * STOCK_COUNT_PER_DIVISION + START_STOCK_NO
        divisions[i]['stop'] = divisions[i]['start'] + STOCK_COUNT_PER_DIVISION

    # 讀取歷史資料
    prevDailyQuotes = StockDailyQuote.loadQuotes(0, 1)[0]

    # 讀取資料
    threads = {}
    for i in range(DIVISION_COUNT):
        args = (divisions[i], prevDailyQuotes)
        threads[i] = Thread(target=retriveStocks, args=args)
        threads[i].daemon = True
        threads[i].start()

    for i in range(DIVISION_COUNT):
        threads[i].join()
    print('\n')

    quotes = {}
    for i in range(DIVISION_COUNT):
        quotes = {**quotes, **divisions[i]['quotes']}

    # 檢查輸出路徑
    path = '../MarginQuote'
    if os.path.exists(path) is False:
        os.mkdir(path)

    # 輸出檔案
    filePath = path + '/MarginQuote(' + str(date.today()) + ').pkl'
    with open(filePath, 'wb') as outputFile:
        pickle.dump(quotes, outputFile, protocol=pickle.HIGHEST_PROTOCOL)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockMarginQuote]')
    print('捕獲股票數量：', len(quotes))
    print('輸出檔案名稱：', filePath)
    print('輸出檔案大小 (位元組)：', os.path.getsize(filePath))
    print('執行時間 (時：分：秒)：', stopTime - startTime)
    print('\n')


def retriveAllStocks():
    # 開始時間
    startTime = datetime.now()

    # 讀取資料
    quotes = {}
    for stockNo in range(1000, 10000):
        print('股票代號：', stockNo)#, end='\r')
        quote = MarginQuote(stockNo)
        if quote.retriveQuote() is True:
            quotes[stockNo] = quote
            #quotes[stockNo].display()
    print('\n')

    # 檢查輸出路徑
    path = '../MarginQuote'
    if os.path.exists(path) is False:
        os.mkdir(path)

    # 輸出檔案
    filePath = path + '/MarginQuote(' + str(date.today()) + ').pkl'
    with open(filePath, 'wb') as outputFile:
        pickle.dump(quotes, outputFile, protocol=pickle.HIGHEST_PROTOCOL)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockMarginQuote]')
    print('捕獲股票數量：', len(quotes))
    print('輸出檔案名稱：', filePath)
    print('輸出檔案大小 (位元組)：', os.path.getsize(filePath))
    print('執行時間 (時：分：秒)：', stopTime - startTime)
    print('\n')


# quarterOffset: 從本月起算，往前計數
# quarterCount: 載入數量
def loadQuotes(quarterOffset, quarterCount):
    path = '../MarginQuote/'
    files = os.listdir(path)
    files.sort(reverse=True)

    start = quarterOffset
    stop = quarterOffset + quarterCount
    if stop > len(files):
        stop = len(files)

    quotes = {}
    for i in range(start, stop):
        with open (path+files[i], 'rb') as inputFile:
            quotes[i] = pickle.load(inputFile)

    return quotes


if __name__ == '__main__':
    # 指令格式(單一股票)：python StockMarginQuote.py [股票代號]
    # 指令格式(全部股票)：python StockMarginQuote.py
    if len(sys.argv) < 2:
        #retriveAllStocks()
        retriveAllStocksMultiThread()
    else:
        stockNo = int(sys.argv[1])
        retriveOneStock(stockNo)
