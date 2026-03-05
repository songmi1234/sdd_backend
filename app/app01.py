from weakref import ref
from fastapi import APIRouter, HTTPException, status, Query, Request, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, field_validator, ValidationError
from typing import List, Union, Optional, Dict
from functools import wraps
import json
import asyncio
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from loguru import logger
import bcrypt
from orm.models import *
from utils import auth_jwt, code_verfy
from starlette.responses import JSONResponse
from type import reposen_model
from tortoise.expressions import Q
router = APIRouter()

# 定义令牌类型，用于载荷区分


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


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
    refreshToken: Optional[str] = ''  # 可选字段，用于存储 Refresh Token


class BaseResponseData(BaseModel):
    """匹配您期望的 'data' 字段结构"""
    token: str          # Access Token
    refreshToken: str   # Refresh Token


class BaseResponse(BaseModel):
    """登录成功时的最终响应模型"""
    code: int = 0
    data: BaseResponseData
    message: str = "登录成功"


class RefreshRequest(BaseModel):
    """刷新令牌请求体模型"""
    refreshToken: str

# 刷新接口的响应模型与登录接口一致，但 message 不同


class RefreshResponse(BaseResponse):
    message: str = "刷新成功"


# ------------------------------
# 5. 接口定义
# ------------------------------
class UserLogin(BaseModel):
    userName: str
    password: str


# A. 登录接口 (/login)
@router.post('/login', response_model=BaseResponse)
async def login(login_form: UserLogin):
    """
    用户登录接口：验证用户名密码并生成 Access Token 和 Refresh Token
    """
    # print('xx')
    username_val = await auth_jwt.validate_user(login_form.userName, login_form.password)
    # print("username_val",username_val)
    if not username_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确"
        )

    token_data = {"name": username_val['username'],
                  "admin": username_val['is_admin'], "roles": username_val['roles']}

    # 1. 生成 Access Token (对应返回体中的 "token")
    access_token = auth_jwt.create_token(token_data, TokenType.ACCESS)

    # 2. 生成 Refresh Token (对应返回体中的 "refreshToken")
    refresh_token = auth_jwt.create_token(token_data, TokenType.REFRESH)

    # 3. 返回符合 BaseResponse 模型的结构
    return BaseResponse(
        data=BaseResponseData(
            token=access_token,
            refreshToken=refresh_token
        )
    )

# B. 刷新接口 (/token/refresh)


@router.post('/token/refresh', response_model=RefreshResponse)
async def refresh_access_token(
    # 依赖项会验证 Refresh Token 的有效性，并返回载荷
    payload_dict: dict = Depends(auth_jwt.refresh_token_verify)
):
    payload = TokenData(**payload_dict)
    username_val = payload.name

    # 1. 生成新的 Access Token (Refresh Token 保持不变)
    new_access_token = auth_jwt.create_token(
        {"name": username_val}, TokenType.ACCESS)

    # 2. 返回新的 Access Token，并复用旧的 Refresh Token
    # 注意：更严格的方案是同时刷新 Refresh Token，但此处遵循常见简单方案
    return RefreshResponse(
        data=BaseResponseData(
            token=new_access_token,
            refreshToken=payload.refreshToken or ''  # 传递旧的 Refresh Token
        )
    )


@router.get('/hash_password/{password}')
async def hash_password_endpoint(password: str):
    """用于生成演示密码 hash 值的临时接口"""
    # password.encode("utf-8")： 这将您传入的 Python 字符串 password 使用 UTF-8 编码 转换为字节序列，使其兼容底层 Bcrypt 算法。
    # bcrypt.gensalt()： 这是一个函数调用，它会根据配置（如默认的工作因子/强度）随机生成一个全新的、安全的 Bcrypt 盐值。
    return {"hash": auth_jwt.bcrypt.hashpw(password=password.encode("utf-8"), salt=auth_jwt.bcrypt.gensalt())}


class EmailSchema(BaseModel):
    # to_emails: List[EmailStr]  # 收件人列表（支持多个）
    subject: str = "FastAPI 测试邮件"  # 邮件主题（默认值）
    body: str = "<h1>邮件发送成功！</h1><p>欢迎使用CLOUD AIGC</p>"  # 正文（支持HTML）
    email: EmailStr  # Pydantic 内置邮箱格式校验
    # code: int = Field(..., ge=100000, description="验证码，最少6位数字（整数）")

    # 可选：自定义邮箱域名白名单（防止无效/垃圾邮箱）
    @field_validator("email")
    def validate_email_domain(cls, v):
        allowed_domains = {"qq.com", "163.com", "gmail.com",
                           "126.com", "sina.com", "company.com"}
        domain = v.split("@")[-1]
        if domain not in allowed_domains:
            raise HTTPException(
                status_code=500, detail=f"邮箱域名不支持：{domain}，仅支持{allowed_domains}")
            # raise ValueError(f"邮箱域名不支持：{domain}，仅支持{allowed_domains}")
        return v

# -------------------------- 4. 邮件发送接口 --------------------------


