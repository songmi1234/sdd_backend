import functools
from http import cookies
from itertools import product
from pickletools import optimize
import re
from loguru import logger
# import quickjs
import json
from urllib.parse import urlencode
import time
from typing import Any, Awaitable, Callable, List, Optional, Union
from type import reposen_model
from enum import Enum
from datetime import date, timedelta
from app import app07
from datetime import datetime
from utils import jxlm
# 第三方库导入
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, ValidationError, field_validator, Field
from tortoise.exceptions import IntegrityError

# 本地模块导入（按字母顺序分组）
from orm.models import *  # 建议明确导入所需模型，避免通配符
from utils import (shop_data_upload, qianchuan_api_service)

from http import cookies
# from rich.progress import (
#     Progress,
#     TextColumn,
#     BarColumn,
#     DownloadColumn,
#     TransferSpeedColumn,
#     TimeRemainingColumn,
#     SpinnerColumn
# )
import numpy as np
import random
import time
import re
import urllib.parse

import json
import execjs
from urllib.parse import urlencode
import requests
from loguru import logger
from src.encrypt import verfyfp
import pandas as pd

import os
from utils import webid
# 使用


def async_timer(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """异步函数计时器装饰器，统计函数执行时间"""
    @functools.wraps(func)  # 保留原函数元信息
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()  # 开始计时
        result = await func(*args, **kwargs)  # 执行原函数
        end_time = time.perf_counter()  # 结束计时

        # 计算耗时（秒），保留3位小数
        execution_time = round(end_time - start_time, 3)

        # 打印耗时信息（可替换为日志记录）
        logger.info(f"函数 {func.__name__} 执行耗时: {execution_time} 秒")

        # 将耗时信息添加到返回结果中（可选）
        if isinstance(result, dict):
            result["execution_time"] = f"{execution_time} 秒"

        return result
    return wrapper


router = APIRouter()

FP_PARAMS = 1710413848097


class douyin_base():
    def __init__(self, cookies: dict, headers: dict, base_url: str = "https://www.douyin.com"):
        self.cookies = cookies
        self.headers = headers
        self.baseurl = base_url
        self.data = {}
        self.UIFID = self.cookies.get('UIFID', '')
        self.verfyfp = verfyfp.VerifyFp.get_verify_fp(FP_PARAMS)
        self.headers['uifid'] = self.UIFID
        self.webid = webid.WebId.get_web_id(self.headers['user-agent'])
        self.msToken = self.cookies.get('msToken', '')
        # print(self.msToken)

    def get(self, url, params: dict):
        self.params = params
        self.data = {}
        self.url = url
        self.a_bogus()
        target_url = f"{self.baseurl}{self.url}?{self.query_string}&a_bogus={self.ab}"
        response = requests.get(
            target_url,
            headers=self.headers,
            cookies=self.cookies,
        )

        print(response.text)
        # input('debug')
        return response.json()

    def video_detail(self,  video_id: int):

        url = "/aweme/v1/web/aweme/detail/"
        if video_id is None:
            raise Exception(f"{video_id}不是有效的视频")
        # x = len(type)

        params = {
            'device_platform': 'webapp',
            'aid': '6383',
            'channel': 'channel_pc_web',
            'aweme_id': str(video_id),
            'request_source': '600',
            'origin_type': 'video_page',
            'update_version_code': '170400',
            'pc_client_type': '1',
            'pc_libra_divert': 'Mac',
            'support_h265': '1',
            'support_dash': '1',
            'cpu_core_num': '10',
            'version_code': '190500',
            'version_name': '19.5.0',
            'cookie_enabled': 'true',
            'screen_width': '1920',
            'screen_height': '1080',
            'browser_language': 'zh-CN',
            'browser_platform': 'MacIntel',
            'browser_name': 'Chrome',
            'browser_version': '143.0.0.0',
            'browser_online': 'true',
            'engine_name': 'Blink',
            'engine_version': '143.0.0.0',
            'os_name': 'Mac OS',
            'os_version': '10.15.7',
            'device_memory': '8',
            'platform': 'PC',
            'downlink': '10',
            'effective_type': '4g',
            'round_trip_time': '50',
        }

        params['webid'] = self.webid
        params['fp'] = self.verfyfp
        params['uifid'] = self.UIFID
        params['verifyFp'] = self.verfyfp
        params['msToken'] = self.msToken
        response = self.get(url, params)

        # print(response)
        # save_json(response)
        if response == None:
            raise Exception("获取失败")
        logger.success(f'aweme_detail请求成功')
        return response

    def url2id(self, url: str):
        if url is None:
            return 0
        # print(url, type(url))
        if "v.douyin.com" in url:
            response = requests.head(
                url, headers=self.headers, allow_redirects=True)
            real_url = response.url
        elif 'www.douyin.com/video' in url:
            real_url = url
        else:
            return 0

        def extract_douyin_id(url: str):
            # 正则表达式解释：
            # video/  -> 匹配固定字符
            # (\d+)   -> 匹配并捕获连续的数字（即 ID 部分）
            pattern = r"video/(\d+)"

            match = re.search(pattern, url)
            if match:
                return match.group(1)
            return 0
        return extract_douyin_id(real_url)
        # print(real_url)
        # pass

    def video_item_Trans(self, video_item: dict, raw_item: dict):
        aweme_detail = video_item.get('aweme_detail', {})
        title = aweme_detail.get('item_title', '未匹配到')
        nickname = aweme_detail.get('author').get('nickname', '未匹配到')
        sec_uid = aweme_detail.get('author').get('sec_uid', '未匹配到')
        short_id = aweme_detail.get('author').get('short_id', '未匹配到')  # 抖音号
        signature = aweme_detail.get('author').get('signature', '未匹配到')
        uid = aweme_detail.get('author').get('uid', '未匹配到')  # uid
        unique_id = aweme_detail.get('author').get('unique_id', '未匹配到')
        author_user_id = aweme_detail.get('author_user_id')  # uid
        caption = aweme_detail.get('caption')
        desc = aweme_detail.get('desc')
        duration = aweme_detail.get('duration')
        preview_title = aweme_detail.get('preview_title')
        create_time = aweme_detail.get('create_time')

        # pass
        # print(extra_json)
        # save_json(extra_json, '泡泡椰yeah的作品extra_json.json')
        # save_json(video_item, '泡泡椰yeah的作品.json')
        raw_item.update({
            '视频标题': title,
            '达人昵称': nickname,
            '抖音号': short_id,
            '达人签名': signature,
            '达人UID': uid,
            '视频时长': f'{round(duration/1000, 2)}s',
            '视频标题(话题)': preview_title,
            '上传时间': int(create_time)*1000

        }
        )
        try:
            extra = aweme_detail.get('anchor_info').get('extra')
            extra_json = json.loads(extra)
            product_id = extra_json[0].get('product_id')
            product_title = extra_json[0].get('title')
            product_short_title = extra_json[0].get('elastic_title')
            raw_item.update({
                '商品ID': product_id,
                '商品标题': product_title,
                '挂车商品标题': product_short_title
            })
        except Exception as e:
            raw_item.update({
                # '商品ID': ,
                '商品标题': '达人未挂车',
                '挂车商品标题': '达人未挂车',
            })
            logger.info('达人未挂车')
        # print(raw_item)
        return raw_item

    def url_item_trans(self, url: str):
        # ulr转换为完整信息

        code = self.url2id(url)
        video_item = self.video_detail(int(code))
        video_dict = {
            '视频链接': url,
            '视频ID': code
        }
        video_dict = self.video_item_Trans(
            video_item=video_item, raw_item=video_dict)
        # print(video_dict)
        return video_dict
        pass

    def post(self, url, params: dict, data: dict):
        self.params = params
        self.data = data
        self.url = url
        self.a_bogus()
        target_url = f"{self.baseurl}{self.url}?{self.query_string}&a_bogus={self.ab}"
        response = requests.post(
            target_url,
            headers=self.headers,
            cookies=self.cookies,
            data=self.json_data_str
        )
        # print(self.json_data_str, self.query_string)
        return response.json()

    def a_bogus(self):

        # Serialize obj to a JSON formatted str
        self.json_data_str = json.dumps(self.data, separators=(',', ':'))
        self.query_string = urlencode(self.params)
        with open('shortab_1.19.js', encoding='utf8') as f:
            js_code = f.read()

        # 传入标准的 query_string 和紧凑的 json_body_str
        ab = execjs.compile(js_code).call(
            'generate_a_bogus',
            self.query_string,
            # self.json_data_str,
            self.headers['user-agent']
        )
        self.ab = ab
        return ab

# # 假设这在你的类方法中

#     def a_bogus(self):
#         # 1. 准备数据
#         self.json_data_str = json.dumps(self.data, separators=(',', ':'))
#         self.query_string = urlencode(self.params)

#         # 2. 读取 JS 代码
#         with open('shortab_1.19.js', encoding='utf8') as f:
#             js_code = f.read()

#         # 3. 使用 QuickJS 执行
#         # 创建上下文对象

#         ctx = quickjs.Context()
#         ctx.eval(
#             "var console = { log: function() {}, warn: function() {}, error: function() {} };")
#         # 在上下文中执行 JS 源码，使函数定义生效
#         ctx.eval(js_code)

#         # 4. 调用 JS 函数
#         # 注意：quickjs 的调用方式是 ctx.get("函数名")(参数1, 参数2...)
#         ab = ctx.get('generate_a_bogus')(
#             self.query_string,
#             # self.json_data_str,  # 如果 JS 里需要这个参数请取消注释
#             self.headers['user-agent']
#         )
#         self.ab = ab
#         return ab


headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,und;q=0.8,en;q=0.7',
    'priority': 'u=1, i',
    'referer': 'https://www.douyin.com/video/7597031033657117958',
    'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'uifid': 'b7ffea4ffb7fd578f49f51586a953ac3b119cdf53ef4e59d8d754c665e3673929d6086833a7e6bb129d5ed592c8b9fd4d85d5c8d7d600c88125703963ba0a3ec4ed369e389d6d753bfa2f9ca16cf1fd1eb07eef9a777eddc01dc221a18c75263aff717d8397d3b8360a895c6b067b737b4e36d4c47bebb622cd42c72235c477a0f649e43f4d0288890694a4d8c6ff6172be3cb0a1dff06ab2eca79761432b8d7',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    'cookie': 'enter_pc_once=1; UIFID_TEMP=b7ffea4ffb7fd578f49f51586a953ac3b119cdf53ef4e59d8d754c665e367392287e2e36623f2a0545be3dc06849ae29ba91fbf073c47cd4c441fe0ab46bc5f3350bcfb86571c1aaf83574c763d755f3; x-web-secsdk-uid=418ddc9c-5066-453e-b361-3c1b100122ad; douyin.com; device_web_cpu_core=10; device_web_memory_size=8; hevc_supported=true; fpk1=U2FsdGVkX19fchvjPJsbDlO4Q7fgcYWljnvZmgVj6Rc4kSbp36oQYKD68RK2476DPB9ICyELySrtHPT6fgoExg==; fpk2=f18b5213b6de2490ec9be218b0f025b0; bd_ticket_guard_client_web_domain=2; d_ticket=7baf3ec298d474f9a8b4cb466713be582f29b; n_mh=0R4r3pHVGJYkb0PGiF6kx2kQUGZPrlrZvuhxDLE1ly8; is_staff_user=false; UIFID=b7ffea4ffb7fd578f49f51586a953ac3b119cdf53ef4e59d8d754c665e3673929d6086833a7e6bb129d5ed592c8b9fd4d85d5c8d7d600c88125703963ba0a3ec4ed369e389d6d753bfa2f9ca16cf1fd1eb07eef9a777eddc01dc221a18c75263aff717d8397d3b8360a895c6b067b737b4e36d4c47bebb622cd42c72235c477a0f649e43f4d0288890694a4d8c6ff6172be3cb0a1dff06ab2eca79761432b8d7; is_dash_user=1; my_rd=2; xgplayer_device_id=15018185140; xgplayer_user_id=269812926369; webcast_local_quality=null; live_use_vvc=%22false%22; SelfTabRedDotControl=%5B%7B%22id%22%3A%227174725284866820128%22%2C%22u%22%3A38%2C%22c%22%3A0%7D%5D; SEARCH_RESULT_LIST_TYPE=%22single%22; csrf_session_id=981e4681a1033541d44c24a1f1af40d5; __druidClientInfo=JTdCJTIyY2xpZW50V2lkdGglMjIlM0E1NDglMkMlMjJjbGllbnRIZWlnaHQlMjIlM0E4MTMlMkMlMjJ3aWR0aCUyMiUzQTU0OCUyQyUyMmhlaWdodCUyMiUzQTgxMyUyQyUyMmRldmljZVBpeGVsUmF0aW8lMjIlM0EyJTJDJTIydXNlckFnZW50JTIyJTNBJTIyTW96aWxsYSUyRjUuMCUyMChNYWNpbnRvc2glM0IlMjBJbnRlbCUyME1hYyUyME9TJTIwWCUyMDEwXzE1XzcpJTIwQXBwbGVXZWJLaXQlMkY1MzcuMzYlMjAoS0hUTUwlMkMlMjBsaWtlJTIwR2Vja28pJTIwQ2hyb21lJTJGMTQzLjAuMC4wJTIwU2FmYXJpJTJGNTM3LjM2JTIyJTdE; __security_mc_1_s_sdk_crypt_sdk=6e8db88f-48bc-aeb2; __security_mc_1_s_sdk_cert_key=d8381cb9-4aa3-a2f1; xg_device_score=7.956601717009935; s_v_web_id=verify_mkj3uj15_jeBnZPm3_RSQ4_43QA_BaEj_N9YV1v7mCWNo; passport_csrf_token=4473fe65587bf00bb6628252c50474eb; passport_csrf_token_default=4473fe65587bf00bb6628252c50474eb; publish_badge_show_info=%220%2C0%2C0%2C1769478737635%22; download_guide=%223%2F20260121%2F1%22; playRecommendGuideTagCount=2; totalRecommendGuideTagCount=2; SEARCH_UN_LOGIN_PV_CURR_DAY=%7B%22date%22%3A1769589897437%2C%22count%22%3A2%7D; record_force_login=%7B%22timestamp%22%3A1769589456995%2C%22force_login_video%22%3A9%2C%22force_login_live%22%3A0%2C%22force_login_direct_video%22%3A0%7D; passport_assist_user=CjwmmJ_CA4rS_XT-8GdcS_RrVDNJVmeCp-g_tha6a3BUMSFTgI6Lbz1nBOVKn8MI0miy3uoxD7H2dIFHLx8aSgo8AAAAAAAAAAAAAFABOM9HsLS0VbjDZvxhuRZUd5fwbtw4n-0sMEHuQEvAl5ySvcqvVOy5I8igbeFCpJWXEK2PiA4Yia_WVCABIgED0Mi-RA%3D%3D; sid_guard=c789ff8474ab48998d70e76e3c23051a%7C1769603260%7C5184000%7CSun%2C+29-Mar-2026+12%3A27%3A40+GMT; uid_tt=71fcc4f6c016840ec1d81f52016f949a; uid_tt_ss=71fcc4f6c016840ec1d81f52016f949a; sid_tt=c789ff8474ab48998d70e76e3c23051a; sessionid=c789ff8474ab48998d70e76e3c23051a; sessionid_ss=c789ff8474ab48998d70e76e3c23051a; session_tlb_tag=sttt%7C15%7Cx4n_hHSrSJmNcOduPCMFGv_________BMnNjDskvw1oE1x5DSyykRv6kzUZh6cB5wDX9pAGHiPk%3D; sid_ucp_v1=1.0.0-KDNiM2RmYTVjYzlmYzViYzM3OWNkMTA2NzQ2OWI0OTZiZDQwZGQxMGUKHwiV3P34vgIQvIHoywYY7zEgDDD7j-HSBTgFQPsHSAQaAmhsIiBjNzg5ZmY4NDc0YWI0ODk5OGQ3MGU3NmUzYzIzMDUxYQ; ssid_ucp_v1=1.0.0-KDNiM2RmYTVjYzlmYzViYzM3OWNkMTA2NzQ2OWI0OTZiZDQwZGQxMGUKHwiV3P34vgIQvIHoywYY7zEgDDD7j-HSBTgFQPsHSAQaAmhsIiBjNzg5ZmY4NDc0YWI0ODk5OGQ3MGU3NmUzYzIzMDUxYQ; __security_mc_1_s_sdk_sign_data_key_web_protect=95891595-4133-a29d; login_time=1769603260267; _bd_ticket_crypt_cookie=197f1b1c9d4fdf285b9b2f8985422419; DiscoverFeedExposedAd=%7B%7D; dy_swidth=1920; dy_sheight=1080; volume_info=%7B%22isMute%22%3Atrue%2C%22isUserMute%22%3Afalse%2C%22volume%22%3A0.449%7D; strategyABtestKey=%221769836846.084%22; ttwid=1%7CG1v7T4ne9nsMN_wxTfrD6zYsrjjPFbANGLDjikI6KwM%7C1769836846%7Cd0ab409678231ac1c31b8a26cec106b0494ac1a6b8402700466731784f92a656; __live_version__=%221.1.4.7838%22; live_can_add_dy_2_desktop=%221%22; PhoneResumeUidCacheV1=%7B%2285616193045%22%3A%7B%22time%22%3A1769838260278%2C%22noClick%22%3A2%7D%7D; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A1%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A1%7D%22; FOLLOW_NUMBER_YELLOW_POINT_INFO=%22MS4wLjABAAAARAyss84G_nzNXcH2-7XCjmFIyg5xGNyMDUNPAVlZCzc%2F1769875200000%2F0%2F0%2F1769843426442%22; biz_trace_id=244da690; FRIEND_NUMBER_RED_POINT_INFO=%22MS4wLjABAAAARAyss84G_nzNXcH2-7XCjmFIyg5xGNyMDUNPAVlZCzc%2F1769875200000%2F1769842241277%2F0%2F0%22; __ac_nonce=0697db22b0056a9916253; __ac_signature=_02B4Z6wo00f01v3XG7gAAIDAzkLt-Wb-far99x8AANYVcc; FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAARAyss84G_nzNXcH2-7XCjmFIyg5xGNyMDUNPAVlZCzc%2F1769875200000%2F0%2F1769845293246%2F0%22; odin_tt=6b41c1097d6c3dbcb38ddca1993797c00b7abb88197a044b638afff923d7cfc55f9a40046ed5b08ab0cdd9612dde6db60add385c5611fea73c0e658a90bb126f; IsDouyinActive=true; home_can_add_dy_2_desktop=%220%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1920%2C%5C%22screen_height%5C%22%3A1080%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A10%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A100%7D%22; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQ095SXlpNk8rcXFGbTljNHU4c3NCWERLSFRWR3IxdldrS0d0V0p4dzZadVd5eXZjN3VxR1hJdlZDV2d1M2syR3hoeWg3K1dRY1FoTnp2dEJyZTZPTkE9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; bd_ticket_guard_client_data_v2=eyJyZWVfcHVibGljX2tleSI6IkJDT3lJeWk2TytxcUZtOWM0dThzc0JYREtIVFZHcjF2V2tLR3RXSnh3Nlp1V3l5dmM3dXFHWEl2VkNXZ3UzazJHeGh5aDcrV1FjUWhOenZ0QnJlNk9OQT0iLCJ0c19zaWduIjoidHMuMi4xOWIwYTY2OTU1MGJlMWEwNTZhNjM4NmU2OTllZDkxYjQ5MDNmOGEwYmViNjU4YjhiNTM0NGFjYjIzN2M2MTJkYzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJBRFlqcHVzUTJJNEg4NTNxczZmNTZvYWJCV3Y5b3N1K1VRMWNEUlUxOGJNPSIsInNlY190cyI6IiNKUHlKSVVHdm9mUmtubzY5QXZiUW1HUG5BdDJVdkFpQjZpSzVMc1FQZzZYcUxqaFQyQ1dkYzZYalhhaHAifQ%3D%3D',
}
douyin_cookies = {}
douyin = douyin_base(cookies=douyin_cookies, headers=headers)
jxlm = jxlm.jinritemai_base(cookies=douyin_cookies, headers=headers)


@router.get('/video', summary='单个视频解析')
async def video_detail(video_id: int):

    # return douyin.video_detail(video_id)
    # pass
    response = douyin.video_detail(video_id)
    if response:
        return reposen_model.BaseResponse(
            code=0,
            data=response,
            message="请求成功"
        )
    else:
        raise HTTPException(
            status_code=200, detail="获取失败"
        )


@router.post('/abogus/20', summary="abogus_20签名")
async def abogus_20():
    pass
