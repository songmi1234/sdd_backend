import requests
import json
from typing import Optional
from loguru import logger


class WebId:
    NAME = "webid"
    API = "https://mcs.zijieapi.com/webid"

    PARAMS = {
        "aid": "6383",
        "sdk_version": "5.1.18_zip",
        "device_platform": "web"
    }

    @classmethod
    def get_web_id(cls, user_agent: str, proxy: Optional[str] = None) -> str:
        # 1. 准备请求头
        headers = {
            "User-Agent": user_agent,
            "Content-Type": "application/json",
            "Referer": "https://www.douyin.com/",
        }

        # 2. 准备 POST 的 Data (Payload)
        # 注意：这里必须是 JSON 格式的字符串
        data = {
            "app_id": 6383,
            "url": "https://www.douyin.com/",
            "user_agent": user_agent,
            "referer": "https://www.douyin.com/",
            "user_unique_id": ""
        }

        # 3. 设置代理（如果有）
        proxies = None
        if proxy:
            proxies = {"http": proxy, "https": proxy} if proxy else None

        try:
            # 4. 发送 POST 请求
            # json=data 会自动将字典转为 JSON 字符串并设置 Content-Type
            response = requests.post(
                cls.API,
                params=cls.PARAMS,
                json=data,
                headers=headers,
                proxies=proxies,
                timeout=10
            )

            # 5. 检查响应并提取 web_id
            response.raise_for_status()  # 如果状态码不是 200 会报错
            result = response.json()
            web_id = result.get("web_id")

            if web_id:
                logger.info(f"获取成功: {web_id}")
                return web_id
            else:
                logger.info("返回结果中没有 web_id")
                return ''

        except Exception as e:
            logger.info(f"获取 webid 失败，错误信息: {e}")
            return ''


# 测试代码
if __name__ == "__main__":
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    wid = WebId.get_web_id(ua)
