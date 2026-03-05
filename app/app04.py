from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import os
from pydantic import BaseModel, Field
import asyncio
import functools
import json
from loguru import logger
import time
from orm.models import AccountList
from type import reposen_model
from typing import Any, Awaitable, Callable, List, Optional, Union
from tortoise import timezone
# 第三方库导入
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, ValidationError, field_validator
from tortoise.exceptions import IntegrityError, DoesNotExist

# 本地模块导入（按字母顺序分组）
from orm.models import *  # 建议明确导入所需模型，避免通配符
from utils import (shop_data_upload, qianchuan_api_service,
                   AudienceAsset_compute)
from utils.uni_data_models_new import *  # 同上，建议明确导入


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
            result['data']["execution_time"] = f"{execution_time} 秒"

        return result
    return wrapper


router = APIRouter()


@router.get("/list/{cc_account_id}", description="更新账户列表 默认cc:1668495993519111")
async def getaccountlist(cc_account_id: int):
    page = 1
    page_size = 100
    request_params = {
        "page": page,
        "page_size": page_size,
        "cc_account_id": cc_account_id,
        "account_source": "QIANCHUAN",  # 新增参数
        "filtering": {"account_name": ""}  # 新增参数
    }
    api_name = "GET_ADVERTISER_LIST"
    data = qianchuan_api_service.invoke_qianchuan_api(api_name, request_params)
    print(data)
    accountLists = data.get("data", {}).get("list")

    await AccountList.bulk_create([AccountList(**data) for data in accountLists], ignore_conflicts=True)

    # return {"code": 200, "detail": f"{len(accountLists)}条内容已更新", "accountLists": accountLists}
    return reposen_model.BaseResponse(
        code=0,
        data={
            "accountLists": accountLists,
            "succuss_count": len(accountLists)
        },
        message="请求成功"
    )


@router.get("/allaccount", description="获取数据库中账户列表")
async def getaccount():
    accountlists = await AccountList.all().values()
    # return accountlists
    return reposen_model.BaseResponse(
        code=0,
        data={
            "accountLists": accountlists,
            # "succuss_count": len(accountLists)
        },
        message="请求成功"
    )


