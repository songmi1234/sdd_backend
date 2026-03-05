import functools
from loguru import logger
import time
from typing import Any, Awaitable, Callable, List, Optional, Union
from datetime import date, timedelta, datetime
import json
import re
# 第三方库导入
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, params, status
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


router = APIRouter()


@router.get("/allaccount/{start_date}", description="获取数据库中账户列表", include_in_schema=False)
async def getaccount(start_date):
    print(start_date)
    # accountlists = await Shop_Data.filter(date__gte=start_date)
    # print(accountlists)
    # return accountlists


@router.get("/all_uni_taks/", description="获取所有全域计划")
async def get_all_uni_tasks(advertise_ids: list[int] = Query(..., description="账户ID列表")):
    accountlists = await UniPromotionList.filter(account_id__in=advertise_ids).values("marketing_goal", "id", "name", "anchor_name", "account_id", "account__advertiser_name")
    return accountlists


@router.get("/all_videos/{days}", description="获取近x天所有账户下视频库内容")
@async_timer
async def get_all_videos(days: int):
    current_date = date.today()

    advertise_lists = await AccountList.all().values("advertiser_id", "advertiser_name")
    if not advertise_lists:
        raise HTTPException(status_code=500, detail="数据库错误")
    success_count = 0
    success_advertise = []
    # advertise_lists=[{"advertiser_id":1770732564116488}]
    try:
        for advertise in advertise_lists:
            advertise_id = advertise.get("advertiser_id")
            advertiser_name = advertise.get("advertiser_name")
            # api
            api_name = "GET_QIANCHUAN_VIDEO"
            # 日志输出
            logger.info(f"advertiser_name:{advertiser_name} 正在获取 ")

            page = 1
            videolists = []
            while True:
                request_params = {
                    "advertiser_id": advertise_id,
                    "filtering": {
                        "start_time": str(current_date-timedelta(days=int(days))),
                        "end_time": str(current_date)},
                    "page": page,
                    "page_size": 100}
                data = qianchuan_api_service.invoke_qianchuan_api(
                    api_name, request_params)
                # logging.info(request_params)
                total_page = data.get("data", {}).get(
                    "page_info").get("total_page")
                videolist = data.get("data", {}).get("list")
                success_count += len(videolist)
                videolists.append(videolist)
                # total_page=1
                # print(data)
                if page >= total_page:
                    break
                else:
                    page += 1
            logger.info(f"advertiser_name:{advertiser_name} 获取完毕")
            videolists_list = [
                video for videolist in videolists for video in videolist]
            objects_to_create = []
            for fields in videolists_list:
                # 💡 核心修复 1：处理 create_time
                raw_time = fields.get("create_time")
                if isinstance(raw_time, str):
                    try:
                        # 解析字符串并强制赋予时区
                        dt = datetime.strptime(raw_time.split('.')[
                                               0], '%Y-%m-%d %H:%M:%S')
                        fields["create_time"] = make_aware(dt)
                    except:
                        # 如果解析失败，给一个默认值或设为 None (前提是模型允许 null)
                        fields["create_time"] = now()

                # 💡 核心修复 2：处理主键 ID
                # 既然模型定义 id 是 CharField(pk=True)，确保 fields 里有 'id' 且不为 None
                if not fields.get("id"):
                    continue  # 跳过没有 ID 的非法数据

                # 💡 核心修复 3：移除 account 相关的干扰项
                # 如果 fields 里已经有 account_id 字符串，删掉它，使用下面传入的对象
                fields.pop('account', None)

                # 构建对象
                obj = VideoList(**fields, account=account)
                objects_to_create.append(obj)
            account = await AccountList.get_or_none(advertiser_id=advertise_id)

            def json_serial(obj):
                from datetime import datetime, date
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
            import json
            with open('x.json', 'w', encoding='utf-8') as f:
                json.dump(
                    videolists_list,
                    f,
                    ensure_ascii=False,
                    indent=4,         # 加上缩进，方便你用肉眼看
                    default=json_serial  # 关键：告诉 JSON 遇到时间怎么办
                )

            objects_to_create = [
                VideoList(** fields, account=account)
                for fields in videolists_list
            ]
            await VideoList.bulk_create(objects_to_create, ignore_conflicts=True)
            success_advertise.append(advertise)
    except Exception as e:
        logger.error(f"发生意外错误：{e}")

    # with open("response.json","w",encoding="utf-8") as f:
    #      f.write(json.dumps(videolists_list, indent=2, ensure_ascii=False))
    return {"success_count": success_count, "success_advertise": success_advertise}


