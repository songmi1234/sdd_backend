import functools

from pickletools import optimize

from signal import raise_signal
from loguru import logger
import time
import datetime
from typing import Any, Awaitable, Callable, List, Optional, Union
from enum import Enum
from type import reposen_model
from app import app07
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


class ad_create(BaseModel):
    advertiser_id: int = Field(
        description="advertiser_id", default=1779271778331655)
    # uid: str = Field(description="uid")
    name: Optional[str] = Field(description="name", default=None)
    aweme_id: int = Field(description="aweme_id", default=0)
    marketing_goal: str = Field(
        description="marketing_goal", default="VIDEO_PROM_GOODS")
    product_id: int = Field(description="product_ids", default=0)
    roi2_goal: float = Field(description="ROI", default=2.5)
    smart_bid_type: str = Field(description="投放类型", default='SMART_BID_CUSTOM')
    qcpx_mode: str = Field(description="是否开启智能优惠券", default='QCPX_MODE_ON')
    budget: float = Field(description="预算", default=30)
    live_schedule_type: str = Field(
        description="直播全域投放时间选择方式", default="SCHEDULE_FROM_NOW")
    video_schedule_type: str = Field(
        description="商品全域投放时间选择方式", default="SCHEDULE_FROM_NOW")
    deep_external_action: str = Field(
        description="优化目标", default="AD_CONVERT_TYPE_LIVE_PURE_PAY_ROI")
    # multi_product_creative_list: list[multi_product_creative]
    aweme_item_id: list[int] = Field(description="视频id", default=[])
    ad_id: Optional[int] = Field(description="计划id", default=0)
    commercial_code: str = Field(
        description="合作码", default="")


class Opt_Status(str, Enum):
    DISABLE = "DISABLE"
    ENABLE = "ENABLE"
    DELETE = "DELETE"


class ad_status_update(BaseModel):
    advertiser_id: int = Field(
        description="advertiser_id", default=1779271778331655)
    # uid: str = Field(description="uid")
    ad_ids: list[int] = Field(description="计划")
    opt_status: Opt_Status = Field(description="更新投放计划状态")
    #     "advertiser_id": 1779271778331655,
    # "ad_ids": [1843475953536376],
    # "opt_status": "DISABLE"


@router.post('/create', summary='抖音计划创建', description='抖音计划创建，可自动获取账号下视频')
async def create_ad(ad: ad_create):
    # print('x')
    ad_data = {
        "advertiser_id": ad.advertiser_id,
        "name": ad.name,
        "aweme_id": ad.aweme_id,
        "marketing_goal": ad.marketing_goal,
        "product_ids": [ad.product_id],
        "delivery_setting": {
            "smart_bid_type": ad.smart_bid_type,
            "roi2_goal": ad.roi2_goal,
            "qcpx_mode": ad.qcpx_mode,
            "budget": ad.budget,
            "video_schedule_type": ad.video_schedule_type,
            "deep_external_action": ad.deep_external_action
        },
        "multi_product_creative_list": [
            {
                "product_id": ad.product_id,
            }
        ]
    }
    if ad.smart_bid_type == 'SMART_BID_CONSERVATIVE':
        ad_data['delivery_setting'].pop('roi2_goal')
    elif ad.smart_bid_type == 'SMART_BID_CUSTOM':
        if ad_data['delivery_setting'].get('budget') < 300:
            ad_data['delivery_setting']['budget'] = 300
    video_materials = await aweme_video_get_video_code(ad)

    # video_materials = [
    #     {
    #         "image_mode": "VIDEO_VERTICAL",
    #         "aweme_item_id": item_id
    #     } for item_id in ad.aweme_item_id
    # ]
    ad_data["multi_product_creative_list"][0].update(
        {'video_material': video_materials})
    logger.info(ad_data)
    # return ad_data
    try:
        response = qianchuan_api_service.invoke_qianchuan_api(
            api_name='CREATE_AD', method='post', payload=ad_data)
    except Exception as e:
        raise HTTPException(status_code=200, detail=f"{str(e)}")
    return response


