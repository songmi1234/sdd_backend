from encodings import ptcp154
from fastapi import APIRouter, HTTPException, status, Query, Request, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, field_validator, ValidationError
from typing import List, Union, Optional, Dict
from functools import wraps
import json
from typing import Callable
import asyncio
from pydantic import BaseModel
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from loguru import logger
import bcrypt
from orm.models import *
# 1. 配置参数
# ------------------------------
SECRET_KEY = "dff212269d2569a41ee6a776e2649593fad5beccf2479ca21d8d1b0e425749d6"
ALGORITHM = "HS256"

# 令牌过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 小时
REFRESH_TOKEN_EXPIRE_MINUTES = 7 * 24 * 60  # 7 天

# 定义令牌类型，用于载荷区分


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# router = APIRouter(tags=["认证相关接口"])
# tokenUrl 指定获取令牌的接口路径
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/apitoken/token")


# ------------------------------
# 2. 数据模型 (匹配期望的返回结构)
# ------------------------------
class TokenData(BaseModel):
    """JWT 载荷内部模型"""
    name: str = ''
    type: str = ''  # 令牌类型 (access/refresh)
    admin: bool
    roles: list[str]


class LoginResponseData(BaseModel):
    """匹配您期望的 'data' 字段结构"""
    token: str          # Access Token
    refreshToken: str   # Refresh Token


class LoginResponse(BaseModel):
    """登录成功时的最终响应模型"""
    code: int = 200
    data: LoginResponseData
    msg: str = "登录成功"


class RefreshRequest(BaseModel):
    """刷新令牌请求体模型"""
    refreshToken: str

# 刷新接口的响应模型与登录接口一致，但 msg 不同


class RefreshResponse(LoginResponse):
    msg: str = "刷新成功"


# ------------------------------
# 3. 工具函数
# ------------------------------
async def validate_user(username: str, password: str) -> dict | None:
    """验证用户凭据（硬编码演示）"""
    # 实际应用中应从数据库查询验证
    user = await User.get_or_none(username=username)
    if user == None:
        logger.error(f'{username} 不存在')
        return None

    if user.status != '1':
        logger.error(f'{username} 未激活')
        return None

    password_hash = user.password_hash
    # print(user,password_hash)
    if bcrypt.checkpw(password=password.encode('utf-8'), hashed_password=password_hash.encode('utf-8')):
        return {
            "username": user.username,
            "is_admin": getattr(user, 'is_admin', False),
            "roles": getattr(user, 'roles', [])
        }
    logger.error(f'{username} 密码错误')
    return None


def create_token(data: dict, token_type: str) -> str:
    """
    通用 JWT 令牌生成函数
    """
    to_encode = data.copy()

    if token_type == TokenType.ACCESS:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    elif token_type == TokenType.REFRESH:
        expires_delta = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    else:
        raise ValueError("Invalid token type specified for creation.")

    # 计算过期时间（使用 UTC 时区）
    expire = datetime.now(timezone.utc) + expires_delta

    # 写入载荷，并添加 'exp' 和 'type' 字段
    to_encode.update({
        "exp": expire,
        "type": token_type,  # 关键：标识令牌类型
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ------------------------------
# 4. 依赖项 (令牌验证)
# ------------------------------
def verify_token_and_extract(token: str, required_type: str) -> dict:
    """
    通用令牌验证和载荷提取函数
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"无法验证凭据或令牌类型不正确 ({required_type})",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码 JWT 令牌
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        print(payload)
        token_data = TokenData(**payload)

        # 1. 检查是否存在 sub 字段
        if token_data.name is None:
            raise credentials_exception

        # 2. 检查令牌类型是否符合要求
        if token_data.type != required_type:
            raise credentials_exception
        # print(token_data)
        print("verify_token_and_extract", token_data)
        dict_token = token_data.model_dump()
        if token_data.type == TokenType.REFRESH:
            dict_token['refreshToken'] = token
        return dict_token
        # return token_data
    except JWTError:
        # 捕获签名、格式、过期等错误
        raise credentials_exception
    except ValidationError:
        # 捕获载荷格式错误
        raise credentials_exception

# 用于受保护 API 的依赖 (验证 Access Token)


def access_token_verify(token: str = Depends(oauth2_scheme)) -> dict:
    """验证并提取 Access Token 载荷"""
    return verify_token_and_extract(token, TokenType.ACCESS)

# 用于刷新接口的依赖 (验证 Refresh Token)


def refresh_token_verify(refresh_req: RefreshRequest) -> dict:
    """验证并提取 Refresh Token 载荷"""
    return verify_token_and_extract(refresh_req.refreshToken, TokenType.REFRESH)


ACCESS = "access"


def header_get(request: Request):
    return dict(request.headers)


def jwt_verify(request: dict = Depends(header_get)):

    try:
        auth_header = request.get('authorization')
        # print(auth_header)
        if not auth_header:
            raise HTTPException(status_code=401, detail="未发现认证凭据")
        token_data = verify_token_and_extract(
            token=auth_header, required_type=ACCESS)
        # print("jwt_verify",token_data)
        return token_data
    except Exception as e:
        logger.error(f"Token 校验失败: {str(e)}")
        raise HTTPException(status_code=401, detail="认证无效或已过期")
    return request


def header_get_3(request: Request):
    return request.client


def role_auth(required_role: str) -> Callable:
    """
    完善后的角色权限校验
    :param required_role: 要求的角色代码，如 'R_SUPER', 'R_ADMIN'
    """
    def _role_checker(token_data: dict = Depends(jwt_verify)) -> dict:
        # 1. 如果 jwt_verify 抛出了异常或返回了错误对象，这里处理
        if isinstance(token_data, Exception):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="登录已过期或无效"
            )

        # 2. 从 Token 数据中获取用户的角色列表
        # 注意：你在 login 时塞进 Token 的数据决定了这里的取值
        # 假设 token_data = {"sub": "rick", "roles": ["R_ADMIN"], ...}
        user_roles = token_data.get("roles", [])
        print(token_data, user_roles)

        # 3. 校验权限
        # 如果是超级管理员，直接放行；否则检查是否包含要求的角色
        if "R_SUPER" in user_roles:
            return token_data

        if "R_ADMIN" in user_roles and required_role == 'R_USER':
            return token_data

        if required_role not in user_roles:
            logger.warning(
                f"权限拒绝: 用户角色 {user_roles} 尝试访问需要 {required_role} 的接口")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要 {required_role} 角色"
            )

        return token_data

    return _role_checker


# ------------------------------
# 5. 接口定义
# ------------------------------
class UserLogin(BaseModel):
    userName: str
    password: str
