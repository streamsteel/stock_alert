import os
import sys
import logging
import requests
import json

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


class WxBot:
    def __init__(self, wxhook=None) -> None:
        # webhook url
        self.wxhook = os.environ.get('WXHOOK') or wxhook
        if not self.wxhook:
            logger.error('没有提供企业微信webhook，请检查!')
            exit(0)

        self.payload = {
            "msgtype": "markdown",
            "markdown": {"content": ""}
        }

        self.headers = {
            'Content-Type': 'application/json'
        }

    def push(self, data=''):
        self.payload["markdown"]["content"] = data
        # print(self.payload)
        try:
            req = requests.post(self.wxhook, data=json.dumps(self.payload), headers=self.headers)
            logger.info('微信推送成功: \n', req.text)
        except Exception as e:
            logger.error('微信推送失败，原因是: '.format(e))