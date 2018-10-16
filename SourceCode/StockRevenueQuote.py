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


class RevenueQuote():
    def __init__(self, stockNo):
        self.stockNo = stockNo          # 股票代號
        self.latestMonth = 0            # 最新公佈的月
        self.prevMonthGrowthRate = 0    # 月營收月增率
        self.lastMonthGrowthRate = 0    # 月營收年增率
        self.cumulativeGrothRate = 0    # 累積年增率
        self.currQuarterGrowthRate = 0  # 季營收季增率
        self.lastQuarterGrowthRate = 0  # 季營收年增率
        self.revenue = {}

    def display(self):
        print('stockNo =', self.stockNo)
        print('latestMonth =', self.latestMonth)
        if self.prevMonthGrowthRate is None:
            print('prevMonthGrowthRate = None')
        else:
            print('prevMonthGrowthRate =', '{0:.4%}'.format(self.prevMonthGrowthRate))
        print('lastMonthGrowthRate =', '{0:.4%}'.format(self.lastMonthGrowthRate))
        print('cumulativeGrothRate =', '{0:.4%}'.format(self.cumulativeGrothRate))
        print('currQuarterGrowthRate =', '{0:.4%}'.format(self.currQuarterGrowthRate))
        print('lastQuarterGrowthRate =', '{0:.4%}'.format(self.lastQuarterGrowthRate))

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
        url = 'http://pchome.megatime.com.tw/stock/sto3/ock2/sid' + stockNo + '.html'
        payload = {'is_check': 1}
        html = self.retriveHtml(url, payload)
        if html is None:
            return False

        # ==========================================================================================
        # 找出全部月營收

        nodes = html.xpath('//tr/td/text() | //tr/th/text()')
        if not nodes:
            return False

        now = date.today()
        year = now.year

        isFound = False
        try:
            index = nodes.index(str(year)+'年')
            nodes = nodes[index:]
            isFound = True
        except:
            isFound = False
        if isFound is False:
            try:
                index = nodes.index(str(year-1)+'年')
                nodes = nodes[index:]
                isFound = True
            except:
                isFound = False
        if isFound is False:
            return False
        #print('nodes =', nodes)

        try:
            year0 = int(nodes[0][:-1])
            year1 = int(nodes[1][:-1])
        except:
            return False

        #print('year0 =', year0)
        #print('year1 =', year1)

        for i in range(1, 13):
            month = '{m:02d}'.format(m=i)
            month0 = year0 * 100 + i
            month1 = year1 * 100 + i

            #print('month =', month)
            #print('month0 =', month0)
            #print('month1 =', month1)

            try:
                index = nodes.index(month)
            except:
                return False
            nodes = nodes[index+1:]
            #print('nodes =', nodes)
            if nodes[0] != month:
                try:
                    self.revenue[month0] = float(nodes[0].replace(',', ''))
                    self.latestMonth = month0
                except:
                    self.revenue[month0] = 0
            else:
                self.revenue[month0] = 0

            try:
                index = nodes.index(month)
            except:
                return False
            nodes = nodes[index+1:]
            try:
                self.revenue[month1] = float(nodes[0].replace(',', ''))
            except:
                self.revenue[month1] = 0

        #print('revenue =', self.revenue)
        #print('latestMonth =', self.latestMonth)

        if self.latestMonth == 0:
            return False

        # ==========================================================================================
        # 月營收月增率、月營收年增率、累積年增率

        # 月營收月增率
        month0 = self.latestMonth
        year = self.latestMonth // 100
        month = self.latestMonth % 100 - 1
        if month == 0:
            month = 12
            year -= 1
        month1 = year * 100 + month

        revenue0 = self.revenue[month0]
        revenue1 = self.revenue[month1]

        #print('month0 =', month0)
        #print('month1 =', month1)
        #print('revenue[month0] =', self.revenue[month0])
        #print('revenue[month1] =', self.revenue[month1])

        if revenue1 != 0:
            self.prevMonthGrowthRate = (revenue0 - revenue1) / revenue1

        # 月營收月增率為零，設為-0.01%
        if self.prevMonthGrowthRate == 0:
            self.prevMonthGrowthRate = -0.0001

        # 月營收年增率
        month0 = self.latestMonth
        year = self.latestMonth // 100 - 1
        month = self.latestMonth % 100
        month1 = year * 100 + month

        revenue0 = self.revenue[month0]
        revenue1 = self.revenue[month1]

        #print('month0 =', month0)
        #print('month1 =', month1)
        #print('revenue[month0] =', self.revenue[month0])
        #print('revenue[month1] =', self.revenue[month1])

        if revenue1 != 0:
            self.lastMonthGrowthRate = (revenue0 - revenue1) / revenue1

        # 累積年增率
        year0 = year = self.latestMonth // 100
        year1 = year = self.latestMonth // 100 - 1
        latestMonth = self.latestMonth % 100
        revenue0 = 0
        revenue1 = 0
        for i in range(1, latestMonth+1):
            month0 = year0 * 100 + i
            month1 = year1 * 100 + i
            revenue0 += self.revenue[month0]
            revenue1 += self.revenue[month1]

        #print('month0 =', month0)
        #print('month1 =', month1)
        #print('revenue[month0] =', self.revenue[month0])
        #print('revenue[month1] =', self.revenue[month1])

        if revenue1 != 0:
            self.cumulativeGrothRate = (revenue0 - revenue1) / revenue1

        # ==========================================================================================
        # 季營收季增率、季營收年增率

        year0 = self.latestMonth // 100
        month = self.latestMonth % 100
        quarter0 = (month - 1) // 3 + 1
        quarter1 = quarter0 - 1
        if quarter1 == 0:
            quarter1 = 4
            year1 = year0 - 1
        else:
            year1 = year0
        year2 = year0 - 1
        quarter2 = quarter0

        # monthsPerQuarter0: 最新一季的月份
        # monthsPerQuarter1: 上一個季的月份
        # monthsPerQuarter2: 去年同季的月份
        monthsPerQuarter0 = {}
        monthsPerQuarter1 = {}
        monthsPerQuarter2 = {}
        for i in range(3):
            month0 = (quarter0 - 1) * 3 + i + 1 + year0 * 100
            month1 = (quarter1 - 1) * 3 + i + 1 + year1 * 100
            month2 = (quarter2 - 1) * 3 + i + 1 + year2 * 100
            if self.revenue[month0] != 0:
                monthsPerQuarter0[i] = month0
            else:
                monthsPerQuarter0.pop(i, None)
            monthsPerQuarter1[i] = month1
            monthsPerQuarter2[i] = month2

        #print('monthsPerQuarter0 =', monthsPerQuarter0)
        #print('monthsPerQuarter1 =', monthsPerQuarter1)
        #print('monthsPerQuarter2 =', monthsPerQuarter2)

        # quarterRevenue0: 最新一季營收
        # quarterRevenue1: 上一個季營收
        # quarterRevenue2: 去年同季營收
        quarterRevenue0 = 0
        quarterRevenue1 = 0
        quarterRevenue2 = 0
        for i in range(3):
            if monthsPerQuarter0.get(i) is not None:
                month0 = monthsPerQuarter0[i]
                quarterRevenue0 += self.revenue[month0]
            month1 = monthsPerQuarter1[i]
            month2 = monthsPerQuarter2[i]
            quarterRevenue1 += self.revenue[month1]
            quarterRevenue2 += self.revenue[month2]

        #print('quarterRevenue0 =', quarterRevenue0)
        #print('quarterRevenue1 =', quarterRevenue1)
        #print('quarterRevenue2 =', quarterRevenue2)

        quarterRevenue1 *= len(monthsPerQuarter0) / 3
        if quarterRevenue1 != 0:
            self.currQuarterGrowthRate = (quarterRevenue0 - quarterRevenue1) / quarterRevenue1

        quarterRevenue2 *= len(monthsPerQuarter0) / 3
        if quarterRevenue2 != 0:
            self.lastQuarterGrowthRate = (quarterRevenue0 - quarterRevenue2) / quarterRevenue2

        return True


