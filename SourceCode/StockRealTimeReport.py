import os
import sys
import pickle
import requests
import shutil
from datetime import date
from datetime import datetime
from lxml.html import fromstring
from threading import Thread

import StockDailyQuote
from StockDailyQuote import DailyQuote


class RealTimeReport():
    def __init__(self, stockNo):
        self.stockNo = stockNo          # 股票代號
        self.stockName = None           # 股票名稱
        self.closePrice = 0             # 成交價
        self.priceChange = 0            # 漲跌
        self.priceChangeRate = 0        # 漲跌幅
        self.volume = 0                 # 成交量
        self.openPrice = 0              # 開盤價
        self.highPrice = 0              # 最高價
        self.lowPrice = 0               # 最低價
        self.prevClosePrice = 0         # 昨收價
        self.averagePrice = 0           # 均價
        self.currTime = None            # 時間
        self.volumes = None             # 分時累計量
        self.prices = None              # 分時成交價
        self.volumes3 = None            # 分時累計量
        self.prices3 = None             # 分時成交價
        self.volumes4 = None            # 分時累計量
        self.prices4 = None             # 分時成交價

    def display(self):
        print('stockNo =', self.stockNo)
        print('stockName =', self.stockName)
        print('closePrice =', self.closePrice)
        print('priceChange =', self.priceChange)
        print('priceChangeRate =', '{0:.4f}'.format(self.priceChangeRate))
        print('volume =', self.volume)
        print('openPrice =', self.openPrice)
        print('highPrice =', self.highPrice)
        print('lowPrice =', self.lowPrice)
        print('prevClosePrice =', self.prevClosePrice)
        print('averagePrice =', '{0:.4f}'.format(self.averagePrice))

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
        url = 'http://pchome.megatime.com.tw/stock/sto0/ock3/sid' + stockNo + '.html'
        payload = {'is_check': 1}
        html = self.retriveHtml(url, payload)
        if html is None:
            return False

        nodes = html.xpath('//meta[@name="description"]/@content')
        if not nodes:
            return False

        nodes1 = nodes[0].split(',')[0].split()
        nodes2 = nodes[0].split(',')[1].split()

        # 股票名稱
        self.stockName = nodes1[0][0:-12]

        # 成交價
        try:
            self.closePrice = float(nodes1[3])
        except:
            self.closePrice = 0

        nodes = html.xpath('//tr/td/span//text() | //tr/td/text() | //tr/th/text()')
        #print('nodes =', nodes)
        if not nodes:
            return False

        index = nodes.index('漲跌') + 10
        nodes = nodes[index:]

        # 漲跌
        try:
            self.priceChange = float(nodes[0].replace(',', ''))
        except:
            self.priceChange = 0

        if self.closePrice > 0 and self.closePrice - self.priceChange != 0:
            self.priceChangeRate = self.priceChange / (self.closePrice - self.priceChange)

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

        # 昨收價
        try:
            self.prevClosePrice = float(nodes[9].replace(',', ''))
        except:
            self.prevClosePrice = 0

        # ==========================================================================================
        # 均價

        nodes = html.xpath('//td/font/text() | //tr/td/text() | //td/span/font/text()')
        if not nodes:
            return False

        try:
            index = nodes.index('累計量(張)')
            nodes = nodes[index+1:]
        except:
            return False

        prices = []
        while nodes:
            try:
                prices.append(float(nodes[3]))
            except:
                pass
            nodes = nodes[7:]

        if len(prices) > 0:
            self.averagePrice = sum(prices) / len(prices)

        # ==========================================================================================
        # 時間
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        currTime = hour * 60 + minute
        #if hour == 9 and minute < 10:
        if currTime >= 9 * 60 and currTime < 10 * 60 + 30:
            minute = now.minute
        else:
            minute = (now.minute // 5) * 5

        if hour * 60 + minute > 13 * 60 + 30:
            self.currTime = '13:30:00'
        else:
            self.currTime = '{h:02d}:{m:02d}:00'.format(h=hour, m=minute)

        # ==========================================================================================
        # 分時成交價、分時成交量

        self.ParseForFile2(html)    # 1 min + 5 min
        self.ParseForFile3(html)    # 5 min
        self.ParseForFile4(html)    # 1 min

        return True

    def ParseForFile2(self, html):
        nodes = html.xpath('//tr/td/text() | //tr/td/font/text()')
        if not nodes:
            return False
        nodes = nodes[17:]
        #print('nodes =', nodes)

        prices = []
        volumes = []

        while len(nodes) > 0:
            try:
                tokens = nodes[0].split(':')
            except:
                break

            try:
                hour = int(tokens[0])
            except:
                nodes = nodes[7:]
                continue

            try:
                minute = int(tokens[1])
            except:
                nodes = nodes[7:]
                continue

            #if hour * 60 + minute <= 9 * 60 + 10:
            #    break
            if hour * 60 + minute <= 10 * 60 + 30:
                break

            cnt = ((13 * 60 + 30) - (hour * 60 + minute)) // 5 + 1
            if ((13 * 60 + 30) - (hour * 60 + minute)) % 5:
                cnt += 1

            #print('hour =', hour)
            #print('minute =', minute)
            #print('cnt =', cnt)
            #print('len(volumes) =', len(volumes))

            if cnt != len(volumes):
                length = cnt - len(volumes)
            else:
                length = 0

            #print('length =', length)

            for i in range(length):
                try:
                    prices.append(float(nodes[3]))
                    volumes.append(int(nodes[6]))
                except:
                    pass

            #print('nodes[3] =', nodes[3])
            #print('nodes[6] =', nodes[6])
            #print('')

            nodes = nodes[7:]

        #print('1: prices =', prices)
        #print('1: volumes =', volumes)

        #print('nodes =', nodes)

        cnt1 = ((13 * 60 + 30) - (10 * 60 + 30)) // 5 + 1

        while len(nodes) > 0:
            #print('1: nodes =', nodes)
            try:
                tokens = nodes[0].split(':')
            except:
                break

            #print('2: nodes =', nodes)

            try:
                hour = int(tokens[0])
            except:
                nodes = nodes[7:]
                continue

            #print('3: nodes =', nodes)

            try:
                minute = int(tokens[1])
            except:
                nodes = nodes[7:]
                continue

            #print('4: nodes =', nodes)

            #cnt = (9 * 60 + 9) - (hour * 60 + minute) + 53 + 1
            cnt = (10 * 60 + 29) - (hour * 60 + minute) + cnt1 + 1

            if cnt != len(volumes):
                length = cnt - len(volumes)
            else:
                length = 0

            for i in range(length):
                try:
                    prices.append(float(nodes[3]))
                    volumes.append(int(nodes[6]))
                except:
                    pass

            nodes = nodes[7:]

            #print('5: nodes =', nodes)

        #print('2: prices =', prices)
        #print('2: volumes =', volumes)

        cnt2 = (10 * 60 + 29) - (9 * 60) + 1

        totalcnt = cnt1 + cnt2
        #print('cnt1 =', cnt1)
        #print('cnt2 =', cnt2)
        #print('totalcnt =', totalcnt)

        if len(volumes) < totalcnt:
            length = totalcnt - len(volumes)
            for i in range(length):
                volumes.append(0)
                prices.append(0)
        #print('len(volumes) =', len(volumes))
        #print('len(prices) =', len(prices))

        self.volumes = volumes
        self.prices = prices

    def ParseForFile3(self, html):
        nodes = html.xpath('//tr/td/text() | //tr/td/font/text()')
        if not nodes:
            return False
        nodes = nodes[17:]
        #print('nodes =', nodes)

        prices = []
        volumes = []

        while len(nodes) > 0:
            try:
                tokens = nodes[0].split(':')
            except:
                break

            try:
                hour = int(tokens[0])
            except:
                nodes = nodes[7:]
                continue

            try:
                minute = int(tokens[1])
            except:
                nodes = nodes[7:]
                continue

            #if hour * 60 + minute <= 9 * 60 + 10:
            #    break
            #if hour * 60 + minute <= 10 * 60 + 30:
            #    break

            cnt = ((13 * 60 + 30) - (hour * 60 + minute)) // 5 + 1
            if ((13 * 60 + 30) - (hour * 60 + minute)) % 5:
                cnt += 1

            #print('hour =', hour)
            #print('minute =', minute)
            #print('cnt =', cnt)
            #print('len(volumes) =', len(volumes))

            if cnt != len(volumes):
                length = cnt - len(volumes)
            else:
                length = 0

            #print('length =', length)

            for i in range(length):
                try:
                    prices.append(float(nodes[3]))
                    volumes.append(int(nodes[6]))
                except:
                    pass

            #print('nodes[3] =', nodes[3])
            #print('nodes[6] =', nodes[6])
            #print('')

            nodes = nodes[7:]

        #print('1: prices =', prices)
        #print('1: volumes =', volumes)

        #print('nodes =', nodes)

        cnt1 = ((13 * 60 + 30) - (9 * 60)) // 5 + 1

        totalcnt = cnt1# + cnt2
        #print('cnt1 =', cnt1)
        #print('cnt2 =', cnt2)
        #print('totalcnt =', totalcnt)

        if len(volumes) < totalcnt:
            length = totalcnt - len(volumes)
            for i in range(length):
                volumes.append(0)
                prices.append(0)
        #print('len(volumes) =', len(volumes))
        #print('len(prices) =', len(prices))

        self.volumes3 = volumes
        self.prices3 = prices


    def ParseForFile4(self, html):
        nodes = html.xpath('//tr/td/text() | //tr/td/font/text()')
        if not nodes:
            return False
        nodes = nodes[17:]
        #print('nodes =', nodes)

        prices = []
        volumes = []

        while len(nodes) > 0:
            #print('1: nodes =', nodes)
            try:
                tokens = nodes[0].split(':')
            except:
                break

            #print('2: nodes =', nodes)

            try:
                hour = int(tokens[0])
            except:
                nodes = nodes[7:]
                continue

            #print('3: nodes =', nodes)

            try:
                minute = int(tokens[1])
            except:
                nodes = nodes[7:]
                continue

            #print('4: nodes =', nodes)

            cnt = (13 * 60 + 30) - (hour * 60 + minute) + 1

            if cnt != len(volumes):
                length = cnt - len(volumes)
            else:
                length = 0

            for i in range(length):
                try:
                    prices.append(float(nodes[3]))
                    volumes.append(int(nodes[6]))
                except:
                    pass

            nodes = nodes[7:]

            #print('5: nodes =', nodes)

        #print('2: prices =', prices)
        #print('2: volumes =', volumes)

        cnt2 = (13 * 60 + 30) - (9 * 60) + 1

        totalcnt = cnt2
        #totalcnt = cnt1 + cnt2
        #print('cnt1 =', cnt1)
        #print('cnt2 =', cnt2)
        #print('totalcnt =', totalcnt)

        if len(volumes) < totalcnt:
            length = totalcnt - len(volumes)
            for i in range(length):
                volumes.append(0)
                prices.append(0)
        #print('len(volumes) =', len(volumes))
        #print('len(prices) =', len(prices))

        self.volumes4 = volumes
        self.prices4 = prices


def calculateAverageVolume(stockNo, dayOffset, dailyQuotes, currQuote, dayCount):
    """計算均量"""

    maxDayCount = len(dailyQuotes)
    if maxDayCount < dayCount:
        dayCount = maxDayCount

    if dayOffset == 0:
        totalVolume = currQuote.volume
    else:
        totalVolume = dailyQuotes[0][stockNo].volume

    actualDayCount = 1
    for i in range(dayOffset, dayOffset+dayCount-1):
        try:
            totalVolume += dailyQuotes[i][stockNo].volume
            actualDayCount += 1
        except:
            pass

    averageVolume = totalVolume / actualDayCount

    return averageVolume


def calculateAveragePrice(stockNo, marketOpen, dailyQuotes, currQuote, dayOffset, dayCount):
    """計算均價"""

    maxDayCount = len(dailyQuotes)
    if maxDayCount < dayCount:
        dayCount = maxDayCount

    if marketOpen is True:
        startDay = dayOffset
        if dayOffset > 0:
            if dailyQuotes[dayOffset-1].get(stockNo) is None:
                totalPrice = 0
                actualDayCount = 0
            else:
                totalPrice = dailyQuotes[dayOffset-1][stockNo].closePrice
                actualDayCount = 1
        else:
            if currQuote is None:
                totalPrice = 0
                actualDayCount = 0
            else:
                totalPrice = currQuote.closePrice
                actualDayCount = 1
    else:
        startDay = dayOffset + 1
        #try:
        #    totalPrice = dailyQuotes[dayOffset][stockNo].closePrice
        #except:
        #    totalPrice = dailyQuotes[dayOffset+1][stockNo].closePrice
        if dailyQuotes[dayOffset].get(stockNo) is None:
            if dailyQuotes[dayOffset+1].get(stockNo) is None:
                totalPrice = 0
                actualDayCount = 0
            else:
                totalPrice = dailyQuotes[dayOffset+1][stockNo].closePrice
                actualDayCount = 1
        else:
            totalPrice = dailyQuotes[dayOffset][stockNo].closePrice
            actualDayCount = 1
    stopDay = startDay + dayCount - 1

    #actualDayCount = 1
    for i in range(startDay, stopDay):
        try:
            totalPrice += dailyQuotes[i][stockNo].closePrice
            actualDayCount += 1
        except:
            pass

    if actualDayCount > 0:
        averagePrice = totalPrice / actualDayCount
    else:
        averagePrice = 0

    return averagePrice


def searchHighPrice(stockNo, dayOffset, dailyQuotes, currQuote, dayCount):
    """搜尋最高價"""

    maxDayCount = len(dailyQuotes)
    if maxDayCount < dayCount:
        dayCount = maxDayCount

    if dayOffset == 0:
        start = 0
        stop = dayCount
        #highPrice = currQuote.highPrice
        #highPrice = dailyQuotes[1][stockNo].highPrice
        if currQuote is None:
            if dailyQuotes[1].get(stockNo) is None:
                highPrice = 0
            else:
                highPrice = dailyQuotes[1][stockNo].highPrice
        else:
            highPrice = currQuote.highPrice
    elif dayOffset == 1:
        start = 1
        stop = dayCount + 1
        if stop > maxDayCount:
            stop = maxDayCount
        #try:
        #    highPrice = dailyQuotes[1][stockNo].highPrice
        #except:
        #    highPrice = dailyQuotes[2][stockNo].highPrice
        if dailyQuotes[1].get(stockNo) is None:
            if dailyQuotes[2].get(stockNo) is None:
                highPrice = 0
            else:
                highPrice = dailyQuotes[2][stockNo].highPrice
        else:
            highPrice = dailyQuotes[1][stockNo].highPrice
    else:
        start = dayOffset + 1
        stop = dayOffset + dayCount
        if stop > maxDayCount:
            stop = maxDayCount
        if dailyQuotes[dayOffset].get(stockNo) is None:
            #return None
            if dailyQuotes[dayOffset+1].get(stockNo) is None:
                return None
            else:
                highPrice = dailyQuotes[dayOffset+1][stockNo].highPrice
        else:
            highPrice = dailyQuotes[dayOffset][stockNo].highPrice

    for i in range(start, stop):
        try:
            if dailyQuotes[i].get(stockNo) is None:
                continue
            else:
                if dailyQuotes[i][stockNo].highPrice > highPrice:
                    highPrice = dailyQuotes[i][stockNo].highPrice
        except:
            pass

    return highPrice


def searchLowPrice(stockNo, dayOffset, dailyQuotes, currQuote, dayCount):
    """搜尋最低價"""

    maxDayCount = len(dailyQuotes)
    if maxDayCount < dayCount:
        dayCount = maxDayCount

    if dayOffset == 0:
        start = 0
        stop = dayCount
        #lowPrice = currQuote.lowPrice
        #lowPrice = dailyQuotes[1][stockNo].lowPrice
        if currQuote is None:
            if dailyQuotes[1].get(stockNo) is None:
                lowPrice = 0
            else:
                lowPrice = dailyQuotes[1][stockNo].lowPrice
        else:
            lowPrice = currQuote.lowPrice
    elif dayOffset == 1:
        start = 1
        stop = dayCount + 1
        if stop > maxDayCount:
            stop = maxDayCount
        #try:
        #    lowPrice = dailyQuotes[1][stockNo].lowPrice
        #except:
        #    lowPrice = dailyQuotes[2][stockNo].lowPrice
        if dailyQuotes[1].get(stockNo) is None:
            if dailyQuotes[2].get(stockNo) is None:
                lowPrice = 0
            else:
                lowPrice = dailyQuotes[2][stockNo].lowPrice
        else:
            lowPrice = dailyQuotes[1][stockNo].lowPrice
    else:
        start = dayOffset + 1
        stop = dayOffset + dayCount
        if dailyQuotes[dayOffset].get(stockNo) is None:
            #return None
            if dailyQuotes[dayOffset+1].get(stockNo) is None:
                return None
            else:
                lowPrice = dailyQuotes[dayOffset+1][stockNo].lowPrice
        else:
            lowPrice = dailyQuotes[dayOffset][stockNo].lowPrice

    for i in range(start, stop):
        try:
            if dailyQuotes[i].get(stockNo) is None:
                continue
            else:
                if dailyQuotes[i][stockNo].lowPrice < lowPrice:
                    lowPrice = dailyQuotes[i][stockNo].lowPrice
        except:
            pass

    return lowPrice


def calculateKD(stockNo, dayOffset, dailyQuotes, currQuote, dayCount=30, kdPeriod=9):
    """計算日KD"""

    maxDayCount = len(dailyQuotes) - kdPeriod
    if maxDayCount < dayCount:
        dayCount = maxDayCount

    if dayOffset == 0:
        start = dayCount - 1
        stop = dayOffset - 1
    elif dayOffset == 1:
        start = dayCount
        stop = dayOffset - 1
    index = dayCount

    rsvs = {}
    ks = {}
    ds = {}

    #print('dayOffset =', dayOffset)
    #print('start =', start)
    #print('stop =', stop)

    prevK = 50
    prevD = 50
    for i in range(start, stop, -1):
        highPrice = searchHighPrice(stockNo, i, dailyQuotes, currQuote, kdPeriod)
        #print('i =', i, 'kdPeriod =', kdPeriod)
        lowPrice = searchLowPrice(stockNo, i, dailyQuotes, currQuote, kdPeriod)
        if highPrice is None or lowPrice is None:
            return (None, None)
        #try:
        #    closePrice = dailyQuotes[i][stockNo].closePrice
        #except:
        #    closePrice = dailyQuotes[i+1][stockNo].closePrice
        if dailyQuotes[i].get(stockNo) is None:
            if dailyQuotes[i+1].get(stockNo) is None:
                return (None, None)
            else:
                closePrice = dailyQuotes[i+1][stockNo].closePrice
        else:
            closePrice = dailyQuotes[i][stockNo].closePrice
        #print('i =', i, 'highPrice =', highPrice, 'lowPrice =', lowPrice, 'closePrice =', closePrice)
        if (highPrice - lowPrice) * 100 == 0:
            rsvs[index] = 0
        else:
            rsvs[index] = (closePrice - lowPrice) / (highPrice - lowPrice) * 100
        ks[index] = (1 - 1 / 3) * prevK + 1 / 3 * rsvs[index]
        ds[index] = (1 - 1 / 3) * prevD + 1 / 3 * ks[index]
        #print('index =', index, 'rsvs =', rsvs[index], 'ks =', ks[index], 'ds =', ds[index])
        prevK = ks[index]
        prevD = ds[index]
        index -= 1

    highPrice = searchHighPrice(stockNo, dayOffset, dailyQuotes, currQuote, kdPeriod-1)
    lowPrice = searchLowPrice(stockNo, dayOffset, dailyQuotes, currQuote, kdPeriod-1)
    if highPrice is None or lowPrice is None or highPrice == lowPrice:
        return (None, None)
    if currQuote.highPrice > highPrice:
        highPrice = currQuote.highPrice
    if currQuote.lowPrice < lowPrice:
        lowPrice = currQuote.lowPrice
    closePrice = currQuote.closePrice
    #print('i =', i, 'highPrice =', highPrice, 'lowPrice =', lowPrice, 'closePrice =', closePrice)
    rsvs[0] = (closePrice - lowPrice) / (highPrice - lowPrice) * 100
    ks[0] = (1 - 1 / 3) * prevK + 1 / 3 * rsvs[0]
    ds[0] = (1 - 1 / 3) * prevD + 1 / 3 * ks[0]
    #print('index =', index, 'rsvs =', rsvs[0], 'ks =', ks[0], 'ds =', ds[0])

    return (ks, ds)


def calculateKD2(highPricesPerMonth, lowPricesPerMonth, closePricesPerMonth, monthCount=30, kdPeriod=9):
    """計算月KD"""

    startMonth = len(closePricesPerMonth) - 1
    stopMonth = -1
    startKD = len(closePricesPerMonth) - kdPeriod
    stopKD = -1

    highPrices = {}
    lowPrices = {}
    closePrices = {}
    for month in range(startMonth, stopMonth, -1):
        highPrice = -1000000
        lowPrice = 1000000
        for day in highPricesPerMonth[month]:
            if highPricesPerMonth[month][day] > highPrice:
                highPrice = highPricesPerMonth[month][day]
            if lowPricesPerMonth[month][day] < lowPrice:
                lowPrice = lowPricesPerMonth[month][day]
        highPrices[month] = highPrice
        lowPrices[month] = lowPrice
        for day in range(0, len(closePricesPerMonth[month])):
            if day in closePricesPerMonth[month]:
                closePrices[month] = closePricesPerMonth[month][day]
                break

    rsvs = {}
    ks = {}
    ds = {}

    try:
        prevK = 50
        prevD = 50
        for i in range(startKD, stopKD, -1):
            highPrice = -1000000
            lowPrice = 1000000
            for j in range(i, i + kdPeriod):
                if highPrices[j] > highPrice:
                    highPrice = highPrices[j]
                if lowPrices[j] < lowPrice:
                    lowPrice = lowPrices[j]
            if (highPrice - lowPrice) * 100 == 0:
                rsvs[i] = 0
            else:
                rsvs[i] = (closePrices[i] - lowPrice) / (highPrice - lowPrice) * 100
            ks[i] = (1 - 1 / 3) * prevK + 1 / 3 * rsvs[i]
            ds[i] = (1 - 1 / 3) * prevD + 1 / 3 * ks[i]
            prevK = ks[i]
            prevD = ds[i]
    except:
        return (None, None)

    return (ks, ds)


def calculateKD3(highPricesPerWeek, lowPricesPerWeek, closePricesPerWeek, weekCount=30, kdPeriod=9):
    """計算週KD"""

    startWeek = len(closePricesPerWeek) - 1
    stopWeek = -1
    startKD = len(closePricesPerWeek) - kdPeriod
    stopKD = -1

    highPrices = {}
    lowPrices = {}
    closePrices = {}
    for month in range(startWeek, stopWeek, -1):
        highPrice = -1000000
        lowPrice = 1000000
        for day in highPricesPerWeek[month]:
            if highPricesPerWeek[month][day] > highPrice:
                highPrice = highPricesPerWeek[month][day]
            if lowPricesPerWeek[month][day] < lowPrice:
                lowPrice = lowPricesPerWeek[month][day]
        highPrices[month] = highPrice
        lowPrices[month] = lowPrice
        for day in range(0, len(closePricesPerWeek[month])):
            if day in closePricesPerWeek[month]:
                closePrices[month] = closePricesPerWeek[month][day]
                break

    rsvs = {}
    ks = {}
    ds = {}

    try:
        prevK = 50
        prevD = 50
        for i in range(startKD, stopKD, -1):
            highPrice = -1000000
            lowPrice = 1000000
            for j in range(i, i + kdPeriod):
                if highPrices[j] > highPrice:
                    highPrice = highPrices[j]
                if lowPrices[j] < lowPrice:
                    lowPrice = lowPrices[j]
            if (highPrice - lowPrice) * 100 == 0:
                rsvs[i] = 0
            else:
                rsvs[i] = (closePrices[i] - lowPrice) / (highPrice - lowPrice) * 100
            ks[i] = (1 - 1 / 3) * prevK + 1 / 3 * rsvs[i]
            ds[i] = (1 - 1 / 3) * prevD + 1 / 3 * ks[i]
            prevK = ks[i]
            prevD = ds[i]
    except:
        return (None, None)

    return (ks, ds)


def getFilePath():
    # 檢查輸出路徑
    #path = '../StockRealTimeReport'
    path = '../ComprehensiveReport'
    if os.path.exists(path) is False:
        os.mkdir(path)

    """
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
    filePath = path + '/StockRealTimeReport(' + currTime1 + '-' + currTime2 + ').csv'
    """

    # 輸出檔案
    filePath = path + '/StockRealTimeReport.csv'

    return filePath


def SaveFile(filePath, quotes):
    # 檢查是否有今日行情
    if isMarketOpen():
        dayOffset = 0
        marketOpen = True
    else:
        dayOffset = 1
        marketOpen = False

    # 讀取歷史資料
    dailyQuotes = StockDailyQuote.loadQuotes(0, 70)

    # 輸出檔案
    with open(filePath, 'w', encoding='UTF-16') as outputFile:
        outputFile.write('股票代號,')
        outputFile.write('股票名稱,')
        outputFile.write('前日開盤價,')
        outputFile.write('前日最高價,')
        outputFile.write('前日最低價,')
        outputFile.write('前日收盤價,')
        outputFile.write('昨日開盤價,')
        outputFile.write('昨日最高價,')
        outputFile.write('昨日最低價,')
        outputFile.write('昨日收盤價,')
        outputFile.write('今日開盤價,')
        outputFile.write('今日最高價,')
        outputFile.write('今日最低價,')
        outputFile.write('今日收盤價,')
        outputFile.write('今日漲跌幅,')
        outputFile.write('今日累計量,')
        outputFile.write('昨日收量,')
        outputFile.write('20日均量,')
        outputFile.write('前5日均價,')
        outputFile.write('前20日均價,')
        outputFile.write('前60日均價,')
        outputFile.write('昨5日均價,')
        outputFile.write('昨20日均價,')
        outputFile.write('昨60日均價,')
        outputFile.write('今5日均價,')
        outputFile.write('今20日均價,')
        outputFile.write('今60日均價,')
        outputFile.write('年最高價,')
        outputFile.write('年最低價,')
        outputFile.write('20日最高價,')
        outputFile.write('20日最低價,')
        outputFile.write('昨9日K,')
        outputFile.write('昨9日D,')
        outputFile.write('今9日K,')
        outputFile.write('今9日D,')
        outputFile.write('時間,')
        outputFile.write('\n')
        for stockNo in range(1000, 10000):
            if quotes.get(stockNo) is None:
                continue

            #if dailyQuotes[dayOffset].get(stockNo) is None:
            #    continue

            #if dailyQuotes[dayOffset+1].get(stockNo) is None:
            #    continue

            # 均量
            averageVolumes = {}
            averageVolumes['20d'] = calculateAverageVolume(stockNo, dayOffset, dailyQuotes, quotes[stockNo], 20)
            #averageVolumes['60d'] = calculateAverageVolume(stockNo, dayOffset, dailyQuotes, quotes[stockNo], 60)

            # 均價 (今日、昨日、前日)
            averagePrices = {0: {}, 1: {}, 2: {}}
            for i in range(len(averagePrices)):
                averagePrices[i]['5d'] = calculateAveragePrice(stockNo, marketOpen, dailyQuotes, quotes[stockNo], i, 5)
                averagePrices[i]['10d'] = calculateAveragePrice(stockNo, marketOpen, dailyQuotes, quotes[stockNo], i, 10)
                averagePrices[i]['20d'] = calculateAveragePrice(stockNo, marketOpen, dailyQuotes, quotes[stockNo], i, 20)
                averagePrices[i]['60d'] = calculateAveragePrice(stockNo, marketOpen, dailyQuotes, quotes[stockNo], i, 60)

            # 最高價
            highPrices = {}
            highPrices['20d'] = searchHighPrice(stockNo, dayOffset, dailyQuotes, quotes[stockNo], 19)
            highPrices['60d'] = searchHighPrice(stockNo, dayOffset, dailyQuotes, quotes[stockNo], 59)
            if quotes[stockNo].highPrice > highPrices['20d']:
                highPrices['20d'] = quotes[stockNo].highPrice
            if quotes[stockNo].highPrice > highPrices['60d']:
                highPrices['60d'] = quotes[stockNo].highPrice

            # 最低價
            lowPrices = {}
            lowPrices['20d'] = searchLowPrice(stockNo, dayOffset, dailyQuotes, quotes[stockNo], 19)
            lowPrices['60d'] = searchLowPrice(stockNo, dayOffset, dailyQuotes, quotes[stockNo], 59)
            if quotes[stockNo].lowPrice < lowPrices['20d']:
                lowPrices['20d'] = quotes[stockNo].lowPrice
            if quotes[stockNo].lowPrice < lowPrices['60d']:
                lowPrices['60d'] = quotes[stockNo].lowPrice

            #print('dayOffset =', dayOffset)
            #print('highPrices =', highPrices)
            #print('lowPrices =', lowPrices)
            #print('averagePrices =', averagePrices)
            #print('averageVolumes =', averageVolumes)

            # KD
            (ks, ds) = calculateKD(stockNo, dayOffset, dailyQuotes, quotes[stockNo])

            # 股票代號
            outputFile.write(str(quotes[stockNo].stockNo)+',')

            # 股票名稱
            outputFile.write(quotes[stockNo].stockName+',')

            # 前日開盤價
            if dailyQuotes[dayOffset+1].get(stockNo) is None:
                if dailyQuotes[dayOffset+2].get(stockNo) is None:
                    outputFile.write(',')
                else:
                    outputFile.write(str(dailyQuotes[dayOffset+2][stockNo].closePrice)+',')
            else:
                outputFile.write(str(dailyQuotes[dayOffset+1][stockNo].openPrice)+',')

            # 前日最高價
            if dailyQuotes[dayOffset+1].get(stockNo) is None:
                if dailyQuotes[dayOffset+2].get(stockNo) is None:
                    outputFile.write(',')
                else:
                    outputFile.write(str(dailyQuotes[dayOffset+2][stockNo].closePrice)+',')
            else:
                outputFile.write(str(dailyQuotes[dayOffset+1][stockNo].highPrice)+',')

            # 前日最低價
            if dailyQuotes[dayOffset+1].get(stockNo) is None:
                if dailyQuotes[dayOffset+2].get(stockNo) is None:
                    outputFile.write(',')
                else:
                    outputFile.write(str(dailyQuotes[dayOffset+2][stockNo].closePrice)+',')
            else:
                outputFile.write(str(dailyQuotes[dayOffset+1][stockNo].lowPrice)+',')

            # 前日收盤價
            if dailyQuotes[dayOffset+1].get(stockNo) is None:
                if dailyQuotes[dayOffset+2].get(stockNo) is None:
                    outputFile.write(',')
                else:
                    outputFile.write(str(dailyQuotes[dayOffset+2][stockNo].closePrice)+',')
            else:
                outputFile.write(str(dailyQuotes[dayOffset+1][stockNo].closePrice)+',')

            # 昨日開盤價
            if dailyQuotes[dayOffset].get(stockNo) is None:
                if dailyQuotes[dayOffset+1].get(stockNo) is None:
                    outputFile.write(',')
                else:
                    outputFile.write(str(dailyQuotes[dayOffset+1][stockNo].closePrice)+',')
            else:
                outputFile.write(str(dailyQuotes[dayOffset][stockNo].openPrice)+',')

            # 昨日最高價
            if dailyQuotes[dayOffset].get(stockNo) is None:
                if dailyQuotes[dayOffset+1].get(stockNo) is None:
                    outputFile.write(',')
                else:
                    outputFile.write(str(dailyQuotes[dayOffset+1][stockNo].closePrice)+',')
            else:
                outputFile.write(str(dailyQuotes[dayOffset][stockNo].highPrice)+',')

            # 昨日最低價
            if dailyQuotes[dayOffset].get(stockNo) is None:
                if dailyQuotes[dayOffset+1].get(stockNo) is None:
                    outputFile.write(',')
                else:
                    outputFile.write(str(dailyQuotes[dayOffset+1][stockNo].closePrice)+',')
            else:
                outputFile.write(str(dailyQuotes[dayOffset][stockNo].lowPrice)+',')

            # 昨日收盤價
            if dailyQuotes[dayOffset].get(stockNo) is None:
                if dailyQuotes[dayOffset+1].get(stockNo) is None:
                    outputFile.write(',')
                else:
                    outputFile.write(str(dailyQuotes[dayOffset+1][stockNo].closePrice)+',')
            else:
                outputFile.write(str(dailyQuotes[dayOffset][stockNo].closePrice)+',')

            # 今日開盤價
            outputFile.write(str(quotes[stockNo].openPrice)+',')

            # 今日最高價
            outputFile.write(str(quotes[stockNo].highPrice)+',')

            # 今日最低價
            outputFile.write(str(quotes[stockNo].lowPrice)+',')

            # 今日收盤價
            outputFile.write(str(quotes[stockNo].closePrice)+',')

            # 今日漲跌幅
            outputFile.write(str(quotes[stockNo].priceChangeRate)+',')

            # 今日累計量
            outputFile.write(str(quotes[stockNo].volume)+',')

            # 昨日收量
            if dailyQuotes[dayOffset].get(stockNo) is None:
                outputFile.write(',')
            else:
                outputFile.write(str(dailyQuotes[dayOffset][stockNo].volume)+',')

            # 20日均量
            outputFile.write('{0:.4f}'.format(averageVolumes['20d'])+',')

            # 前5日均價、前20日均價、前60日均價
            # 昨5日均價、昨20日均價、昨60日均價
            # 今5日均價、今20日均價、今60日均價
            for i in range(len(averagePrices)-1, -1, -1):
                outputFile.write('{0:.4f}'.format(averagePrices[i]['5d'])+',')
                outputFile.write('{0:.4f}'.format(averagePrices[i]['20d'])+',')
                outputFile.write('{0:.4f}'.format(averagePrices[i]['60d'])+',')

            # 年最高價
            if dailyQuotes[dayOffset].get(stockNo) is None:
                if dailyQuotes[dayOffset+1].get(stockNo) is None:
                    yearHighPrice = None
                else:
                    yearHighPrice = dailyQuotes[dayOffset+1][stockNo].yearHighPrice
            else:
                yearHighPrice = dailyQuotes[dayOffset][stockNo].yearHighPrice

            if yearHighPrice is None:
                outputFile.write(',')
            else:
                if yearHighPrice > highPrices['20d']:
                    outputFile.write('{0:.4f}'.format(yearHighPrice)+',')
                else:
                    outputFile.write('{0:.4f}'.format(highPrices['20d'])+',')

            # 年最低價
            if dailyQuotes[dayOffset].get(stockNo) is None:
                if dailyQuotes[dayOffset+1].get(stockNo) is None:
                    yearLowPrice = None
                else:
                    yearLowPrice = dailyQuotes[dayOffset+1][stockNo].yearLowPrice
            else:
                yearLowPrice = dailyQuotes[dayOffset][stockNo].yearLowPrice

            if yearLowPrice is None:
                outputFile.write(',')
            else:
                if yearLowPrice < lowPrices['20d']:
                    outputFile.write('{0:.4f}'.format(yearLowPrice)+',')
                else:
                    outputFile.write('{0:.4f}'.format(lowPrices['20d'])+',')

            # 20日最高價
            if highPrices['20d'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(highPrices['20d'])+',')

            # 20日最低價
            if lowPrices['20d'] is None:
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(lowPrices['20d'])+',')

            # 昨9日K、昨9日D
            # 今9日K、今9日D
            if ks is None or ds is None:
                outputFile.write(',')
                outputFile.write(',')
                outputFile.write(',')
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(ks[1])+',')
                outputFile.write('{0:.4f}'.format(ds[1])+',')
                outputFile.write('{0:.4f}'.format(ks[0])+',')
                outputFile.write('{0:.4f}'.format(ds[0])+',')

            # 時間
            outputFile.write(quotes[stockNo].currTime+',')

            outputFile.write('\n')