@router.get("/uni_task", description="获取全域计划")
# @qps_limiter(200)
async def get_uni_task():

    data_now = datetime.now().date()
    accountlists = await AccountList.all()
    success_advertise = []
    if accountlists:
        for accountlist in accountlists:
            # logger.info(accountlist.advertiser_id)z
            ADVERTISER_ID = accountlist.advertiser_id
            START_TIME = str(data_now-timedelta(days=10))+" 00:00:00"
            END_TIME = str(data_now)+" 23:59:59"
            FIELDS = ["stat_cost"]

            # time.sleep(1)
            await UniPromotionList.filter(
                account_id=ADVERTISER_ID
            ).delete()
            marketing_goals = ["LIVE_PROM_GOODS", "VIDEO_PROM_GOODS"]
            for marketing_goal in marketing_goals:
                MARKETING_GOAL = marketing_goal
                page = 1
                total_page = 1
                while page <= total_page:
                    request_params = {
                        "advertiser_id": ADVERTISER_ID,
                        "start_time": START_TIME,
                        "end_time": END_TIME,
                        "marketing_goal": MARKETING_GOAL,
                        "fields": FIELDS,
                        "page": page,
                        "page_size": 100}
                    api_name = "GET_UNIFIED_PROMOTION"
                    data = qianchuan_api_service.invoke_qianchuan_api(
                        api_name, request_params)
                    page += 1
                    try:
                        total_page = data.get('data', {}).get(
                            'page_info').get('total_page')
                    except:
                        total_page = 1

                    print(request_params, data)
                    ad_lists = data.get("data", {}).get("ad_list", [])

                    # 关键修改：提前查询账户实例
                    account = await AccountList.get_or_none(advertiser_id=ADVERTISER_ID)
                    if not account:
                        logger.error(f"账户 {ADVERTISER_ID} 不存在")
                        raise HTTPException(
                            status_code=404, detail=f"账户 {ADVERTISER_ID} 不存在")
                    # 删除之前的计划

                    for ad_list in ad_lists:
                        ad_info = ad_list.get("ad_info")
                        if ad_list.get("product_info"):
                            product_info = ad_list.get("product_info")[0]
                        else:
                            product_info = {}
                        if ad_list.get("room_info"):
                            room_info = ad_list.get("room_info")[0]
                        else:
                            room_info = {}

                        # 明确字段映射关系（从API数据到模型字段）
                        model_fields = {
                            "id": ad_info.get("id"),
                            "name": ad_info.get("name"),
                            "marketing_goal": ad_info.get("marketing_goal"),
                            "roi2_goal": ad_info.get("roi2_goal"),
                            "status": ad_info.get("status"),
                            "start_time": ad_info.get("start_time"),
                            "product_id": product_info.get("product_id"),
                            "product_name": product_info.get("product_name"),
                            "product_image": product_info.get("product_image"),
                            "anchor_id": room_info.get("anchor_id"),
                            "anchor_name": room_info.get("anchor_name"),
                            "anchor_avatar": room_info.get("anchor_avatar"),
                            "budget": ad_info.get("budget")
                        }
                        # logger.info(model_fields)
                        # 验证必填字段
                        # logger.info(model_fields)
                        if not model_fields["id"]:
                            logger.info(f"警告：计划ID缺失，跳过记录")
                            continue

                        # try:
                        #     # 创建记录（直接传递参数，而非嵌套实例化）
                        #     await UniPromotionList.create(
                        #         **model_fields,
                        #         account=account,created_at=str(data_now)  # 关联账户实例
                        #     )
                        #     logger.info(f"成功创建计划 {model_fields['id']}")
                        # except Exception as e:
                        #     logger.info(f"创建计划失败：{str(e)}")
                        #     # 可以选择记录错误并继续处理其他计划
                        try:
                            # 尝试获取已存在的计划（按id查询，id是唯一标识）
                            plan_instance = await UniPromotionList.get(id=model_fields['id'])
                            # 如果存在则更新字段
                            # 保留原有字段处理逻辑，增加更新操作
                            update_data = {**model_fields,
                                           'account': account,
                                           'created_at': str(data_now)
                                           }

                            # 更新实例字段
                            plan_instance.update_from_dict(update_data)
                            await plan_instance.save()
                            logger.info(f"成功更新计划 {model_fields['id']}")

                        except DoesNotExist:
                            # 如果不存在则创建新计划（保留原有创建逻辑）
                            try:
                                await UniPromotionList.create(
                                    **model_fields,
                                    account=account,
                                    created_at=str(data_now)  # 关联账户实例
                                )
                                logger.info(f"成功创建计划 {model_fields['id']}")
                            except Exception as e:
                                logger.error(f"创建计划失败：{str(e)}")
                        except Exception as e:
                            # 处理其他可能的异常
                            logger.error(
                                f"处理计划 {model_fields.get('id')} 时出错：{str(e)}")

                success_advertise.append(accountlist.advertiser_id)

        return reposen_model.BaseResponse(
            code=0,
            data={
                "success_advertise": success_advertise
                # "succuss_count": len(accountLists)
            },
            message="请求成功"
        )


