import json
import execjs
from urllib.parse import urlencode
import requests
from loguru import logger
from src.encrypt import verfyfp
import pandas as pd
import time
import os
from dotenv import load_dotenv
import datetime
FP_PARAMS = 1710413848097
EWID = '02200744efdbbaf11f6edcbe9df14f01'
APP_ID = 1128
load_dotenv('.env', override=False)


class jinritemai_base():
    def __init__(self, cookies: dict, headers: dict, base_url: str = "https://buyin.jinritemai.com"):
        self.cookies = cookies
        self.headers = headers
        self.baseurl = base_url
        self.data = {}
        self.mstoken = self.cookies.get('msToken', '')
        self.verfyfp = verfyfp.VerifyFp.get_verify_fp(FP_PARAMS)
        self.ewid = EWID
        self.app_id = str(APP_ID)
        with open('longab_1.20.js', encoding='utf8') as f:
            js_code = f.read()
        self.js_context = execjs.compile(js_code)  # 预热 JS 环境
        logger.info("JS 逆向环境初始化成功")

    def __str__(self):
        return f"这是一个精选联盟程序，当前环境：{self.baseurl}，当前用户：{self.cookies.get('ttwid', '')}"

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
        return response.json()

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
        # print(target_url, self.json_data_str, self.query_string, response.text)
        return response.json()

    def a_bogus(self):

        # Serialize obj to a JSON formatted str
        self.json_data_str = json.dumps(self.data, separators=(',', ':'))
        self.query_string = urlencode(self.params)

        # 传入标准的 query_string 和紧凑的 json_body_str
        ab = self.js_context.call(
            'getABogus',
            self.query_string,
            self.json_data_str,
            self.headers['user-agent']
        )

        self.ab = ab

    def a_bogus_20_standard(self, data, params, headers):
        """标准版 无需借助其他信息去生成20版bogus"""
        # Serialize obj to a JSON formatted str
        json_data_str = json.dumps(data, separators=(',', ':'))
        query_string = urlencode(params)

        # 传入标准的 query_string 和紧凑的 json_body_str
        ab = self.js_context.call(
            'getABogus',
            query_string,
            json_data_str,
            headers['user-agent']
        )

        # self.ab = ab
        return ab

    def search(self, data=None):  # 找达人

        url = "/square_pc_api/square/search_feed_author"
        params = {}
        params['ewid'] = self.ewid
        params['msToken'] = self.mstoken
        mock_data = {
            "page": 1,
            "refresh": True,
            "type": 1,  # 1-全部 3-视频达人 2-直播达人 4-图文达人 5-橱窗达人
            "query": "好妹妹好物",
            "search_id": "",
            "filters": {
                "main_cate_new": [],
                "content_type": [],
                "total_sales": [],
                "live_total_sales": [],
                "video_total_sales": [],
                "image_text_total_sales": [],
                "windows_total_sales": [],
                "live_sale_avg": [],
                "live_watching_times": [],
                "video_sale_single": [],
                "video_play_time": [],
                "common_range_selection_video_nature_rate": [],
                "image_text_sale_single": [],
                "image_text_play_time": [],
                "window_order_cnt": [],
                "window_product_cnt": [],
                "author_level_new": [
                    "3",
                    "4",
                    "5",
                    "6"
                ],
                "fans_num": [],
                "author_portrait": [],
                "fan_portrait": [],
                "fans_profile": [],
                "high_response_rate_im": [],
                "has_contact": [],
                "common_selection_no_view_contact_60d": [],
                "can_connect": [],
                "common_selection_no_send_im_message_60d": [],
                "common_selection_author_account_type": [],
                "common_selection_hide_news_account": []
            }
        }
        if not data:
            data = mock_data
        try:
            response = self.post(url, params, data)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            logger.success(f'code:{response.get('code')} 获取成功')

            return response.get('data', {'list': []})
        except Exception as e:
            logger.info(str(e))
            return {'list': []}

    def msg_send(self, data=None):  # 批量建联
        """
        msg_send 的 Docstring
        这是批量批量建联工具
        :param data: 说明
        """
        url = "/connection/pc/im/shangda/msgs/send"
        params = {}
        params['ewid'] = self.ewid
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        mock_data = {
            'receiver_messages': [
                {
                    'receiver': {
                        'account_id': 'v2_0a271a6afce04c4d1a8855ddc45e2efd56d15ab08e6802e9600897749316dc009656c8614e346bebb71a4b0a3c00000000000000000000500e3b8e07cc3fd820a038589b33c54f3171c092433ceabfda6ee1cbd693f45b31efb0e445fccb3bd234cbeb862e78c334aa10b2a1890e18e5ade4c9012001220103985f040d',
                        'account_type': 24,
                    },
                },
                {
                    'receiver': {
                        'account_id': 'v2_0a2c25238d2b37b73f233418270813e880f458e00191d348c004aea7eb17674946c8a8d72861c37201a5238ca4c41a4b0a3c00000000000000000000500e3b8e07cc3fd820a038589b33c54f3171c092433ceabfda6ee1cbd693f45b31efb0e445fccb3bd234cbeb862e78c334aa10b2a1890e18e5ade4c90120012201031bd8c92c',
                        'account_type': 24,
                    },
                }
            ],
            'message_content': {
                'invite_card': {
                    'content': '哈喽呀，我们是真不二品牌方，致力于打造轻便简单懒人式养生理念给大家。目前已经做到抖音、天猫平台的TOP1啦 ~ 诚邀合作，最近这些产品在年货节热度都非常高，感兴趣的话留一下联系方式哦',
                    'rights': [],
                    'product_ids': [
                        '3586239767043541570',  # 热敷靴
                        '3670236344942199236',  # 艾灸棒套盒
                        '3576957230110651749',  # 玫瑰灸贴
                        '3635199643333309578',  # 湿汗通贴
                        '3570483977649299435',  # 茶香枕
                    ],
                    'product_setting': [
                        {
                            'product_id': '3570483977649299435',
                            'author_sample_status': 1,
                        },
                        {
                            'product_id': '3586239767043541570',
                            'author_sample_status': 0,
                        },
                        {
                            'product_id': '3670236344942199236',
                            'author_sample_status': 1,
                        },
                        {
                            'product_id': '3635199643333309578',
                            'author_sample_status': 0,
                        }, {
                            'product_id': '3576957230110651749',
                            'author_sample_status': 0,
                        },
                    ],
                    'is_open_feed': True,
                },
                'contact_info': {
                    'phone': '',
                    'wechat': 'Songmi-Young',
                },
            },
            'event_param': {
                'client_form': 'pc',
                'web_did': '02200744efdbbaf11f6edcbe9df14f01',
                'seraph_did': '',
                'x_pigeon_did': '',
            },
            'source': 5,
        }
        if not data:
            data = mock_data
        try:
            response = self.post(url, params, data)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def author_profile(self, uid=None):  # 达人信息概览

        url = "/square_pc_api/homePage/author/profile"
        params: dict[str, str] = {
            # 'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'uid': 'v2_0a2cbaeb6a8379a38cb42c3e88b4f10b07162bd43586a841cf32b15a7b5c3c463a7846e9d1aa2ab45c431765f2361a4b0a3c000000000000000000005001d529225fd8162c9cfed6c3ae6f6ef75af8340b95ba74beb75b6cc26868041ea361e5c1d01551d8ee93a41bd76081cc9a10f08f880e18e5ade4c9012001220103de323cde',
            'works_type': '1',
        }
        params['ewid'] = self.ewid
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        if uid:
            params['uid'] = uid
        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(f'text:{response} 获取成功')
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def get_contact(self,  origin_uid: str, type=['wechat'],):  # 获取联系方式

        url = "/api/contact/contact_info"
        contact = {
            'times_left': 0,
            'phone': 0,
            'wechat': ''

        }
        # x = len(type)
        for i in type:
            params = {
                # 'ewid': '02200744efdbbaf11f6edcbe9df14f01',
                'origin_uid': origin_uid,
                # 'app_id': '1128',
                'contact_mode': '2',
                'check_mode': '2',
                'scene': '1',
            }
            params['app_id'] = self.app_id
            params['ewid'] = self.ewid
            params['msToken'] = self.mstoken
            params['fp'] = self.verfyfp
            params['verifyFp'] = self.verfyfp
            if i == 'wechat':
                params['contact_mode'] = '2'
            else:
                params['contact_mode'] = '1'
            try:
                response = self.get(url, params)
                code = response.get('code')
                if code != 0:
                    raise Exception("获取失败")
                logger.success(f'code:{response.get('code')} 获取成功')

                contact['times_left'] = response.get('data', {}).get(
                    'contact_info').get('times_left')

                if i == 'wechat':
                    contact['wechat'] = response.get('data', {}).get(
                        'contact_info').get('contact_value')
                else:
                    contact['phone'] = response.get('data', {}).get(
                        'contact_info').get('contact_value')
                    # return response.get('data', {})
            except Exception as e:
                logger.info(str(e))
                times_left = contact.get('times_left', 0)
                if times_left <= 5:
                    logger.info(f'times_left::{times_left} 请注意')
                return contact

    def get_conversations(self, data=None):  # 获取对话列表
        url = "/connection/pc/im/conversations"
        params = {'PIGEON_BIZ_TYPE': '5', }
        mock_data = {
            "filters": [
                {
                    "key": "conversation_status",
                    "values": [
                        "1", "2"  # 1可沟通 2 待回复 3已拒绝
                    ]
                },
                {
                    "key": "role",
                    "values": [
                        "daren"  # captain：团长  mcn：机构 如果不是daren 其他选项都没有了
                    ]
                },
                # {
                #     "key": "fans",
                #     "values": [
                #         "1k-1w"
                #     ]
                # },
                # {
                #     "key": "category",
                #     "values": [
                #         "智能家居"
                #     ]
                # },
                {
                    "key": "level",  # 达人带货等级
                    "values": [
                        "3",
                        "4",
                        "5",
                        "6"
                    ]
                }
            ],
            "page": 1,
            "page_size": 200,
            "tab_ids": [2],  # 1 未读 2 我发起的 3 我接收的
            "sort_conditions": [
                {
                    "sort_field": "default",
                    "is_asc": False
                }
            ],
            "time_mode": 1  # 重要参数

        }
        if not data:
            data = mock_data
        # params['ewid'] = self.ewid
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        try:
            response = self.post(url, params, data)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def get_conversations_datail(self, data=None):  # 获取对话列表需要pigeon_id
        raw_baseurl = self.baseurl
        self.baseurl = 'https://darenim.jinritemai.com'
        url = "/chat/api/backstage/getUserInfo"
        params = {
            'PIGEON_BIZ_TYPE': '5',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'msToken': '6qcJWDYAlkVhj9PoRUKVVDFxh3JAlT2JwzeM1uTJUtPWWsumrhnGEpZJqjBOx3vBVNwkOsZYSA7xzXhLOgqgBNrsjFwXGAmzyV-6Jlha5HeYLlieGc0WsX8ZvEPJEMrua-NCZuehzQ0KUcyLeKQ9F36uJGEZUyhyFNS-cdwtYpjrqg==',
            # 'a_bogus': 'YvsnD7SyDdWnK3lG8OkxCllUO6VlNTuynFTKWuNTtoY9aqFbfnpqOHMDnFOX5QRAWYMlw1l7SVbgYVEYmIQA8HqpFmpfui0R5tAVIh8L8qqfYFiMDHSLewhFKwMxURsql5nAE1kRls0e2DQWVHAdlQ/a95FP5YYDSNFjdZ8cb9AbfS6P8prSOZLAOfqPmQoRMD==',
        }
        data = {
            'pigeonUidList': ["7036865808173236511"]
        }
        # if True:
        #     data = mock_data
        # params['ewid'] = self.ewid
        # params['msToken'] = self.mstoken
        # params['fp'] = self.verfyfp
        # params['verifyFp'] = self.verfyfp
        try:
            response = self.post(url, params, data)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))
        finally:
            self.baseurl = raw_baseurl
            # {'check_spam_resp': {'decision': 'PASS', 'verify_type': '', 'check_spam_detail': {}, 'spam_scene': ''}, 'code': 0, 'data': [{'pigeonUid': '7036865808173236511', 'screenName': '邦邦的', 'avatarUrl': 'https://p3.douyinpic.com/aweme/100x100/aweme-avatar/tos-cn-avt-0015_eee5ef3619350aa2c6e9dd85cb6a8483.jpeg?from=3782654143', 'outerId': '6978801421463388430', 'uniqueId': '77213983895', 'account_type': 0, 'profile_url': 'https://buyin.jinritemai.com/dashboard/servicehall/daren-profile?uid=01d7763e679db5479ead2240a9236c21', 'enUniqueId': '01d7763e679db5479ead2240a9236c21'}], 'msg': '', 'request_arrived_time': 1769671924677, 'server_execution_end_time': 1769671924728, 'st': 0}
            # 网址和其他不同，uniqueId =uid  enUniqueId =uid 默认是长的，也可以是origin_uid（短的）

    def author_fans(self, uid=None):  # 达人粉丝信息
        url = "/api/authorStatData/authorFansV2"
        params = {
            # 'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'uid': 'v2_0a2cbaeb6a8379a38cb42c3e88b4f10b07162bd43586a841cf32b15a7b5c3c463a7846e9d1aa2ab45c431765f2361a4b0a3c000000000000000000005001d529225fd8162c9cfed6c3ae6f6ef75af8340b95ba74beb75b6cc26868041ea361e5c1d01551d8ee93a41bd76081cc9a10f08f880e18e5ade4c9012001220103de323cde',
            'fans_club': '0',
            'works_type': '1', }
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid
        if uid:
            params['uid'] = uid
        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def video_shop_data(self, uid=None):  # 达人视频带货数据
        url = "/square_pc_api/homePage/scene_analysis/overview"
        params = {
            'uid': 'v2_0a2cbaeb6a8379a38cb42c3e88b4f10b07162bd43586a841cf32b15a7b5c3c463a7846e9d1aa2ab45c431765f2361a4b0a3c000000000000000000005001d529225fd8162c9cfed6c3ae6f6ef75af8340b95ba74beb75b6cc26868041ea361e5c1d01551d8ee93a41bd76081cc9a10f08f880e18e5ade4c9012001220103de323cde',
            'content_type': '3',
            'is_only_ecom': 'true',
            'date_type': '30d',
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'msToken': 'jlo8jkYbAiFhrxeR78NljHB3_6faRBRwnApMrjJMfWF9YNSmJNNOHBCyxCFLz_1Ylpi-zRjN9fXyW-Nj2xUngypd4yX6c-T8KQOZbJIG-oO8b8zXMKtMzB9pzhBrjbI02LHwMv7XwPeUUKF0qbyR8_XoJPbPUjARQph4UliRQE-ooiHyamvNE4Y=',
            # 'a_bogus': 'dy4fk7XjmpQ5KpAtmck2CVOlCHyANsuyyeiobFlT7KTAahMTpopqKNbdcoo6VxvA-up-wHA7SVeMYxVb8VssZCrpqmhfuqXSUGIAI06o/qNpblU0DqSuewDzqw0NUbTql5cVEADRWsMCId5WVrAKlpMGH5FP5YRDbrFfd20cj9AYDCgPm1a6OZwWEfqN0W5U',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
        }
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid
        if uid:
            params['uid'] = uid
        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def video_hd_data(self, uid=None):  # 达人视频互动数据
        url = "/square_pc_api/homePage/scene_analysis/video_list"
        params = {
            'uid': 'v2_0a2cbaeb6a8379a38cb42c3e88b4f10b07162bd43586a841cf32b15a7b5c3c463a7846e9d1aa2ab45c431765f2361a4b0a3c000000000000000000005001d529225fd8162c9cfed6c3ae6f6ef75af8340b95ba74beb75b6cc26868041ea361e5c1d01551d8ee93a41bd76081cc9a10f08f880e18e5ade4c9012001220103de323cde',
            'page': '1',
            'is_only_ecom': 'true',
            'with_product': 'true',
            'date_type': '30d',
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'msToken': 's8v4H4nSIV34cnDwX9ZkUicRuYaVN08hy7wa1FZMxu4ku7Qc6DVFIjgxjXxz6nFSeCOumm8ZthXrGnLGi4DgMsrpA5OiZHWL-3xzPJqL9ZSCJyEq2U3kiep8-Q2XF_K85G_8P3x0S_6zy3vC5FHOpkZ8gBk_9s29SxtYDqBT_qrVpw==',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
        }
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid
        if uid:
            params['uid'] = uid
        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def video_player(self, uid=None):  # 短视频观众数据
        url = "/api/authorStatData/playerAnalyzeV2"
        params = {
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'uid': 'v2_0a2cbaeb6a8379a38cb42c3e88b4f10b07162bd43586a841cf32b15a7b5c3c463a7846e9d1aa2ab45c431765f2361a4b0a3c000000000000000000005001d529225fd8162c9cfed6c3ae6f6ef75af8340b95ba74beb75b6cc26868041ea361e5c1d01551d8ee93a41bd76081cc9a10f08f880e18e5ade4c9012001220103de323cde',
            'msToken': 'jlo8jkYbAiFhrxeR78NljHB3_6faRBRwnApMrjJMfWF9YNSmJNNOHBCyxCFLz_1Ylpi-zRjN9fXyW-Nj2xUngypd4yX6c-T8KQOZbJIG-oO8b8zXMKtMzB9pzhBrjbI02LHwMv7XwPeUUKF0qbyR8_XoJPbPUjARQph4UliRQE-ooiHyamvNE4Y=',
            # 'a_bogus': 'mfURhFS7Qo/ccpltuckQCWalLUV/NsWyA-TKSbNTyFKZPZFTCopB/nt2aoLg/VJR-uB3wCB79VaAGndb8VkzZ9HkFmhvudzRUGA9Ih8o0qwkbltsLrSDeuhFKw0x05Tqe5nCEID5UsMCIEcWVNIdlpQat5FaQYYDSrqjdZmbJ9WTDC6Pu3aWO/EANfqY-moRjD==',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM', }
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid
        if uid:
            params['uid'] = uid
        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def sale_product_list(self, uid=None):  # 在售商品数据
        url = "/square_pc_api/homePage/sale_analysis/sale_product_list"
        params = {
            'uid': 'v2_0a2cbaeb6a8379a38cb42c3e88b4f10b07162bd43586a841cf32b15a7b5c3c463a7846e9d1aa2ab45c431765f2361a4b0a3c000000000000000000005001d529225fd8162c9cfed6c3ae6f6ef75af8340b95ba74beb75b6cc26868041ea361e5c1d01551d8ee93a41bd76081cc9a10f08f880e18e5ade4c9012001220103de323cde',
            'date_type': '30d',
            'room_id': '0',
            'indus_cat': '',
            'brand': '',
            'page': '1',
            'pageSize': '15',
            'match_type': '',
            'sort_type': '0',
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'msToken': 'Rgp7ZlZPgigzJFEzA0O7r-wZzo5HrbMMWt--IBwK0DnOq85vqikpKyBQ-WViZNVfAYsueadq82vy4Ar45n-xCayBqOUo2wT_Ixo-vzxfo9_1iIs_cS1M7Sdnu3yUyAfA1Io-V_ThjHNhwuMiN-7dA0j4maxNrcZL0b5lmdBpsg5h-6C1qQvesn0=',
            # 'a_bogus': 'DX0fDHUymqmjc3AtYOsOCU1UEtEANs8yBPTKbExTtKzpPZtbbIpZ/rSqrxu6f9tclYBrwHq7CVG/PVncuIsTZCrkomZvuNhfGtAnI08L0qwDbt0sDqyEeLDFKwMr0csq-/c5ElhR1s0C2DQWINAxlQMGH5zaQQRDSrF6d2sbG9ATfC6PY3r6O2iWTfwaQY25Uj==',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
        }
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid
        if uid:
            params['uid'] = uid
        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def live_viewer(self, uid=None):  # 直播观众数据
        url = "/api/authorStatData/viewerAnalyzeV2"
        params = {
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'uid': 'v2_0a2cbaeb6a8379a38cb42c3e88b4f10b07162bd43586a841cf32b15a7b5c3c463a7846e9d1aa2ab45c431765f2361a4b0a3c000000000000000000005001d529225fd8162c9cfed6c3ae6f6ef75af8340b95ba74beb75b6cc26868041ea361e5c1d01551d8ee93a41bd76081cc9a10f08f880e18e5ade4c9012001220103de323cde',
            'fans_club': '2',
            'works_type': '1',
            'msToken': 'Rgp7ZlZPgigzJFEzA0O7r-wZzo5HrbMMWt--IBwK0DnOq85vqikpKyBQ-WViZNVfAYsueadq82vy4Ar45n-xCayBqOUo2wT_Ixo-vzxfo9_1iIs_cS1M7Sdnu3yUyAfA1Io-V_ThjHNhwuMiN-7dA0j4maxNrcZL0b5lmdBpsg5h-6C1qQvesn0=',
            # 'a_bogus': 'QfURhH6jmNAfPpCtuKk2Cf-lngfANTSyRFT2WiPPSoO7PhFTmxpNOctLGxoXO6jcluBewexH7Ve/aDnc8dkiZeHpLmhvSZvRUtI5IhXLgqNkYUzsDHy8ewhFuw0rUbsqa/cnE1DRUsMFIdcWVrIKlB/aS5FO5QmDRrFSdMmba9WbDALPmZajOMEATDHuU7Qy',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
        }
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid
        if uid:
            params['uid'] = uid
        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def Competitor_shop_koc(self, sec_shop_id=None):  # 同行达人
        url = "/square_pc_api/shop/shopProfileAuthorList"
        params = {
            'page_no': '1',
            'page_size': '20',
            'query': '',
            'log_id': '',
            'main_cate': '',
            'first_cate': '',
            'sort_field': 'sale',
            'sort_type': '1',
            'day': '30',
            'sec_shop_id': 'v2_0a2445f4dd6ec6f425e8ae3690a750d4d2ffb9837625cbf806b59833f14c6139a16c4bbbdd321a4b0a3c00000000000000000000500239c8815b842afc229615145942ddb82d775c09a3712180a1598567c22009755ce18deb803ad713226ac4a1efc0e80e2f109099880e18e5ade4c901200122010340b222e8',
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'msToken': 'J3i_dNbWcDJ-Ft-tQ8JA_BzAW85tU3Iu8tochda2P0wowOR5K34YuWd4YoOYSgWyrOSrWrzWVbKonpHI2mB3Q49hP0PiuaeDTkMqMvyicWX_IgJbT5pxrMmQA2mLJy4hyEtGsjvVKZljuha0OTvzltCuEhZE0nny6SmG6fd9CH3_aaM6CgZDn8Y=',
            # 'a_bogus': 'Dv4fgzXiDp/fKpCb8Cs/CW5UZ/jlNTuyvFTObKpTCKTpPwUTbnBMQnt4cxugMXWISuBHweI77VaAbfdcm2szZC9kumhvSYJjcGA5Ig8o2qqXb00MEryYeLhFLw0N0c4qa5nIE1gRUs0eIDQW9qAxlQMat5FP5QbDRNFydZmcc9WGfW6Pu3ajO2iAiEwa-5o40f==',
        }

        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid
        if sec_shop_id:
            params['sec_shop_id'] = sec_shop_id
        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def Competitor_shop_search(self, query=None):  # 同行搜索
        def generate_log_id():
            # 1. 获取当前时间，格式为 YYYYMMDDHHMMSS
            now = datetime.datetime.now()
            time_str = now.strftime("%Y%m%d%H%M%S")

            # 2. 生成后半部分的 16 位十六进制字符
            # 在实际逆向中，这部分可能关联设备ID，但在初步测试时，可以使用随机值
            random_part = os.urandom(10).hex().upper()[:16]

            # 3. 拼接（注意：你提供的样本是 30 位，14位时间 + 16位随机）
            log_id = f"{time_str}{random_part}"
            return log_id
        url = "/square_pc_api/peer/shopPeerList"
        params = {
            'page_no': '1',
            'page_size': '20',
            'query': '灸春堂',
            'log_id': '2026012815075949D865ED429A9AFC8024',
            'main_cate': '',
            'first_cate': '',
            'sort_field': 'sale',
            'sort_type': '1',
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'msToken': 'JKGYE7ric_US5YPky-newsE2N3XU9CZgmr2SowFJUdNvSyzYRxdhuryF3TFtNNFsAMxsuiVL-fkslJEvYLEPPVj-_Y-6OPyD5Y6rqh9wui1omyr7LI3uFTNDUP9PCSRg6kgNgCAE5ETRM7Jf_MnDJ9aiuHIZrzkUVCTbl8LTlyBECg==',
            # 'a_bogus': 'dvsfh76wDZmRK3eG8ckKCUnlmu6MNPWyzaiQRtcPtoTLPZ0YC2pqQxSdrxogE2vA5RpHwqF7SValPfxb8IksZ9epushfussRW0IVIU8L0qw3bMv/ENyYeLhzqw0x0bGqa5nVEIkR6sMKIEOWVqIxlBBGS5zP5YbDSrqyd/0br9WGfC6P81aSO2EAOEwYB59-ej==',
        }

        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid
        params['log_id'] = generate_log_id()
        if query:
            params['query'] = query
        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def similar_kol(self, uid=None):  # 相似达人
        url = "/square_pc_api/similar_kol/list"
        params = {
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'msToken': 'tKJX_vp5otNEBCiRJ4NAzLhE9Unn_t0yL9wuvx2lobo-OFVppxbfPm-JJ49qAgdzpiRn3PXghIfiZMJRvvUAlzbEHMJh4i2slt5p5ZXAXwgpf5QlmXx0ScV8LkNaZwWryOgMyK8EUoOzbSi2H8-cJucoXkGLnc3uO05m1rYceB_R1Q==',
            'a_bogus': 'Q70fhqSyDoAccpltYckKCfol1hLANsWybMTObEMPtKzGPqMbPIpqKw5pcOE6YWhWcRZlw8A7HVGcjndTYVmS879kumZfu/k6W0IcIW0LZqqvaeGsDqS8eukFuw0rUb4qe/n5EAD5IsMFIDOWVqI/ldMGy5zOQmmDWNq6d2mbj9WGDAyPm1aSO/wWPfqNBbo5df==',
        }
        data = {
            'page': 1,
            'refresh': True,
            'author_id': 'v2_0a2b2fbcbda9d4c65e5d0250ff59b5fd128d621e32fd66500c932a67810df6232b934f6824572dfcf0d3d0d6741a4b0a3c000000000000000000005001d529225fd8162c9cfed6c3ae6f6ef75af8340b95ba74beb75b6cc26868041ea361e5c1d01551d8ee93a41bd76081cc9a10d88e880e18e5ade4c901200122010311ebb7e5',
            'req_source': 1,
            'filters': {},
        }
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid
        if uid:
            params['author_id'] = uid
        try:
            response = self.post(url, params, data)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def dmp_search(self):  # dmp搜达人
        url = "/square_pc_api/recommend/crowd_pack_rec_author"
        params = {
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'msToken': 'pTKzR97rHP1-Iz_uQ2FuxVLo2GBPmFJFPcRprFm_IUAb7Jrm90nQCq8-jNK9_NNGJkPqa1Wovd3tDP1Ix2NyqoL5cxu-K8n4sbxdnwbM0nSt9zkrRXHU38PDowjdnQgj6YQBpabYTGbiGTHzEQfYACXJC7VbxJ5d9v9bzS9xMC90jg==',
            'a_bogus': 'OXURg77jD25japlG8KkdCAOUG8IlNsuyVPToRTQPeoFYPwUYHxppQo4OnoOhWVR9ebMaw6-H93CpLxxT8Vpm8yNkomZkuwiRGGI9I0vo2qNDG0JBgNymeuhFuwMn05GqaQnnElh5lsMFIDOW9HA2lQQae5zOQOYDSNq6d28cc9WbDAgP8pa6O/EAEDHzU4Ab',
        }

        data = {
            'page': 1,
            'filters': {
                'author_type': [
                    '2',  # type 2 直播达人 3 视频达人
                ],
                'target_crowd': [
                    '2',
                ],
                'matching_method': [
                    '1',
                ],
                'main_cate': [
                    '13',
                ],
            },
            'page_size': 20,
        }
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid

        try:
            response = self.post(url, params, data)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def similar_product(self):  # 相似达人
        url = "/square_pc_api/prd_2_kol/list"
        params = {
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'msToken': 'tKJX_vp5otNEBCiRJ4NAzLhE9Unn_t0yL9wuvx2lobo-OFVppxbfPm-JJ49qAgdzpiRn3PXghIfiZMJRvvUAlzbEHMJh4i2slt5p5ZXAXwgpf5QlmXx0ScV8LkNaZwWryOgMyK8EUoOzbSi2H8-cJucoXkGLnc3uO05m1rYceB_R1Q==',
            'a_bogus': 'Q70fhqSyDoAccpltYckKCfol1hLANsWybMTObEMPtKzGPqMbPIpqKw5pcOE6YWhWcRZlw8A7HVGcjndTYVmS879kumZfu/k6W0IcIW0LZqqvaeGsDqS8eukFuw0rUb4qe/n5EAD5IsMFIDOWVqI/ldMGy5zOQmmDWNq6d2mbj9WGDAyPm1aSO/wWPfqNBbo5df==',
        }
        data = {
            'page': 1,
            'pid': '3791984099120513255',
            'loadmore': False,
            'filters': {},
        }
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid

        try:
            response = self.post(url, params, data)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def weekly_rec_author(self):  # 相似达人
        url = "/square_pc_api/recommend/weekly_rec_author"
        params = {
            'loadmore': 'false',
            'req_id': '',
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'msToken': 'tV4VtaY9T3ndf7mfGpbhl_hL-qygQr48pWEA7O6gdHSKzIzqJjH41_asPugsyDzoLCtl7fjNSwBZI29qUA0IHzjChu3Qio-U0Cqk1_mq5AVBCB6n37_hoRz05lvDAofO3HqXTPTcaRZm1xKsJ8Vt_lwLF6vegnqFhJjkkAxlr6RwrA==',
            'a_bogus': 'DvUnDtyiYx8nK3eb8KkOCVAU88olrBuywBT/SooT9KTJPZ0bLxpFQPSKaoLgWVDjeYB1wH1H7VeMYDxcu2shZ9nkompDSQi6UzIAI00L/qqvTziBEHyYewgzowMxU54ql5c9ElhRIs0C2D5WVHIold/aS5FPQmbDSqFjdZmcn9ATfS6Pm1ajO2LWPEqKQco4VE==',
        }

        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid

        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def history_content(self, uid=None):  # 获取历史带货视频
        url = "/square_pc_api/homePage/overview/history_content"
        params = {
            'content_type': '3',  # 2-直播 3-短视频 4-图文
            'sort_type': '1',  # 1-按发布时间排序 2-按观看人数排序
            'is_only_ecom': 'true',  # 只看带货内容
            'uid': 'v2_0a2cf09733b5abeff4e8e909edae241e7a1e03032732d17471a5c17425da1732f1eb95f4a82f1dfe0ee68bbb8d801a4b0a3c000000000000000000005006a59661227050c246361e2082c9acef90a56630759d031b044b3a201cbfaa8aa98616fb404165aba05488a7d514a2f8ec1093c4880e18e5ade4c9012001220103df54269c',
            'date_type': '30d',
            'dont_know_is_only_ecom': 'false',
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'msToken': 'ErqsJfd-h6I5qEwA4azpYlT64sWnchsgrm6upPvZ7fBXYMp0Rwg9kdHXLO5iBMvZdWveViPSaKkwPI5wML5QlcdXpgXojK5qZuHFKLrkgbfbC2pAkz2s44b33PJhxANewTxAGCueLucKNbRx6wz1wnhh07aaPHKwtWIz8Mbm5k8F5Q==',
            # 'a_bogus': 'xy4nkqW7D2RjcpetuKs/C35UVt9ANsWy0Mi2WO5TtqTZPwzYDxpN/NGmaoKgkxRIGbB-iHZ7yVG/TjxcYVkzZeapLmZDu87SetAIV08oZqq3GUG8gqyQCwzFqwBr0O7waQnbE1jRlsBe2EcWVrA/lpMaC5zO5YRDRrqfd/sbJ9WbDSLPupryOZEWYfwSQQ95kj==',
        }
        if uid:
            params['uid'] = uid
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid

        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def overview_fans_portrait(self, uid=None):  # 获取简单粉丝画像
        url = "/square_pc_api/homePage/overview/fans_portrait"
        params = {
            'uid': '9bb91c366d891a3da7f23b529fcfc35c',
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'msToken': 'd9hYJuVMTi-8YoXK4vyp8gDpP_QMCnWAHW9IE9HiKJSVSuGlibsg0mXfD7w8f0a4FXPaVYYOJOfUMb3rHH6VcTIKDGFiuQebAckhpFn4Fnyy_el19pWqTydVrW17OAnSXctbmCKD-LOLApxNBnMPUk2iEKGdjnHLuL-UA4O-_uz53Q==',
            # 'a_bogus': 'OyU5htXJxq8nKplbYcsoC6Vlx2n/NTWy2eT2bynPHKOcPqFYb2BFOabEbxK6mybSUSB1iHVHSVeAbxdcYVskZ9HpzmkvukijetIAV8vLMqNdGlG8gNSdCzTFFwBx0OhwaQnfE1yRWsBKIDOWVrAOlQMGS5FOQQmDRHF6d/scj9WGfCyP8Zr6OMwAij7aUvKb',
        }

        if uid:
            params['uid'] = uid
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid

        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def overview_goods_portrait(self, uid=None):  # 获取简商品画像
        url = "/square_pc_api/homePage/overview/goods_portrait"
        params = {
            'uid': 'b70411d7e31730071807ae911aaf5589',
            'date_type': '30d',
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'msToken': '_LMqif_ffxHGHidBJC5l6tEgGj4x16AwQdP4zRvk1NksOEPqai8oVOIStWRZAjhAvWA2ATjsDbQbfE4yN17OKDFXDLexsPV1jWLCy8U15dCAyZc1Dq6Zd0KsMbYTImbp_C4DfL01LM6QyKBOUjn1eGJWexjigTE11Vudf2HkrjdxCg==',
            # 'a_bogus': 'mf4fhqWExqQVcpltucs/CRMlgXyMNB8yaPiQRjZT9oY-ahMGTxpqKxGObxuhmgb9GSB3iHIHCVeAbxdcmdk0Z99pompkSmUfaTA5V8sLMqwDTt7mgqSoCuTFzwBnUYhweQcWElJR1sBe2DQW9qAxlBBaC5Fa5mYDbHqfd28bn9WTfSgPYZaSO2LAiEwC-Y2RNf==',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
        }

        if uid:
            params['uid'] = uid
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid

        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))

    def overview_core(self, uid=None):  # 获取核心数据 综合匹配度
        url = "/square_pc_api/homePage/overview/core"
        params = {
            'date_type': '30d',
            'uid': '9bb91c366d891a3da7f23b529fcfc35c',
            'ewid': '02200744efdbbaf11f6edcbe9df14f01',
            'verifyFp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'fp': 'verify_mkqf9hcy_e9OoGuRt_5ipm_47la_AOLa_FSEy8OOKYhNM',
            'msToken': 'd9hYJuVMTi-8YoXK4vyp8gDpP_QMCnWAHW9IE9HiKJSVSuGlibsg0mXfD7w8f0a4FXPaVYYOJOfUMb3rHH6VcTIKDGFiuQebAckhpFn4Fnyy_el19pWqTydVrW17OAnSXctbmCKD-LOLApxNBnMPUk2iEKGdjnHLuL-UA4O-_uz53Q==',
            # 'a_bogus': 'Ef0VgFSiD25japeG8ckQC61UtgxMrBSynBixSEVT71cdaheYRVpFOcbxcxugm9bS4YBai91HCVtlbdncudkTZHrkLmpfuot6aTInV0fo/qNdGts8gHyxCzYFzwsNUm7weAcfEl7RlsBC2EcWnqI2lpBG95zO5mbDWHqfd/8cb9ATDWLPmZr6O2EAxfHN05Oy',
        }

        if uid:
            params['uid'] = uid
        params['msToken'] = self.mstoken
        params['fp'] = self.verfyfp
        params['verifyFp'] = self.verfyfp
        params['ewid'] = self.ewid

        try:
            response = self.get(url, params)
            code = response.get('code')
            if code != 0:
                raise Exception("获取失败")
            # save_json(response)
            logger.success(f'code:{response.get('code')} 获取成功')
            logger.info(response)
            return response.get('data', {})
        except Exception as e:
            logger.info(str(e))