def getFilePath2():
    # 檢查輸出路徑
    path = '../StockRealTimeReport'
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
    filePath = path + '/StockCumulativeVolumeReport(' + currTime1 + '-' + currTime2 + ').csv'

    return filePath


def SaveFile2(filePath, quotes):
    with open(filePath, 'w', encoding='UTF-16') as outputFile:
        outputFile.write('股票代號,')
        outputFile.write('股票名稱,')
        outputFile.write('時間,')
        outputFile.write('累計量,')
        outputFile.write('收盤量,')
        #outputFile.write('成交價,')
        outputFile.write('漲跌差異%,')
        outputFile.write('成交量差異%,')
        outputFile.write('\n')
        cnt1 = ((13 * 60 + 30) - (10 * 60 + 30)) // 5 + 1
        #for stock in stocks:
        for stockNo in range(1000, 10000):
            if quotes.get(stockNo) is None:
                continue

            currTime = 13 * 60 + 30
            while currTime >= 10 * 60 + 30:
                outputFile.write(str(quotes[stockNo].stockNo)+',')
                outputFile.write(quotes[stockNo].stockName+',')
                hour = currTime // 60
                minute = currTime % 60
                outputFile.write('{h:02d}:{m:02d}:00,'.format(h=hour, m=minute))

                currIndex = (13 * 60 + 30 - currTime) // 5
                prevIndex1 = currIndex + 1
                prevIndex2 = currIndex + 2

                if quotes[stockNo].volumes is None or quotes[stockNo].prices is None:
                    outputFile.write('0,')
                    outputFile.write('0,')
                    outputFile.write('0,')
                    outputFile.write('0,')
                else:
                    outputFile.write(str(quotes[stockNo].volumes[currIndex])+',')
                    outputFile.write(str(quotes[stockNo].volumes[0])+',')
                    #outputFile.write(str(quotes[stockNo].prices[currIndex])+',')

                    if prevIndex1 < len(quotes[stockNo].prices) and quotes[stockNo].prices[prevIndex1] > 0:
                        curr = quotes[stockNo].prices[currIndex]
                        prev = quotes[stockNo].prices[prevIndex1]
                        changeRate = (curr - prev) / prev
                        outputFile.write('{0:.4f}'.format(changeRate)+',')
                    else:
                        outputFile.write('0,')

                    if currTime == 10 * 60 + 30:
                        outputFile.write('0,')
                    elif currTime == 10 * 60 + 35:
                        curr = quotes[stockNo].volumes[currIndex]
                        prev1 = quotes[stockNo].volumes[prevIndex1]
                        if prev1 == 0:
                            changeRate = 0
                        else:
                            changeRate = (curr - prev1) / prev1
                        outputFile.write('{0:.4f}'.format(changeRate)+',')
                    else:
                        if prevIndex2 < len(quotes[stockNo].volumes):
                            curr = quotes[stockNo].volumes[currIndex]
                            prev1 = quotes[stockNo].volumes[prevIndex1]
                            prev2 = quotes[stockNo].volumes[prevIndex2]
                            diff = prev1 - prev2
                            if diff == 0:
                                changeRate = 0
                            else:
                                changeRate = (curr - prev1) / diff
                            outputFile.write('{0:.4f}'.format(changeRate)+',')
                        else:
                            outputFile.write('0,')

                outputFile.write('\n')
                currTime -= 5

            currTime = 10 * 60 + 29
            while currTime >= 9 * 60:
                outputFile.write(str(quotes[stockNo].stockNo)+',')
                outputFile.write(quotes[stockNo].stockName+',')
                hour = currTime // 60
                minute = currTime % 60
                outputFile.write('{h:02d}:{m:02d}:00,'.format(h=hour, m=minute))

                currIndex = (10 * 60 + 29 - currTime) + cnt1
                prevIndex1 = currIndex + 1
                prevIndex2 = currIndex + 2

                if quotes[stockNo].volumes is None or quotes[stockNo].prices is None:
                    outputFile.write('0,')
                    outputFile.write('0,')
                    outputFile.write('0,')
                    outputFile.write('0,')
                else:
                    outputFile.write(str(quotes[stockNo].volumes[currIndex])+',')
                    outputFile.write(str(quotes[stockNo].volumes[0])+',')
                    #outputFile.write(str(quotes[stockNo].prices[currIndex])+',')

                    if prevIndex1 < len(quotes[stockNo].prices) and quotes[stockNo].prices[prevIndex1] > 0:
                        curr = quotes[stockNo].prices[currIndex]
                        prev = quotes[stockNo].prices[prevIndex1]
                        changeRate = (curr - prev) / prev
                        outputFile.write('{0:.4f}'.format(changeRate)+',')
                    else:
                        outputFile.write('0,')

                    if currTime == 9 * 60:
                        outputFile.write('0,')
                    elif currTime == 9 * 60 + 1:
                        curr = quotes[stockNo].volumes[currIndex]
                        prev1 = quotes[stockNo].volumes[prevIndex1]
                        if prev1 == 0:
                            changeRate = 0
                        else:
                            changeRate = (curr - prev1) / prev1
                        outputFile.write('{0:.4f}'.format(changeRate)+',')
                    else:
                        if prevIndex2 < len(quotes[stockNo].volumes):
                            curr = quotes[stockNo].volumes[currIndex]
                            prev1 = quotes[stockNo].volumes[prevIndex1]
                            prev2 = quotes[stockNo].volumes[prevIndex2]
                            diff = prev1 - prev2
                            if diff == 0:
                                changeRate = 0
                            else:
                                changeRate = (curr - prev1) / diff
                            outputFile.write('{0:.4f}'.format(changeRate)+',')
                        else:
                            outputFile.write('0,')

                outputFile.write('\n')
                currTime -= 1