@router.get("/aweme_lists/one/{advertiser_id}", description="获取单个千川账户下可投广抖音号", summary="获取特定账户下抖音号", include_in_schema=True)
async def get_aweme_lists(advertiser_id: int):
    # 验证账户存在性
    account = await AccountList.get_or_none(advertiser_id=advertiser_id)

    if not account:
        raise HTTPException(status_code=404, detail=f"账户 {advertiser_id} 不存在")

    # 提前删除
    await Uni_aweme_list.filter(account_id=advertiser_id).delete()
    # 初始化

    page, total_page = 1, 1
    model_fields_list = []
    while page <= total_page:
        request_params = {
            "advertiser_id": advertiser_id,
            "page": page,
            "page_size": 100
        }

        api_name = "GET_AUTHORIZED_AWEME"
        response = qianchuan_api_service.invoke_qianchuan_api(
            api_name, request_params)

        try:
            total_page = response.get('data', {}).get(
                'page_info').get('total_page')

        except:
            total_page = 1
        # 更简洁直观，直接在字符串中嵌入变量
        logger.info(
            f"获取抖音号列表 - advertiser_id: {advertiser_id}, 当前页: {page}, 总页数: {total_page}")
        page += 1
        if response:
            aweme_id_lists = response.get("data", {}).get("aweme_id_list", [])
            for aweme_item in aweme_id_lists:
                # 处理auth_type，避免索引错误
                auth_type_list = aweme_item.get("auth_type", [])
                auth_type = auth_type_list[0] if auth_type_list else None

                # 处理布尔值转为字符串（与模型CharField匹配）
                is_aweme_c = aweme_item.get("is_aweme_c", False)
                is_aweme_c_str = "是" if is_aweme_c else "否"  # 转为中文或"true"/"false"

                model_fields = {
                    "aweme_avatar": aweme_item.get("aweme_avatar"),
                    "aweme_name": aweme_item.get("aweme_name"),
                    "aweme_id": aweme_item.get("aweme_id"),
                    "auth_type": auth_type,
                    "is_aweme_c": is_aweme_c_str,  # 存入字符串
                    "has_authorized": aweme_item.get("has_authorized"),
                    "has_shop_permission": aweme_item.get("has_shop_permission"),
                    "has_live_permission": aweme_item.get("has_live_permission"),
                    "has_roi2_group_created": aweme_item.get("has_roi2_group_created"),
                    "anchor_forbidden": aweme_item.get("anchor_forbidden"),
                    "is_allow_mall": aweme_item.get("is_allow_mall"),
                    "aweme_show_id": aweme_item.get("aweme_show_id")
                }
                model_fields_list.append(model_fields)

    logger.info(model_fields_list)
    # 批量创建并处理重复数据
    success_count = 0
    failed_records = []
    if model_fields_list:
        # 先过滤掉aweme_id为空的无效数据
        valid_fields = [f for f in model_fields_list if f.get(
            "aweme_id") is not None]
        if not valid_fields:
            return {"message": "无有效抖音号数据", "response": response}

        try:
            # 批量创建（如果无重复数据，效率更高）
            objects_to_create = [
                Uni_aweme_list(** fields, account=account)
                for fields in valid_fields
            ]
            await Uni_aweme_list.bulk_create(objects_to_create)
            success_count = len(valid_fields)
        except IntegrityError:
            # 有重复数据时，逐个创建并跳过重复项
            for fields in valid_fields:
                try:
                    # 用get_or_create确保重复数据只创建一次
                    await Uni_aweme_list.get_or_create(
                        defaults={**fields, "account": account},
                        aweme_id=fields["aweme_id"]  # 以aweme_id为唯一标识
                    )
                    success_count += 1
                except Exception as e:
                    failed_records.append({
                        "aweme_id": fields["aweme_id"],
                        "error": str(e)
                    })

    return reposen_model.BaseResponse(
        code=0,
        data={
            "total": len(model_fields_list),
            "success": success_count,
            "failed": len(failed_records),
            "failed_details": failed_records,
            "response": response
        },
        message="请求成功"
    )


@router.get("/aweme_lists/all/", description="获取所有千川账户下可投广抖音号", summary="获取所有账户下抖音号")
@async_timer
async def get_aweme_lists_all():

    account_list = await AccountList.all().values()
    if not account_list:
        raise HTTPException(status_code=404, detail="无账户数据")
    advertiser_id_lists: list[int] = []

    for account in account_list:
        # 1. 提取 advertiser_id 并检查是否为整数
        adv_id = account.get("advertiser_id") if isinstance(
            account, dict) else getattr(account, "advertiser_id", None)

        if isinstance(adv_id, int):
            advertiser_id_lists.append(adv_id)
        else:
            logger.info(f"无效的 advertiser_id: {adv_id}")

    total = len(advertiser_id_lists)
    success_count = 0
    failed_records = []

    # 2. 调用单个账户接口时确保参数有效
    for advertiser_id in advertiser_id_lists:
        time.sleep(0.5)
        try:
            # 此时 advertiser_id 一定是 int 类型，符合函数要求
            await get_aweme_lists(advertiser_id)
            success_count += 1
        except Exception as e:
            failed_records.append({
                "advertiser_id": advertiser_id,
                "error": str(e)
            })

    return reposen_model.BaseResponse(
        code=0,
        data={
            "total_accounts": total,
            "success": success_count,
            "failed": len(failed_records),
            "failed_details": failed_records
        },
        message="请求成功"
    )