@router.post('/update')
async def update_ad(ad: ad_create):
    # print('x')
    ad_data = {
        "advertiser_id": ad.advertiser_id,
        "ad_id": ad.ad_id,
        "name": ad.name,
        "aweme_id": ad.aweme_id,
        "marketing_goal": ad.marketing_goal,
        "product_ids": [ad.product_id],
        "delivery_setting": {
            "smart_bid_type": ad.smart_bid_type,
            "roi2_goal": ad.roi2_goal,
            "qcpx_mode": ad.qcpx_mode,
            "budget": ad.budget,
            "video_schedule_type": ad.video_schedule_type,
            "deep_external_action": ad.deep_external_action
        },
        "multi_product_creative_list": [
            {
                "product_id": ad.product_id,
            }
        ]
    }
    if ad.smart_bid_type == 'SMART_BID_CONSERVATIVE':
        ad_data['delivery_setting'].pop('roi2_goal')
    elif ad.smart_bid_type == 'SMART_BID_CUSTOM':
        if ad_data['delivery_setting'].get('budget') < 300:
            ad_data['delivery_setting']['budget'] = 300
    video_materials = await aweme_video_get_video_code(ad)

    # video_materials = [
    #     {
    #         "image_mode": "VIDEO_VERTICAL",
    #         "aweme_item_id": item_id
    #     } for item_id in ad.aweme_item_id
    # ]
    ad_data["multi_product_creative_list"][0].update(
        {'video_material': video_materials})
    logger.info(ad_data)
    # return ad_data
    try:
        response = qianchuan_api_service.invoke_qianchuan_api(
            api_name='UPDATA_AD', method='post', payload=ad_data)
    except Exception as e:
        raise HTTPException(status_code=200, detail=f"{str(e)}")
    return response


@router.post('/status/update')
async def update_ad_status(ad: ad_status_update):
    ad_data = {
        "advertiser_id": ad.advertiser_id,
        "ad_ids": ad.ad_ids,
        "opt_status": ad.opt_status.name
    }
    try:
        response = qianchuan_api_service.invoke_qianchuan_api(
            api_name='CHANGE_AD_STATUS', method='post', payload=ad_data)
    except Exception as e:
        raise HTTPException(status_code=200, detail=f"{str(e)}")
    print(response)
    return response


# material/add/