def getFilePath3():
    # 檢查輸出路徑
    path = '../StockRealTimeReport'
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
    filePath = path + '/StockCumulativeVolumeReport5Min(' + currTime1 + '-' + currTime2 + ').csv'

    return filePath


def SaveFile3(filePath, quotes):
    with open(filePath, 'w', encoding='UTF-16') as outputFile:
        outputFile.write('股票代號,')
        outputFile.write('股票名稱,')
        outputFile.write('時間,')
        outputFile.write('累計量,')
        outputFile.write('收盤量,')
        #outputFile.write('成交價,')
        outputFile.write('漲跌差異%,')
        outputFile.write('成交量差異%,')
        outputFile.write('\n')

        for stockNo in range(1000, 10000):
            if quotes.get(stockNo) is None:
                continue

            currTime = 13 * 60 + 30
            while currTime >= 9 * 60:
                outputFile.write(str(quotes[stockNo].stockNo)+',')
                outputFile.write(quotes[stockNo].stockName+',')
                hour = currTime // 60
                minute = currTime % 60
                outputFile.write('{h:02d}:{m:02d}:00,'.format(h=hour, m=minute))

                if quotes[stockNo].volumes3 is None or quotes[stockNo].prices3 is None:
                    outputFile.write('0,')
                    outputFile.write('0,')
                    outputFile.write('0,')
                    outputFile.write('0,')
                else:
                    currIndex = (13 * 60 + 30 - currTime) // 5
                    outputFile.write(str(quotes[stockNo].volumes3[currIndex])+',')
                    outputFile.write(str(quotes[stockNo].volumes3[0])+',')
                    #outputFile.write(str(quotes[stockNo].prices[currIndex])+',')

                    prevIndex = currIndex + 1
                    if prevIndex < len(quotes[stockNo].prices3) and quotes[stockNo].prices3[prevIndex] > 0:
                        curr = quotes[stockNo].prices3[currIndex]
                        prev = quotes[stockNo].prices3[prevIndex]
                        changeRate = (curr - prev) / prev
                        outputFile.write('{0:.4f}'.format(changeRate)+',')
                    else:
                        outputFile.write('0,')
                    if prevIndex < len(quotes[stockNo].volumes3) and quotes[stockNo].volumes3[prevIndex] > 0:
                        curr = quotes[stockNo].volumes3[currIndex]
                        prev = quotes[stockNo].volumes3[prevIndex]
                        changeRate = (curr - prev) / prev
                        outputFile.write('{0:.4f}'.format(changeRate)+',')
                    else:
                        outputFile.write('0,')

                outputFile.write('\n')
                currTime -= 5



