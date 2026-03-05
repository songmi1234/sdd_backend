import base64
from signal import raise_signal
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES
import json
import os
from loguru import logger
from typing import Any, Optional, Dict, List

# 密钥需与前端一致 (16字节)
# AES_KEY = b"your-secure-key!"
# AES_IV = b"1234567890123456"


def encrypt_data(data: Any) -> str:

    key_str = os.environ.get("AES_KEY", '')
    iv_str = os.environ.get("AES_IV", '')

    if not key_str or not iv_str:
        raise RuntimeError("环境变量 AES_KEY 或 AES_IV 未设置，加密失败")
    # 2. 核心：转换为字节串 (Bytes)
    # AES 要求 Key 必须是 16, 24 或 32 字节
    AES_KEY = key_str.encode('utf-8')
    AES_IV = iv_str.encode('utf-8')
    """将数据转为JSON并进行AES加密"""
    # 1. 序列化数据 Serialize obj to a JSON formatted str
    json_str = json.dumps(data)
    # 2. 加密
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    ct_bytes = cipher.encrypt(pad(json_str.encode('utf-8'), AES.block_size))
    # 3. Base64编码返回字符串
    return base64.b64encode(ct_bytes).decode('utf-8')


if __name__ == '__main__':  # 必须是 __main__
    test_data = {"id": 1, "name": "Gemini", "roles": ["admin"]}
    encrypted = encrypt_data(test_data)
    logger.info(f"加密结果: {encrypted}")
