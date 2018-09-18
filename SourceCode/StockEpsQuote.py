import os
import sys
import pickle
import requests
from datetime import date
from datetime import datetime
from lxml.html import fromstring
from threading import Thread

import StockDailyQuote
from StockDailyQuote import DailyQuote


class EpsQuote():
    def __init__(self, stockNo):
        self.stockNo = stockNo          # 股票代號
        self.latestQuarter = 0          # 最新公佈的季
        self.currGrowthRate = 0         # 季EPS季增率
        self.lastGrowthRate = 0         # 季EPS年增率
        self.cumulativeGrowthRate = 0   # 累計年增率
        self.latestOneQuarterEps = 0    # 最新一季EPS
        self.latestFourQuarterEps = 0   # 最新四季EPS
        self.cumulativeEps = 0          # 累計EPS
        self.eps = {}

    def display(self):
        print('stockNo =', self.stockNo)
        print('latestQuarter =', self.latestQuarter)
        if self.currGrowthRate is None:
            print('currGrowthRate = None')
        else:
            print('currGrowthRate =', '{0:.4%}'.format(self.currGrowthRate))
        print('lastGrowthRate =', '{0:.4%}'.format(self.lastGrowthRate))
        print('cumulativeGrowthRate =', '{0:.4%}'.format(self.cumulativeGrowthRate))
        print('latestOneQuarterEps =', self.latestOneQuarterEps)
        print('latestFourQuarterEps =', self.latestFourQuarterEps)
        print('eps =', self.eps)

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
        url = 'http://pchome.megatime.com.tw/stock/sto2/ock2/sid' + stockNo + '.html'
        payload = {'is_check': 1}
        html = self.retriveHtml(url, payload)
        if html is None:
            return False

        # ==========================================================================================
        # 找出全部EPS

        nodes = html.xpath('//tr/td/text() | //tr/th/text()')
        if not nodes:
            return False

        index = nodes.index('科目名稱')
        nodes = nodes[index:]

        for i in range(8):
            try:
                year = int(nodes[i*2+1][:-1])
                quarter = int(nodes[i*2+2][1:-1])
                #print(i, year, quarter, nodes[i+109])
                if self.latestQuarter == 0:
                    self.latestQuarter = year * 100 + quarter
                if self.eps.get(year) is None:
                    self.eps[year] = {}
                self.eps[year][quarter] = float(nodes[i+109])
            except:
                pass

        if self.latestQuarter is None:
            return False

        for i in range(1, 3):
            year = self.latestQuarter // 100 - i * 2
            quarter = '{y:04d}4'.format(y=year)
            stockNo = '{n:04d}'.format(n=self.stockNo)
            url = 'http://pchome.megatime.com.tw/stock/sto2/ock2/' + quarter + '/sid' + stockNo + '.html'
            payload = {'is_check': 1}
            html = self.retriveHtml(url, payload)
            if html is None:
                break

            nodes = html.xpath('//tr/td/text() | //tr/th/text()')
            if not nodes:
                break

            try:
                index = nodes.index('科目名稱')
                nodes = nodes[index:]
            except:
                break

            for i in range(8):
                try:
                    year = int(nodes[i*2+1][:-1])
                    quarter = int(nodes[i*2+2][1:-1])
                    if self.eps.get(year) is None:
                        self.eps[year] = {}
                    self.eps[year][quarter] = float(nodes[i+109])
                except:
                    pass

        # ==========================================================================================
        # 季EPS季增率、季EPS年增率、累計年增率

        # 本季
        currYear = self.latestQuarter // 100
        currQuarter = self.latestQuarter % 100

        #print('currYear =', currYear)
        #print('currQuarter =', currQuarter)

        # 上一季
        prevYear = currYear
        prevQuarter = currQuarter - 1
        if prevQuarter == 0:
            prevQuarter = 4
            prevYear -= 1

        #print('prevYear =', prevYear)
        #print('prevQuarter =', prevQuarter)

        # 去年同季
        lastYear = currYear - 1
        lastQuarter = currQuarter

        #print('lastYear =', lastYear)
        #print('lastQuarter =', lastQuarter)

        if self.eps.get(currYear) is None:
            return False
        if self.eps.get(prevYear) is None:
            return False
        if self.eps.get(lastYear) is None:
            return False

        # 最新一季的EPS
        if self.eps[currYear].get(currQuarter) is None:
            currEps = 0
        else:
            currEps = self.eps[currYear][currQuarter]

        # 上一季的EPS
        if self.eps[prevYear].get(prevQuarter) is None:
            prevEps = 0
        else:
            prevEps = self.eps[prevYear][prevQuarter]

        # 去年同季的EPS
        if self.eps[lastYear].get(lastQuarter) is None:
            lastEps = 0
        else:
            lastEps = self.eps[lastYear][lastQuarter]

        #print('currEps =', currEps)
        #print('prevEps =', prevEps)
        #print('lastEps =', lastEps)

        # 最新一季的EPS季增率
        if prevEps != 0 and prevEps != None:
            self.currGrowthRate = (currEps - prevEps) / abs(prevEps)

        # 去年同季EPS的年增率
        if lastEps != 0 and lastEps != None:
            self.lastGrowthRate = (currEps - lastEps) / abs(lastEps)

        culmulativeEps = {'curr': 0, 'last': 0}
        for i in range(1, currQuarter+1):
            if self.eps[currYear].get(i) is not None:
                culmulativeEps['curr'] += self.eps[currYear][i]
            if self.eps[lastYear].get(i) is not None:
                culmulativeEps['last'] += self.eps[lastYear][i]

        #print('culmulativeEps =', culmulativeEps)

        # 累計EPS年增率
        if culmulativeEps['last'] != 0:
            self.cumulativeGrowthRate = (culmulativeEps['curr'] - culmulativeEps['last']) \
                                        / abs(culmulativeEps['last'])

        # 累計EPS
        self.cumulativeEps = culmulativeEps['curr']

        # 最新一季EPS
        if self.eps[currYear].get(currQuarter) is not None:
            self.latestOneQuarterEps = self.eps[currYear][currQuarter]

        # 最新四季EPS
        year = currYear
        quarter = currQuarter
        for i in range(4):
            if self.eps[year].get(quarter) is not None:
                self.latestFourQuarterEps += self.eps[year][quarter]
            quarter -= 1
            if quarter == 0:
                quarter = 4
                year -= 1
                if self.eps.get(year) is None:
                    break

        return True


