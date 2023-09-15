import os
import sys
import pickle
import requests
from datetime import date
from datetime import datetime
from lxml.html import fromstring
from threading import Thread


class DailyQuote():
    def __init__(self, stockNo):
        self.stockNo = stockNo          # 股票代號
        self.stockName = None           # 股票名稱
        self.closePrice = 0             # 成交價
        self.priceChange = 0            # 漲跌
        self.volume = 0                 # 成交量
        self.openPrice = 0              # 開盤價
        self.highPrice = 0              # 最高價
        self.lowPrice = 0               # 最低價

        self.industry = None            # 公司產業
        self.group = None               # 所屬集團
        self.capital = 0                # 資本額(億元)
        self.marketValue = 0            # 市值(億元)
        self.eps = 0                    # 每股盈餘(EPS)
        self.per = 0                    # 本益比(PER)
        self.cashDividend = 0           # 現金股利(元)
        self.shareDividend = 0          # 股票股利(元)
        self.cashYieldRate = 0          # 現金殖利率
        self.roe = 0                    # 股東權益報酬率(ROE)
        self.roa = 0                    # 資產報酬率(ROA)
        self.worthPerShare = 0          # 每股淨值(元)
        self.yearHighPrice = 0          # 一年內最高
        self.yearLowPrice = 0           # 一年內最低

    def display(self):
        print('stockNo =', self.stockNo)
        print('stockName =', self.stockName)
        print('closePrice =', self.closePrice)
        print('priceChange =', self.priceChange)
        print('volume =', self.volume)
        print('openPrice =', self.openPrice)
        print('highPrice =', self.highPrice)
        print('lowPrice =', self.lowPrice)

        print('industry =', self.industry)
        print('group =', self.group)
        print('capital =', self.capital)
        print('marketValue =', self.marketValue)
        print('eps =', self.eps)
        print('per =', self.per)
        print('cashDividend =', self.cashDividend)
        print('shareDividend =', self.shareDividend)
        if self.cashYieldRate is None:
            print('cashYieldRate = None')
        else:
            print('cashYieldRate =', '{0:.4%}'.format(self.cashYieldRate))
        print('roe =', '{0:.4%}'.format(self.roe))
        print('roa =', '{0:.4%}'.format(self.roa))
        print('worthPerShare =', self.worthPerShare)
        if self.yearHighPrice is None:
            print('yearHighPrice = None')
        else:
            print('yearHighPrice =', self.yearHighPrice)
        if self.yearLowPrice is None:
            print('yearHighPrice = None')
        else:
            print('yearLowPrice =', self.yearLowPrice)

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
        url = 'http://pchome.megatime.com.tw/stock/sid' + stockNo + '.html'
        payload = {'is_check': 1}
        html = self.retriveHtml(url, payload)
        if html is None:
            return False

        nodes = html.xpath('//meta[@name="description"]/@content')
        if not nodes:
            return False

        nodes1 = nodes[0].split(',')[0].split()
        # nodes2 = nodes[0].split(',')[1].split()

        # 股票名稱
        self.stockName = nodes1[0][0:-12]

        # 成交價
        try:
            self.closePrice = float(nodes1[3])
        except:
            self.closePrice = 0

        nodes = html.xpath('//tr/td/span//text() | //tr/td/text() | //tr/th/text() | \
                            //tr/th/a/text() | //tr/th/a/font/text()')
        if not nodes:
            return False

        index = nodes.index('漲跌') + 10
        nodes = nodes[index:]

        # 漲跌
        try:
            self.priceChange = float(nodes[0].replace(',', ''))
        except:
            self.priceChange = 0

        # 成交量
        try:
            self.volume = int(nodes[1].replace(',', ''))
        except:
            return False

        # 開盤價
        try:
            self.openPrice = float(nodes[6].replace(',', ''))
        except:
            self.openPrice = 0

        # 最高價
        try:
            self.highPrice = float(nodes[7].replace(',', ''))
        except:
            self.highPrice = 0

        # 最低價
        try:
            self.lowPrice = float(nodes[8].replace(',', ''))
        except:
            self.lowPrice = 0

        index = nodes.index('公司產業')
        nodes = nodes[index:]

        # 公司產業
        try:
            self.industry = nodes[9].split()[0]
        except:
            self.industry = None

        # 所屬集團
        try:
            self.group = nodes[10].split()[0]
        except:
            self.group = None

        # 資本額(億元)
        try:
            self.capital = float(nodes[11].replace(',', ''))
        except:
            self.capital = None

        # 市值(億元)
        try:
            self.marketValue = float(nodes[12].replace(',', ''))
        except:
            self.marketValue = None

        # 每股盈餘(EPS)
        try:
            self.eps = float(nodes[13])
        except:
            self.eps = None

        # 本益比(PER)
        try:
            self.per = float(nodes[14])
        except:
            self.per = None

        index = nodes.index('現金股利(元)')
        nodes = nodes[index:]

        # 現金股利(元)
        try:
            self.cashDividend = float(nodes[12])
        except:
            self.cashDividend = None

        # 股票股利(元)
        try:
            self.shareDividend = float(nodes[13])
        except:
            self.shareDividend = None

        # 現金殖利率
        try:
            self.cashYieldRate = float(nodes[14][:-1]) / 100
        except:
            self.cashYieldRate = None

        # 股東權益報酬率(ROE)
        try:
            self.roe = float(nodes[15][:-1]) / 100
        except:
            self.roe = None

        # 資產報酬率(ROA)
        try:
            self.roa = float(nodes[16][:-1]) / 100
        except:
            self.roa = None

        # 每股淨值(元)
        try:
            self.worthPerShare = float(nodes[17])
        except:
            self.worthPerShare = None

        index = nodes.index('累計營收(億元)')
        nodes = nodes[index:]

        # 一年內最高
        try:
            self.yearHighPrice = float(nodes[14])
        except:
            self.yearHighPrice = None

        # 一年內最低
        try:
            self.yearLowPrice = float(nodes[15])
        except:
            self.yearLowPrice = None

        return True


