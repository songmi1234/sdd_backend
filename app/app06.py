import asyncio
import functools
import json
from loguru import logger
import time
from typing import Any, Awaitable, Callable, List, Optional, Union, Dict
from utils.uni_data_models_new import *

# 第三方库导入
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, ValidationError, field_validator
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
# @router.get("/allaccount/{start_date}",description="获取数据库中账户列表")
# async def getaccount(start_date):
#     print(start_date)
#     accountlists=await Shop_Data.filter(date__gte=start_date)
#     print(accountlists)
#     return accountlists

# @router.get("/all_uni_taks/{advertise_id}",description="获取所有全域计划")
# async def get_all_uni_tasks(advertise_ids: list[int] = Query(..., description="账户ID列表")):
#     accountlists=await UniPromotionList.filter(account_id__in=advertise_ids).values("marketing_goal","id","name","anchor_name","account_id","account__advertiser_name")
#     return accountlists


#  # 主键字段（自增ID，符合数据库设计规范）
#     id = fields.IntField(pk=True, description="数据库自增主键ID")

#     # 业务字段（与需求一一对应）
#     event_id = fields.IntField(description="违规单id",unique=True)
#     account = fields.ForeignKeyField('models.AccountList', related_name='violationrecord')
#     ad_id = fields.IntField(description="计划id")
#     material_id = fields.CharField(max_length=255, description="素材id")
#     violation_evidence_img = fields.CharField(max_length=512, null=True, blank=True, description="违规证据截图（URL或存储路径）")
#     score = fields.FloatField(description="扣罚分值")
#     reject_reason = fields.TextField(description="拒绝理由")
#     create_time = fields.DatetimeField(description="创建时间（自动解析字符串格式）")

#     # 状态字段（使用Choice枚举约束可选值）
#     status = fields.CharField(max_length=255,description="违规单状态")

#     # 违规类型字段（Choice枚举约束）
#     illegal_type = fields.CharField(max_length=255,description="违规类型")


# 定义所有需要更新的字段列表（排除主键和外键ID，以及自增时间戳）
FIELDS_TO_UPDATE = [
    # 'ad_id',
    'material_id',
    'violation_evidence_img',
    # 'score',
    'reject_reason',
    # 'create_time', # 包含在内，即使是字符串也需要同步
    'status',
    # 'illegal_type',
]

FIELDS_TO_UPDATE_2orm = [
    *FIELDS_TO_UPDATE,  # 复用上面的字段，避免重复写
    'update_at'   # 关键：包含更新时间字段
]


