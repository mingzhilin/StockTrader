import StockDailyQuote
from StockDailyQuote import DailyQuote


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


def searchStrongRaiseStock():
    DAY_COUNT = 30

    dailyQuotes = StockDailyQuote.loadQuotes(0, DAY_COUNT)

    for stockNo in range(1000, 10000):
        isSkip = False
        for i in range(DAY_COUNT):
            if dailyQuotes[i].get(stockNo) is None:
                isSkip = True
                break
        if isSkip is True:
            continue

        if dailyQuotes[2][stockNo].volume < 1000:
            continue

        # 量縮二天
        if dailyQuotes[0][stockNo].volume > dailyQuotes[2][stockNo].volume * 3 / 4 or \
           dailyQuotes[1][stockNo].volume > dailyQuotes[2][stockNo].volume * 3 / 4:
            continue

        # 今日小於昨日
        if dailyQuotes[0][stockNo].closePrice > dailyQuotes[1][stockNo].closePrice:
            continue

        # 連漲二天
        if dailyQuotes[2][stockNo].closePrice < dailyQuotes[3][stockNo].closePrice * 1.01 or \
           dailyQuotes[3][stockNo].closePrice < dailyQuotes[4][stockNo].closePrice * 1.01:
           continue

        # 股價在MA30之上
        if dailyQuotes[0][stockNo].closePrice < calculateAveragePrice(dailyQuotes, stockNo, DAY_COUNT):
            continue

        print('[多]', stockNo, dailyQuotes[0][stockNo].stockName)


if __name__ == '__main__':
    searchStrongRaiseStock()
