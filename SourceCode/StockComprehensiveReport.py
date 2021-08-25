import os
import sys
import pickle
import requests
from datetime import date
from datetime import datetime
from lxml.html import fromstring

import StockDailyQuote
import StockDividendQuote
import StockEpsQuote
import StockMarginQuote
import StockProfitQuote
import StockRevenueQuote
import StockLegalTrader

from StockDailyQuote import DailyQuote
from StockDividendQuote import DividendQuote
from StockEpsQuote import EpsQuote
from StockMarginQuote import MarginQuote
from StockProfitQuote import ProfitQuote
from StockRevenueQuote import RevenueQuote
from StockLegalTrader import LegalTrader


def calculateNetBuySell(legalTrader, stockNo):
    """計算法人買賣超"""

    if legalTrader.get(stockNo) is None:
        netBuySell = {'foreign': None, 'domestic': None, 'dealer': None}
        return netBuySell

    netBuySell = {'foreign': {}, 'domestic': {}, 'dealer': {}}

    if legalTrader[stockNo].netBuySell['foreign'] is None:
        netBuySell['foreign'] = None
    else:
        netBuySell['foreign']['1d'] = legalTrader[stockNo].netBuySell['foreign'][0]
        netBuySell['foreign']['5d'] = 0
        for i in range(5):
            netBuySell['foreign']['5d'] += legalTrader[stockNo].netBuySell['foreign'][i] 

    if legalTrader[stockNo].netBuySell['domestic'] is None:
        netBuySell['domestic'] = None
    else:
        netBuySell['domestic']['1d'] = legalTrader[stockNo].netBuySell['domestic'][0]
        netBuySell['domestic']['5d'] = 0
        for i in range(5):
            netBuySell['domestic']['5d'] += legalTrader[stockNo].netBuySell['domestic'][i] 

    if legalTrader[stockNo].netBuySell['dealer'] is None:
        netBuySell['dealer'] = None
    else:
        netBuySell['dealer']['1d'] = legalTrader[stockNo].netBuySell['dealer'][0]
        netBuySell['dealer']['5d'] = 0
        for i in range(5):
            netBuySell['dealer']['5d'] += legalTrader[stockNo].netBuySell['dealer'][i] 

    return netBuySell


def calculateAveragePrice(dailyQuote, stockNo, dayCount):
    """計算均價"""

    maxDayCount = len(dailyQuote)
    if maxDayCount < dayCount:
        dayCount = maxDayCount

    totalPrice = 0
    actualDayCount = 0
    for i in range(dayCount):
        try:
            totalPrice += dailyQuote[i][stockNo].closePrice
            actualDayCount += 1
        except:
            pass

    if actualDayCount > 0:
        averagePrice = totalPrice / actualDayCount
    else:
        averagePrice = 0

    return averagePrice


def calculateAverageVolume(dailyQuote, stockNo, dayCount):
    """計算均量"""

    maxDayCount = len(dailyQuote)
    if maxDayCount < dayCount:
        dayCount = maxDayCount

    totalVolume = 0
    actualDayCount = 0
    for i in range(dayCount):
        try:
            totalVolume += dailyQuote[i][stockNo].volume
            actualDayCount += 1
        except:
            pass

    if actualDayCount > 0:
        averageVolume = totalVolume / actualDayCount
    else:
        averageVolume = 0

    return averageVolume


def searchHighPrice(dailyQuote, stockNo, dayCount):
    """搜尋最高價"""

    maxDayCount = len(dailyQuote)
    if maxDayCount < dayCount:
        dayCount = maxDayCount

    highPrice = dailyQuote[0][stockNo].highPrice
    for i in range(1, dayCount):
        try:
            if dailyQuote[i][stockNo].highPrice > highPrice:
                highPrice = dailyQuote[i][stockNo].highPrice
        except:
            pass

    return highPrice


def searchLowPrice(dailyQuote, stockNo, dayCount):
    """搜尋最低價"""

    maxDayCount = len(dailyQuote)
    if maxDayCount < dayCount:
        dayCount = maxDayCount

    lowPrice = dailyQuote[0][stockNo].lowPrice
    for i in range(dayCount):
        try:
            if dailyQuote[i][stockNo].lowPrice < lowPrice:
                lowPrice = dailyQuote[i][stockNo].lowPrice
        except:
            pass

    return lowPrice


