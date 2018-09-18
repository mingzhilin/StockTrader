import os
import sys
import requests
from lxml.html import fromstring
from datetime import date
from datetime import datetime


class Stock():
    def __init__(self, stockno):
        self.stockno = '{n:04d}'.format(n=stockno)
        self.stockname = ''
        self.category = ''      # 個股分類
        self.capital = 0        # 普通股股本
        self.scope = ''         # 經營業務內容
        self.addr = ''          # 公司地址
        self.agency = ''        # 股票過戶機構
        self.agencyaddr = ''    # 過戶地址

    def display_stockinfo(self):
        print('股票代號 =', self.stockno)
        print('股票名稱 =', self.stockname)
        print('個股分類 =', self.category)
        print('普通股股本 =', self.capital)
        print('經營業務內容 =', self.scope)
        print('公司地址 =', self.addr)
        print('股票過戶機構 =', self.agency)
        print('過戶地址 =', self.agencyaddr)

    def retrive_html(self, url, payload=""):
        while True:
            try:
                response = requests.post(url, data=payload, timeout=5)
            except requests.exceptions.RequestException:
                #print('timeout')
                continue
            break
        html = fromstring(response.content)
        return html

    def retrive_stockinfo(self):
        url = 'http://pchome.megatime.com.tw/stock/sto3/'
        url += 'sid' + self.stockno + '.html'
        #print("url =", url)
        payload = {'is_check': 1}
        html = self.retrive_html(url, payload)

        nodes = html.xpath('//meta[@name="description"]/@content')
        #print('nodes =', nodes)
        if not nodes:
            return False

        nodes = nodes[0].split(',')[0].split()

        # 股票名稱
        self.stockname = nodes[0][0:-12]

        nodes = html.xpath('//tr/th/text() | //tr/td/text() | //tr/td/a/text()')
        #print('nodes =', nodes)
        if not nodes:
            return False

        startidx = nodes.index('個股分類') + 1
        stopidx = nodes.index('掛牌類別')
        #nodes = nodes[startidx:]
        for i in range(startidx, stopidx):
            nodes[i] = nodes[i].replace(' ', '')
            nodes[i] = nodes[i].replace('\r\n', '')
            self.category += nodes[i]

        #nodes = nodes[stopidx+1:]
        startidx = nodes.index('普通股股本') + 1
        try:
            self.capital = int(nodes[startidx].replace(',', ''))
        except:
            self.capital = 0

        #nodes = nodes[startidx+1:]
        startidx = nodes.index('經營業務內容') + 1
        self.scope = nodes[startidx].replace(',', '、')

        #nodes = nodes[startidx+1:]
        startidx = nodes.index('公司地址') + 1
        self.addr = nodes[startidx].replace(',', '、')

        #nodes = nodes[startidx+1:]
        startidx = nodes.index('股票過戶機構') + 1
        self.agency = nodes[startidx].replace(',', '、')

        #nodes = nodes[startidx+1:]
        startidx = nodes.index('過戶機構地址') + 1
        self.agencyaddr = nodes[startidx].replace(',', '、')

        return True


def search_whole_market():
    # 開始時間
    startTime = datetime.now()

    stocks = []
    for stockno in range(1000, 10000):
        print('stock no =', stockno, end='\r')
        stock = Stock(stockno)
        if stock.retrive_stockinfo() is False:
            continue
        stocks.append(stock)
    print('\n')

    # 檢查輸出路徑
    path = '../CompanyInfo'
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

    filePath = path + '/CompanyInfo(' + currTime1 + '-' + currTime2 + ').csv'

    with open(filePath, 'w', encoding='UTF-16') as fout:
        fout.write('股票代號,')
        fout.write('股票名稱,')
        fout.write('公司地址,')
        fout.write('個股分類,')
        fout.write('經營業務內容,')
        fout.write('普通股股本,')
        fout.write('股票過戶機構,')
        fout.write('過戶地址,')
        fout.write('\n')
        for stock in stocks:
            fout.write(stock.stockno+',')
            fout.write(stock.stockname+',')
            fout.write(stock.addr+',')
            fout.write(stock.category+',')
            fout.write(stock.scope+',')
            fout.write(str(stock.capital)+',')
            fout.write(stock.agency+',')
            fout.write(stock.agencyaddr+',')
            fout.write('\n')

    # 結束時間
    stopTime = datetime.now()

    # 輸出執行結果
    print('[CompanyInfo]')
    print('捕獲股票數量：', len(stocks))
    print('輸出檔案名稱：', filePath)
    print('輸出檔案大小 (位元組)：', os.path.getsize(filePath))
    print('執行時間 (時：分：秒)：', stopTime - startTime)
    print('\n')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        stockno = None
    else:
        stockno = int(sys.argv[1])

    if not stockno:
        search_whole_market()
    else:
        stock = Stock(stockno)
        stock.retrive_stockinfo()
        stock.display_stockinfo()