def getFilePath4():
    # 檢查輸出路徑
    path = '../StockRealTimeReport'
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
    filePath = path + '/StockRealTimeReport月K(' + currTime1 + '-' + currTime2 + ').csv'

    return filePath


def SaveFile4(filePath, quotes):
    with open(filePath, 'w', encoding='UTF-16') as outputFile:
        outputFile.write('股票代號,')
        outputFile.write('股票名稱,')
        outputFile.write('時間,')
        outputFile.write('累計量,')
        outputFile.write('收盤量,')
        #outputFile.write('成交價,')
        outputFile.write('漲跌差異%,')
        outputFile.write('成交量差異%,')
        outputFile.write('\n')

        for stockNo in range(1000, 10000):
            if quotes.get(stockNo) is None:
                continue

            if quotes[stockNo].volumes3 is None or quotes[stockNo].prices3 is None:
                continue

            currTime = 13 * 60 + 30
            while currTime >= 9 * 60:
                currIndex = (13 * 60 + 30 - currTime)
                prevIndex1 = currIndex + 1
                prevIndex2 = currIndex + 2

                priceChangeRate = 0
                if prevIndex1 < len(quotes[stockNo].prices4) and quotes[stockNo].prices4[prevIndex1] > 0:
                    curr = quotes[stockNo].prices4[currIndex]
                    prev = quotes[stockNo].prices4[prevIndex1]
                    priceChangeRate = (curr - prev) / prev

                if priceChangeRate >= 0.005:
                    outputFile.write(str(quotes[stockNo].stockNo)+',')
                    outputFile.write(quotes[stockNo].stockName+',')

                    hour = currTime // 60
                    minute = currTime % 60
                    outputFile.write('{h:02d}:{m:02d}:00,'.format(h=hour, m=minute))

                    #print('hour =', hour)
                    #print('minute =', minute)
                    #print('currPrice =', curr)
                    #print('prevPrice =', prev)

                    outputFile.write(str(quotes[stockNo].volumes4[currIndex])+',')
                    outputFile.write(str(quotes[stockNo].volumes4[0])+',')
                    outputFile.write('{0:.4f}'.format(priceChangeRate)+',')

                    volumeChangeRate = 0

                    if currTime == 9 * 60:
                        volumeChangeRate = 0
                        #outputFile.write('0,')
                    elif currTime == 9 * 60 + 1:
                        curr = quotes[stockNo].volumes4[currIndex]
                        prev1 = quotes[stockNo].volumes4[prevIndex1]
                        if prev1 == 0:
                            volumeChangeRate = 0
                        else:
                            volumeChangeRate = (curr - prev1) / prev1
                        #outputFile.write('{0:.4f}'.format(volumeChangeRate)+',')
                    elif currTime == 13 * 60 + 30:
                        if len(quotes[stockNo].volumes4) >= 6:
                            curr = quotes[stockNo].volumes4[currIndex]
                            prev1 = quotes[stockNo].volumes4[5]
                            prev2 = quotes[stockNo].volumes4[6]
                            diff = prev1 - prev2
                            if diff == 0:
                                volumeChangeRate = 0
                            else:
                                volumeChangeRate = (curr - prev1) / diff
                            #outputFile.write('{0:.4f}'.format(volumeChangeRate)+',')
                    else:
                        if prevIndex2 < len(quotes[stockNo].volumes4):
                            curr = quotes[stockNo].volumes4[currIndex]
                            prev1 = quotes[stockNo].volumes4[prevIndex1]
                            prev2 = quotes[stockNo].volumes4[prevIndex2]
                            #print('currVolume =', curr)
                            #print('prevVolume1 =', prev1)
                            #print('prevVolume2 =', prev2)
                            diff = prev1 - prev2
                            if diff == 0:
                                volumeChangeRate = 0
                            else:
                                volumeChangeRate = (curr - prev1) / diff
                            #outputFile.write('{0:.4f}'.format(volumeChangeRate)+',')
                        #else:
                        #    outputFile.write('0,')

                    outputFile.write('{0:.4f}'.format(volumeChangeRate)+',')
                    outputFile.write('\n')

                currTime -= 1