# important
@router.post('/material/add/', summary='计划自动添加素材|创建计划', description='需要广告id 达人uid（awemeid） 产品id')
async def material_add(ad: ad_create):

    # 方案a 自动获取item_id并且填充
    try:
        if not all([ad.advertiser_id, ad.aweme_id, ad.product_id]):
            raise HTTPException(
                status_code=400, detail='需要广告id | 达人uid（awemeid）| 产品id')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"业务错误{str(e)}")

    # 需要根据awemeid去找到计划id 如果有就看看有没有计划
    aweme_data = await Uni_aweme_list.filter(aweme_id=ad.aweme_id).first()
    # , has_authorized=True
    # print(aweme_data.aweme_id)
    # return reposen_model.BaseResponse(code=0, data='', message='计划创建成功')
    if aweme_data:
        pro_ad_data = await UniPromotionList.filter(account=ad.advertiser_id, status__in=["DELIVERY_OK"], marketing_goal="VIDEO_PROM_GOODS", product_id=ad.product_id, anchor_id=aweme_data.aweme_show_id).first()
        # 计划信息
        # pro_ad_data = None
        if pro_ad_data:  # 有计划就直接添加
            # video_material 可以通过aweme_video_get_video_code获取
            video_material = await aweme_video_get_video_code(ad)
            # print(video_material)
            ad_data = {
                "advertiser_id": ad.advertiser_id,
                "ad_id":  pro_ad_data.id,
                "multi_product_creative_list": [
                    {
                        "product_id": ad.product_id,
                        "video_material": video_material
                    }
                ]
            }
            try:
                response = qianchuan_api_service.invoke_qianchuan_api(
                    api_name='MATERIAL_ADD', method='post', payload=ad_data)
                return reposen_model.BaseResponse(code=0, data=response, message='素材更新成功')
            except Exception as e:
                raise HTTPException(status_code=200, detail=f"{str(e)}")

        else:
            # raise HTTPException(status_code=400, detail=f"没有找到计划")
            # 创建计划
            ad_default_setting = await AdPlacement.filter(product_id=ad.product_id).first()

            if ad_default_setting:
                ad.roi2_goal = ad_default_setting.roi
                ad.budget = float(ad_default_setting.budget)
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                ad.name = f'{date_str}_{aweme_data.aweme_name}_{ad_default_setting.product_name}'
                # 创建计划

                result = await create_ad(ad)
                # return result
                return reposen_model.BaseResponse(code=0, data=result, message='计划创建成功')
            else:
                logger.error(f'商品信息不存在,product_id为{ad.product_id}')
                raise HTTPException(
                    status_code=200, detail=f'商品信息不存在,product_id为{ad.product_id}')

    # 没有找到自动发起邀请
    else:
        awemeinfo = await Awemeinfo.filter(aweme_id=ad.aweme_id).first()
        if not awemeinfo:
            raise HTTPException(status_code=400, detail=f"没有找到达人且信息中无授权码")
        else:
            awame_params = app07.awame(
                uid=str(ad.aweme_id),
                commercial_code=awemeinfo.commercial_code,
                cooperation_type='',
                advertise_id=ad.advertiser_id
            )

            result = await app07.newawame(params=awame_params)
            # raise HTTPException(status_code=400, detail=f"没有找到达人")
            # return result
            return reposen_model.BaseResponse(code=0, data=result, message='发起授权中')
            # return newawame_data


@router.post('/video/aweme/get/', summary='抖音号下视频获取【完整版】', description='需要广告id 达人uid（awemeid） 产品id')
async def aweme_video_get(ad: ad_create):
    try:
        if not all([ad.advertiser_id, ad.aweme_id]):
            raise HTTPException(
                status_code=400, detail='需要广告id | 达人uid（awemeid）| 产品id')
        get_data = {
            "advertiser_id": ad.advertiser_id,
            "aweme_id": ad.aweme_id,
            # "filtering": {
            #     "product_id": ad.product_id
            # }
        }
        if ad.product_id:
            get_data['filtering'] = {  # type: ignore
                "product_id": ad.product_id
            }
        # logger.info(get_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"业务错误{str(e)}")

    try:
        response = qianchuan_api_service.invoke_qianchuan_api(
            api_name='AWEME_VIDEO_GET', method='get', params=get_data)
    except Exception as e:
        raise HTTPException(status_code=200, detail=f"{str(e)}")
    return response


