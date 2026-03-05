import asyncio
import functools
import json
from loguru import logger
import time
from typing import Any, Awaitable, Callable, List, Optional, Union, Dict
from utils.uni_data_models_new import *
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
# 第三方库导入
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, ValidationError, field_validator, Field
from tortoise.exceptions import IntegrityError
from tortoise.functions import Sum
# 本地模块导入（按字母顺序分组）
from orm.models import *  # 建议明确导入所需模型，避免通配符
from utils import shop_data_upload

import pandas as pd


# 使用async_timer装饰器来计时异步函数
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


@router.get('/data')
@async_timer
async def get_data():
    s1 = time.perf_counter()  # 记录开始时刻

    yesterday = date.today() - timedelta(days=1)
    last_year_yesterday = yesterday.replace(
        year=yesterday.year - 1)
    last_year_month_start = yesterday.replace(day=1).replace(
        year=yesterday.year - 1)
    # 本月第一天
    month_start = yesterday.replace(day=1)
    uni_list = await Uni_aweme_list.filter(auth_type__in=['OFFICIAL', 'SELF']).all().values("aweme_name", "aweme_id")
    print("yesterday::", yesterday, "last_year_yesterday::", last_year_yesterday,
          "month_start::", month_start, "last_year_month_start::", last_year_month_start)
    tasks = {
        # "today": Shop_Data.filter(date =today).annotate(s=Sum("transaction_amount")).values_list("s", flat=True),
        yesterday: Shop_Data.filter(date=yesterday).annotate(
            transaction_amount_sum=Sum("transaction_amount"),
            refund_amount_sum=Sum("refund_amount"),
            transaction_orders_sum=Sum("transaction_orders"),
            transaction_buyers_sum=Sum("transaction_buyers"),
            new_customer_amount_sum=Sum("new_customer_amount"),
            new_customer_orders_sum=Sum("new_customer_orders"),

        ).group_by("account_type", "media_type", "shop_account").values("shop_account", "account_type", "media_type", "transaction_amount_sum", "refund_amount_sum"),
        "month": Shop_Data.filter(date__range=[month_start, yesterday]).annotate(transaction_amount_sum=Sum("transaction_amount"), refund_amount_sum=Sum("refund_amount")).group_by("account_type", "media_type", "shop_account").values("shop_account", "account_type", "media_type", "transaction_amount_sum", "refund_amount_sum"),
        last_year_yesterday: Shop_Data.filter(date=last_year_yesterday).annotate(transaction_amount_sum=Sum("transaction_amount"), refund_amount_sum=Sum("refund_amount")).group_by("account_type", "media_type", "shop_account").values("shop_account", "account_type", "media_type", "transaction_amount_sum", "refund_amount_sum"),
        "last_year_month": Shop_Data.filter(date__range=[last_year_month_start, last_year_yesterday]).annotate(transaction_amount_sum=Sum("transaction_amount"), refund_amount_sum=Sum("refund_amount")).group_by("account_type", "media_type", "shop_account").values("shop_account", "account_type", "media_type", "transaction_amount_sum", "refund_amount_sum"),
    }

    # 使用 asyncio.gather 并发执行，速度翻倍
    results = await asyncio.gather(*tasks.values())
    # print(results, type(results))
    s2 = time.perf_counter()    # 记录结束时刻
    duration = s2 - s1
    print(f"asyncio.gather任务耗时: {duration:.4f} 秒")
    df_list = []
    for key, data in zip(tasks.keys(), results):
        print(f"Key: {key}, Data count: {len(data)}")
        temp_df = pd.DataFrame(data)
        if not temp_df.empty:
            temp_df['period'] = key  # 添加一列标识：yesterday, this_month 等
            df_list.append(temp_df)

    # 2. 合并成一个大表
    df: pd.DataFrame = pd.concat(df_list, ignore_index=True)

    # 3. 处理空值并统一格式
    df[['transaction_amount_sum', 'refund_amount_sum']] = df[[
        'transaction_amount_sum', 'refund_amount_sum']].fillna(0).astype(float)

    df['gsv'] = df['transaction_amount_sum'] - df['refund_amount_sum']
    # 计算退款率 (注意防止除以 0)    
    df['refund_rate'] = (df['refund_amount_sum'] / df['transaction_amount_sum']
                         ).replace([float('inf'), -float('inf')], 0).fillna(0)

    df = df.round(2)
    mapping = {str(uni["aweme_id"]): uni["aweme_name"] for uni in uni_list}
    df['shop_account'] = df['shop_account'].replace(mapping)
    data_detail = df.to_dict(orient='records')

    df_summary = df.groupby(['period', 'shop_account', 'account_type']).agg({
        'transaction_amount_sum': 'sum',
        'refund_amount_sum': 'sum',
        'gsv': 'sum'
    }).reset_index()
    df_summary['refund_rate'] = (df_summary['refund_amount_sum'] / df_summary['transaction_amount_sum']
                                 ).replace([float('inf'), -float('inf')], 0).fillna(0)
    df_summary = df_summary.round(2)
    data_summary = df_summary.to_dict(orient='records')
    df.to_csv('df_all.csv', index=False, encoding='utf-8-sig')
    df_summary.to_csv('data_summary.csv', index=False, encoding='utf-8-sig')
    s3 = time.perf_counter()    # 记录结束时刻
    duration = s3 - s2
    print(f"pandas耗时: {duration:.4f} 秒")
    # print(uni_list)
    return {'data': {'detail': data_detail, 'summary': data_summary}, 'message': 'success'}