def retriveOneStock(stockNo):
    quote = RevenueQuote(stockNo)
    quote.retriveQuote()
    quote.display()


def retriveStocks(division, prevDailyQuotes):
    for stockNo in range(division['start'], division['stop']):
        print('股票代號：', stockNo, end='\r')
        if prevDailyQuotes.get(stockNo) is None:
            continue
        quote = RevenueQuote(stockNo)
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

    # 全部股票的月營收，找出最新公佈的年月
    latestMonth = 0
    for stockNo in range(1000, 10000):
        if quotes.get(stockNo):
            if quotes[stockNo].latestMonth > latestMonth:
                latestMonth = quotes[stockNo].latestMonth

    # 已公佈月營收的公司，是否大於五家
    count = 0
    isReset = False
    for stockNo in range(1000, 10000):
        if quotes.get(stockNo):
            if quotes[stockNo].latestMonth == latestMonth:
                count += 1
                if count >= 5:
                    isReset = True
                    break

    # 若已月營收公司，大於五家，清除未公佈的公司月營收月增率
    if isReset is True:
        for stockNo in range(1000, 10000):
            if quotes.get(stockNo):
                if quotes[stockNo].latestMonth < latestMonth:
                    quotes[stockNo].prevMonthGrowthRate = None

    # 檢查輸出路徑
    path = '../RevenueQuote'
    if os.path.exists(path) is False:
        os.mkdir(path)

    # 輸出檔案
    now = date.today()
    currMonth = str(now.year) + '-' + str(now.month)
    filePath = path + '/RevenueQuote(' + currMonth + ').pkl'
    with open(filePath, 'wb') as outputFile:
        pickle.dump(quotes, outputFile, protocol=pickle.HIGHEST_PROTOCOL)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockRevenueQuote]')
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
        quote = RevenueQuote(stockNo)
        if quote.retriveQuote() is True:
            quotes[stockNo] = quote
            #quotes[stockNo].display()
    print('\n')

    # 全部股票的月營收，找出最新公佈的年月
    latestMonth = 0
    for stockNo in range(1000, 10000):
        if quotes.get(stockNo):
            if quotes[stockNo].latestMonth > latestMonth:
                latestMonth = quotes[stockNo].latestMonth

    # 若有公司已公佈月營收，則未公佈的公司清除月營收月增率
    for stockNo in range(1000, 10000):
        if quotes.get(stockNo):
            if quotes[stockNo].latestMonth < latestMonth:
                quotes[stockNo].prevMonthGrowthRate = None

    # 檢查輸出路徑
    path = '../RevenueQuote'
    if os.path.exists(path) is False:
        os.mkdir(path)

    # 輸出檔案
    now = date.today()
    currMonth = '{y:04d}-{m:02d}'.format(y=now.year, m=now.month)
    filePath = path + '/RevenueQuote(' + currMonth + ').pkl'
    with open(filePath, 'wb') as outputFile:
        pickle.dump(quotes, outputFile, protocol=pickle.HIGHEST_PROTOCOL)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockRevenueQuote]')
    print('捕獲股票數量：', len(quotes))
    print('輸出檔案名稱：', filePath)
    print('輸出檔案大小 (位元組)：', os.path.getsize(filePath))
    print('執行時間 (時：分：秒)：', stopTime - startTime)
    print('\n')


# monthOffset: 從本月起算，往前計數
# monthCount: 載入數量
def loadQuotes(monthOffset, monthCount):
    path = '../RevenueQuote/'
    files = os.listdir(path)
    files.sort(reverse=True)

    start = monthOffset
    stop = monthOffset + monthCount
    if stop > len(files):
        stop = len(files)

    quotes = {}
    for i in range(start, stop):
        with open (path+files[i], 'rb') as inputFile:
            quotes[i] = pickle.load(inputFile)

    return quotes


if __name__ == '__main__':
    # 指令格式(單一股票)：python StockRevenueQuote.py [股票代號]
    # 指令格式(全部股票)：python StockRevenueQuote.py
    if len(sys.argv) < 2:
        #retriveAllStocks()
        retriveAllStocksMultiThread()
    else:
        stockNo = int(sys.argv[1])
        retriveOneStock(stockNo)