def GetFilePath5():
    # 檢查輸出路徑
    #path = '../StockRealTimeReport'
    path = '../ComprehensiveReport'
    if os.path.exists(path) is False:
        os.mkdir(path)

    """
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
    filePath = path + '/StockRealTimeReportMonthKD(' + currTime1 + '-' + currTime2 + ').csv'
    """

    # 輸出檔案
    filePath = path + '/StockRealTimeReportMonthKD.csv'

    return filePath


def SaveFile5(filePath, quotes):
    # 檢查是否有今日行情
    #if isMarketOpen():
    #    dayOffset = 0
    #    marketOpen = True
    #else:
    #    dayOffset = 1
    #    marketOpen = False

    # 讀取歷史資料
    path = '../DailyQuote/'
    if os.path.isdir(path) is False:
        return None
    files = os.listdir(path)
    files.sort(reverse=True)

    closePricesPerMonth = {}
    openPricesPerMonth = {}
    highPricesPerMonth = {}
    lowPricesPerMonth = {}
    volumesPerMonth = {}
    for stockNo in range(1000, 10000):
        if quotes.get(stockNo) is None:
            closePricesPerMonth[stockNo] = None
            openPricesPerMonth[stockNo] = None
            highPricesPerMonth[stockNo] = None
            lowPricesPerMonth[stockNo] = None
            volumesPerMonth[stockNo] = None
            continue
        closePricesPerMonth[stockNo] = {}
        openPricesPerMonth[stockNo] = {}
        highPricesPerMonth[stockNo] = {}
        lowPricesPerMonth[stockNo] = {}
        volumesPerMonth[stockNo] = {}

    month = -1
    day = -1
    filesPerMonth = {}
    monthStr = None
    for fileName in files:
        if fileName[11:18] != monthStr:
            monthStr = fileName[11:18]
            month += 1
            day = 0
            filesPerMonth[month] = {}
            for stockNo in range(1000, 10000):
                if quotes.get(stockNo) is None:
                    continue
                closePricesPerMonth[stockNo][month] = {}
                openPricesPerMonth[stockNo][month] = {}
                highPricesPerMonth[stockNo][month] = {}
                lowPricesPerMonth[stockNo][month] = {}
                volumesPerMonth[stockNo][month] = {}
        filesPerMonth[month][day] = fileName
        with open(path + fileName, 'rb') as inputFile:
            try:
                quote = pickle.load(inputFile)
            except:
                continue
            for stockNo in range(1000, 10000):
                if quotes.get(stockNo) is None:
                    continue
                if quote.get(stockNo) is None:
                    continue
                closePricesPerMonth[stockNo][month][day] = quote[stockNo].closePrice
                openPricesPerMonth[stockNo][month][day] = quote[stockNo].openPrice
                highPricesPerMonth[stockNo][month][day] = quote[stockNo].highPrice
                lowPricesPerMonth[stockNo][month][day] = quote[stockNo].lowPrice
                volumesPerMonth[stockNo][month][day] = quote[stockNo].volume
        day += 1

    # 輸出檔案
    with open(filePath, 'w', encoding='UTF-16') as outputFile:
        outputFile.write('股票代號,')
        outputFile.write('股票名稱,')
        outputFile.write('前月開盤價,')
        outputFile.write('前月最高價,')
        outputFile.write('前月最低價,')
        outputFile.write('前月收盤價,')
        outputFile.write('上月開盤價,')
        outputFile.write('上月最高價,')
        outputFile.write('上月最低價,')
        outputFile.write('上月收盤價,')
        outputFile.write('本月開盤價,')
        outputFile.write('本月最高價,')
        outputFile.write('本月最低價,')
        outputFile.write('本月收盤價,')
        outputFile.write('本月累計量,')
        outputFile.write('上月收量,')
        outputFile.write('上月9月K,')
        outputFile.write('上月9月D,')
        outputFile.write('本月9月K,')
        outputFile.write('本月9月D,')
        outputFile.write('\n')
        for stockNo in range(1000, 10000):
            if quotes.get(stockNo) is None:
                continue

            # 股票代號
            outputFile.write(str(quotes[stockNo].stockNo)+',')

            # 股票名稱
            outputFile.write(quotes[stockNo].stockName+',')

            # 前月開盤價
            try:
                month = 2
                day = len(openPricesPerMonth[stockNo][month]) - 1
                openPrice = openPricesPerMonth[stockNo][month][day]
                outputFile.write(str(openPrice)+',')
            except:
                outputFile.write(',')

            # 前月最高價
            try:
                month = 2
                highPrice = -1
                for day in highPricesPerMonth[stockNo][month]:
                    if highPricesPerMonth[stockNo][month][day] > highPrice:
                        highPrice = highPricesPerMonth[stockNo][month][day]
                outputFile.write(str(highPrice)+',')
            except:
                outputFile.write(',')

            # 前月最低價
            try:
                month = 2
                lowPrice = 1000000
                for day in lowPricesPerMonth[stockNo][month]:
                    if lowPricesPerMonth[stockNo][month][day] < lowPrice:
                        lowPrice = lowPricesPerMonth[stockNo][month][day]
                outputFile.write(str(lowPrice)+',')
            except:
                outputFile.write(',')

            # 前月收盤價
            try:
                month = 2
                day = 0
                closePrice = closePricesPerMonth[stockNo][month][day]
                outputFile.write(str(closePrice)+',')
            except:
                outputFile.write(',')

            # 上月開盤價
            try:
                month = 1
                day = len(openPricesPerMonth[stockNo][month]) - 1
                openPrice = openPricesPerMonth[stockNo][month][day]
                outputFile.write(str(openPrice)+',')
            except:
                outputFile.write(',')

            # 上月最高價
            try:
                month = 1
                highPrice = -1
                for day in highPricesPerMonth[stockNo][month]:
                    if highPricesPerMonth[stockNo][month][day] > highPrice:
                        highPrice = highPricesPerMonth[stockNo][month][day]
                outputFile.write(str(highPrice)+',')
            except:
                outputFile.write(',')

            # 上月最低價
            try:
                month = 1
                lowPrice = 1000000
                for day in lowPricesPerMonth[stockNo][month]:
                    if lowPricesPerMonth[stockNo][month][day] < lowPrice:
                        lowPrice = lowPricesPerMonth[stockNo][month][day]
                outputFile.write(str(lowPrice)+',')
            except:
                outputFile.write(',')

            # 上月收盤價
            try:
                month = 1
                day = 0
                closePrice = closePricesPerMonth[stockNo][month][day]
                outputFile.write(str(closePrice)+',')
            except:
                outputFile.write(',')

            # 本月開盤價
            try:
                month = 0
                day = len(openPricesPerMonth[stockNo][month]) - 1
                openPrice = openPricesPerMonth[stockNo][month][day]
                outputFile.write(str(openPrice)+',')
            except:
                outputFile.write(',')

            # 本月最高價
            try:
                month = 0
                highPrice = -1
                for day in highPricesPerMonth[stockNo][month]:
                    if highPricesPerMonth[stockNo][month][day] > highPrice:
                        highPrice = highPricesPerMonth[stockNo][month][day]
                outputFile.write(str(highPrice)+',')
            except:
                outputFile.write(',')

            # 本月最低價
            try:
                month = 0
                lowPrice = 1000000
                for day in lowPricesPerMonth[stockNo][month]:
                    if lowPricesPerMonth[stockNo][month][day] < lowPrice:
                        lowPrice = lowPricesPerMonth[stockNo][month][day]
                outputFile.write(str(lowPrice)+',')
            except:
                outputFile.write(',')

            # 本月收盤價
            try:
                month = 0
                day = 0
                closePrice = closePricesPerMonth[stockNo][month][day]
                outputFile.write(str(closePrice)+',')
            except:
                outputFile.write(',')

            # 本月累計量
            if volumesPerMonth[stockNo] is None:
                outputFile.write(',')
            else:
                month = 0
                totalVolume = 0
                for day in volumesPerMonth[stockNo][month]:
                    totalVolume += volumesPerMonth[stockNo][month][day]
                outputFile.write(str(totalVolume)+',')

            # 上月累計量
            if volumesPerMonth[stockNo] is None:
                outputFile.write(',')
            else:
                month = 1
                totalVolume = 0
                for day in volumesPerMonth[stockNo][month]:
                    totalVolume += volumesPerMonth[stockNo][month][day]
                outputFile.write(str(totalVolume)+',')

            # KD
            (ks, ds) = calculateKD2(highPricesPerMonth[stockNo], lowPricesPerMonth[stockNo], closePricesPerMonth[stockNo])

            # 上月9月K、上月9月D
            # 本月9月K、本月9月D
            if ks is None or ds is None:
                outputFile.write(',')
                outputFile.write(',')
                outputFile.write(',')
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(ks[1])+',')
                outputFile.write('{0:.4f}'.format(ds[1])+',')
                outputFile.write('{0:.4f}'.format(ks[0])+',')
                outputFile.write('{0:.4f}'.format(ds[0])+',')

            outputFile.write('\n')


