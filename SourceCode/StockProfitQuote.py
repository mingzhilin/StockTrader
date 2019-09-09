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


class ProfitQuote():
    def __init__(self, stockNo):
        self.stockNo = stockNo          # 股票代號
        self.latestYear = None          # 最新公佈的年
        self.latestQuarter = None       # 最新公佈的季
        self.grossProfitMargin = {}     # 毛利率
        self.operateProfitMargin = {}   # 營益率
        self.operateIncomePerShare = {} # 每股營業額
        self.operateProfitPerShare = {} # 每股營業利益
        self.roe = {}                   # 稅後淨值報酬率 (ROE)
        self.roa = {}                   # 總資產報酬率 (ROA)
        self.grossProfitGrowthRate = {
            'qoq': 0,                   # 毛利季增率
            'yoy': 0,                   # 毛利年增率
            'cumulative': 0             # 毛利累計年增率
        }
        self.operateProfitGrowthRate = {
            'qoq': 0,                   # 營益季增率
            'yoy': 0,                   # 營益年增率
            'cumulative': 0             # 營益累計年增率
        }
        self.roeGrowthRate = {
            'avg5Y': 0,                 # 近5年均ROE
            'avg4Q': 0                  # 近四季ROE成長率
        }
        self.roaGrowthRate = {
            'avg5Y': 0,                 # 近5年均ROA
            'avg4Q': 0                  # 近四季ROA成長率
        }

    def display(self):
        print('stockNo =', self.stockNo)
        print('latestYear =', self.latestYear)
        print('latestQuarter =', self.latestQuarter)
        print('grossProfitMargin =', self.grossProfitMargin)
        print('operateProfitMargin =', self.operateProfitMargin)
        print('operateIncomePerShare =', self.operateIncomePerShare)
        print('operateProfitPerShare =', self.operateProfitPerShare)
        print('roe =', self.roe)
        print('roa =', self.roa)
        print('grossProfitGrowthRate =', self.grossProfitGrowthRate)
        print('operateProfitGrowthRate =', self.operateProfitGrowthRate)
        print('roeGrowthRate =', self.roeGrowthRate)
        print('roaGrowthRate =', self.roaGrowthRate)

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

    def retriveAvg5Y(self):
        stockNo = '{n:04d}'.format(n=self.stockNo)
        url = 'http://pchome.megatime.com.tw/stock/sto2/ock6/sid' + stockNo + '.html'
        payload = {'is_check': 1}
        html = self.retriveHtml(url, payload)
        if html is None:
            return False

        # ==========================================================================================
        # 找出全部(年度)稅後淨值報酬率(ROE)、總資產報酬率(ROA)

        nodes = html.xpath('//tr/td/text() | //tr/th/text()')
        if not nodes:
            return False

        index = nodes.index('科目名稱')
        nodes = nodes[index:]

        #print('nodes =', nodes)

        for i in range(5):
            try:
                year = int(nodes[i+1][:-1])

                if self.latestYear is None:
                    self.latestYear = year

                if self.roe.get(year) is None:
                    self.roe[year] = {}
                self.roe[year]['annual'] = float(nodes[i+119])

                if self.roa.get(year) is None:
                    self.roa[year] = {}
                self.roa[year]['annual'] = float(nodes[i+128])
            except:
                pass

        if self.latestYear is None:
            return False

        return True

    def calculateAvg5Y(self, growthRate):
        if self.latestYear is None:
            return 0

        startYear = self.latestYear - 5
        stopYear = self.latestYear + 1

        #print('startYear =', startYear)
        #print('stopYear =', stopYear)

        avg5Y = 0
        totalGrowthRate = 0
        totalYearCount = 0

        for year in range(startYear, stopYear):
            if growthRate.get(year) is None:
                continue
            if growthRate[year].get('annual') is None:
                continue
            totalYearCount += 1
            #print('year =', year, 'annualGrowthRate =', growthRate[year]['annual'])
            totalGrowthRate += growthRate[year]['annual']
        #print('totalGrowthRate =', totalGrowthRate)

        if totalYearCount > 0:
            avg5Y = totalGrowthRate / totalYearCount / 100

        return avg5Y

    def calculateAvg4Q(self, growthRate):
        avg4Q = 0
        currAvgGrowthRate = 0
        prevAvgGrowthRate = 0

        year = self.latestQuarter // 100
        quarter = self.latestQuarter % 100

        count = 0
        totalGrowthRate = 0
        for i in range(4):
            if growthRate.get(year) is None:
                continue
            if growthRate[year].get(quarter) is None:
                continue
            count += 1
            totalGrowthRate += growthRate[year][quarter]
            quarter -= 1
            if quarter == 0:
                quarter = 4
                year -= 1
        if count > 0:
            currAvgGrowthRate = totalGrowthRate / count

        count = 0
        totalGrowthRate = 0
        for i in range(4):
            if growthRate.get(year) is None:
                continue
            if growthRate[year].get(quarter) is None:
                continue
            count += 1
            totalGrowthRate += growthRate[year][quarter]
            quarter -= 1
            if quarter == 0:
                quarter = 4
                year -= 1
        if count > 0:
            prevAvgGrowthRate = totalGrowthRate / count

        #print('currAvgGrowthRate =', currAvgGrowthRate)
        #print('prevAvgGrowthRate =', prevAvgGrowthRate)

        avg4Q = (currAvgGrowthRate - prevAvgGrowthRate) / 100

        return avg4Q

    def retriveQuote(self):
        stockNo = '{n:04d}'.format(n=self.stockNo)
        url = 'http://pchome.megatime.com.tw/stock/sto2/ock2/sid' + stockNo + '.html'
        payload = {'is_check': 1}
        html = self.retriveHtml(url, payload)
        if html is None:
            return False

        # ==========================================================================================
        # 找出全部毛利率、營益率、每股營業額、每股營業利益、稅後淨值報酬率(ROE)、總資產報酬率(ROA)

        nodes = html.xpath('//tr/td/text() | //tr/th/text()')
        if not nodes:
            return False

        index = nodes.index('科目名稱')
        nodes = nodes[index:]

        #print('nodes =', nodes)

        for i in range(8):
            try:
                year = int(nodes[i*2+1][:-1])
                quarter = int(nodes[i*2+2][1:-1])

                if self.latestQuarter is None:
                    self.latestQuarter = year * 100 + quarter

                if self.grossProfitMargin.get(year) is None:
                    self.grossProfitMargin[year] = {}
                self.grossProfitMargin[year][quarter] = float(nodes[i+19])

                if self.operateProfitMargin.get(year) is None:
                    self.operateProfitMargin[year] = {}
                self.operateProfitMargin[year][quarter] = float(nodes[i+28])

                if self.operateIncomePerShare.get(year) is None:
                    self.operateIncomePerShare[year] = {}
                self.operateIncomePerShare[year][quarter] = float(nodes[i+64])

                if self.operateProfitPerShare.get(year) is None:
                    self.operateProfitPerShare[year] = {}
                self.operateProfitPerShare[year][quarter] = float(nodes[i+73])

                if self.roe.get(year) is None:
                    self.roe[year] = {}
                self.roe[year][quarter] = float(nodes[i+127])

                if self.roa.get(year) is None:
                    self.roa[year] = {}
                self.roa[year][quarter] = float(nodes[i+136])
            except:
                pass

        if self.latestQuarter is None:
            return False

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

        # ==========================================================================================
        # 毛利成長率、營益成長率

        for i in range(2):
            if self.grossProfitMargin.get(currYear-i) is None:
                return False
            if self.operateProfitMargin.get(currYear-i) is None:
                return False
            if self.operateIncomePerShare.get(currYear-i) is None:
                return False
            if self.operateProfitPerShare.get(currYear-i) is None:
                return False

        try:
            curr = self.grossProfitMargin[currYear][currQuarter]
            prev = self.grossProfitMargin[prevYear][prevQuarter]
            self.grossProfitGrowthRate['qoq'] = (curr - prev) / 100
        except:
            self.grossProfitGrowthRate['qoq'] = 0

        try:
            curr = self.grossProfitMargin[currYear][currQuarter]
            last = self.grossProfitMargin[lastYear][lastQuarter]
            self.grossProfitGrowthRate['yoy'] = (curr - last) / 100
        except:
            self.grossProfitGrowthRate['yoy'] = 0

        try:
            self.grossProfitGrowthRate['cumulative'] = self.calculateAvg4Q(self.grossProfitMargin)
        except:
            self.grossProfitGrowthRate['cumulative'] = 0

        try:
            curr = self.operateProfitMargin[currYear][currQuarter]
            prev = self.operateProfitMargin[prevYear][prevQuarter]
            self.operateProfitGrowthRate['qoq'] = (curr - prev) / 100
        except:
            self.operateProfitGrowthRate['qoq'] = 0

        try:
            curr = self.operateProfitMargin[currYear][currQuarter]
            last = self.operateProfitMargin[lastYear][lastQuarter]
            self.operateProfitGrowthRate['yoy'] = (curr - last) / 100
        except:
            self.operateProfitGrowthRate['yoy'] = 0

        try:
            self.operateProfitGrowthRate['cumulative'] = self.calculateAvg4Q(self.operateProfitMargin)
        except:
            self.operateProfitGrowthRate['cumulative'] = 0

        # ==========================================================================================
        # ROE成長率、ROA成長率

        self.retriveAvg5Y()
        self.roeGrowthRate['avg5Y'] = self.calculateAvg5Y(self.roe)
        self.roaGrowthRate['avg5Y'] = self.calculateAvg5Y(self.roa)
        self.roeGrowthRate['avg4Q'] = self.calculateAvg4Q(self.roe)
        self.roaGrowthRate['avg4Q'] = self.calculateAvg4Q(self.roa)

        return True