@router.get("/get_qianchuan", description="违规单查询", summary="违规单")
async def violationrecord(account_id: Optional[int] = Query(None, description="账户ID（关联AccountList的id，可选筛选）")):

    api_name = "GET_ViolationRecord"
    success_list: List[Dict[str, Any]] = []
    error_list: List[Dict[str, Any]] = []
    # 示例数据源
    advertiser_ids = [1791216574500928]
    account = await AccountList.all().values("advertiser_id")
    # advertiser_ids = [1791216574500928]
    advertiser_ids = [item["advertiser_id"] for item in account]
    print(advertiser_ids)
    # 模拟 API 返回数据，您的真实代码会调用 qianchuan_api_service.invoke_qianchuan_api
    # mock_api_data = [{'ad_id': 1831351612472570, 'advertiser_id': 1791216574500928, 'create_time': '2025-11-16 14:39:21', 'event_id': 6285293, 'illegal_type': 'TWOTHREECLASS', 'material_id': '7537983065661407251', 'reject_reason': '原因1117', 'score': 1, 'status': 'TIMEOUT', 'violation_evidence_img': None}, {'ad_id': 2770421951518669, 'advertiser_id': 1791216574500928, 'create_time': '2025-10-27 14:45:28', 'event_id': 6053213, 'illegal_type': 'TWOTHREECLASS', 'material_id': '7533519615915671590', 'reject_reason': '原因2', 'score': 1, 'status': 'TIMEOUT', 'violation_evidence_img': None}, {'ad_id': 2770421951518669, 'advertiser_id': 1791216574500928, 'create_time': '2025-06-03 16:58:42', 'event_id': 4771800, 'illegal_type': 'TWOTHREECLASS', 'material_id': '7510877186283749414', 'reject_reason': '原因3', 'score': 1, 'status': 'FAILAPPEAL', 'violation_evidence_img': None}, {'ad_id': 2770421951518669, 'advertiser_id': 1791216574500928, 'create_time': '2025-01-04 12:26:40', 'event_id': 3366436, 'illegal_type': 'TWOTHREECLASS', 'material_id': '7446593800388165682', 'reject_reason': '原因4', 'score': 1, 'status': 'TIMEOUT', 'violation_evidence_img': 'https://p3-bes-img.byteimg.com/tos-cn-i-mzjikbws1s/70251488352b432c8cefc92bbff8dc14~tplv-mzjikbws1s-wmk.png'}]

    for advertiser_id in advertiser_ids:
        # api_调取信息
        try:
            request_params = {
                "advertiser_id": advertiser_id,
                "business_line": "QIANCHUAN",
                "page": 1,
                "page_size": 100}
            response = qianchuan_api_service.invoke_qianchuan_api(
                api_name, request_params)
            data = response.get("data", {}).get("adv_score_event", [])
            # data = mock_api_data  # 使用模拟数据

            if not data:
                logger.info(f"Advertiser ID {advertiser_id}: API返回数据为空。")
                continue

            # 统计成功
            success_list.append({
                "advertiser_id": advertiser_id,
                "数量": len(data)
            })

        except Exception as e:
            error_list.append({
                "advertiser_id": advertiser_id,
                "错误原因": str(e)
            })
            logger.error(f"API调用失败 for {advertiser_id}: {e}")
            continue

        # --- 准备数据和查找现有记录 ---

        event_ids = [item["event_id"] for item in data]

        # 1. 查找现有 ORM 实例 (用于更新)
        existing_records_orm = await ViolationRecord.filter(event_id__in=event_ids).all()

        # 2. 将现有 ORM 实例转换为以 event_id 为键的字典，方便查找和修改
        existing_orm_map = {
            item.event_id: item for item in existing_records_orm}

        new_items_data: List[Dict[str, Any]] = []
        objects_to_update: List[ViolationRecord] = []

        for item in data:
            event_id = item["event_id"]

            if event_id in existing_orm_map:
                # 这是要更新的记录
                record_instance = existing_orm_map[event_id]

                # 检查并更新字段
                is_changed = False
                for field in FIELDS_TO_UPDATE:
                    api_value = item.get(field)
                    current_value = getattr(record_instance, field)

                    # 使用 str() 转换确保类型一致，特别是对于 BigInt/Int/Float 和 None
                    # 仅在值不同时才设置，避免不必要的数据库操作
                    if str(api_value) != str(current_value):
                        setattr(record_instance, field, api_value)
                        is_changed = True

                # 如果有字段发生了变化，添加到批量更新列表
                if is_changed:
                    # print("xxxx")
                    setattr(record_instance, "update_at", datetime.now())
                    objects_to_update.append(record_instance)
            else:
                # 这是要创建的新记录
                new_items_data.append(item)

        # --- 执行批量更新 (Bulk Update) ---
        if objects_to_update:
            try:

                updated_count = await ViolationRecord.bulk_update(
                    objects_to_update,
                    fields=FIELDS_TO_UPDATE_2orm
                )
                logger.info(
                    f"Advertiser ID {advertiser_id}: 批量更新了 {updated_count} 条记录。")
            except Exception as e:
                logger.error(f"批量更新失败 for {advertiser_id}: {e}")

        # --- 执行批量创建 (Bulk Create) ---
        if new_items_data:
            account = await AccountList.get_or_none(advertiser_id=advertiser_id)
            if account:
                objects_to_create = [
                    ViolationRecord(**fields, account=account,
                                    create_at=datetime.now())  # 注意：account 是外键对象
                    for fields in new_items_data
                ]
                try:
                    await ViolationRecord.bulk_create(objects_to_create, ignore_conflicts=True)
                    logger.info(
                        f"Advertiser ID {advertiser_id}: 批量创建了 {len(objects_to_create)} 条记录。")
                except Exception as e:
                    logger.error(f"批量创建失败 for {advertiser_id}: {e}")
            else:
                logger.warning(
                    f"Advertiser ID {advertiser_id} 对应的 AccountList 记录不存在，无法创建违规单。")

    return {
        "code": 200,
        "msg": "success",
        "data": {
            "success": success_list,
            "error": error_list,
            "updated_count": len(objects_to_update) if 'objects_to_update' in locals() else 0,
            "created_count": len(new_items_data) if 'new_items_data' in locals() else 0,
        }
    }

# @router.get("/test", description="违规单查询")
# async def test1():
#     uni = await UniPromotionList.get_or_none(id=1809800600290339)
#     unii = await uni.values()
#     print()
