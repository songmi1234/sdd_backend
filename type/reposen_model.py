from pydantic import BaseModel, EmailStr, Field, field_validator, field_serializer
from datetime import datetime
from typing import Optional, List, Union, Any
from enum import Enum

from datetime import datetime, timezone, timedelta
BEIJING_TZ = timezone(timedelta(hours=8))


class LoginResponse(BaseModel):
    """登录成功时的最终响应模型"""
    code: int = 0
    data: dict
    message: str = "登录成功"


class BaseResponse(BaseModel):
    """登录成功时的最终响应模型"""
    code: int = 0
    data: Union[Any, str] = None
    message: str = "登录成功"


class UserStatus(str, Enum):
    """用户状态枚举（和前端约定的状态值对齐）"""
    ENABLE = "1"    # 启用
    DISABLE = "2"   # 禁用
    LOCKED = "3"    # 锁定（可选：扩展状态）

    # 可选：添加语义描述，方便前端展示

    @property
    def desc(self):
        desc_map = {
            self.ENABLE: "启用",
            self.DISABLE: "禁用",
            self.LOCKED: "锁定"
        }
        return desc_map[self]


class UserGender(str, Enum):
    """用户性别枚举，对接 ORM 和 Pydantic"""
    MALE = "男"
    FEMALE = "女"
    UNKNOWN = "未知"


# 1. 类名遵循大驼峰命名法（PEP8规范），去掉下划线更符合Python习惯
class UserInfo(BaseModel):
    """用户信息模型（适配前端返回格式）"""
    # 核心必填字段
    id: int = Field(..., ge=1, description="用户ID，正整数")
    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="用户名，1-50个字符",
        alias='userName'  # 映射前端userName
    )
    email: Optional[EmailStr] = Field(
        None,
        description="用户邮箱，符合邮箱格式规范",
        alias='userEmail'  # 映射前端userEmail
    )

    # 基础必填字段（补充updateTime，前端需要）
    create_by: Optional[str] = Field("系统", alias='createBy')
    update_by: Optional[str] = Field("系统", alias='updateBy')
    created_at: datetime = Field(
        ...,
        description="创建时间（自动生成，格式：YYYY-MM-DD HH:MM:SS）",
        alias='createTime'  # 映射前端createTime
    )

    updated_at: datetime = Field(
        ...,
        description="最后更新时间（自动生成，格式：YYYY-MM-DD HH:MM:SS）",
        alias='updateTime'  # 补充前端需要的updateTime字段
    )

    # 状态字段（前端status是字符串，调整类型+alias）
    status: UserStatus = Field(
        ...,
        description="账号状态（如2=禁用，1=启用）",
        alias='status'  # 显式声明alias，和前端字段名一致
    )

    # 可选字段
    user_gender: Optional[UserGender] = Field(
        '未知',
        description="用户性别，可选值：男/女/未知",
        alias='userGender'  # 映射前端userGender
    )
    nick_name: Optional[str] = Field(
        "",
        max_length=50,
        description="用户昵称，最多50个字符",
        alias='nickName'  # 映射前端nickName
    )
    user_phone: Optional[str] = Field(  # 改为str，适配前端字符串手机号
        "13000000000",
        pattern=r"^1[3-9]\d{9}$",  # 11位手机号正则校验
        description="用户手机号，11位数字字符串",
        alias='userPhone'  # 映射前端userPhone
    )

    # 角色字段（映射前端userRoles）
    roles: List[str] = Field(
        [],
        min_items=1,
        description="用户角色列表，至少包含1个角色（如：['R_SUPER', 'user']）",
        alias='userRoles'  # 映射前端userRoles
    )

    class Config:
        populate_by_name = True
        # --- 修复 3: 忽略多余字段 ---
        # 报错提示 password_hash, buttons 等多余，改成 ignore 就不报错了
        extra = "ignore"

    @field_serializer('created_at', 'updated_at')
    def serialize_dt(self, dt: datetime):
        # .astimezone() 确保它转成北京时间（如果是本地运行通常会自动对齐）
        # strftime 的全称是 String Format Time，意思就是“把时间格式化为字符串”。
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @field_validator('user_phone', mode='before')
    @classmethod
    def set_default_phone(cls, v):
        # 如果值是 None 或者空字符串，就返回默认手机号
        return v or "13000000000"
