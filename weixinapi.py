from calendar import c
import json
import os
import re
import shutil
import requests
from loguru import logger


class WeiXin_api():
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret

    def http_get(self, url, query):
        rep = requests.get(url=url, params=query
                           )
        if rep.status_code == 200:
            logger.success(
                f"请求成功{url}"
            )
            return rep.json()
        else:
            logger.error('请求错误')
            # logger
            raise Exception

    def http_post(self, url, data, query=None):
        rep = requests.post(url=url, params=query, json=data
                            )
        if rep.status_code == 200:
            logger.success(
                f"{url}请求成功"
            )
            return rep.json()
        else:
            logger.error(f'请求错误{rep.text}')
            return {}
            # logger

    def get_access_token(self):
        """
        作用：获取access_token

        返回参考： {'access_token': '101_I-SDTxs87o24s3Iut-JdtcYAy_mWFw-KfV8xHe4-HlbMSMrR0OIiCjODvP9DC_OrPFS_dj2_hyeoquRewh4EVoqI7QLo3weJxeHYdQT7uEE73IQLPi7GCwIkMbAKSWcAJAZHL', 'expires_in': 5945}
        """
        url = "https://api.weixin.qq.com/cgi-bin/stable_token"
        json_data = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }
        logger.info('正在获取access token')
        rep = self.http_post(url, data=json_data)

        print(rep)
        # return rep

    def code2Session(self, js_code):
        """
        拿到openid 和 session_key

        resp:{'session_key': 't+cRUHe4Iwo6Apon3qgYXA==', 'openid': 'om91I1znjGABHQllHeJNF0SdYzpw'}
        """
        url = 'https://api.weixin.qq.com/sns/jscode2session'
        query = {"appid": self.app_id,
                 "secret": self.app_secret, 'js_code': js_code, 'grant_type': 'authorization_code'}
        logger.info('正在解析phone number')
        rep = self.http_get(url=url, query=query)
        try:
            openid = rep.get('openid')
            session_key = rep.get('session_key')
        except:
            logger.error(
                f'code2Session{rep}'
            )
        print(rep)
        return rep

    def getPhoneNumber(self, access_token, code):
        """
        功能：获取用户手机号

        返回参考：{'errcode': 0, 'errmsg': 'ok', 'phone_info': {'phoneNumber': '18437910867', 'purePhoneNumber': '18437910867', 'countryCode': '86', 'watermark': {'timestamp': 1772690701, 'appid': 'wx5c69e4836a3a8a41'}}}
        """
        url = "https://api.weixin.qq.com/wxa/business/getuserphonenumber"
        query = {'access_token': access_token}
        data = {
            "code": code
        }
        rep = self.http_post(url=url, query=query, data=data)
        print(rep)
        return rep


if __name__ == "__main__":
    access_token = '101_I-SDTxs87o24s3Iut-JdtcYAy_mWFw-KfV8xHe4-HlbMSMrR0OIiCjODvP9DC_OrPFS_dj2_hyeoquRewh4EVoqI7QLo3weJxeHYdQT7uEE73IQLPi7GCwIkMbAKSWcAJAZHL'
    wechat = WeiXin_api(app_id="wx5c69e4836a3a8a41",
                        app_secret="73fbf906099e6eebf0ef18f1bbab7890")
    wechat.get_access_token()
    wechat.code2Session(js_code="0e3gbCFa15XpiL0xzJGa1JZekM1gbCFH")
    wechat.getPhoneNumber(access_token=access_token,
                          code="bc49619bf0f8c99a4530b4e9c49e936bbb8bdcd3695ab626ee959d9db956b5f2")
    pass