def GetFilePath6():
    # 檢查輸出路徑
    #path = '../StockRealTimeReport'
    path = '../ComprehensiveReport'
    if os.path.exists(path) is False:
        os.mkdir(path)

    """
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
    filePath = path + '/StockRealTimeReportWeekKD(' + currTime1 + '-' + currTime2 + ').csv'
    """

    # 輸出檔案
    filePath = path + '/StockRealTimeReportWeekKD.csv'

    return filePath


def SaveFile6(filePath, quotes):
    # 檢查是否有今日行情
    #if isMarketOpen():
    #    dayOffset = 0
    #    marketOpen = True
    #else:
    #    dayOffset = 1
    #    marketOpen = False

    # 讀取歷史資料
    path = '../DailyQuote/'
    if os.path.isdir(path) is False:
        return None
    files = os.listdir(path)
    files.sort(reverse=True)

    closePricesPerWeek = {}
    openPricesPerWeek = {}
    highPricesPerWeek = {}
    lowPricesPerWeek = {}
    volumesPerWeek = {}
    for stockNo in range(1000, 10000):
        if quotes.get(stockNo) is None:
            closePricesPerWeek[stockNo] = None
            openPricesPerWeek[stockNo] = None
            highPricesPerWeek[stockNo] = None
            lowPricesPerWeek[stockNo] = None
            volumesPerWeek[stockNo] = None
            continue
        closePricesPerWeek[stockNo] = {}
        openPricesPerWeek[stockNo] = {}
        highPricesPerWeek[stockNo] = {}
        lowPricesPerWeek[stockNo] = {}
        volumesPerWeek[stockNo] = {}

    week = -1
    day = -1
    filesPerWeek = {}
    currDate = date.today()
    currDayOfWeek = -1
    for fileName in files:
        try:
            prevDate = date.fromisoformat(fileName[11:21])
        except:
            # avoid .DS_Store (for Mac OS)
            continue
        prevDayOfWeek = prevDate.weekday()
        if prevDayOfWeek >= currDayOfWeek or (currDate-prevDate).days > 5:
            week += 1
            day = 0
            filesPerWeek[week] = {}
            for stockNo in range(1000, 10000):
                if quotes.get(stockNo) is None:
                    continue
                closePricesPerWeek[stockNo][week] = {}
                openPricesPerWeek[stockNo][week] = {}
                highPricesPerWeek[stockNo][week] = {}
                lowPricesPerWeek[stockNo][week] = {}
                volumesPerWeek[stockNo][week] = {}
        filesPerWeek[week][day] = fileName
        with open(path + fileName, 'rb') as inputFile:
            try:
                quote = pickle.load(inputFile)
            except:
                continue
            for stockNo in range(1000, 10000):
                if quotes.get(stockNo) is None:
                    continue
                if quote.get(stockNo) is None:
                    continue
                closePricesPerWeek[stockNo][week][day] = quote[stockNo].closePrice
                openPricesPerWeek[stockNo][week][day] = quote[stockNo].openPrice
                highPricesPerWeek[stockNo][week][day] = quote[stockNo].highPrice
                lowPricesPerWeek[stockNo][week][day] = quote[stockNo].lowPrice
                volumesPerWeek[stockNo][week][day] = quote[stockNo].volume
        day += 1
        currDate = prevDate
        currDayOfWeek = prevDayOfWeek

    """
    for week in filesPerWeek:
        print(week, ':', 'filesPerWeeks =', filesPerWeek[week])
    """

    # 輸出檔案
    with open(filePath, 'w', encoding='UTF-16') as outputFile:
        outputFile.write('股票代號,')
        outputFile.write('股票名稱,')
        outputFile.write('前週開盤價,')
        outputFile.write('前週最高價,')
        outputFile.write('前週最低價,')
        outputFile.write('前週收盤價,')
        outputFile.write('上週開盤價,')
        outputFile.write('上週最高價,')
        outputFile.write('上週最低價,')
        outputFile.write('上週收盤價,')
        outputFile.write('本週開盤價,')
        outputFile.write('本週最高價,')
        outputFile.write('本週最低價,')
        outputFile.write('本週收盤價,')
        outputFile.write('本週累計量,')
        outputFile.write('上週收量,')
        outputFile.write('上週9週K,')
        outputFile.write('上週9週D,')
        outputFile.write('本週9週K,')
        outputFile.write('本週9週D,')
        outputFile.write('\n')
        for stockNo in range(1000, 10000):
            if quotes.get(stockNo) is None:
                continue

            # 股票代號
            outputFile.write(str(quotes[stockNo].stockNo)+',')

            # 股票名稱
            outputFile.write(quotes[stockNo].stockName+',')

            # 前週開盤價
            try:
                week = 2
                day = len(openPricesPerWeek[stockNo][week]) - 1
                openPrice = openPricesPerWeek[stockNo][week][day]
                outputFile.write(str(openPrice)+',')
            except:
                outputFile.write(',')

            # 前週最高價
            try:
                week = 2
                highPrice = -1
                for day in highPricesPerWeek[stockNo][week]:
                    if highPricesPerWeek[stockNo][week][day] > highPrice:
                        highPrice = highPricesPerWeek[stockNo][week][day]
                outputFile.write(str(highPrice)+',')
            except:
                outputFile.write(',')

            # 前週最低價
            try:
                week = 2
                lowPrice = 1000000
                for day in lowPricesPerWeek[stockNo][week]:
                    if lowPricesPerWeek[stockNo][week][day] < lowPrice:
                        lowPrice = lowPricesPerWeek[stockNo][week][day]
                outputFile.write(str(lowPrice)+',')
            except:
                outputFile.write(',')

            # 前週收盤價
            try:
                week = 2
                day = 0
                closePrice = closePricesPerWeek[stockNo][week][day]
                outputFile.write(str(closePrice)+',')
            except:
                outputFile.write(',')

            # 上週開盤價
            try:
                week = 1
                day = len(openPricesPerWeek[stockNo][week]) - 1
                openPrice = openPricesPerWeek[stockNo][week][day]
                outputFile.write(str(openPrice)+',')
            except:
                outputFile.write(',')

            # 上週最高價
            try:
                week = 1
                highPrice = -1
                for day in highPricesPerWeek[stockNo][week]:
                    if highPricesPerWeek[stockNo][week][day] > highPrice:
                        highPrice = highPricesPerWeek[stockNo][week][day]
                outputFile.write(str(highPrice)+',')
            except:
                outputFile.write(',')

            # 上週最低價
            try:
                week = 1
                lowPrice = 1000000
                for day in lowPricesPerWeek[stockNo][week]:
                    if lowPricesPerWeek[stockNo][week][day] < lowPrice:
                        lowPrice = lowPricesPerWeek[stockNo][week][day]
                outputFile.write(str(lowPrice)+',')
            except:
                outputFile.write(',')

            # 上週收盤價
            try:
                week = 1
                day = 0
                closePrice = closePricesPerWeek[stockNo][week][day]
                outputFile.write(str(closePrice)+',')
            except:
                outputFile.write(',')

            # 本週開盤價
            try:
                week = 0
                day = len(openPricesPerWeek[stockNo][week]) - 1
                openPrice = openPricesPerWeek[stockNo][week][day]
                outputFile.write(str(openPrice)+',')
            except:
                outputFile.write(',')

            # 本週最高價
            try:
                week = 0
                highPrice = -1
                for day in highPricesPerWeek[stockNo][week]:
                    if highPricesPerWeek[stockNo][week][day] > highPrice:
                        highPrice = highPricesPerWeek[stockNo][week][day]
                outputFile.write(str(highPrice)+',')
            except:
                outputFile.write(',')

            # 本週最低價
            try:
                week = 0
                lowPrice = 1000000
                for day in lowPricesPerWeek[stockNo][week]:
                    if lowPricesPerWeek[stockNo][week][day] < lowPrice:
                        lowPrice = lowPricesPerWeek[stockNo][week][day]
                outputFile.write(str(lowPrice)+',')
            except:
                outputFile.write(',')

            # 本週收盤價
            try:
                week = 0
                day = 0
                closePrice = closePricesPerWeek[stockNo][week][day]
                outputFile.write(str(closePrice)+',')
            except:
                outputFile.write(',')

            # 本週累計量
            if volumesPerWeek[stockNo] is None:
                outputFile.write(',')
            else:
                week = 0
                totalVolume = 0
                try:
                    for day in volumesPerWeek[stockNo][week]:
                        totalVolume += volumesPerWeek[stockNo][week][day]
                except:
                    totalVolume = 0
                outputFile.write(str(totalVolume)+',')

            # 上週累計量
            if volumesPerWeek[stockNo] is None:
                outputFile.write(',')
            else:
                week = 1
                totalVolume = 0
                try:
                    for day in volumesPerWeek[stockNo][week].keys():
                        totalVolume += volumesPerWeek[stockNo][week][day]
                except:
                    totalVolume = 0
                outputFile.write(str(totalVolume)+',')

            # KD
            (ks, ds) = calculateKD3(highPricesPerWeek[stockNo], lowPricesPerWeek[stockNo], closePricesPerWeek[stockNo])

            # 上週9週K、上週9週D
            # 本週9週K、本週9週D
            if ks is None or ds is None:
                outputFile.write(',')
                outputFile.write(',')
                outputFile.write(',')
                outputFile.write(',')
            else:
                outputFile.write('{0:.4f}'.format(ks[1])+',')
                outputFile.write('{0:.4f}'.format(ds[1])+',')
                outputFile.write('{0:.4f}'.format(ks[0])+',')
                outputFile.write('{0:.4f}'.format(ds[0])+',')

            outputFile.write('\n')