def retriveOneStock(stockNo):
    quote = EpsQuote(stockNo)
    quote.retriveQuote()
    quote.display()


def retriveStocks(division, prevDailyQuotes):
    for stockNo in range(division['start'], division['stop']):
        print('股票代號：', stockNo, end='\r')
        if prevDailyQuotes.get(stockNo) is None:
            continue
        quote = EpsQuote(stockNo)
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

    # 全部股票的季EPS，找出最新公佈的年季
    latestQuarter = 0
    for stockNo in range(1000, 10000):
        if quotes.get(stockNo):
            if quotes[stockNo].latestQuarter > latestQuarter:
                latestQuarter = quotes[stockNo].latestQuarter

    # 已公佈季EPS的公司，是否大於五家
    count = 0
    isReset = False
    for stockNo in range(1000, 10000):
        if quotes.get(stockNo):
            if quotes[stockNo].latestQuarter == latestQuarter:
                count += 1
                if count >= 5:
                    isReset = True
                    break

    # 若已季EPS公司，大於五家，清除未公佈的公司季EPS的EPS季增率
    if isReset is True:
        for stockNo in range(1000, 10000):
            if quotes.get(stockNo):
                if quotes[stockNo].latestQuarter < latestQuarter:
                    quotes[stockNo].currGrowthRate = None

    # 檢查輸出路徑
    path = '../EpsQuote'
    if os.path.exists(path) is False:
        os.mkdir(path)

    # 輸出檔案
    now = date.today()
    currQuarter = str(now.year) + '-' + str((now.month - 1) // 3 + 1)
    filePath = path + '/EpsQuote(' + currQuarter + ').pkl'
    with open(filePath, 'wb') as outputFile:
        pickle.dump(quotes, outputFile, protocol=pickle.HIGHEST_PROTOCOL)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockEpsQuote]')
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
        quote = EpsQuote(stockNo)
        if quote.retriveQuote() is True:
            quotes[stockNo] = quote
            #quotes[stockNo].display()
    print('\n')

    # 檢查輸出路徑
    path = '../EpsQuote'
    if os.path.exists(path) is False:
        os.mkdir(path)

    # 輸出檔案
    now = date.today()
    currQuarter = str(now.year) + '-' + str((now.month - 1) // 3 + 1)
    filePath = path + '/EpsQuote(' + currQuarter + ').pkl'
    with open(filePath, 'wb') as outputFile:
        pickle.dump(quotes, outputFile, protocol=pickle.HIGHEST_PROTOCOL)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockEpsQuote]')
    print('捕獲股票數量：', len(quotes))
    print('輸出檔案名稱：', filePath)
    print('輸出檔案大小 (位元組)：', os.path.getsize(filePath))
    print('執行時間 (時：分：秒)：', stopTime - startTime)
    print('\n')


# quarterOffset: 從本月起算，往前計數
# quarterCount: 載入數量
def loadQuotes(quarterOffset, quarterCount):
    path = '../EpsQuote/'
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
    # 指令格式(單一股票)：python StockEpsQuote.py [股票代號]
    # 指令格式(全部股票)：python StockEpsQuote.py
    if len(sys.argv) < 2:
        #retriveAllStocks()
        retriveAllStocksMultiThread()
    else:
        stockNo = int(sys.argv[1])
        retriveOneStock(stockNo)