def retriveOneStock(stockNo):
    quote = DailyQuote(stockNo)
    quote.retriveQuote()
    quote.display()


def retriveStocks(division):
    for stockNo in range(division['start'], division['stop']):
        print('股票代號：', stockNo, end='\r')
        quote = DailyQuote(stockNo)
        if quote.retriveQuote() is True:
            division['quotes'][stockNo] = quote


def retriveAllStocksMultiThread():
    if isMarketOpen() is False:
        print('\n[StockDailyQuote]')
        print('最近一個交易日的資料已存在\n')
        return

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

    # 讀取資料
    threads = {}
    for i in range(DIVISION_COUNT):
        threads[i] = Thread(target=retriveStocks, args=(divisions[i],))
        threads[i].daemon = True
        threads[i].start()

    for i in range(DIVISION_COUNT):
        threads[i].join()
    print('\n')

    quotes = {}
    for i in range(DIVISION_COUNT):
        quotes = {**quotes, **divisions[i]['quotes']}

    # 檢查輸出路徑
    path = '../DailyQuote'
    if os.path.exists(path) is False:
        os.mkdir(path)

    # 輸出檔案
    filePath = path + '/DailyQuote(' + str(date.today()) + ').pkl'
    with open(filePath, 'wb') as outputFile:
        pickle.dump(quotes, outputFile, protocol=pickle.HIGHEST_PROTOCOL)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockDailyQuote]')
    print('捕獲股票數量：', len(quotes))
    print('輸出檔案名稱：', filePath)
    print('輸出檔案大小 (位元組)：', os.path.getsize(filePath))
    print('執行時間 (時：分：秒)：', stopTime - startTime)
    print('\n')


def retriveAllStocks():
    if isMarketOpen() is False:
        return

    # 開始時間
    startTime = datetime.now()

    # 讀取資料
    quotes = {}
    for stockNo in range(1000, 10000):
        print('股票代號：', stockNo, end='\r')
        quote = DailyQuote(stockNo)
        if quote.retriveQuote() is True:
            quotes[stockNo] = quote
            #quotes[stockNo].display()
    print('\n')

    # 檢查輸出路徑
    path = '../DailyQuote'
    if os.path.exists(path) is False:
        os.mkdir(path)

    # 輸出檔案
    filePath = path + '/DailyQuote(' + str(date.today()) + ').pkl'
    with open(filePath, 'wb') as outputFile:
        pickle.dump(quotes, outputFile, protocol=pickle.HIGHEST_PROTOCOL)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockDailyQuote]')
    print('捕獲股票數量：', len(quotes))
    print('輸出檔案名稱：', filePath)
    print('輸出檔案大小 (位元組)：', os.path.getsize(filePath))
    print('執行時間 (時：分：秒)：', stopTime - startTime)
    print('\n')


# dayOffset: 從今日起算，往前計數
# dayCount: 載入數量
def loadQuotes(dayOffset, dayCount):
    path = '../DailyQuote/'
    if os.path.isdir(path) is False:
        return None

    files = os.listdir(path)
    files.sort(reverse=True)

    start = dayOffset
    stop = dayOffset + dayCount
    if stop > len(files):
        stop = len(files)

    quotes = {}
    for i in range(start, stop):
        with open(path+files[i], 'rb') as inputFile:
            quotes[i] = pickle.load(inputFile)

    return quotes


def isMarketOpen():
    stockNos = [1301, 1326, 2317, 2330, 2882]

    prevDailyQuotes = loadQuotes(0, 1)
    if prevDailyQuotes is None:
        return True

    prevDailyQuote = prevDailyQuotes[0]
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
    # 指令格式(單一股票)：python StockDailyQuote.py [股票代號]
    # 指令格式(全部股票)：python StockDailyQuote.py
    if len(sys.argv) < 2:
        #retriveAllStocks()
        retriveAllStocksMultiThread()
    else:
        stockNo = int(sys.argv[1])
        retriveOneStock(stockNo)
    #quotes = loadQuotes(0, 2)
    #quotes[0][2330].display()
    #quotes[1][2317].display()
