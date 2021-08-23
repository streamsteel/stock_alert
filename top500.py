import requests
from datetime import datetime, timedelta
from lxml import etree
from requests.sessions import session

from wx import WxBot
from config import *


class Top:
    def __init__(self) -> None:
        self.flag = True
        self.endtime = datetime.today()
        self.session = requests.Session()
        self.proxies = {'http': 'http://localhost:7890',
                        'https': 'http://localhost:7890'}

        self.message = ''

    def fetch_index_html(self):
        start_url = BASE_URL + INDEX
        req = self.session.get(start_url)
        html = req.text

        selector = etree.HTML(html)
        instList = selector.xpath('//*[@id="new"]/tr[2]/td/table/tr')
        for inst in instList:
            tds = inst.findall('td[@class="tdlefttop"]')
            for td in tds:
                title = td.find('a').get('title')
                href = td.find('a').get('href')
                yield title, href

    def fetch_article(self, title, alink):
        global message

        url = BASE_URL + alink
        req = self.session.get(url)
        html = req.text

        selector = etree.HTML(html)
        tableList = selector.xpath(
            '//*[@id="table1"]/tr[3]/td/table[4]/tr[position()>1]')
        for tr in tableList:
            ops = [col.text for col in tr.findall('td')]
            updateDate = datetime.strptime(ops[7].strip(), '%Y-%m-%d')
            if updateDate >= self.endtime:
                self.message += "\n<font size=12>{code}\t{name}\t{manage}\t{change}</font>\n".format(
                    code=ops[1],
                    name=ops[2],
                    manage=title,
                    change=ops[-2]) if ops[-2] in ('新进', '增加') else ''
            else:
                break


if __name__ == '__main__':
    top = Top()
    result = top.fetch_index_html()
    for r in result:
        top.fetch_article(r[0], r[1])

    # 企业微信推送
    wx = WxBot(
        wxhook='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=cf440b68-85d6-4b62-ba3c-a1ec18299b5c')
    wx.push(top.message)
