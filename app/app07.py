import asyncio
import functools
import json
from loguru import logger
import time
from typing import Any, Awaitable, Callable, List, Optional, Union, Dict
from utils.uni_data_models_new import *

# 第三方库导入
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, ValidationError, field_validator, Field
from tortoise.exceptions import IntegrityError

# 本地模块导入（按字母顺序分组）
from orm.models import *  # 建议明确导入所需模型，避免通配符
from utils import (shop_data_upload, qianchuan_api_service)


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
# tortoise_orm study


router = APIRouter()


class awame(BaseModel):
    uid: str = Field(description="uid")
    # 明确指定日期时间格式
    commercial_code: str = Field(..., description="合作码")
    cooperation_type: Optional[str] = Field('个人', description="合作类型")
    advertise_id: Optional[int] = Field(1779271778331655, description="千川户")


@router.get('/newawame')
async def newawame(params: awame = Query(...)):

    aweme_auth = {"advertiser_id": params.advertise_id,
                  "aweme_id": str(params.uid),
                  "code": str(params.commercial_code),
                  "auth_type": "AWEME_COOPERATOR",
                  "end_time": "2099-12-31 23:59:59",
                  "notes": str(params.cooperation_type)}
    uni_product = {
        "advertiser_id": params.advertise_id,
        "aweme_ids": [
            int(params.uid)
        ],
        "marketing_goal": "VIDEO_PROM_GOODS",
        "shop_id": 1082858
    }
    # step1
    try:
        api_name = "POST_AWAME_AUTH"
        rep1 = qianchuan_api_service.invoke_qianchuan_api(
            api_name=api_name, method='post', payload=aweme_auth)
        code = rep1.get('code', 0)
    except Exception as e:
        raise HTTPException(status_code=403, detail=f'{e}{rep1}')
     # step2
    if code == 0:
        try:
            api_name = "UNI_PROMOTION_AUTHORIZATION"
            rep2 = qianchuan_api_service.invoke_qianchuan_api(
                api_name=api_name, method='post', payload=uni_product)
        except Exception as e:
            raise HTTPException(status_code=403, detail=f'{e}')

    return {'aweme_auth': aweme_auth, 'uni_product': uni_product, "rep1": rep1, "rep2": rep2}


# @router.get('/awame_video')
# async def awame_video(account_id: int = 1779271778331655):
#     api_name = "GET_AWAME_VIDEO"

#     uni_promotions = await UniPromotionList.filter(account_id__in=[account_id], status__in=['DELIVERY_OK']).all()
#     # x=10
#     # print(uni_promotions)
#     success = []
#     error = []
#     if uni_promotions == None:
#         return {'code': 4000, 'detail': "查询失败"}
#     for uni_promotion in uni_promotions:
#         # x +=1
#         anchor_id = uni_promotion.anchor_id
#         product_id = uni_promotion.product_id
#         aweme = await Uni_aweme_list.get_or_none(account_id=account_id, aweme_show_id=anchor_id)
#         if aweme == None:
#             error.append({'anchor_id': anchor_id, 'product_id': product_id,
#                          'uni_promotions': uni_promotion.id})
#             continue
#         # print(aweme_lists)
#         success.append(aweme)
#         aweme_id = aweme.aweme_id
#         request_params = {
#             "advertiser_id": account_id,
#             "aweme_id": aweme_id,
#             "filtering": {
#                 "product_id": product_id,
#             },
#             "cursor": 0,
#             "count": 50}
#         rep = qianchuan_api_service.invoke_qianchuan_api(
#             api_name=api_name, params=request_params)
#         if rep.get('code') != 0:
#             continue

#         # print(rep)

#         account = await AccountList.get_or_none(advertiser_id=account_id)

#         # logger.info(advertiser_id,anchor_id,aweme)
#         objects_to_create = [
#             AwemeVideo(** fields, uni_plan=uni_promotion, aweme=aweme,
#                        account=account, created_at=datetime.now())
#             for fields in rep.get('data').get('video_list')
#         ]
#         await AwemeVideo.bulk_create(objects_to_create,  on_conflict=["video_id"],  # 这里的字段必须在数据库中有唯一索引（Unique Index）
#                                      # update_fields=update_fields  # 发生冲突时，要更新哪些字段)
#                                      )

#         # if x>=2:
#         # return rep
#     return {'code': 4000, 'detail': {'success': success, 'error': error}}
#     # 信息存储
# # GET_AWAME_VIDEO
