import functools
from itertools import product
from pickletools import optimize
import re
from loguru import logger
import time
from typing import Any, Awaitable, Callable, List, Optional, Union
from type import reposen_model
from enum import Enum
from datetime import date, timedelta
from app import app07
from datetime import datetime
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


router = APIRouter()
# 多维表格同步


class awemeinfo_tp(BaseModel):

    aweme_id: int = Field(
        description="达人UID", alias='达人UID')
    aweme_show_id: str = Field(description="抖音号", alias='抖音号', default='')
    aweme_name: str = Field(description="达人昵称", alias='达人昵称', default='')
    phone_number: int = Field(description="手机号", alias='手机号')
    address: str = Field(description="达人昵称", alias='地址', default='地址')
    address_name: str = Field(description="收件人", alias='收件人', default='收件人')
    commercial_code: str = Field(description="合作码", alias='合作码', default='')
    qianchuan_auto_cop: bool = Field(
        description="千川自动授权", alias='千川自动授权', default=True)
    business_type: str = Field(description="建联方式", alias='建联方式', default='')


@router.post('/awemeinfo')
async def awemeinfo_sync(awemeinfo: list[awemeinfo_tp]):
    # 打印转换后的第一个字典，检查 key 是否和数据库字段名对得上
    if awemeinfo:
        print(f"DEBUG: Data to insert: {awemeinfo[0].model_dump()}")

    objects_to_create = [Awemeinfo(**item.model_dump()) for item in awemeinfo]

   # 唯一索引 即不变的内容，可以作为参考系
    on_conflict = "aweme_id"
    all_fields = awemeinfo[0].model_dump().keys()
    update_fields = [f for f in all_fields if f != on_conflict]
    # bulk_create 返回创建的对象列表（注意：某些驱动下返回为空）
    await Awemeinfo.bulk_create(
        objects_to_create,

        on_conflict=[on_conflict],  # 这里的字段必须在数据库中有唯一索引（Unique Index）
        update_fields=update_fields)  # 发生冲突时，要更新哪些字段))

    return {"status": "success", "count": len(objects_to_create)}


class adlacement_tp(BaseModel):

    product_id: int = Field(
        description="商品ID", alias='商品ID')
    product_name: str = Field(description="商品名称", alias='商品名称', default='')
    roi: float = Field(description="预期ROI", alias='预期ROI', default=2.5)
    budget: float = Field(description="预算金额", alias='预算金额', default=300.00)


@router.post('/adplacement')
async def adplacement_sync(adplacement: list[adlacement_tp]):
    # 打印转换后的第一个字典，检查 key 是否和数据库字段名对得上
    if adplacement:
        print(f"DEBUG: Data to insert: {adplacement[0].model_dump()}")

    objects_to_create = [AdPlacement(**item.model_dump())
                         for item in adplacement]
    # 唯一索引 即不变的内容，可以作为参考系
    on_conflict = "product_id"
    all_fields = adplacement[0].model_dump().keys()
    update_fields = [f for f in all_fields if f != on_conflict]
    # bulk_create 返回创建的对象列表（注意：某些驱动下返回为空）
    await AdPlacement.bulk_create(
        objects_to_create,

        on_conflict=[on_conflict],  # 这里的字段必须在数据库中有唯一索引（Unique Index）
        update_fields=update_fields)  # 发生冲突时，要更新哪些字段))
    # bulk_create 返回创建的对象列表（注意：某些驱动下返回为空）

    return {"status": "success", "count": len(objects_to_create)}


class OrderLogisticsSchema(BaseModel):
    # 使用 Field 别名匹配你原始数据中的中文 Key
    shipping_warehouse: Optional[str] = Field(None, alias='发货仓库')
    shipping_shop: Optional[Union[float, str]] = Field(None, alias='发货店铺')
    shipping_category: Optional[str] = Field(None, alias='发货类别')
    shipping_address: Optional[str] = Field(None, alias='收件地址')
    logistics_info: Optional[str] = Field(None, alias='物流信息')
    logistics_company: Optional[str] = Field(None, alias='物流公司')
    logistics_track_no: Optional[str] = Field(None, alias='物流单号')
    logistics_update_time: Optional[datetime] = Field(None, alias='物流更新时间')
    logistics_status: Optional[str] = Field(None, alias='物流状态')
    online_order_id: Optional[str] = Field(None, alias='线上订单号')
    offline_order_id: Optional[Union[float, int]] = Field(None, alias='线下订单号')
    order_status: Optional[str] = Field(None, alias='订单状态')
    influencer_name: Optional[str] = Field(None, alias='达人昵称')
    influencer_uid: Optional[str] = Field(None, alias='达人UID')
    shipping_time: Optional[datetime] = Field(None, alias='发货时间')


@router.post('/express')
async def express_sync(express: list[OrderLogisticsSchema]):
    # 打印转换后的第一个字典，检查 key 是否和数据库字段名对得上
    if express:
        print(f"DEBUG: Data to insert: {express[0].model_dump()}")

    objects_to_create = [Express(**item.model_dump())
                         for item in express]
    # 唯一索引 即不变的内容，可以作为参考系
    on_conflict = "online_order_id"
    all_fields = express[0].model_dump().keys()
    update_fields = [f for f in all_fields if f != on_conflict]
    # bulk_create 返回创建的对象列表（注意：某些驱动下返回为空）
    await Express.bulk_create(
        objects_to_create,

        on_conflict=[on_conflict],  # 这里的字段必须在数据库中有唯一索引（Unique Index）
        update_fields=update_fields)  # 发生冲突时，要更新哪些字段))

    return {"status": "success", "count": len(objects_to_create)}