def retriveOneStock(stockNo):
    # 檢查是否有今日行情
    if isMarketOpen():
        dayOffset = 0
        marketOpen = True
    else:
        dayOffset = 1
        marketOpen = False

    quotes = RealTimeReport(stockNo)
    quotes.retriveQuote()
    quotes.display()

    dailyQuotes = StockDailyQuote.loadQuotes(0, 70)

    # 均量
    averageVolumes = {}
    averageVolumes['20d'] = calculateAverageVolume(stockNo, dayOffset, dailyQuotes, quotes, 20)
    #averageVolumes['60d'] = calculateAverageVolume(stockNo, dayOffset, dailyQuotes, quotes[stockNo], 60)

    # 均價 (今日、昨日、前日)
    averagePrices = {0: {}, 1: {}, 2: {}}
    for i in range(len(averagePrices)):
        averagePrices[i]['5d'] = calculateAveragePrice(stockNo, marketOpen, dailyQuotes, quotes, i, 5)
        averagePrices[i]['10d'] = calculateAveragePrice(stockNo, marketOpen, dailyQuotes, quotes, i, 10)
        averagePrices[i]['20d'] = calculateAveragePrice(stockNo, marketOpen, dailyQuotes, quotes, i, 20)
        averagePrices[i]['60d'] = calculateAveragePrice(stockNo, marketOpen, dailyQuotes, quotes, i, 60)

    # 最高價
    highPrices = {}
    highPrices['20d'] = searchHighPrice(stockNo, dayOffset, dailyQuotes, quotes, 19)
    highPrices['60d'] = searchHighPrice(stockNo, dayOffset, dailyQuotes, quotes, 59)
    if quotes.highPrice > highPrices['20d']:
        highPrices['20d'] = quotes.highPrice
    if quotes.highPrice > highPrices['60d']:
        highPrices['60d'] = quotes.highPrice

    # 最低價
    lowPrices = {}
    lowPrices['20d'] = searchLowPrice(stockNo, dayOffset, dailyQuotes, quotes, 19)
    lowPrices['60d'] = searchLowPrice(stockNo, dayOffset, dailyQuotes, quotes, 59)
    if quotes.lowPrice < lowPrices['20d']:
        lowPrices['20d'] = quotes.lowPrice
    if quotes.lowPrice < lowPrices['60d']:
        lowPrices['60d'] = quotes.lowPrice

    print('highPrices =', highPrices)
    print('lowPrices =', lowPrices)
    print('averagePrices =', averagePrices)
    print('averageVolumes =', averageVolumes)

    print('yearHighPrice =', dailyQuotes[0][stockNo].yearHighPrice)
    print('yearLowPrice =', dailyQuotes[0][stockNo].yearLowPrice)

    (ks, ds) = calculateKD(stockNo, dayOffset, dailyQuotes, quotes)
    print('ks =', ks)
    print('ds =', ds)


