#!/usr/bin/env python
# -*- encoding: utf-8 -*-

'''
@File          : stock_alert.py
@Author        : HugoMark
@Description   : 腾讯云函数用于监控股票价格并通过Server酱做出微信告警
@Date          : 2020/12/11 13:19:01
@Version       : 1.0
'''


import os
import sys
import datetime
import time
from pandas.core.frame import DataFrame
import requests
import akshare as ak
import logging
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

logging.basicConfig(level=logging.INFO,
                    stream=open('./task.log', encoding='utf-8', mode='a'),
                    format='[%(asctime)s] %(levelname)s : %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.FileHandler('./task.log', encoding='utf-8')
logger = logging.getLogger()


console = logging.StreamHandler()
formarter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
console.setFormatter(formarter)
console.setLevel(logging.INFO)

logger.addHandler(console)


# 下面是需要手动设置的东西
config = {
    'sz000671': {
        'buy_price': '6.36',
        'buy_date': datetime.datetime(2021, 3, 4)
    },
    'sz002544': {
        'buy_price': '13.787',
        'buy_date': datetime.datetime(2021, 2, 22)
    },
}

CONSTANT = {
    'yestoday_close': '昨收',
    'yestoday_income': '昨日涨跌',
    'hold_income': '持有涨跌',
    'lower': '今日跌停价',
    'higher': '今日涨停价',
    'hold_days': '持有天数',
    'sell_signal': '卖出信号'
}


def get_data(symbol, start, end):
    # 获取某只股票的
    logger.info('Start get [{}] stock daily data.'.format(symbol))
    try:
        data = ak.stock_zh_a_daily(
            symbol=symbol, start_date=start, end_date=end, adjust="qfq")
        return data
    except Exception as e:
        logger.error('Can not get the data, error: {}'.format(e))
        exit(-1)


def parse_data(data, symbol):
    # 计算单只收益
    his_close_prices = data.close.values
    yestoday_close = his_close_prices[-1]
    before_close = his_close_prices[-2]
    # 1.昨日涨跌
    yestoday_income = np.round(yestoday_close - before_close, decimals=3)
    # 2.明日跌停涨停告警
    lower = np.round(yestoday_close * np.float64(0.9), decimals=3)
    higher = np.round(yestoday_close * np.float64(1.1), decimals=3)

    hold_income = None
    hold_days = None
    sell_signal = None
    if config[symbol].get('buy_price'):
        # 3.持有收益
        hold_income = np.round(
            yestoday_close - np.float64(config[symbol]['buy_price']), decimals=3)

        # 卖出告警: 1.持有收益大于50%；2.止损13%；3.持股达到60天
        hold_days = (datetime.datetime.today() -
                     config[symbol]['buy_date']).days

        # 4.卖出信号
        income_per = hold_income / np.float64(config[symbol]['buy_price'])
        sell_signal = False
        if income_per < np.float64(-.13) or income_per > np.float64(0.5):
            sell_signal = True

    return {
        'yestoday_close': yestoday_close,
        'yestoday_income': yestoday_income,
        'hold_income': hold_income,
        'lower': lower,
        'higher': higher,
        'hold_days': hold_days,
        'sell_signal': sell_signal
    }


def push_weixin(url, all_context):
    # Server酱微信推送
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": '##{} 股票收益统计\n\n'.format(datetime.date.today())
        }
    }

    wxheaders = {
        'Content-Type': 'application/json'
    }

    payload['markdown']['content'] += '> 总收益: <font color=\"warning\">{:.2%}<font>\n'.format(
        all_context['hold_all_income_per'])
    try:
        for symbol, value in all_context['stock'].items():
            payload['markdown']['content'] += '**{}**'.format(symbol)
            if config[symbol].get('buy_price'):
                payload['markdown']['content'] += ' - 买入价:{}\n\n'.format(
                    config[symbol]['buy_price'])
            else:
                payload['markdown']['content'] += '\n\n'
            for quota, qval in value.items():
                if quota == 'sell_signal' and qval:
                    logger.warn('{} 出现卖出信号！'.format(symbol))
                if qval:
                    payload['markdown']['content'] += '{}: {}\n\n'.format(
                        CONSTANT[quota], qval)
    except Exception as e:
        logger.error('Error - {}'.format(e))
    else:
        try:
            req = requests.post(url, data=payload, headers=wxheaders)
            logger.info(req.text)
        except Exception as e:
            logger.error('Error - {}'.format(e))


if __name__ == "__main__":
    # webhook url
    wxhook = os.environ.get('WXHOOK')
    if not wxhook:
        logger.error('没有提供企业微信webhook，请检查!')
        exit(0)

    end = datetime.datetime.today()
    start = end + datetime.timedelta(days=-10)

    all_context = {
        'hold_all_income_per': np.float64(0),
        'stock': {}
    }

    for symbol, value in config.items():
        data = get_data(symbol=symbol, start=start, end=end)
        if not isinstance(data, DataFrame):
            logger.error(
                '{} Daily data is None, please check your code'.format(symbol))
            # 发送Server
            pass
        context = parse_data(data, symbol)
        logger.info('Stock [{}] info: {}'.format(symbol, context))

        # 统计数据汇总
        if config[symbol].get('buy_price'):
            income_per = context['hold_income'] / \
                np.float64(config[symbol]['buy_price'])
            all_context['hold_all_income_per'] += np.round(
                income_per, decimals=4)
        if not all_context['stock'].get(symbol):
            all_context['stock'][symbol] = context
        else:
            all_context['stock'][symbol].update(context)

        time.sleep(2)

    logger.info('All hold info: {}'.format(all_context))

    try:
        push_weixin(wxhook, all_context)
    except Exception as e:
        logger.error('微信推送失败，原因是: '.format(e))