class Uni_data(BaseModel):
    advertiser_id: Optional[int] = Field(None, description="广告主ID")
    # 明确指定日期时间格式
    start_time: date = Field(..., description="开始时间，格式: YYYY-MM-DD")
    end_time: date = Field(..., description="结束时间，格式: YYYY-MM-DD")


@router.get("/uni_data_self/one/", description="获取单个千川账户下投放数据", summary="获取单个千川账户下投放数据")
@async_timer
async def get_uni_data_one(params: Uni_data = Query(...)):
    advertiser_id = params.advertiser_id
    DATA_TOPIC_CLASSES_haslive = [
        SITE_PROMOTION_POST_DATA_VIDEO,
        SITE_PROMOTION_POST_DATA_LIVE,
        SITE_PROMOTION_POST_DATA_OTHER,
        SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE,
        SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO,
        SITE_PROMOTION_PRODUCT_POST_DATA_OTHER,
        ROI2_IMAGE_AGG_MATERIAL_ANALYSIS
    ]
    DATA_TOPIC_CLASSES_nolive = [

        SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE,
        SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO,
        SITE_PROMOTION_PRODUCT_POST_DATA_OTHER
    ]
    unilists = await UniPromotionList.filter(account=params.advertiser_id, status__in=["DELIVERY_OK", "DISABLE", "ROME_OFF"], marketing_goal="LIVE_PROM_GOODS").values("account__advertiser_id", "anchor_id", "status")
    # unilists = await UniPromotionList.filter(account_id=params.advertiser_id, status__in=["DELIVERY_OK"], marketing_goal="LIVE_PROM_GOODS").values("account__advertiser_id", "anchor_id", "status")
    # aweme_lists=await Uni_aweme_list.filter(account_id=params.advertiser_id,).all()
    # 先查全域推广状态
    # print("unilists")
    logger.info(f"unilists:: {unilists}")

    if not unilists:
        raise HTTPException(
            status_code=404, detail=f"账户 {params.advertiser_id}下无全域在投达人")
    success_count = 0
    for unilist in unilists:
        # logger.info(f"unilist:{unilist}")
        anchor_id = unilist.get("anchor_id", None)
        # logger.info(anchor_id)
        aweme_lists = await Uni_aweme_list.filter(account_id=params.advertiser_id, aweme_show_id=anchor_id).values("aweme_id", "has_roi2_group_created")
        # aweme_lists=[{'aweme_id': 2013936617539725, 'has_roi2_group_created': 'True'}]
        # 05户1773009188090892
        if not aweme_lists:
            DATA_TOPIC_CLASSES_S = DATA_TOPIC_CLASSES_nolive
        elif aweme_lists[0].get("has_roi2_group_created", False):
            DATA_TOPIC_CLASSES_S = DATA_TOPIC_CLASSES_haslive
        else:
            DATA_TOPIC_CLASSES_S = DATA_TOPIC_CLASSES_nolive
        # logger.info(1)
        for DATA_TOPIC_CLASSES in DATA_TOPIC_CLASSES_S:

            for aweme_list in aweme_lists:
                page = 1
                datalists = []
                # 获取
                while True:

                    anchor_id = aweme_list.get("aweme_id", False)
                    getdata = DATA_TOPIC_CLASSES(anchor_id=str(anchor_id))
                    data_topic = getdata.data_topic
                    dimensions = getdata.dimensions
                    metrics = getdata.metrics
                    order_by = getdata.order_by
                    filters = getdata.filters
                    request_params = {
                        "advertiser_id": advertiser_id,
                        "data_topic": data_topic,
                        "dimensions": dimensions,  #
                        "metrics": metrics,        #

                        "filters": filters,
                        "start_time": str(params.start_time)+" 00:00:00",
                        "end_time": str(params.end_time)+" 23:59:59",
                        "order_by": order_by,
                        "page": page,
                        "page_size": 100
                    }

                    # logger.info(request_params)

                    time.sleep(0.0025)
                    # logger.info(request_params)

                    api_name = "GET_UNI_PROMOTION_DATA"
                    response = qianchuan_api_service.invoke_qianchuan_api(
                        api_name, request_params)
                    # logger.info("response",response)
                    # print(response)
                    # data,total_page=getdata.resolvedata(response)
                    try:
                        data, total_page = getdata.resolvedata(response)
                        print(data, total_page)
                    except Exception as e:
                        logger.info(
                            f"错误原因{e} api_name:{api_name}, request_params :{request_params}")
                    # logger.info(request_params,data)
                    logger.info(
                        f"data_topic:{data_topic}\n total_page:{total_page},page:{page}")
                    # total_page = 2
                    datalists.append(data)
                    if page >= total_page:
                        break
                    else:
                        page += 1
                # 存储
                # with open("tests.txt", "w", encoding="utf-8") as f:
                #     for data in datalists:
                #         f.write(str(data))
                new_datalist = [
                    data for datalist in datalists for data in datalist]
                # 外键
                print(new_datalist)

                # return
                account = await AccountList.get_or_none(advertiser_id=advertiser_id)
                aweme = await Uni_aweme_list.get_or_none(aweme_id=anchor_id, account_id=advertiser_id)
                # logger.info(advertiser_id,anchor_id,aweme)
                objects_to_create = [
                    Uni_data_clip(** fields, account=account,
                                  aweme=aweme, created_at=datetime.now())
                    for fields in new_datalist
                ]
                await Uni_data_clip.bulk_create(objects_to_create, ignore_conflicts=True)
                success_count += len(new_datalist)

    return reposen_model.BaseResponse(
        code=0,
        data={
            "success_count": success_count,
            "advertiser_id": advertiser_id
        },
        message="请求成功"
    )