def retriveStocks(division, prevDailyQuotes):
    for stockNo in range(division['start'], division['stop']):
        print('股票代號：', stockNo, end='\r')
        if prevDailyQuotes.get(stockNo) is None:
            continue
        quote = RealTimeReport(stockNo)
        if quote.retriveQuote() is True:
            division['quotes'][stockNo] = quote


def retriveAllStocksMultiThread():
    print('\n')

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

    #now = datetime.now()
    #currTime = now.hour * 60 * 60 + now.minute * 60 + now.second
    #marketStartTime = 9 * 60 * 60
    #marketStopTime = 14 * 60 * 60 + 30 * 60

    # 輸出報表
    #if currTime < marketStartTime or currTime > marketStopTime:
    #    filePath = getFilePath2()
    #    SaveFile2(filePath, quotes)
    filePath = getFilePath2()
    SaveFile2(filePath, quotes)

    # 5 min
    #filePath = getFilePath3()
    #SaveFile3(filePath, quotes)

    # 1 min
    #filePath = getFilePath4()
    #SaveFile4(filePath, quotes)

    # 月KD
    filePath = GetFilePath5()
    SaveFile5(filePath, quotes)

    # 週KD
    filePath = GetFilePath6()
    SaveFile6(filePath, quotes)

    filePath = getFilePath()
    SaveFile(filePath, quotes)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockRealTimeReport]')
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
        quote = RealTimeReport(stockNo)
        if quote.retriveQuote() is True:
            quotes[stockNo] = quote
            #quotes[stockNo].display()
    print('\n')

    # 輸出報表
    filePath = getFilePath2()
    SaveFile2(filePath, quotes)
    filePath = getFilePath()
    SaveFile(filePath, quotes)

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[StockRealTimeReport]')
    print('捕獲股票數量：', len(quotes))
    print('輸出檔案名稱：', filePath)
    print('輸出檔案大小 (位元組)：', os.path.getsize(filePath))
    print('執行時間 (時：分：秒)：', stopTime - startTime)
    print('\n')


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
    # 指令格式(單一股票)：python StockRealTimeReport.py [股票代號]
    # 指令格式(全部股票)：python StockRealTimeReport.py
    if len(sys.argv) < 2:
        #retriveAllStocks()
        retriveAllStocksMultiThread()
    else:
        stockNo = int(sys.argv[1])
        retriveOneStock(stockNo)