@router.post('/video/aweme/get/video_code', summary='抖音号下视频获取【精简版】', description='需要广告id 达人uid（awemeid） 产品id')
async def aweme_video_get_video_code(ad: ad_create, list_or_dict: str = 'dict'):
    # list_or_dict = 'list'
    try:
        if not all([ad.advertiser_id, ad.aweme_id, ad.product_id]):
            raise HTTPException(
                status_code=400, detail='需要广告id | 达人uid（awemeid）| 产品id')
        get_data = {
            "advertiser_id": ad.advertiser_id,
            "aweme_id": ad.aweme_id,
            "filtering": {
                "product_id": ad.product_id
            }
        }
        logger.info(get_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"业务错误{str(e)}")
    try:
        response = qianchuan_api_service.invoke_qianchuan_api(
            api_name='AWEME_VIDEO_GET', method='get', params=get_data)
    except Exception as e:
        raise HTTPException(status_code=200, detail=f"{str(e)}")
    if response.get('code') == 0:
        video_code_list = [video.get('aweme_item_id') for video in response.get(
            'data', {}).get('video_list')]
        if list_or_dict == 'list':
            return video_code_list
        elif list_or_dict == 'dict':
            video_materials = [
                {
                    "image_mode": "VIDEO_VERTICAL",
                    "aweme_item_id": item_id
                } for item_id in video_code_list
            ]
            return video_materials
    # {
    #     "advertiser_id": 1779271778331655,
    #     "ad_ids": [1843475953536376],
    #     "opt_status": "DISABLE"
    # }
    # @router.get("/allaccount/{start_date}", description="获取数据库中账户列表", include_in_schema=False)
    # async def getaccount(start_date):
    #     print(start_date)
    #     # accountlists = await Shop_Data.filter(date__gte=start_date)
    #     # print(accountlists)
    #     # return accountlists
    # @router.get("/all_uni_taks/", description="获取所有全域计划")
    # async def get_all_uni_tasks(advertise_ids: list[int] = Query(..., description="账户ID列表")):
    #     accountlists = await UniPromotionList.filter(account_id__in=advertise_ids).values("marketing_goal", "id", "name", "anchor_name", "account_id", "account__advertiser_name")
    #     return accountlists
    # @router.get("/all_videos/{days}", description="获取近x天所有账户下视频库内容")
    # @async_timer
    # async def get_all_videos(days: int):
    #     current_date = date.today()
    #     advertise_lists = await AccountList.all().values("advertiser_id", "advertiser_name")
    #     if not advertise_lists:
    #         raise HTTPException(status_code=500, detail="数据库错误")
    #     success_count = 0
    #     success_advertise = []
    #     # advertise_lists=[{"advertiser_id":1770732564116488}]
    #     try:
    #         for advertise in advertise_lists:
    #             advertise_id = advertise.get("advertiser_id")
    #             advertiser_name = advertise.get("advertiser_name")
    #             # api
    #             api_name = "GET_QIANCHUAN_VIDEO"
    #             # 日志输出
    #             logger.info(f"advertiser_name:{advertiser_name} 正在获取 ")
    #             page = 1
    #             videolists = []
    #             while True:
    #                 request_params = {
    #                     "advertiser_id": advertise_id,
    #                     "filtering": {
    #                         "start_time": str(current_date-timedelta(days=int(days))),
    #                         "end_time": str(current_date)},
    #                     "page": page,
    #                     "page_size": 100}
    #                 data = qianchuan_api_service.invoke_qianchuan_api(
    #                     api_name, request_params)
    #                 # logging.info(request_params)
    #                 total_page = data.get("data").get(
    #                     "page_info").get("total_page")
    #                 videolist = data.get("data").get("list")
    #                 success_count += len(videolist)
    #                 videolists.append(videolist)
    #                 # total_page=1
    #                 # print(data)
    #                 if page >= total_page:
    #                     break
    #                 else:
    #                     page += 1
    #             logger.info(f"advertiser_name:{advertiser_name} 获取完毕")
    #             videolists_list = [
    #                 video for videolist in videolists for video in videolist]
    #             objects_to_create = []
    #             for fields in videolists_list:
    #                 # 💡 核心修复 1：处理 create_time
    #                 raw_time = fields.get("create_time")
    #                 if isinstance(raw_time, str):
    #                     try:
    #                         # 解析字符串并强制赋予时区
    #                         dt = datetime.strptime(raw_time.split('.')[
    #                                                0], '%Y-%m-%d %H:%M:%S')
    #                         fields["create_time"] = make_aware(dt)
    #                     except:
    #                         # 如果解析失败，给一个默认值或设为 None (前提是模型允许 null)
    #                         fields["create_time"] = now()
    #                 # 💡 核心修复 2：处理主键 ID
    #                 # 既然模型定义 id 是 CharField(pk=True)，确保 fields 里有 'id' 且不为 None
    #                 if not fields.get("id"):
    #                     continue  # 跳过没有 ID 的非法数据
    #                 # 💡 核心修复 3：移除 account 相关的干扰项
    #                 # 如果 fields 里已经有 account_id 字符串，删掉它，使用下面传入的对象
    #                 fields.pop('account', None)
    #                 # 构建对象
    #                 obj = VideoList(**fields, account=account)
    #                 objects_to_create.append(obj)
    #             account = await AccountList.get_or_none(advertiser_id=advertise_id)
    #             def json_serial(obj):
    #                 from datetime import datetime, date
    #                 if isinstance(obj, (datetime, date)):
    #                     return obj.isoformat()
    #                 raise TypeError(f"Type {type(obj)} not serializable")
    #             import json
    #             with open('x.json', 'w', encoding='utf-8') as f:
    #                 json.dump(
    #                     videolists_list,
    #                     f,
    #                     ensure_ascii=False,
    #                     indent=4,         # 加上缩进，方便你用肉眼看
    #                     default=json_serial  # 关键：告诉 JSON 遇到时间怎么办
    #                 )
    #             objects_to_create = [
    #                 VideoList(** fields, account=account)
    #                 for fields in videolists_list
    #             ]
    #             await VideoList.bulk_create(objects_to_create, ignore_conflicts=True)
    #             success_advertise.append(advertise)
    #     except Exception as e:
    #         logger.error(f"发生意外错误：{e}")
    #     # with open("response.json","w",encoding="utf-8") as f:
    #     #      f.write(json.dumps(videolists_list, indent=2, ensure_ascii=False))
    #     return {"success_count": success_count, "success_advertise": success_advertise}
    # @router.get("/all_reject_reason", description="获取所有账户下审核建议")
    # @async_timer
    # async def all_reject_reason():
    #     advertise_lists = await AccountList.all().values("advertiser_id", "advertiser_name")
    #     if not advertise_lists:
    #         raise HTTPException(status_code=404, detail=f"数据库错误")
    #     success_count = 0
    #     success_advertise = []
    #     reason_lists = []
    #     reason_lists_all = []
    #     for advertise in advertise_lists:
    #         advertise_id = advertise.get("advertiser_id")
    #         uni_list = await UniPromotionList.filter(account_id=advertise_id).all().values("id")
    #         # print(uni_list)
    #         if not uni_list:
    #             continue
    #         for uni in uni_list:
    #             plan_id = uni.get("id")  # 获取计划id
    #             # 预先将所有modedify 设置为true
    #             # await AuditSuggestion.filter(account=advertise_id,uni_id=plan_id).update(modify=True)
    #             # print(id)
    #             api_name = "GET_UNI_PROMOTION_REJECT_REASON"
    #             page = 1
    #             while True:
    #                 request_params = {
    #                     "advertiser_id": advertise_id,
    #                     "ad_id": plan_id,
    #                     "page": page,
    #                     "page_size": 100}
    #                 data = qianchuan_api_service.invoke_qianchuan_api(
    #                     api_name, request_params)
    #                 total_page = data.get("data").get(
    #                     "page_info").get("total_page")
    #                 reason_list = data.get("data").get("list")
    #                 success_count += len(reason_list)
    #                 if page >= total_page:
    #                     break
    #                 else:
    #                     page += 1
    #             if reason_list:
    #                 success_count += len(reason_list)
    #                 reason_lists.append(reason_list)
    #                 account = await AccountList.get_or_none(advertiser_id=advertise_id)
    #                 uni_id = await UniPromotionList.get_or_none(id=plan_id)
    #                 for reason in reason_list:
    #                     material_id = reason.get("material_id", None)
    #                     if material_id:
    #                         video_material_id = await VideoList.get_or_none(material_id=material_id, account_id=advertise_id)
    #                     else:
    #                         video_material_id = None
    #                     audit_data = {
    #                         # 核心审核字段（从 reason 提取，设默认值避免 None）
    #                         "audit_platform": reason.get("audit_platform", ""),
    #                         "audit_reason": reason.get("audit_reason", []),
    #                         "desc": reason.get("desc", "视频"),
    #                         "material_id": material_id,
    #                         "image_material": reason.get("image_material", {}),
    #                         "video_material": reason.get("video_material", {}),
    #                         "is_aweme_video_title": reason.get("is_aweme_video_title"),
    #                         "product_id": reason.get("product_id"),
    #                         "related_video_material_id": reason.get("related_video_material_id"),
    #                         # 外键字段（仅传实例或 None）
    #                         "account": account,
    #                         "uni_id": uni_id,  # 已确保是实例或 None
    #                         # 普通字段（整数类型，直接传）
    #                         "video_material_id": video_material_id,
    #                         "modedify": False
    #                     }
    #                     # print(audit_data)
    #                     # await AuditSuggestion.create(** audit_data)
    #                     try:
    #                         await AuditSuggestion.create(** audit_data)
    #                     except IntegrityError as e:
    #                         if "Duplicate entry" in str(e):
    #                             logger.info(
    #                                 f"跳过重复记录: {audit_data.get('uid')} 和 {audit_data.get('account')}")
    #                         else:
    #                             raise
    #             logger.info(f"advertise_id:{advertise_id}下计划{plan_id}处理完毕")
    #         success_advertise.append(advertise)
    #         # video_material_id = await AccountList.get_or_none(advertiser_id=advertise_id)
    #         # objects_to_create = [
    #         #     VideoList(** fields, account=account)
    #         #     for fields in videolists_list
    #         # ]
    #         # await VideoList.bulk_create(objects_to_create,ignore_conflicts=True)
    #         # success_advertise.append(advertise)
    #         # reason_lists=[reson for reason_list in reason_lists for reson in reason_list]
    #     return {"code": 0, "data":
    #             {"success_advertise": success_advertise,
    #              "success_count": success_count}}
    # @router.get("/test")
    # async def test():
    #     from datetime import date, timedelta
    #     current_date = date.today()
    #     request = {
    #         "start_time": str(current_date-timedelta(days=7))+" 00:00:00",
    #         "end_time": str(current_date)+" 23:59:59"}
    #     return request

    # 全域商品计划创建


