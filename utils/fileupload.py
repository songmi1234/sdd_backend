import requests
import hashlib
import os
from pathlib import Path
import aiohttp
import asyncio
from aiohttp import FormData
# 准备请求参数
advertiser_id = 1791216574500928  # 替换为实际广告主ID
access_token =  os.environ.get("access_token")  # 替换为实际的Access Token
# video_file_path = r"C:\Users\Administrator\Desktop\素材\32户\32户\6.5木槿冬青-三伏贴-痛点1.mp4"  # 替换为实际视频文件路径

# 计算视频文件的MD5值
def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
async def upload_video(video_file_path, advertiser_id):
    """
    异步上传视频到指定的广告账户
    
    参数:
        video_file_path (str): 视频文件的路径
        advertiser_id (int): 广告主ID
        access_token (str): API访问令牌
    
    返回:
        dict: API响应结果
    """
    # 检查文件是否存在
    if not os.path.exists(video_file_path):
        raise FileNotFoundError(f"视频文件不存在: {video_file_path}")
    
    # 检查文件大小
    min_size = 5 * 1024 * 1024  # 5MB
    if os.path.getsize(video_file_path) < min_size:
        raise Exception(f"{os.path.basename(video_file_path)}小于{min_size/(1024*1024)}MB，不符合要求")
    
    # 构建请求
    url = "https://ad.oceanengine.com/open_api/2/file/video/ad/"
    headers = {
        "Access-Token": access_token
    }
    
    # 创建 FormData 对象并添加文件和其他参数
    data = FormData()
    
    # 显式打开文件并在finally块中关闭
    file_obj = None
    try:
        file_obj = open(video_file_path, "rb")
        data.add_field(
            "video_file",
            file_obj,
            filename=os.path.basename(video_file_path),
            content_type="video/mp4"  # 根据实际文件类型调整
        )
        
        # 添加其他表单字段
        data.add_field("advertiser_id", str(advertiser_id))
        data.add_field("upload_type", "UPLOAD_BY_FILE")
        data.add_field("video_signature", calculate_md5(video_file_path))
        
        # 发送请求
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                response.raise_for_status()  # 检查请求是否成功
                result = await response.json()
                print("请求成功:", result)
                return result
    except aiohttp.ClientError as e:
        print("请求失败:", e)
        if 'response' in locals():
            print(f"状态码: {response.status}")
            print(f"响应内容: {await response.text()}")
        raise
    finally:
        # 确保文件被关闭
        if file_obj is not None:
            file_obj.close()
# 数据库设计
#    id filepath accountid 
# 思路 
# 上传数据库模块
#       检查文件比列是否正常 
#       逐条获取文件md5值
#      和数据库比对去重
#      比对通过后 status=wait——upload
# 上传到千川后台模块
# 
#      从数据库中匹配出 status=wait——upload 提取出accountid md5值
#       逐条上传
#          成功 status=success
#          失败=failed
#          打印失败原因（自动重试）
if __name__ == "__main__":
    folder = Path(r"D:\素材上传\7.11白矾慕荷-小茴香-1改")
    file_paths = list(folder.rglob("*"))
    print("程序启动")
    x=0
    for file in file_paths:
        upload_video(file,advertiser_id)
        print(f"{file.name} 上传成功")
        x+=1
    print(x)