def clean_audit_reason(raw_data):
    """
    将原始审核理由列表转为明文中文文本，并移除干扰的 HTML 标签
    """
    if not raw_data:
        return ""

    # 1. 如果是列表，用换行符连接，这样在数据库里看是多行，很清晰
    if isinstance(raw_data, list):
        full_text = "\n".join([str(item) for item in raw_data])
    else:
        full_text = str(raw_data)

    # 2. 核心修复：使用正则表达式剔除所有 <img ...> 标签
    # 这样能把长度从 1000+ 缩减到几十个字符
    clean_text = re.sub(r'<img[^>]*>', '', full_text)

    # 3. 移除多余的转义符和首尾空格
    clean_text = clean_text.replace('\\"', '"').strip()

    # 4. 长度保险：如果你的字段是 CharField(505)
    # 截断至 500 字符，预留安全空间避免 ValidationError
    if len(clean_text) > 500:
        clean_text = clean_text[:497] + "..."

    return clean_text


@router.get("/all_reject_reason", description="获取单个账户下审核建议", summary='获取单个账户下审核建议')
@async_timer
async def all_reject_reason(advertise_id: int = Query(description="账户ID", default=1779271778331655)):
    # advertise_lists = await AccountList.all().values("advertiser_id", "advertiser_name")
    advertise_lists = [advertise_id]
    if not advertise_lists:
        raise HTTPException(status_code=404, detail=f"数据库错误")
    success_count = 0
    success_advertise = []

    reason_lists = []
    reason_lists_all = []
    for advertise in advertise_lists:
        # advertise_id = advertise.get("advertiser_id")
        advertise = advertise

        uni_list = await UniPromotionList.filter(account_id=advertise_id).all().values("id")
        # print(uni_list)
        if not uni_list:
            continue
        for uni in uni_list:
            plan_id = uni.get("id")  # 获取计划id
            # 删除以前的信息
            await AuditSuggestion.filter(account=advertise_id, ad_id=plan_id).delete()
            # 预先将所有modedify 设置为true
            # await AuditSuggestion.filter(account=advertise_id,uni_id=plan_id).update(modify=True)
            # print(id)
            api_name = "GET_UNI_PROMOTION_REJECT_REASON"
            page = 1

            while True:
                request_params = {
                    "advertiser_id": advertise_id,
                    "ad_id": plan_id,
                    "page": page,
                    "page_size": 100}
                data = qianchuan_api_service.invoke_qianchuan_api(
                    api_name, request_params)

                total_page = data.get("data", {}).get(
                    "page_info").get("total_page")
                reason_list = data.get("data", {}).get("list")
                success_count += len(reason_list)
                if page >= total_page:
                    break
                else:
                    page += 1

            if reason_list:
                success_count += len(reason_list)
                reason_lists.append(reason_list)
                account = await AccountList.get_or_none(advertiser_id=advertise_id)
                ad_id = plan_id

                # uni_id = await UniPromotionList.get_or_none(id=plan_id)
                reason_list_pure = []
                update_fields = ['audit_reason', 'video_material']
                for reason in reason_list:
                    desc = reason.get('desc')
                    # 1. 拿到原始列表
                    raw_audit_reason = reason.get("audit_reason", [])

                    # 2. 手动序列化，关键参数：ensure_ascii=False
                    # 这样生成的字符串里就是明文中文了
                    # reason_text = json.dumps(
                    #     raw_audit_reason, ensure_ascii=False)

                    reason_text = clean_audit_reason(raw_audit_reason)
                    if not desc:
                        logger.error(f'无内容reason {reason}')
                        continue
                    elif desc == '商品':
                        audit_data = {
                            # 核心审核字段（从 reason 提取，设默认值避免 None）
                            "audit_platform": reason.get("audit_platform", ""),
                            "audit_reason": reason_text,
                            "desc": desc,
                            # "material_id": material_id,
                            # "image_material": reason.get("image_material", {}),
                            # "video_material": reason.get("video_material", {}),
                            # "is_aweme_video_title": reason.get("is_aweme_video_title"),
                            "product_id": reason.get("product_id"),
                            # "related_video_material_id": reason.get("related_video_material_id"),
                            # 外键字段（仅传实例或 None）
                            "account": account,
                            "ad_id": ad_id,  # 已确保是实例或 None
                            # 普通字段（整数类型，直接传）
                            # "video_material_id": video_material_id,
                            "modedify": False
                        }
                    elif desc == '视频':
                        audit_data = {
                            # 核心审核字段（从 reason 提取，设默认值避免 None）
                            "audit_platform": reason.get("audit_platform", ""),
                            "audit_reason": reason_text,
                            "desc": desc,
                            "material_id":  reason.get("material_id", None),
                            # "image_material": reason.get("image_material", {}),
                            "video_material": reason.get("video_material", {}),
                            "is_aweme_video_title": reason.get("is_aweme_video_title", None),
                            # "product_id": reason.get("product_id"),
                            # "related_video_material_id": reason.get("related_video_material_id"),
                            # 外键字段（仅传实例或 None）
                            "aweme_item_id": reason.get("video_material", {}).get('aweme_item_id'),
                            "account": account,
                            "ad_id": ad_id,  # 已确保是实例或 None
                            # 普通字段（整数类型，直接传）
                            # "video_material_id": video_material_id,
                            "modedify": False
                        }
                    reason_list_pure.append(audit_data)
                    # material_id = reason.get("material_id", None)
                    # if material_id:
                    #     video_material_id = await VideoList.get_or_none(material_id=material_id, account_id=advertise_id)
                    # else:
                    #     video_material_id = None

                    # audit_data = {
                    #     # 核心审核字段（从 reason 提取，设默认值避免 None）
                    #     "audit_platform": reason.get("audit_platform", ""),
                    #     "audit_reason": reason.get("audit_reason", []),
                    #     "desc": reason.get("desc", "视频"),
                    #     "material_id": material_id,
                    #     "image_material": reason.get("image_material", {}),
                    #     "video_material": reason.get("video_material", {}),
                    #     "is_aweme_video_title": reason.get("is_aweme_video_title"),
                    #     "product_id": reason.get("product_id"),
                    #     "related_video_material_id": reason.get("related_video_material_id"),
                    #     # 外键字段（仅传实例或 None）
                    #     "account": account,
                    #     "uni_id": uni_id,  # 已确保是实例或 None
                    #     # 普通字段（整数类型，直接传）
                    #     "video_material_id": video_material_id,
                    #     "modedify": False
                    # }
                    # # print(audit_data)
                    # # await AuditSuggestion.create(** audit_data)
                    # try:
                    #     await AuditSuggestion.create(** audit_data)
                    # except IntegrityError as e:
                    #     if "Duplicate entry" in str(e):
                    #         logger.info(
                    #             f"跳过重复记录: {audit_data.get('uid')} 和 {audit_data.get('account')}")
                    #     else:
                    #         raise

                    # logger.info(f"advertise_id:{advertise_id}下计划{plan_id}处理完毕")

                    # success_advertise.append(advertise)

                    # video_material_id = await AccountList.get_or_none(advertiser_id=advertise_id)

                    # objects_to_create = [
                    #     VideoList(** fields, account=account)
                    #     for fields in videolists_list
                    # ]
                    # await VideoList.bulk_create(objects_to_create,ignore_conflicts=True)
                    # success_advertise.append(advertise)
                    # reason_lists=[reson for reason_list in reason_lists for reson in reason_list]
                objects_to_create = [
                    AuditSuggestion(** fields,
                                    created_at=datetime.now())
                    for fields in reason_list_pure
                ]
                await AuditSuggestion.bulk_create(objects_to_create,  on_conflict=["material_id"],  # 这里的字段必须在数据库中有唯一索引（Unique Index）
                                                  update_fields=update_fields  # 发生冲突时，要更新哪些字段)
                                                  )
    return {"code": 0, "data":
            {"success_advertise": success_advertise,
             "success_count": success_count}}


@router.get("/test")
async def test():
    from datetime import date, timedelta
    current_date = date.today()
    request = {
        "start_time": str(current_date-timedelta(days=7))+" 00:00:00",
        "end_time": str(current_date)+" 23:59:59"}
    return request
