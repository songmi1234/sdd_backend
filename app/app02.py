from fastapi import Depends, APIRouter
from tortoise.expressions import Q
from fastapi import APIRouter, HTTPException, status, Query, Request, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, field_validator, ValidationError
from typing import List, Union, Optional, Dict
from functools import wraps
import json
import asyncio
from utils import auth_jwt
from typing import Callable
from loguru import logger
from type import reposen_model
from orm.models import User
from pydantic import BaseModel, EmailStr, Field, field_validator, field_serializer


router = APIRouter()


@router.get("/info")
async def info(
    # 直接依赖角色校验，它会自动先去跑 jwt_verify
    user_info: dict = Depends(auth_jwt.role_auth("R_USER"))
):
    # 如果代码运行到这里，说明：
    # 1. Token 有效
    # 2. 用户拥有 R_ADMIN 权限 或 R_SUPER 权限

    # 我们可以根据 Token 里的用户名去数据库查最新的详细信息

    user = await User.get_or_none(username=user_info["name"])
    if user:
        user_data = {
            "userId": str(user.id),
            "userName": user.username,
            "roles": user.roles,
            "buttons": user.buttons,
            "email": user.email
        }
        # print(user.buttons)
        return reposen_model.BaseResponse(code=0, data=user_data, message=f"请求成功")
    raise HTTPException(status_code=401, detail="用户未注册")


class GetUserSchema(BaseModel):
    # 使用 Optional 让搜索变为可选
    current: int = Query(1, ge=1, description="当前页码")
    size: int = Query(20, ge=1, le=100, description="每页条数")
    userName: Optional[str] = Query(
        "", description="用户名查询", str_strip_whitespace=True)
    userPhone: Optional[str] = Query("", description="手机号查询")
    #  /api/user/list?current=1&size=20&userName=rick2&userPhone=13000000000&status=1
    userEmail: Optional[str] = Query("", description="email查询")
    userGender: Optional[str] = Query("", description="性别")
    status: Optional[str] = Query("", description="状态")

    @field_validator('userName', 'userPhone', mode='before')
    @classmethod
    def trim_all_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator('userGender', mode='before')
    @classmethod
    def trim_all_string(cls, v):
        if isinstance(v, str):
            if v == '1':
                return '男'
            else:
                return '女'
        return v


@router.get("/list")
async def user_list(get_user: GetUserSchema = Depends(), user_info: dict = Depends(auth_jwt.role_auth("R_SUPER"))):
    # 1. 初始化查询对象（不立即执行）
    query = User.all()
    # print(get_user)
    # 2. 动态构建过滤条件 (增加搜索功能)
    # 如果前端传了 userName，进行模糊查询
    if get_user.userName:
        query = query.filter(username__icontains=get_user.userName)
    # contains 区分大小写的包含
    # 如果前端传了 userPhone，进行精确匹配
    if get_user.userPhone:
        query = query.filter(user_phone=get_user.userPhone)

    # 如果前端传了 userEmail，进行精确匹配
    # print(get_user.userEmail,get_user.userGender)
    if get_user.userEmail:
        query = query.filter(email__icontains=get_user.userEmail)

    # 3. 获取符合条件的总记录数 (真分页必备)
    total = await query.count()

    # 4. 执行真分页查询 (计算偏移量)
    # offset: 跳过的条数, limit: 取多少条
    offset = (get_user.current - 1) * get_user.size
    all_users = await query.offset(offset).limit(get_user.size).values()

    # 5. 序列化数据 (利用你之前写的 Loguru 记录)
    # 此时 model_dump(by_alias=True) 会处理好 userName, createTime 等
    users = [
        reposen_model.UserInfo.model_validate(user).model_dump(by_alias=True)
        for user in all_users
    ]

    # 6. 计算分页元数据
    total_pages = (total + get_user.size - 1) // get_user.size  # 向上取整

    # 7. 返回规范化响应
    return reposen_model.BaseResponse(
        code=0,
        data={
            "records": users,
            "current": get_user.current,
            "size": get_user.size,
            "total": total,
            "totalPages": total_pages,
            "isLastPage": get_user.current >= total_pages
        },
        message="请求成功"
    )


# required_role: Optional[str] = None
