import random
def generate_6digit_code():
    """生成 6 位纯数字验证码"""
    # 从 0-9 中随机选 6 个字符，join 成字符串
    code = ''.join(random.choices('0123456789', k=6))

    return code