async def get_one_finance_def(advertise_id: int, start_date: str, end_date: str):
    # 校验account
    now_naive = datetime.now().replace(tzinfo=None)
    account = await AccountList.get_or_none(advertiser_id=advertise_id)
    if not account:
        logger.error(f"账户 {advertise_id} 不存在")
        raise HTTPException(status_code=404, detail=f"账户 {advertise_id} 不存在")

    page = 1
    finance_lists = []
    while True:
        request_params = {
            "advertiser_id": advertise_id,
            "start_date": start_date,
            "end_date": end_date,
            "page": page,
            "page_size": 100
        }
        api_name = "GET_FINANCE_DETAIL"
        data = qianchuan_api_service.invoke_qianchuan_api(
            api_name, request_params)

        totalt_page = data.get("data", {}).get(
            "page_info").get("total_page", 0)
        logger.info(
            f"项目:getfaniinall,advertise_id:{advertise_id} page:{page} totalt_page:{totalt_page}")
        for raw_data in data.get("data", {}).get("list", []):
            processed_data = {
                key: value /
                100000 if isinstance(value, (int, float)) else value
                for key, value in raw_data.items()}
            finance_lists.append(processed_data)
            # logger.info(processed_data)
        if totalt_page >= page:
            break
        else:
            page += 1
            time.sleep(0.2)  # 休息器

    # 写入
    objects_to_create = [
        FinanceData(** fields, account=account,
                    created_at=timezone.now())
        for fields in finance_lists
    ]
    for i in objects_to_create:
        print(now_naive)
    await FinanceData.bulk_create(objects_to_create, ignore_conflicts=True)
    # logger.info(advertise_id,"写入成功")

    return finance_lists