@router.post('/aweme/auto', summary='计划自动添加素材|创建计划', description='需要广告id 达人uid（awemeid） 产品id', include_in_schema=False)
async def aweme_auto(ad: ad_create):
    # 先判断有没有 如果没有计划就先创建
    try:
        if not all([ad.advertiser_id, ad.aweme_id, ad.product_id]):
            raise HTTPException(
                status_code=400, detail='需要广告id | 达人uid（awemeid）| 产品id')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"业务错误{str(e)}")

    # 需要根据awemeid去找到计划id
    aweme_data = await Uni_aweme_list.filter(aweme_id=ad.aweme_id).first()
    # print(aweme_data.aweme_id)
    if aweme_data:
        pro_ad_data = await UniPromotionList.filter(account=ad.advertiser_id, status__in=["DELIVERY_OK"], marketing_goal="VIDEO_PROM_GOODS", product_id=ad.product_id, anchor_id=aweme_data.aweme_show_id).first()
        # values("account__advertiser_id", "anchor_id", "status", 'id')

    else:
        # 自动开始
        raise HTTPException(status_code=400, detail=f"没有找到达人")
    if pro_ad_data:
        # return result
        # video_material 可以通过aweme_video_get_video_code获取
        video_material = await aweme_video_get_video_code(ad)
        # print(video_material)
        ad_data = {
            "advertiser_id": ad.advertiser_id,
            "ad_id":  pro_ad_data.id,
            "multi_product_creative_list": [
                {
                    "product_id": ad.product_id,
                    "video_material": video_material
                }
            ]
        }
        try:
            response = qianchuan_api_service.invoke_qianchuan_api(
                api_name='MATERIAL_ADD', method='post', payload=ad_data)
        except Exception as e:
            raise HTTPException(status_code=200, detail=f"{str(e)}")
    else:
        # raise HTTPException(status_code=400, detail=f"没有找到计划")
        # 先看看
        # 系统中没有计划就需要创建了
        pass

    return response