def retriveOneStock(stockNo):
    quote = ProfitQuote(stockNo)
    quote.retriveQuote()
    quote.display()


def retriveStocks(division, prevDailyQuotes):
    for stockNo in range(division['start'], division['stop']):
        print('股票代號：', stockNo, end='\r')
        if prevDailyQuotes.get(stockNo) is None:
            continue
        quote = ProfitQuote(stockNo)
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

    while True:
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

        # 捕獲股票數量大於1000，結束
        if len(quotes) > 1000:
            break
        else:
            print('\n\nProfitQuote: 再執行一次\n\n')

    # 檢查輸出路徑
    path = '../ProfitQuote'
    if os.path.exists(path) is False:
        os.mkdir(path)

    # 輸出檔案
    now = date.today()
    currQuarter = str(now.year) + '-' + str((now.month - 1) // 3 + 1)
    filePath = path + '/ProfitQuote(' + currQuarter + ').pkl'
    with open(filePath, 'wb') as outputFile:
        pickle.dump(quotes, outputFile, protocol=pickle.HIGHEST_PROTOCOL)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockProfitQuote]')
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
        print('股票代號：', stockNo, end='\r')
        quote = ProfitQuote(stockNo)
        if quote.retriveQuote() is True:
            quotes[stockNo] = quote
            #quotes[stockNo].display()
    print('\n')

    # 檢查輸出路徑
    path = '../ProfitQuote'
    if os.path.exists(path) is False:
        os.mkdir(path)

    # 輸出檔案
    now = date.today()
    currQuarter = str(now.year) + '-' + str((now.month - 1) // 3 + 1)
    filePath = path + '/ProfitQuote(' + currQuarter + ').pkl'
    with open(filePath, 'wb') as outputFile:
        pickle.dump(quotes, outputFile, protocol=pickle.HIGHEST_PROTOCOL)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockProfitQuote]')
    print('捕獲股票數量：', len(quotes))
    print('輸出檔案名稱：', filePath)
    print('輸出檔案大小 (位元組)：', os.path.getsize(filePath))
    print('執行時間 (時：分：秒)：', stopTime - startTime)
    print('\n')


# quarterOffset: 從本月起算，往前計數
# quarterCount: 載入數量
def loadQuotes(quarterOffset, quarterCount):
    path = '../ProfitQuote/'
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
    # 指令格式(單一股票)：python StockProfitQuote.py [股票代號]
    # 指令格式(全部股票)：python StockProfitQuote.py
    if len(sys.argv) < 2:
        #retriveAllStocks()
        retriveAllStocksMultiThread()
    else:
        stockNo = int(sys.argv[1])
        retriveOneStock(stockNo)