@router.get("/finance/detail/one", summary="获取单个账户下财务数据")
async def get_one_finance(params: Uni_data = Query(...)):

    advertise_id = params.advertiser_id
    if not isinstance(advertise_id, (int)):
        logger.error(f" advertise_id 必须输入")
        raise HTTPException(status_code=404, detail=f" advertise_id 必须输入")
    start_date = str(params.start_time)
    end_date = str(params.end_time)

    # 执行
    finance_lists = await get_one_finance_def(advertise_id, start_date, end_date)
    return reposen_model.BaseResponse(
        code=0,
        data={

            "finance_lists": finance_lists
        },
        message="请求成功"
    )


@router.get("/finance/detail/all", summary="获取所有账户下财务数据")
@async_timer
async def get_all_finance(params: Uni_data = Query(...)):
    account = await AccountList.all().values("advertiser_id")
    # logger.info(type(account))
    if not account:
        logger.error(f"accout错误")
        raise HTTPException(status_code=500, detail=f"accout错误")
    start_date = str(params.start_time)
    end_date = str(params.end_time)

    for account_list in account:
        advertise_id: int = account_list.get("advertiser_id", 0)
        await get_one_finance_def(advertise_id, start_date, end_date)  # 执行
        # logger.info(advertise_id)
    # return {"message": f"{len(account)}个账户写入成功", "detail": account}
    return reposen_model.BaseResponse(
        code=0,
        data={
            "finance_lists": account,
            "success_count": len(account)
        },
        message="请求成功"
    )


@router.post("/upload/shop_data/multi/{awemeid}", summary="上传商品数据", description="个护:2013936617539725,官方:2770421951518669")
@async_timer
async def upload_shop_data(awemeid: int, uploadfiles_s: List[UploadFile]):
    # 验证awemeid
    VALID_AWEMEIDS = {
        2013936617539725: ["个护", "个人"],
        2770421951518669: ["真不二官方", "官旗"]
    }

    if awemeid not in VALID_AWEMEIDS:  # 仅验证键
        raise HTTPException(
            status_code=400, detail=f"awemeid:{awemeid}不存在或不被支持")

    # 配置参数
    BASE_PATH = "static/shop_file"
    ALLOWED_EXTENSIONS = {'.csv', '.xlsx'}
    required_keywords = VALID_AWEMEIDS[awemeid]

    results = []
    errors = []
    t1 = time.perf_counter()
    # 确保目录存在
    os.makedirs(BASE_PATH, exist_ok=True)

    async def process_file(upload_file: UploadFile):
        """处理单个文件的辅助函数"""
        try:
            # 安全处理文件名
            safe_filename = Path(upload_file.filename).name
            file_name, file_ext = os.path.splitext(safe_filename)

            # 验证文件扩展名
            if file_ext.lower() not in ALLOWED_EXTENSIONS:
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": f"不支持的文件类型，只支持{ALLOWED_EXTENSIONS}"
                }

            # 验证文件名包含所需关键词
            if not any(keyword in file_name for keyword in required_keywords):
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": f"文件名必须包含以下关键词之一: {required_keywords}"
                }

            # 构建带时间戳的文件路径
            timestamp = datetime.now().strftime('%Y%m%d')
            file_path = os.path.join(
                BASE_PATH, f"{file_name}_{awemeid}_{timestamp}{file_ext}")

            # 检查文件是否已存在
            if os.path.exists(file_path):
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": "文件已存在"
                }

            # 保存文件
            try:
                with open(file_path, "wb") as f:
                    content = await upload_file.read()
                    f.write(content)
            except Exception as e:
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": f"文件保存失败: {str(e)}"
                }
            t2 = time.perf_counter()

            logger.info(f"{file_name}保存成功,时间为{round(t2-t1, 2)}")
            # 处理文件内容
            try:
                shop_data_lists = shop_data_upload.shop_data(file_path)
            except Exception as e:
                os.remove(file_path)  # 删除无效文件
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": f"文件内容解析失败: {str(e)}"
                }
            t3 = time.perf_counter()

            logger.info(f"解析成功,时间为{round(t3-t2, 2)}")
            # 批量写入数据库
            try:
                objects_to_create = [
                    Shop_Data(**fields, shop_account=awemeid,
                              created_at=datetime.now())
                    for fields in shop_data_lists
                ]
                await Shop_Data.bulk_create(objects_to_create, ignore_conflicts=True)

                t4 = time.perf_counter()
                logger.info(f"{file_name}导入到数据库成功,时间为{round(t4-t3, 2)}")

                # logger.info(f"解析成功")
            except Exception as e:
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": f"数据库写入失败: {str(e)}"
                }

            return {
                "filename": safe_filename,
                "status": "success",
                "message": "上传并处理成功"
            }

        finally:
            await upload_file.close()

    # 处理所有文件
    for upload_file in uploadfiles_s:
        result = await process_file(upload_file)
        if result["status"] == "success":
            results.append(result)
        else:
            errors.append(result)

    return reposen_model.BaseResponse(
        code=0,
        data={
            "success": results,
            "errors": errors
        },
        message="请求成功"
    )


