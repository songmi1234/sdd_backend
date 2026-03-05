import re
from fastapi import APIRouter, HTTPException, status, Query, Request, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, field_validator, ValidationError
from typing import List, Union, Optional, Dict
from functools import wraps
import json
import asyncio
from pydantic import BaseModel
from type import reposen_model
from typing import Any
import requests
import os
from type import reposen_model
from utils import auth_jwt, tools
from orm.models import User
from tortoise.expressions import F
import httpx
import time

router = APIRouter()
client = httpx.AsyncClient(timeout=10.0)

url = "https://qianchuan.jinritemai.com/apps/crm_node/business/mpdc/common_diagnosis/short_video/material_bench?aavid=1834790203717834"


class GetVideo(BaseModel):
    daterange: list[str]
    industryIdss: list[list]
    video_title: Optional[str] = ''
    costLevels: Optional[list[str]] = None
    roiLevel: Optional[str] = ''
    qcMarketingGoal: Optional[str] = None
    sortField: Optional[str] = 'cost'
    avgPriceLevels: Optional[list[str]] = None
    pageSize: Optional[int] = 20
    currentPage: Optional[int] = 1
    price_high: Optional[int] = 1000
    video_duration: Optional[list[int]] = None
    price_low: Optional[int] = 0
    adlabMode: Optional[str] = '全域'


def qianchuan_reponse_encry(response: Any):
    # t1 = time.perf_counter()
    # 1. 获取原始数据 (Pydantic 对象使用 .data 访问)
    raw_data = response.get('data')

    # 2. 调用你之前的加密工具函数
    encrypted_str = tools.encrypt_data(raw_data)

    # 3. 关键：将加密后的密文重新赋值给 data 字段
    # 注意：这要求你的 BaseResponse 模型中 data 字段允许接收字符串类型
    response['data'] = encrypted_str
    t2 = time.perf_counter()
    # print(t2-t1)
    # 4. 返回修改后的对象
    return response


@router.post("/get", summary="加密返回千川数据")
async def login2(search: GetVideo, user_info: dict = Depends(auth_jwt.role_auth("R_ADMIN"))):
    username = user_info.get('name')
    searcher_data = search.model_dump()

    # 1. 预校验必填项，避免先扣费后报错
    if not searcher_data.get('daterange') or not searcher_data.get('industryIdss'):
        raise HTTPException(status_code=400, detail="缺少必要查询参数")

    # 2. 扣除配额（原子操作）
    updated_rows = await User.filter(
        username=username,
        get_clip_quota__gte=1
    ).update(get_clip_quota=F("get_clip_quota") - 1)

    if not updated_rows:
        raise HTTPException(status_code=400, detail="额度不足")

    # 使用 try 块确保一旦请求失败或逻辑错误，能归还额度
    try:
        # 3. 构造 Payload
        payload_json = {
            "page": searcher_data.get('currentPage', 1),
            "pageSize": searcher_data.get('pageSize', 20),
            "packageName": "@byted-dcma/dcma-component-ec-short-video-diagnosis-material-bench",
            "params": {
                "scene": "qianchuan",
                "dcmaViewScene": "EC-ADVID",
                "adlabMode": searcher_data.get('adlabMode', "全域"),
                "advId": "1834790203717834",
                "dateRange": searcher_data.get('daterange'),
                "industryIdss": searcher_data.get('industryIdss'),
                "roiLevel": searcher_data.get('roiLevel', "平均"),
                "sortType": "descend",
                "sortField": searcher_data.get('sortField', "cost"),
                "video_title": searcher_data.get('video_title', ''),
                "fromResource": "true",
                "ignoreShopInfo": "false"
            },
            "userIdentity": {"advId": "1834790203717834"}
        }

        # 映射可选参数
        optional_fields = ['costLevels', 'qcMarketingGoal',
                           'avgPriceLevels', 'video_duration']
        for field in optional_fields:
            if val := searcher_data.get(field):
                payload_json['params'][field] = val

        if searcher_data.get('price_low') or searcher_data.get('price_high'):
            payload_json['params']['price_range'] = [searcher_data.get(
                'price_low', 0), searcher_data.get('price_high', 1000)]

        headers = {
            "User-Agent": "Mozilla/5.0...",
            "Content-Type": "application/json",
            "Cookie": os.getenv('COOKIES', "")
        }

        # 4. 异步请求 (HTTPX)
        resp = await client.post(url, json=payload_json, headers=headers)
        resp_data = resp.json()

        if resp.status_code != 200 or resp_data.get('code') != 0:
            raise Exception("外部接口返回异常")

        # 5. 处理分页逻辑 (保持原有逻辑，但改为异步)
        if searcher_data.get('currentPage') == 1:

            return qianchuan_reponse_encry(resp_data)

        # 深度分页处理
        total = resp_data['data'][0]['data'][0].get('total', 0)
        if total <= 50:
            return qianchuan_reponse_encry(resp_data)

        final_data = resp_data
        final_data['data'][0]['data'] = []

        # 注意：此处循环请求可能会很慢，建议根据需求优化
        page = 11
        while (page * 5) <= total:
            payload_json['params']['page'] = page
            payload_json['params']['pageSize'] = 5
            sub_resp = await client.post(url, json=payload_json, headers=headers)
            sub_json = sub_resp.json()

            if sub_json.get('code') == 0:
                final_data['data'][0]['data'].extend(
                    sub_json['data'][0]['data'])
            page += 1

        return qianchuan_reponse_encry(final_data)

    except Exception as e:
        # 只有在发生异常时才归还额度
        await User.filter(username=username).update(get_clip_quota=F("get_clip_quota") + 1)
        raise HTTPException(status_code=500, detail=f"服务内部错误: {str(e)}")


@router.get("/get_clip_quota")
async def get_clip_quota(user_info: dict = Depends(auth_jwt.role_auth("R_ADMIN"))):
    # logger.info(search.model_dump())

    username = user_info.get('name')
    # info = await User.filter(username=username).all().values()
    user_data = await User.filter(
        username=username
    ).all().values('get_clip_quota')
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")
    return reposen_model.BaseResponse(
        code=0,
        data=user_data[0],
        message="请求成功"
    )


@router.get('encrypt_data')
async def encrypt_data_test():

    test_data = {"id": 1, "name": "Gemini", "roles": ["admin"]}
    encrypted = tools.encrypt_data(test_data)
    return encrypted