def save_json(data, filename: str = 'x.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f,
                  ensure_ascii=False, indent=4)
    logger.info(f'{filename}保存成功')


def get_env():
    running_in_docker = os.getenv('RUNNING_IN_DOCKER')
    redis_host = os.getenv('REDIS_HOST')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    dbredis_pw = os.getenv('DB_REDIS_PW')
    db_database = os.getenv('DB_DATABASE')
    qq_email = os.getenv('QQ_EMAIL')
    qq_auth_code = os.getenv('QQ_AUTH_CODE')
    return {
        'running_in_docker': running_in_docker,
        'redis_host': redis_host,
        'db_port': db_port,
        'db_host': db_host,
        'dbredis_pw': dbredis_pw,
        'db_database': db_database,
        'qq_email': qq_email,
        'qq_auth_code': qq_auth_code
    }


# def save_df_to_postgres(df):
#     for col in df.columns:
#         # 检查每一列的第一个非空值是否是 dict 或 list
#         sample_value = df[col].dropna(
#         ).iloc[0] if not df[col].dropna().empty else None
#         if isinstance(sample_value, (dict, list)):
#             print(f"正在转换复杂列: {col}")
#             # 将 dict/list 转换为 JSON 字符串
#             df[col] = df[col].apply(lambda x: json.dumps(
#                 x, ensure_ascii=False) if x is not None else None)
#     # 1. 获取环境变量（复用你之前的 get_env 函数）
#     env = get_env()