@router.post("/upload/shop_data/multi/audience_assets/", summary="上传5a人群", description="上传5a人群")
@async_timer
async def upload_audience_data(uploadfiles_s: List[UploadFile]):
    # 验证awemeid
    required_keywords = ["5A关系资产"]

    # 配置参数
    BASE_PATH = "static/audience_assets"
    ALLOWED_EXTENSIONS = {'.csv', '.xlsx'}

    results = []
    errors = []

    # 确保目录存在
    os.makedirs(BASE_PATH, exist_ok=True)

    async def process_file(upload_file: UploadFile):
        """处理单个文件的辅助函数"""
        try:
            if not upload_file.filename:
                raise HTTPException(status_code=400, detail=f"无法获取文件名")
            # 安全处理文件名
            safe_filename = Path(upload_file.filename).name
            file_name, file_ext = os.path.splitext(safe_filename)

            # 验证文件扩展名
            if file_ext.lower() not in ALLOWED_EXTENSIONS:
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": f"不支持的文件类型，只支持{ALLOWED_EXTENSIONS}"
                }

            # 验证文件名包含所需关键词
            if not any(keyword in file_name for keyword in required_keywords):
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": f"文件名必须包含以下关键词之一: {required_keywords}"
                }

            # 构建带时间戳的文件路径
            timestamp = datetime.now().strftime('%Y%m%d')
            file_path = os.path.join(
                BASE_PATH, f"{file_name}_{timestamp}{file_ext}")

            # 检查文件是否已存在
            if os.path.exists(file_path):
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": "文件已存在"
                }

            # 保存文件
            try:
                with open(file_path, "wb") as f:
                    content = await upload_file.read()
                    f.write(content)
            except Exception as e:
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": f"文件保存失败: {str(e)}"
                }
            logger.info(f"{file_name}保存成功")
            # 处理文件内容
            try:
                AudienceAsset_list = AudienceAsset_compute.audience_assets_compute(
                    file_path)
            except Exception as e:
                os.remove(file_path)  # 删除无效文件
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": f"文件内容解析失败: {str(e)}"
                }

             # 批量写入数据库
            try:
                objects_to_create = [
                    AudienceAsset(**fields, created_at=datetime.now())
                    for fields in AudienceAsset_list
                ]
                await AudienceAsset.bulk_create(objects_to_create, ignore_conflicts=True)
                logger.info(f"{file_name}导入到数据库成功")
            except Exception as e:
                return {
                    "filename": safe_filename,
                    "status": "error",
                    "message": f"数据库写入失败: {str(e)}"
                }

            return {
                "filename": safe_filename,
                "status": "success",
                "message": "上传并处理成功"
            }

        finally:
            await upload_file.close()

    # 处理所有文件
    for upload_file in uploadfiles_s:
        result = await process_file(upload_file)
        if result["status"] == "success":
            results.append(result)
        else:
            errors.append(result)

    return {
        "code": 0,
        "data": {
            "success": f"处理完成",
            "detail": {
                "success": results,
                "errors": errors
            }
        }
    }