@router.post("/sendemail", summary="发送邮件", description="发送验证码")
async def send_email(Email_form: EmailSchema, request: Request):
    code_ver = await request.app.state.redis.get(f"email:{Email_form.email}")
    logger.info(code_ver)
    if code_ver:
        return reposen_model.BaseResponse(code=401, data={}, message=f"邮件发送失败：请勿重复获取")
    code = code_verfy.generate_6digit_code()
    await request.app.state.redis.set(f"email:{Email_form.email}", code, ex=60*5)
    # code_ver = await request.app.state.redis.get(f"user:{email.to_emails[0]}")
    # logger.info(code_ver)
    email_body = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ margin: 0; padding: 0; background-color: #f4f7f9; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
        .wrapper {{ width: 100%; table-layout: fixed; background-color: #f4f7f9; padding-bottom: 40px; }}
        .main {{ background-color: #ffffff; margin: 0 auto; width: 100%; max-width: 600px; border-spacing: 0; color: #444444; border-radius: 16px; overflow: hidden; margin-top: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }}
        .header {{ background: linear-gradient(135deg, #007aff 0%, #00c6ff 100%); padding: 40px 20px; text-align: center; color: white; }}
        .header h1 {{ margin: 0; font-size: 28px; font-weight: 700; letter-spacing: 1px; }}
        .content {{ padding: 40px 30px; line-height: 1.6; }}
        .welcome-text {{ font-size: 18px; font-weight: 600; color: #1a1a1a; margin-bottom: 10px; }}
        .code-container {{ background-color: #f8faff; border: 2px dashed #007aff; border-radius: 12px; padding: 30px; text-align: center; margin: 30px 0; }}
        .code-label {{ font-size: 14px; color: #718096; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 2px; }}
        .code-value {{ font-size: 42px; font-weight: 800; color: #007aff; letter-spacing: 12px; margin: 0; font-family: 'Courier New', Courier, monospace; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #a0aec0; line-height: 1.5; }}
        .warning-box {{ background-color: #fffaf0; border-left: 4px solid #ed8936; padding: 15px; margin-top: 25px; border-radius: 4px; }}
        .warning-text {{ font-size: 13px; color: #744210; margin: 0; }}
        @media only screen and (max-width: 600px) {{
            .main {{ margin-top: 0 !important; border-radius: 0 !important; }}
            .code-value {{ font-size: 34px !important; letter-spacing: 8px !important; }}
        }}
    </style>
</head>
<body>
    <center class="wrapper">
        <table class="main">
            <tr>
                <td class="header">
                    <h1>CLOUD AIGC SERVICE</h1>
                    <p style="margin-top:10px; opacity: 0.8;">安全身份验证</p>
                </td>
            </tr>
            <tr>
                <td class="content">
                    <p class="welcome-text">尊敬的用户，您好！</p>
                    <p>您正在进行账户关键操作，请使用下方验证码完成身份校验。为了您的账户安全，切勿将此代码泄露给他人。</p>
                    
                    <div class="code-container">
                        <div class="code-label">您的验证码为</div>
                        <div class="code-value">{code}</div>
                    </div>

                    <div class="warning-box">
                        <p class="warning-text">
                            <strong>⚠️ 安全提醒：</strong><br>
                            • 该验证码将在 <strong>5分钟</strong> 后失效。<br>
                            • 如果这不是您本人操作，请及时检查账户安全或联系管理员。
                        </p>
                    </div>
                </td>
            </tr>
            <tr>
                <td class="footer">
                    <p>此邮件由系统自动生成，请勿直接回复</p>
                    <p>© {datetime.now().year} CLOUD AIGC Service Inc. All Rights Reserved.</p>
                </td>
            </tr>
        </table>
    </center>
</body>
</html>
'''
    try:

        # 核心：发送邮件（一行代码！）
        request.app.state.yagmail_qq.send(
            to=Email_form.email,  # 收件人
            subject=Email_form.subject,  # 主题
            # contents=email.body,  # 正文（HTML格式自动识别）
            contents=email_body
            # 如果需要发送附件，加 attachments 参数：attachments=["文件路径1", "文件路径2"]
        )
        logger.info(
            f"验证验证码发送成功 | 用户：{Email_form.email} | 发送验证码：{code} | Redis已存储验证码：{code_ver}")
        return reposen_model.BaseResponse(code=0, data={}, message=f"邮件发送成功")
    except Exception as e:
        await request.app.state.redis.delete(f"email:{Email_form.email}")
        raise HTTPException(status_code=500, detail=f"邮件发送失败：{str(e)}")


class EmailCode_verfy(BaseModel):
    email: EmailStr  # Pydantic 内置邮箱格式校验
    code: str = Field(
        ...,  # 必填字段
        pattern=r"^\d{6}$",  # 正则：恰好6位纯数字
        description="验证码，必须为6位数字字符串（支持前导零）"
    )

    # 可选：自定义邮箱域名白名单（防止无效/垃圾邮箱）
    @field_validator("email")
    def validate_email_domain(cls, v):
        allowed_domains = {"qq.com", "163.com", "gmail.com",
                           "126.com", "sina.com", "company.com"}
        domain = v.split("@")[-1]
        if domain not in allowed_domains:
            raise HTTPException(
                status_code=500, detail=f"邮箱域名不支持：{domain}，仅支持{allowed_domains}")
            # raise ValueError(f"邮箱域名不支持：{domain}，仅支持{allowed_domains}")
        return v


@router.post("/verfiy_code", summary="邮件验证码验证")
async def verfiy_code(Emailcode: EmailCode_verfy, request: Request):

    try:

        # code_ver = await request.app.state.redis.get(f"email:{Emailcode.email}")
        # logger.info(f"验证验证码 | 用户：{Emailcode.email} | 传入验证码：{Emailcode.code} | Redis存储验证码：{code_ver}")
        # # logger.info(type(code),type(code_ver))
        # if code_ver == None :
        #     raise HTTPException(status_code=401, detail="验证码不存在或已过期")
        # elif Emailcode.code!= str(code_ver):
        #     raise HTTPException(status_code=401, detail="验证码错误")
        # else:
        #     await request.app.state.redis.delete(f"email:{Emailcode.email}")
        await verfycode(request=request, email=Emailcode.email, code=Emailcode.code)
        return reposen_model.BaseResponse(code=0, data={}, message=f"验证码正确")
    except Exception as e:
        logger.info(e)


async def verfycode(request: Request, email: str, code: str, type: str = 'verfycode'):
    code_ver = await request.app.state.redis.get(f"email:{email}")
    logger.info(f"验证操作：{type} | 用户：{email} | 传入：{code} | Redis：{code_ver}")

    if code_ver is None:
        raise HTTPException(status_code=401, detail="验证码不存在或已过期")

    # 注意：Redis 取出的是 bytes，需要转换
    if code != str(code_ver):
        raise HTTPException(status_code=401, detail="验证码错误")

    # 验证成功逻辑
    if type == 'register':
        # 注册时在这里不删，等数据库入库成功后再删，或者确认验证通过后立即删
        await request.app.state.redis.delete(f"email:{email}")
    return True


class Register(BaseModel):
    email: EmailStr  # Pydantic 内置邮箱格式校验
    code: str = Field(
        ...,  # 必填字段
        pattern=r"^\d{6}$",  # 正则：恰好6位纯数字
        description="验证码，必须为6位数字字符串（支持前导零）"
    )
    username: str = Field(
        ...,  # 必填字段
        # pattern=r"^\d{6}$",  # 正则：恰好6位纯数字
        description="用户名"
    )

    password: str = Field(
        ...,  # 必填字段
        # pattern=r"^\d{6}$",  # 正则：恰好6位纯数字
        description="密码"
    )
    # 可选：自定义邮箱域名白名单（防止无效/垃圾邮箱）

    @field_validator("email")
    def validate_email_domain(cls, v):
        allowed_domains = {"qq.com", "163.com", "gmail.com",
                           "126.com", "sina.com", "company.com"}
        domain = v.split("@")[-1]
        if domain not in allowed_domains:
            raise HTTPException(
                status_code=500, detail=f"邮箱域名不支持：{domain}，仅支持{allowed_domains}")
            # raise ValueError(f"邮箱域名不支持：{domain}，仅支持{allowed_domains}")
        return v


@router.post("/register", summary="用户注册")
async def user_registration(User_reg_form: Register, request: Request):
    # 1. 校验验证码 (传入 type='register' 确保验证后删除 Redis 记录)
    await verfycode(
        request=request,
        email=User_reg_form.email,
        code=User_reg_form.code,
        type='register'
    )

    # 2. 检查用户是否已存在 (用户名 或 邮箱)
    existing_user = await User.filter(
        Q(username=User_reg_form.username) | Q(email=User_reg_form.email)
    ).first()

    if existing_user:
        detail = "用户名已存在" if existing_user.username == User_reg_form.username else "该邮箱已被注册"
        raise HTTPException(status_code=400, detail=detail)

    # 3. 密码加密 (bcrypt)
    password_bytes = User_reg_form.password.encode("utf-8")
    hashed_password = auth_jwt.bcrypt.hashpw(
        password_bytes, auth_jwt.bcrypt.gensalt())
    # 转为字符串存储
    pwd_str = hashed_password.decode("utf-8")

    # 4. 写入数据库
    try:
        new_user = await User.create(
            username=User_reg_form.username,
            password_hash=pwd_str,
            email=str(User_reg_form.email),
            roles=["R_USER"],
            buttons={"edit": True, "delete": False},
            is_admin=False,
            # is_active=False # 建议直接激活，或根据业务逻辑定
            # status='1'
        )
        logger.info(f"新用户注册成功: {new_user.username} (ID: {new_user.id})")

        return reposen_model.BaseResponse(
            code=0,
            data={"username": new_user.username},
            message="注册成功，请登录"
        )
    except Exception as e:
        logger.error(f"数据库写入失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误，请稍后再试")
