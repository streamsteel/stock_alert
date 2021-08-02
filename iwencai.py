#!/usr/bin/env python
# -*- encoding: utf-8 -*-

'''
@File          : stock_alert.py
@Author        : HugoMark
@Description   : 每天9点30选择可能会涨停的15只股票
@Date          : 2020/12/11 13:19:01
@Version       : 1.0
'''

import os
import sys
import datetime
import time
import requests
import logging

from requests.api import head

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


def fetch_data(istr: str):
    '''
    @istr: 问财搜索语句
    '''

    url = 'http://www.iwencai.com/unifiedwap/unified-wap/v2/result/get-robot-data'

    data = {
        'question': istr,
        'perpage': '50',
        'page': '1',
        'secondary_intent': '',
        'log_info': '{"input_type":"typewrite"}',
        'source': 'Ths_iwencai_Xuangu',
        'version': '2.0',
        'query_area': '',
        'block_list': '',
        'add_info': '{"urp":{"scene":1,"company":1,"business":1},"contentType":"json","searchInfo":true}',
    }

    headers = {
        'Host': 'www.iwencai.com',
        'hexin-v': 'A2U1fdTIaGNT8Iy_VZ6tq6afdCqcogoHY0r9n2dYJC2rWotcL_IpBPOmDlH0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    }

    req = requests.post(url, headers=headers, data=data)
    try:
        txt = req.json().get('data').get('answer')[0].get('txt')
        content = txt[0].get('content').get('components')[0]['data']['datas']
        for ct in content:
            yield ct
    except Exception as e:
        logger.error('数据解析错误')
        return



def push_weixin(url, all_context):
    # 企业微信推送
    payload = {
        "msgtype": "text",
        "text": {
            "content": '##{} 股票涨停分析\n\n'.format(datetime.date.today())
        }
    }
    wxheaders = {
        'Content-Type': 'application/json'
    }

    for context in all_context:
        payload['text']['content'] += '{}\n'.format(context)

    try:
        req = requests.post(url, data=payload, headers=wxheaders)
        logger.info('企业微信推送成功: {}'.format(req.text))
    except Exception as e:
        logger.error('发生错误', e)


if __name__ == '__main__':
    wxhook = os.environ.get('WXHOOK')
    isstr = os.environ.get('ISSTR')
    if not isstr or not wxhook:
        print('没有提供相关参数，请检查！')

    data = fetch_data(isstr)
    push_weixin(wxhook, data)