class VideoPromotionSchema(BaseModel):
    video_url: Optional[str] = Field(None, alias="视频链接")
    dup_check: Optional[str] = Field(None, alias="重复检测")
    ads_status: Optional[str] = Field(None, alias="投流状态")
    auto_ads: Optional[str] = Field(None, alias="自动投放")
    video_id: Optional[str] = Field(None, alias="视频ID")
    influencer_name: Optional[str] = Field(None, alias="达人昵称")
    product_id: Optional[str] = Field(None, alias="商品ID")
    product_title: Optional[str] = Field(None, alias="商品标题")
    cart_product_title: Optional[str] = Field(None, alias="挂车商品标题")
    video_topic: Optional[str] = Field(None, alias="视频标题(话题)")
    video_title: Optional[str] = Field(None, alias="视频标题")
    douyin_id: Optional[str] = Field(None, alias="抖音号")
    influencer_bio: Optional[str] = Field(None, alias="达人签名")
    influencer_uid: Optional[str] = Field(None, alias="达人UID")
    video_duration: Optional[str] = Field(None, alias="视频时长")
    upload_time: Optional[datetime] = Field(None, alias="上传时间")


@router.post('/aweme/video')
async def aweme_video_sync(aweme: list[VideoPromotionSchema]):
    # 打印转换后的第一个字典，检查 key 是否和数据库字段名对得上
    if aweme:
        print(f"DEBUG: Data to insert: {aweme[0].model_dump()}")
    # # 1. 准备要插入的对象列表
    objects_to_create = [AwemeVideo_koc(**item.model_dump())
                         for item in aweme]
    # 2. 定义冲突时需要更新的字段（排除掉主键或唯一键本身）
    all_fields = aweme[0].model_dump().keys()
    update_fields = [f for f in all_fields if f != "video_id"]

    # bulk_create 返回创建的对象列表（注意：某些驱动下返回为空）
    await AwemeVideo_koc.bulk_create(
        objects_to_create,
        on_conflict=["video_id"],  # 这里的字段必须在数据库中有唯一索引（Unique Index）
        update_fields=update_fields  # 发生冲突时，要更新哪些字段)
    )
    # on_conflict=unique_fields,
    # update_fields = update_fields  # 自动计算出来的列表
    return {"status": "success", "count": len(objects_to_create)}


@router.get('/all_awame_video', summary='获取账户下所有达人视频')
async def awame_video(account_id: int = 1779271778331655):
    api_name = "GET_AWAME_VIDEO"
    uni_promotions = await UniPromotionList.filter(account_id__in=[account_id], status__in=['DELIVERY_OK']).all()
    # x=10
    # print(uni_promotions)
    all_fields = ['aweme_item_id', 'comment_cnt', 'duration', 'height', 'image_mode', 'is_ai_create', 'is_recommend',
                  'like_cnt', 'material_id', 'share_cnt', 'title', 'url', 'video_cover_url', 'video_id', 'view_cnt', 'width']

    update_fields = [f for f in all_fields if f != "video_id"]
    success = []
    error = []
    if uni_promotions == None:
        return {'code': 4000, 'detail': "查询失败"}
    for uni_promotion in uni_promotions:
        # x +=1
        anchor_id = uni_promotion.anchor_id
        product_id = uni_promotion.product_id
        aweme = await Uni_aweme_list.get_or_none(account_id=account_id, aweme_show_id=anchor_id)
        if aweme == None:
            error.append({'anchor_id': anchor_id, 'product_id': product_id,
                         'uni_promotions': uni_promotion.id})
            continue
        # print(aweme_lists)
        success.append(aweme)
        aweme_id = aweme.aweme_id
        request_params = {
            "advertiser_id": account_id,
            "aweme_id": aweme_id,
            "filtering": {
                "product_id": product_id,
            },
            "cursor": 0,
            "count": 50}
        rep = qianchuan_api_service.invoke_qianchuan_api(
            api_name=api_name, params=request_params)
        if rep.get('code') != 0 or len(rep.get('data', {}).get(
                'video_list')) == 0:
            continue

        account = await AccountList.get_or_none(advertiser_id=account_id)

        # logger.info(advertiser_id,anchor_id,aweme)
        objects_to_create = [
            AwemeVideo(** fields, uni_plan=uni_promotion, aweme=aweme,
                       account=account, created_at=datetime.now())
            for fields in rep.get('data', {}).get('video_list')
        ]
        await AwemeVideo.bulk_create(objects_to_create,  on_conflict=["video_id"],  # 这里的字段必须在数据库中有唯一索引（Unique Index）
                                     update_fields=update_fields  # 发生冲突时，要更新哪些字段)
                                     )

        # if x>=2:
        # return rep
    return {'code': 4000, 'detail': {'success': success, 'error': error}}
    # 信息存储
# GET_AWAME_VIDEO


class Allrejectreasonlist(BaseModel):
    video_list: List[str] = Field(alias="抖音视频id")


@router.post('/allrejectreason', summary='获取视频审核建议')
async def allrejectreason(video_list: List[str]):
    rejectreasons = await AuditSuggestion.filter(aweme_item_id__in=video_list).all()
    if not rejectreasons:
        raise HTTPException(status_code=200, detail='没有查到该视频')
    print(rejectreasons)
    # material_ids = [item.get('material_id') for item in material_ids_raw]
    # rejectreasons = await AuditSuggestion.filter(material_id__in=material_ids).all()
    # if not rejectreasons:
    #     raise HTTPException(status_code=200, detail='没有找到违规信息')
    return rejectreasons
