from six.moves.urllib.parse import urlencode, urlunparse
from six import string_types
import json
import os
import requests
import logging
from enum import Enum, auto
import time
from utils import gettoken
from typing import Any, Awaitable, Callable, List, Optional, Union, Dict
# 配置日志
logger = logging.getLogger("ad_api_client")

# API路径映射（使用更规范的命名）
API_ENDPOINTS = {
    "GET_ADVERTISER_LIST": "/open_api/2/customer_center/advertiser/list/",
    "GET_AUTHORIZED_AWEME": "/open_api/v1.0/qianchuan/uni_aweme/authorized/get/",
    "GET_FINANCE_DETAIL": "/open_api/v1.0/qianchuan/finance/detail/get/",
    # "GET_CUSTOM_REPORT": "/open_api/v1.0/qianchuan/report/custom/get/", #旧数据接口
    "GET_UNI_PROMOTION_DATA": "/open_api/v1.0/qianchuan/report/uni_promotion/data/get/",  # 全域数据接口
    "GET_UNIFIED_PROMOTION": "/open_api/v1.0/qianchuan/uni_promotion/list/",  # 获取全域计划
    # 千川视频库 https://open.oceanengine.com/labels/12/docs/1739309912219663?origin=left_nav
    "GET_QIANCHUAN_VIDEO": "/open_api/v1.0/qianchuan/video/get/",
    # 千川图片库 https://open.oceanengine.com/labels/12/docs/1739304248623182?origin=left_nav
    "GET_QIANCHUAN_IMAGE": "/open_api/v1.0/qianchuan/image/get/",
    # "GET_QIANCHUAN_CARUSEL":"/open_api/v1.0/qianchuan/carousel/get/", #千川图文
    # "GET_QIANCHUAN_AWAME_IMAGE":"/open_api/v1.0/qianchuan/carousel/aweme/get/", #千川抖音号图文
    # 获取全域计划审核建议 https://open.oceanengine.com/labels/12/docs/1832628101966183?origin=left_nav
    "GET_UNI_PROMOTION_REJECT_REASON": "/open_api/v1.0/qianchuan/uni_promotion/ad/suggestion/",
    # https://api.oceanengine.com/open_api/v3.0/security/score_violation_event/get/
    "GET_ViolationRecord": "/open_api/v3.0/security/score_violation_event/get/",
    "POST_AWAME_AUTH": "/open_api/v1.0/qianchuan/tools/aweme_auth/",
    "UNI_PROMOTION_AUTHORIZATION": "/open_api/v1.0/qianchuan/uni_promotion/authorization/apply/",
    "GET_AWAME_VIDEO": "/open_api/v1.0/qianchuan/file/video/aweme/get/",
    "UPDATA_AD": "/open_api/v1.0/qianchuan/uni_aweme/ad/update/",
    "CHANGE_AD_STATUS": "/open_api/v1.0/qianchuan/uni_promotion/ad/status/update/",
    "CREATE_AD": "/open_api/v1.0/qianchuan/uni_aweme/ad/create/",
    "AWEME_VIDEO_GET": "/open_api/v1.0/qianchuan/file/video/aweme/get/",
    "MATERIAL_ADD": "/open_api/v1.0/qianchuan/uni_promotion/ad/material/add/",
    "AD_DETAIL": "/open_api/v1.0/qianchuan/uni_promotion/ad/detail/"
}


class ResponseCode(Enum):
    """API响应状态码枚举"""
    SUCCESS = 0
    AUTH_FAILURE = 40100, 51010, 40105
    TOKEN_EXPIRED = 40102
    OTHER_FAILURE = 400154  # 视频库获取业务代码错误


def build_api_url(api_path: str, query_params: dict = {}) -> str:
    """构建完整的API请求URL"""
    scheme, netloc = "https", "ad.oceanengine.com"

    # 处理查询参数（字符串直接使用，其他类型JSON序列化）
    encoded_params = urlencode({
        k: v if isinstance(v, string_types) else json.dumps(v)
        for k, v in query_params.items()
    })

    return urlunparse((scheme, netloc, api_path, "", encoded_params, ""))


def send_api_request_with_retry(url: str, method: str, payload: Optional[dict] = None) -> dict:
    """发送API请求并处理重试逻辑"""
    # 获取访问令牌
    access_token = os.environ.get("access_token")
    headers = {"Access-Token": access_token}

    # 创建会话并设置重试策略
    session = requests.Session()
    max_retries = 5
    timeout = 5

    for attempt in range(max_retries):
        try:
            # 发送请求
            if method == 'get':
                response = session.get(url, headers=headers, timeout=timeout)
            elif method == 'post':
                response = session.post(
                    url, headers=headers, timeout=timeout, json=payload)
            response.raise_for_status()  # 检查HTTP状态码

            # 解析响应
            result = response.json()
            logger.info("请求")
            logger.info(result)
            # print(response)
            code = result.get("code", -1)

            if code == ResponseCode.SUCCESS.value:
                if attempt == 0:
                    logger.info(f" 第1次成功数据获取成功")
                else:

                    logger.info(f"尝试第 {attempt}/{max_retries} 次成功")
                return result  # 成功返回数据
            elif code in ResponseCode.AUTH_FAILURE.value or code == ResponseCode.OTHER_FAILURE.value:
                logger.warning(result)
                logger.warning(f"认证失败，尝试第 {attempt+1}/{max_retries} 次重试")
                # print(f"认证失败，尝试第 {attempt+1}/{max_retries} 次重试")
                time.sleep(3)  # 等待2秒后重试
                continue
            elif code == ResponseCode.TOKEN_EXPIRED.value:
                logger.info("Token过期，刷新Token")
                gettoken.refresh_access_token()  # 刷新Token
                access_token = os.environ.get("access_token")
                headers["Access-Token"] = access_token  # 更新请求头
            else:
                logger.error(f"业务错误 {code}: {result}")
                logger.error(f"请求异常 url:{url}")
                return {"error": f"业务错误 {code}", "details": result}

        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常 ({attempt+1}/{max_retries}): {str(e)}")
            logger.error(f"请求异常 url:{url}")
            if attempt == max_retries - 1:
                return {"error": "请求失败", "details": str(e)}

    return {"error": f"达到最大重试次数 ({max_retries})"}


def invoke_qianchuan_api(api_name: str, params: Optional[dict] = {}, method: str = 'get', payload: Optional[dict] = None) -> dict:
    """调用千川API的统一入口"""
    if api_name not in API_ENDPOINTS:
        raise ValueError(f"未知API名称: {api_name}")

    api_path = API_ENDPOINTS[api_name]
    url = build_api_url(api_path, params)
    # print(url)
    return send_api_request_with_retry(url, method, payload)


if __name__ == '__main__':
    # 示例：获取广告主列表
    gettoken.refresh_access_token()
    api_name = "GET_UNIFIED_PROMOTION"
    request_params = {
        "page": 1,
        "page_size": 1,
        "cc_account_id": 11,
        "account_source": "QIANCHUAN",  # 新增参数
        "filtering": {"account_name": ""}  # 新增参数
    }

    result = invoke_qianchuan_api(api_name, request_params)
    print(json.dumps(result, indent=2, ensure_ascii=False))