#     # 2. 构建连接字符串 (同步模式)
#     # 注意：SQLAlchemy 写入通常用 postgresql://
#     user = "root"
#     password = urllib.parse.quote_plus(str(env.get('dbredis_pw', '')))
#     host = env['db_host']
#     port = env['db_port']
#     db = env['db_database']

#     db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
#     print(db_url)
#     # 3. 创建引擎
#     engine = create_engine(db_url)

#     # 4. 写入数据库
#     # name: 表名
#     # if_exists: 'fail' (默认), 'replace' (删除重建), 'append' (追加)
#     # index: 是否把 DataFrame 的索引也存为一列
#     df.to_sql('qianhcuandaren', engine, if_exists='append', index=False)
#     print("✅ 数据已成功写入 Postgres")


# 调用


def main():
    cookies = {
        'qc_tt_tag': '0',
        'is_staff_user': 'false',
        'passport_csrf_token': '0e85fa8b594f271adfc8a0d7b7c77539',
        'passport_csrf_token_default': '0e85fa8b594f271adfc8a0d7b7c77539',
        'buyin_shop_type': '11',
        'buyin_shop_type_v2': '11',
        'buyin_account_child_type_v2': '1',
        'buyin_app_id_v2': '13',
        'ucas_c0': 'CkEKBTEuMC4wEL-IhZS-gurAaRjmJiDNztD44ozIByiwITDO6bDsiIzlAkCX0IbMBkiXhMPOBlCjvILSzJbJ_2dYbxIUadTcfYrlSQHLQB7F6_eBb1iB6Y0',
        'ucas_c0_ss': 'CkEKBTEuMC4wEL-IhZS-gurAaRjmJiDNztD44ozIByiwITDO6bDsiIzlAkCX0IbMBkiXhMPOBlCjvILSzJbJ_2dYbxIUadTcfYrlSQHLQB7F6_eBb1iB6Y0',
        'PHPSESSID': '16da039c4231e8ba2ab6d6d726716933',
        'PHPSESSID_SS': '16da039c4231e8ba2ab6d6d726716933',
        's_v_web_id': 'verify_ml6aqpof_LN0CXAKc_oGdi_4VxV_809r_Zvrq0JwuvNe5',
        'scmVer': '1.0.1.9814',
        'COMPASS_LUOPAN_DT': 'session_7602843735982063924',
        'passport_auth_status': '76d9ab3a8858258fca191f6530c8d1f7%2C9bdd4cf9c4b1c7ea9b216da5fbf2c978',
        'passport_auth_status_ss': '76d9ab3a8858258fca191f6530c8d1f7%2C9bdd4cf9c4b1c7ea9b216da5fbf2c978',
        'uid_tt': 'c71a9148f5e48de6dd44c81c36690e39',
        'uid_tt_ss': 'c71a9148f5e48de6dd44c81c36690e39',
        'sid_tt': '609b2b3a83c44905e34d0fae6a8bade7',
        'sessionid': '609b2b3a83c44905e34d0fae6a8bade7',
        'sessionid_ss': '609b2b3a83c44905e34d0fae6a8bade7',
        'Hm_lvt_b6520b076191ab4b36812da4c90f7a5e': '1770370115,1770606138,1770609520,1770686816',
        'HMACCOUNT': '515B172AA3E9021D',
        'ucas_c0_buyin': 'CkEKBTEuMC4wELSIg4bHq6LFaRjmJiDNztD44ozIByiwITDO6bDsiIzlAkDhkqrMBkjhxubOBlCjvILSzJbJ_2dYbxIUc4ZexOdq-XyaGSaq0ooSWqZUymk',
        'ucas_c0_ss_buyin': 'CkEKBTEuMC4wELSIg4bHq6LFaRjmJiDNztD44ozIByiwITDO6bDsiIzlAkDhkqrMBkjhxubOBlCjvILSzJbJ_2dYbxIUc4ZexOdq-XyaGSaq0ooSWqZUymk',
        'sid_guard': '609b2b3a83c44905e34d0fae6a8bade7%7C1770686817%7C5184000%7CSat%2C+11-Apr-2026+01%3A26%3A57+GMT',
        'session_tlb_tag': 'sttt%7C20%7CYJsrOoPESQXjTQ-uaout5_________-i34afE9ZKfK_tp0u4chgi360gFyCMBu5qHQtXCtzynyI%3D',
        'sid_ucp_v1': '1.0.0-KDNiZDE0MGM1YmVjOTRjNDgyNmE3MWUyMDY5MjU5MzA3ZGEwZWIzNTMKGQjO6bDsiIzlAhDhkqrMBhimDCAMOAJA8QcaAmxxIiA2MDliMmIzYTgzYzQ0OTA1ZTM0ZDBmYWU2YThiYWRlNw',
        'ssid_ucp_v1': '1.0.0-KDNiZDE0MGM1YmVjOTRjNDgyNmE3MWUyMDY5MjU5MzA3ZGEwZWIzNTMKGQjO6bDsiIzlAhDhkqrMBhimDCAMOAJA8QcaAmxxIiA2MDliMmIzYTgzYzQ0OTA1ZTM0ZDBmYWU2YThiYWRlNw',
        'SASID': 'SID2_7605039942650134838',
        'BUYIN_SASID': 'SID2_7605039942650134838',
        'buyin_account_child_type': '1',
        'buyin_app_id': '13',
        'ecom_us_lt_buyin': '9e75c03fa13c9621458cdb7fc9231919f19946a8aaf5bf589dd0f6f8a69d7dc2',
        'ecom_us_lt_ss_buyin': '9e75c03fa13c9621458cdb7fc9231919f19946a8aaf5bf589dd0f6f8a69d7dc2',
        'gfkadpd': '2631,22740',
        'csrf_session_id': 'd26a63537d4c8877193909aff9da598b',
        'odin_tt': '0e187a5d7921d6e554744be48ceb85621d7147fa6a1bafe138c55ec93fcafa72ce965d123af93840f1b7bc988d893825',
        'ttwid': '1%7CMw7RXoqOwUgvsIIhnrINwgLcYoBmOvmJvj5Zo_choMk%7C1770709557%7C03a429afa9a8ba8133775d815d9a960476c399b11fb3c9cd93da93a6c490e276',
        '_tea_utm_cache_3813': 'undefined',
        'Hm_lpvt_b6520b076191ab4b36812da4c90f7a5e': '1770712327',
        'msToken': 'FK0K8YgWd_6KxPdb-ZESHicT0-MEu4Nf9FBasVUNT1AsIzInqoStIRm1R7CPtEdimJoxvVoKKIRL4zouxdwissZVvuJgp7tswtNRXYMsZG6Tko_-h1O2Cvt9Tgcjs6HJmw1I',
        'tt_scid': 'qsIdJdn04sL9TAEmDGi9T9E0Ghqi.To5AxzkhLT7wlneQQbwVP2GzWmlNlu90kt9e012',
    }
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,und;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://buyin.jinritemai.com',
        'priority': 'u=1, i',
        'referer': 'https://buyin.jinritemai.com/dashboard/servicehall/daren-square',
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36', }

    new_daren = jinritemai_base(cookies, headers)

    # print(get_contact(new_daren, type=['wechat', 'phone']))
    s1 = time.perf_counter()
    # search_data = search(new_daren, json_data)
    s2 = time.perf_counter()
    # print(type(search_data.get('list', [])))
    # df = pd.json_normalize(search_data.get('list', []))
    # print(df.head(6))
    # df.to_csv('x.csv')
    # s3 = time.perf_counter()
    # print(f's2-s1::{round(s2-s1, 2)}||s3-s2::{round(s3-s2, 2)}')
    # # save_df_to_postgres(df)
    # save_json(search_data, '抖店搜索结果.json')
    # print(1)
    # fan_data = authorFans(new_daren, uid='v2_0a2c2e287a985a3dae4ec5a5af98c1e9e4fa55a76f1f8148f3c3827cb5870e42c3ac98903d90801117c6ec7f0e711a4b0a3c000000000000000000004ff7762bd20f0d7425105bda30a4bc17cdf179d5b3d829ec9de091895f3486ccab14b354bc41cedf00b41530c7dd2b84168810d59e870e18e5ade4c9012001220103d3723db2')
    # df = pd.json_normalize(fan_data.get('analysis'))
    # df.to_csv('x.csv')
    # print(df.head(6))
    # print(fan_data.get('analysis'))
    # new_daren.author_fans('v2_0a2cbaeb6a8379a38cb42c3e88b4f10b07162bd43586a841cf32b15a7b5c3c463a7846e9d1aa2ab45c431765f2361a4b0a3c000000000000000000005001d529225fd8162c9cfed6c3ae6f6ef75af8340b95ba74beb75b6cc26868041ea361e5c1d01551d8ee93a41bd76081cc9a10f08f880e18e5ade4c9012001220103de323cde')
    # authorFans(new_daren, uid='')

    # new_daren.video_shop_data()
    # print(dir(new_daren))
    new_daren.msg_send()
    # new_daren.msg_send()


if __name__ == "__main__":
    main()


# uid 默认是长的，也可以是origin_uid（短的）
# jxlm_shop 是地基
# 上层建筑 先搜索 得出结果，可以选择批量建联，也可以单个建联，建联后可以查看粉丝画像，历史带货视频，核心数据等

# 批量获取私信信息加上用户uid，再配合联系方式获取，然后可以批量建联，建联后可以获取粉丝画像，历史带货视频，核心数据等

# 后期数据跟踪