@router.post('/conversion', summary='计划自动放量', description='需要计划id', include_in_schema=True)
async def ad_convert(adlist: list[int]):
    for ad_id in adlist:

        unipro = await UniPromotionList.filter(id=ad_id, status='DELIVERY_OK').first()
        # unipro2 = await UniPromotionList.filter(id=ad_id, status='DELIVERY_OK').first()
        if unipro:
            # 先关闭计划
            ad = ad_status_update(
                advertiser_id=getattr(unipro, "account_id"),
                ad_ids=[unipro.id],
                opt_status=Opt_Status.DISABLE
            )
            # print('ad_id', ad_id, 'unipro.id', unipro.id, "name", unipro.name)
            # print(ad.model_dump())
            try:
                result = await update_ad_status(ad)
                print(result)
                logger.info(f'计划：{ad_id}已关闭')
            except:
                pass
            #

            # 获取计划详细信息
            ad_detail = await get_ad_datail(ad_id)
            smart_bid_type = ad_detail.get('data', {}).get(
                'delivery_setting').get('smart_bid_type')
            product_id = ad_detail.get('data', {}).get(
                'multi_product_creative_list')[0].get('product_id')
            name = ad_detail.get('data', {}).get(
                'name')
            aweme_id = ad_detail.get('data', {}).get(
                'aweme_id')
            # 查询anchor_id
            awmem_data = await Uni_aweme_list.filter(aweme_id=aweme_id).first()
            if awmem_data:
                # 查询有没有放量计划
                unipro2 = await UniPromotionList.filter(status='SYSTEM_DISABLE', product_id=product_id, anchor_id=awmem_data.aweme_show_id).first()
                if unipro2:
                    # print(unipro2.id)
                    logger.info('计划已经存在')
                    ad = ad_status_update(
                        advertiser_id=getattr(unipro2, "account_id"),
                        ad_ids=[unipro2.id],
                        opt_status=Opt_Status.ENABLE
                    )
                    try:
                        result = await update_ad_status(ad)
                        logger.info(f'计划：{ad_id}已启动')
                    except:
                        pass
                else:
                    if smart_bid_type == "SMART_BID_CUSTOM":
                        smart_bid_type_new = "SMART_BID_CONSERVATIVE"
                    else:
                        smart_bid_type_new = "SMART_BID_CUSTOM"
                    logger.info(
                        f'目前计划为{smart_bid_type}计划开始创建{smart_bid_type_new}计划')
                    ad = ad_create()
                    ad.budget = float(300)
                    ad.smart_bid_type = smart_bid_type_new
                    ad.product_id = product_id
                    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                    ad.name = name+f'({date_str} 转投放量)'
                    ad.aweme_id = aweme_id
                    ad.ad_id = ad_id
                    # ad.name = f'{date_str}_{aweme_data.aweme_name}_{ad_default_setting.product_name}'
                    # 创建计划

                    result = await create_ad(ad)

                    print(result)
                    return result

            return ad_detail

            # return ad.model_dump()
            # result = await app07.newawame(params=awame_params)
        # print(unipro.anchor_name)
        else:
            pass
    return adlist
    # 自动转换
    pass


@router.post('/ad_datail', summary='获取计划详细信息', description='')
async def get_ad_datail(ad_id: int):
    # ad_data = {
    #     "advertiser_id": ad.advertiser_id,
    #     "ad_ids": ad.ad_ids,
    #     "opt_status": ad.opt_status.name
    # }
    unipro = await UniPromotionList.filter(id=ad_id).first()
    if unipro:
        params = {
            'ad_id': ad_id,
            'advertiser_id': getattr(unipro, "account_id"),
        }
        try:
            response = qianchuan_api_service.invoke_qianchuan_api(
                api_name='AD_DETAIL', method='get', params=params)
        except Exception as e:
            raise HTTPException(status_code=200, detail=f"{str(e)}")
        return response
    else:
        return