def retriveOneStock(stockNo):
    stockQuotes = {}

    print('\nDailyQuote:')
    dailyQuote = StockDailyQuote.loadQuotes(0, 60)
    dailyQuote[0][stockNo].display()

    print('\nDividendQuote:')
    dividendQuote = StockDividendQuote.loadQuotes(0, 1)[0]
    dividendQuote[stockNo].display()

    print('\nRevenueQuote:')
    revenueQuote = StockRevenueQuote.loadQuotes(0, 1)[0]
    revenueQuote[stockNo].display()

    print('\nEpsQuote:')
    epsQuote = StockEpsQuote.loadQuotes(0, 1)[0]
    epsQuote[stockNo].display()

    print('\nProfitQuote:')
    profitQuote = StockProfitQuote.loadQuotes(0, 1)[0]
    profitQuote[stockNo].display()

    print('\nMarginQuote:')
    marginQuote = StockMarginQuote.loadQuotes(0, 1)[0]
    if marginQuote.get(stockNo):
        marginQuote[stockNo].display()

    print('\nLegalTrader:')
    legalTrader = StockLegalTrader.loadQuotes(0, 1)[0]
    if legalTrader.get(stockNo):
        legalTrader[stockNo].display()


def retriveAllStocks():
    print('\n')

    if IsMarketOpen() is True:
        isMarketOpen = True
    else:
        isMarketOpen = False

    # 開始時間
    startTime = datetime.now()

    dailyQuote = StockDailyQuote.loadQuotes(0, 60)
    dividendQuote = StockDividendQuote.loadQuotes(0, 1)[0]
    revenueQuote = StockRevenueQuote.loadQuotes(0, 1)[0]
    epsQuote = StockEpsQuote.loadQuotes(0, 1)[0]
    profitQuote = StockProfitQuote.loadQuotes(0, 1)[0]
    marginQuote = StockMarginQuote.loadQuotes(0, 1)[0]
    legalTrader = StockLegalTrader.loadQuotes(0, 1)[0]

    currYear = date.today().year

    # 檢查輸出路徑
    path = '../ComprehensiveReport'
    if os.path.exists(path) is False:
        os.mkdir(path)

    now = date.today()
    year = now.year
    month = now.month
    day = now.day

    now = datetime.now()
    hour = now.hour
    minute = now.minute
    second = now.second

    currTime1 = '{y:02d}.{m:02d}.{d:02d}'.format(y=year, m=month, d=day)
    currTime2 = '{h:02d}.{m:02d}.{s:02d}'.format(h=hour, m=minute, s=second)

    # 輸出檔案
    #filePath = path + '/ComprehensiveReport(' + str(date.today()) + ').csv'
    #filePath = path + '/ComprehensiveReport(' + currTime1 + '-' + currTime2 + ').csv'
    filePath = path + '/ComprehensiveReport.csv'

    with open(filePath, 'w', encoding='UTF-16') as outputFile:
        outputFile.write('股票代號,')
        outputFile.write('股票名稱,')
        #outputFile.write('60日均價,')
        #outputFile.write('60日最高價,')
        #outputFile.write('60日最低價,')
        #outputFile.write('一年最高價,')
        #outputFile.write('一年最低價,')
        #outputFile.write('20日最高價,')
        #outputFile.write('20日最低價,')
        #outputFile.write('20日均價,')
        #outputFile.write('5日均價,')
        #outputFile.write('10日均價,')
        #outputFile.write('昨日收量,')
        #outputFile.write('20日均量,')
        outputFile.write('營收月增率,')
        outputFile.write('近月營收年增率,')
        outputFile.write('季營收季增率,')
        outputFile.write('季營收年增率,')
        outputFile.write('累計營收年增率,')
        outputFile.write('EPS季增率,')
        outputFile.write('近季EPS年增率,')
        outputFile.write('累計EPS年增率,')
        outputFile.write('毛利季增率,')
        outputFile.write('毛利年增率,')
        outputFile.write('毛利累計年增率,')
        outputFile.write('營益季增率,')
        outputFile.write('營益年增率,')
        outputFile.write('營益累計年增率,')
        outputFile.write('近四季ROE成長,')
        outputFile.write('近四季ROA成長,')
        outputFile.write('近五年均ROE,')
        outputFile.write('近五年均ROA,')
        #outputFile.write('最近一季EPS,')
        outputFile.write('累計EPS,')
        outputFile.write('最近四季EPS,')
        outputFile.write('5年平均股利,')
        outputFile.write('5年均配利率,')
        outputFile.write('配息年度,')
        #outputFile.write(str(currYear-2)+'現金股息,')
        #outputFile.write(str(currYear-2)+'股票股利,')
        outputFile.write('現金股息,')
        outputFile.write('股票股利,')
        outputFile.write('5日外資,')
        outputFile.write('近日外資,')
        outputFile.write('5日投信,')
        outputFile.write('近日投信,')
        outputFile.write('5日自營商,')
        outputFile.write('近日自營商,')
        outputFile.write('券資比,')
        outputFile.write('\n')

        stockCount = {
            'output': 0,
            'daily': 0,
            'dividend': 0,
            'eps': 0,
            'margin': 0,
            'profit': 0,
            'revenue': 0
        }

        for stockNo in range(1000, 10000):
            print('股票代號：', stockNo, end='\r')

            if dailyQuote[0].get(stockNo) is None:
                continue
            if dailyQuote[0].get(stockNo):
                stockCount['daily'] += 1

            #if dividendQuote.get(stockNo) is None:
            #    continue
            if dividendQuote.get(stockNo):
                stockCount['dividend'] += 1

            #if epsQuote.get(stockNo) is None:
            #    continue
            if epsQuote.get(stockNo):
                stockCount['eps'] += 1

            #if marginQuote.get(stockNo) is None:
            #    continue
            if marginQuote.get(stockNo):
                stockCount['margin'] += 1

            #if profitQuote.get(stockNo) is None:
            #    continue
            if profitQuote.get(stockNo):
                stockCount['profit'] += 1

            #if revenueQuote.get(stockNo) is None:
            #    continue
            if revenueQuote.get(stockNo):
                stockCount['revenue'] += 1

            # 過濾年最高價、最低價
            if dailyQuote[0][stockNo].yearHighPrice is None:
                continue
            if dailyQuote[0][stockNo].yearLowPrice is None:
                continue

            # 最高價
            highPrices = {}
            highPrices['20d'] = searchHighPrice(dailyQuote, stockNo, 20)
            highPrices['60d'] = searchHighPrice(dailyQuote, stockNo, 60)

            # 最低價
            lowPrices = {}
            lowPrices['20d'] = searchLowPrice(dailyQuote, stockNo, 20)
            lowPrices['60d'] = searchLowPrice(dailyQuote, stockNo, 60)

            # 均價
            averagePrices = {}
            averagePrices['5d'] = calculateAveragePrice(dailyQuote, stockNo, 5)
            averagePrices['10d'] = calculateAveragePrice(dailyQuote, stockNo, 10)
            averagePrices['20d'] = calculateAveragePrice(dailyQuote, stockNo, 20)
            averagePrices['60d'] = calculateAveragePrice(dailyQuote, stockNo, 60)

            # 均量
            averageVolumes = {}
            averageVolumes['20d'] = calculateAverageVolume(dailyQuote, stockNo, 20)
            averageVolumes['60d'] = calculateAverageVolume(dailyQuote, stockNo, 60)

            #print('highPrices =', highPrices)
            #print('lowPrices =', lowPrices)
            #print('averagePrices =', averagePrices)
            #print('averageVolumes =', averageVolumes)

            # 過濾20日均量
            if averageVolumes['20d'] < 50:
                continue

            # 5年平均股利、5年均配利率
            averageDividend = 0
            averageDividendRate = 0

            totalDividend = 0
            dividendRate = {}
            for i in range(currYear-1, currYear-6, -1):
                #if stockNo == 3556:
                #    print('i =', i)
                try:
                    dividend = dividendQuote[stockNo].cashDividend[i] + dividendQuote[stockNo].shareDividend[i]
                    #if stockNo == 3556:
                    #    print('cashDividend =', dividendQuote[stockNo].cashDividend[i])
                    #    print('shareDividend =', dividendQuote[stockNo].shareDividend[i])
                    #    print('dividend =', dividend)
                    totalDividend += dividend
                    eps = 0
                    for j in range(1, 5):
                        eps += epsQuote[stockNo].eps[i][j]
                    #if stockNo == 3556:
                    #    print('eps =', eps)
                    dividendRate[i] = dividend / eps
                    if dividendRate[i] > 1:
                        dividendRate[i] = 1
                    #if stockNo == 3556:
                    #    print('dividendRate =', dividendRate[i])
                except:
                    dividendRate[i] = None

            totalDividendRate = 0
            yearCount = 0
            for i in range(currYear-1, currYear-6, -1):
                #if stockNo == 3556:
                #    print('i =', i, dividendRate[i])
                if dividendRate[i] is not None:
                    if dividendRate[i] > 0 and dividendRate[i] <= 1:
                        totalDividendRate += dividendRate[i]
                        yearCount += 1
            #if stockNo == 3556:
            #    print('yearCount =', yearCount)
            #    print('totalDividend =', totalDividend)
            #    print('totalDividendRate =', totalDividendRate)
            if yearCount > 0:
                averageDividend = totalDividend / 5
                averageDividendRate = totalDividendRate / yearCount
            #if stockNo == 3556:
            #    print('averageDividend =', averageDividend)
            #    print('averageDividendRate =', averageDividendRate)

            stockCount['output'] += 1

            # 法人買賣超
            legalTragerNetBuySell = {}
            legalTragerNetBuySell = calculateNetBuySell(legalTrader, stockNo)

            # 股票代號
            outputFile.write(str(dailyQuote[0][stockNo].stockNo)+',')

            # 股票名稱
            outputFile.write(str(dailyQuote[0][stockNo].stockName)+',')

            # 60日均價
            #outputFile.write('{0:.4f}'.format(averagePrices['60d'])+',')

            # 60日最高價
            #outputFile.write('{0:.4f}'.format(highPrices['60d'])+',')

            # 60日最低價
            #outputFile.write('{0:.4f}'.format(lowPrices['60d'])+',')

            # 一年最高價
            #if dailyQuote[0][stockNo].yearHighPrice is None:
            #    outputFile.write(',')
            #else:
            #    outputFile.write('{0:.4f}'.format(dailyQuote[0][stockNo].yearHighPrice)+',')

            # 一年最低價
            #if dailyQuote[0][stockNo].yearLowPrice is None:
            #    outputFile.write(',')
            #else:
            #    outputFile.write('{0:.4f}'.format(dailyQuote[0][stockNo].yearLowPrice)+',')

            # 20日最高價
            #outputFile.write('{0:.4f}'.format(highPrices['20d'])+',')

            # 20日最低價
            #outputFile.write('{0:.4f}'.format(lowPrices['20d'])+',')

            # 20日均價
            #outputFile.write('{0:.4f}'.format(averagePrices['20d'])+',')

            # 5日均價
            #outputFile.write('{0:.4f}'.format(averagePrices['5d'])+',')

            # 10日均價
            #outputFile.write('{0:.4f}'.format(averagePrices['10d'])+',')

            # 昨日收量
            #if dailyQuote[1].get(stockNo) is None or dailyQuote[1][stockNo].volume is None:
            #    outputFile.write(',')
            #else:
            #    outputFile.write(str(dailyQuote[1][stockNo].volume)+',')

            # 20日均量
            #outputFile.write('{0:.4f}'.format(averageVolumes['20d'])+',')

            # 營收月增率
            if revenueQuote.get(stockNo) is None or revenueQuote[stockNo].prevMonthGrowthRate is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(revenueQuote[stockNo].prevMonthGrowthRate)+',')

            # 近月營收年增率
            if revenueQuote.get(stockNo) is None or revenueQuote[stockNo].lastMonthGrowthRate is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(revenueQuote[stockNo].lastMonthGrowthRate)+',')

            # 季營收季增率
            if revenueQuote.get(stockNo) is None or revenueQuote[stockNo].currQuarterGrowthRate is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(revenueQuote[stockNo].currQuarterGrowthRate)+',')

            # 季營收年增率
            if revenueQuote.get(stockNo) is None or revenueQuote[stockNo].lastQuarterGrowthRate is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(revenueQuote[stockNo].lastQuarterGrowthRate)+',')

            # 累計營收年增率
            if revenueQuote.get(stockNo) is None or revenueQuote[stockNo].cumulativeGrothRate is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(revenueQuote[stockNo].cumulativeGrothRate)+',')

            # EPS季增率
            if epsQuote.get(stockNo) is None or epsQuote[stockNo].currGrowthRate is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(epsQuote[stockNo].currGrowthRate)+',')

            # 近季EPS年增率
            if epsQuote.get(stockNo) is None or epsQuote[stockNo].lastGrowthRate is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(epsQuote[stockNo].lastGrowthRate)+',')

            # 累計EPS年增率
            if epsQuote.get(stockNo) is None or epsQuote[stockNo].cumulativeGrowthRate is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(epsQuote[stockNo].cumulativeGrowthRate)+',')

            # 毛利季增率
            if profitQuote.get(stockNo) is None or profitQuote[stockNo].grossProfitGrowthRate['qoq'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(profitQuote[stockNo].grossProfitGrowthRate['qoq'])+',')

            # 毛利年增率
            if profitQuote.get(stockNo) is None or profitQuote[stockNo].grossProfitGrowthRate['yoy'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(profitQuote[stockNo].grossProfitGrowthRate['yoy'])+',')

            # 毛利累計年增率
            if profitQuote.get(stockNo) is None or profitQuote[stockNo].grossProfitGrowthRate['cumulative'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(profitQuote[stockNo].grossProfitGrowthRate['cumulative'])+',')

            # 營益季增率
            if profitQuote.get(stockNo) is None or profitQuote[stockNo].operateProfitGrowthRate['qoq'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(profitQuote[stockNo].operateProfitGrowthRate['qoq'])+',')

            # 營益年增率
            if profitQuote.get(stockNo) is None or profitQuote[stockNo].operateProfitGrowthRate['yoy'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(profitQuote[stockNo].operateProfitGrowthRate['yoy'])+',')

            # 營益累計年增率
            if profitQuote.get(stockNo) is None or profitQuote[stockNo].operateProfitGrowthRate['cumulative'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(profitQuote[stockNo].operateProfitGrowthRate['cumulative'])+',')

            # 近四季ROE成長
            if profitQuote.get(stockNo) is None or profitQuote[stockNo].roeGrowthRate['avg4Q'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(profitQuote[stockNo].roeGrowthRate['avg4Q'])+',')

            # 近四季ROA成長
            if profitQuote.get(stockNo) is None or profitQuote[stockNo].roaGrowthRate['avg4Q'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(profitQuote[stockNo].roaGrowthRate['avg4Q'])+',')

            # 近五年均ROE
            if profitQuote.get(stockNo) is None or profitQuote[stockNo].roeGrowthRate['avg5Y'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(profitQuote[stockNo].roeGrowthRate['avg5Y'])+',')

            # 近五年均ROA
            if profitQuote.get(stockNo) is None or profitQuote[stockNo].roaGrowthRate['avg5Y'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(profitQuote[stockNo].roaGrowthRate['avg5Y'])+',')

            # 最近一季EPS
            #if epsQuote.get(stockNo) is None or epsQuote[stockNo].latestOneQuarterEps is None:
            #    outputFile.write(',')
            #else:
            #    outputFile.write('{0:.4f}'.format(epsQuote[stockNo].latestOneQuarterEps)+',')

            # 累計EPS
            if epsQuote.get(stockNo) is None or epsQuote[stockNo].cumulativeEps is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(epsQuote[stockNo].cumulativeEps)+',')

            # 最近四季EPS
            if epsQuote.get(stockNo) is None or epsQuote[stockNo].latestFourQuarterEps is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(epsQuote[stockNo].latestFourQuarterEps)+',')

            # 5年平均股利
            if averageDividend is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(averageDividend)+',')

            # 5年均配利率
            if averageDividendRate is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(averageDividendRate)+',')

            """
            # 現金股息
            if dividendQuote.get(stockNo) is None or dividendQuote[stockNo].cashDividend.get(currYear-2) is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(dividendQuote[stockNo].cashDividend[currYear-2])+',')
            """

            """
            # 股票股利
            if dividendQuote.get(stockNo) is None or dividendQuote[stockNo].shareDividend.get(currYear-2) is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(dividendQuote[stockNo].shareDividend[currYear-2])+',')
            """

            # 配息年度、現金股息、股票股利
            dividendYear = None
            if dividendQuote.get(stockNo) is not None:
                if dividendQuote[stockNo].cashDividend.get(currYear-1) is not None and \
                   dividendQuote[stockNo].shareDividend.get(currYear-1) is not None:
                    dividendYear = currYear - 1
                    totalDividend = 0
                    if dividendQuote[stockNo].cashDividend.get(currYear-1):
                        totalDividend = dividendQuote[stockNo].cashDividend[currYear-1]
                    if dividendQuote[stockNo].shareDividend.get(currYear-1):
                        totalDividend += dividendQuote[stockNo].shareDividend[currYear-1]
                    if totalDividend == 0:
                        dividendYear = None

                if dividendYear is None and \
                   dividendQuote[stockNo].cashDividend.get(currYear-2) is not None and \
                   dividendQuote[stockNo].shareDividend.get(currYear-2) is not None:
                    dividendYear = currYear - 2
                    totalDividend = 0
                    if dividendQuote[stockNo].cashDividend.get(currYear-2):
                        totalDividend = dividendQuote[stockNo].cashDividend[currYear-2]
                    if dividendQuote[stockNo].shareDividend.get(currYear-2):
                        totalDividend += dividendQuote[stockNo].shareDividend[currYear-2]
                    if totalDividend == 0:
                        dividendYear = None

            if dividendYear is None:
                outputFile.write(',')
                outputFile.write(',')
                outputFile.write(',')
            else:
                outputFile.write(str(dividendYear)+',')
                outputFile.write('{0:.4f}'.format(dividendQuote[stockNo].cashDividend[dividendYear])+',')
                outputFile.write('{0:.4f}'.format(dividendQuote[stockNo].shareDividend[dividendYear])+',')

            # 外資持股
            if legalTrader.get(stockNo) is None or legalTragerNetBuySell['foreign'] is None:
                outputFile.write(',')
                outputFile.write(',')
            else:
                if legalTragerNetBuySell['foreign']['5d'] == 0:
                    outputFile.write(',')
                else:
                    outputFile.write('{0:.4f}'.format(legalTragerNetBuySell['foreign']['5d'])+',')
                if legalTragerNetBuySell['foreign']['1d'] == 0:
                    outputFile.write(',')
                else:
                    outputFile.write('{0:.4f}'.format(legalTragerNetBuySell['foreign']['1d'])+',')

            # 投信持股
            if legalTrader.get(stockNo) is None or legalTragerNetBuySell['domestic'] is None:
                outputFile.write(',')
                outputFile.write(',')
            else:
                if legalTragerNetBuySell['domestic']['5d'] == 0:
                    outputFile.write(',')
                else:
                    outputFile.write('{0:.4f}'.format(legalTragerNetBuySell['domestic']['5d'])+',')
                if legalTragerNetBuySell['domestic']['1d'] == 0:
                    outputFile.write(',')
                else:
                    outputFile.write('{0:.4f}'.format(legalTragerNetBuySell['domestic']['1d'])+',')

            # 自營商持股
            if legalTrader.get(stockNo) is None or legalTragerNetBuySell['dealer'] is None:
                outputFile.write(',')
                outputFile.write(',')
            else:
                if legalTragerNetBuySell['dealer']['5d'] == 0:
                    outputFile.write(',')
                else:
                    outputFile.write('{0:.4f}'.format(legalTragerNetBuySell['dealer']['5d'])+',')
                if legalTragerNetBuySell['dealer']['1d'] == 0:
                    outputFile.write(',')
                else:
                    outputFile.write('{0:.4f}'.format(legalTragerNetBuySell['dealer']['1d'])+',')

            # 券資比
            if marginQuote.get(stockNo) is None or marginQuote[stockNo].marginShort['ratio'] is None:
                outputFile.write('0,')
            else:
                outputFile.write('{0:.4f}'.format(marginQuote[stockNo].marginShort['ratio'])+',')

            outputFile.write('\n')

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockComprehensiveReport]')
    print('輸出股票數量 (stockCount)：', stockCount)
    #print('輸出股票數量：', stockCount['output'])
    print('輸出檔案名稱：', filePath)
    print('輸出檔案大小 (位元組)：', os.path.getsize(filePath))
    print('執行時間 (時：分：秒)：', stopTime - startTime)
    print('\n')


def IsMarketOpen():
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
    # 指令格式(單一股票)：python StockComprehensiveReport.py [股票代號]
    # 指令格式(全部股票)：python StockComprehensiveReport.py
    if len(sys.argv) < 2:
        retriveAllStocks()
    else:
        stockNo = int(sys.argv[1])
        retriveOneStock(stockNo)
