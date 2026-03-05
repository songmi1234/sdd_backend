from email.policy import default
from enum import unique
from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from type import reposen_model
from tortoise.models import Model


class User(models.Model):
    """
    用户核心信息表（ORM 模型）
    对齐前端返回的 UserInfo 模型字段，补充缺失字段+规范约束
    """
    # 核心主键
    id = fields.IntField(pk=True, description="用户ID，自增主键")

    # 登录基础信息（对齐 UserInfo）
    username = fields.CharField(
        max_length=50,
        unique=True,
        index=True,
        null=False,
        description="登录账号（用户名），1-50个字符，唯一非空"
    )
    password_hash = fields.CharField(
        max_length=255,
        null=False,
        description="加密后的密码（适配BCrypt/SHA256等算法）"
    )
    email = fields.CharField(
        max_length=128,
        null=True,
        description="用户邮箱（符合邮箱格式，业务层校验）"
    )

    create_by = fields.CharField(
        max_length=50,
        null=True,
        default='user_self',
        description="创建人（用户名/ID）"
    )
    update_by = fields.CharField(
        max_length=50,
        null=True,
        description="最后更新人（用户名/ID）"
    )

    # 性别字段（对齐 UserInfo，用枚举约束值）
    user_gender = fields.CharEnumField(
        reposen_model.UserGender,
        default=reposen_model.UserGender.UNKNOWN,
        description="用户性别（可选值：男/女/未知）"
    )
    # 昵称字段（对齐 UserInfo）
    nick_name = fields.CharField(
        max_length=50,
        default="",
        description="用户昵称，最多50个字符"
    )
    # 手机号字段（对齐 UserInfo，字符串类型+11位约束）
    user_phone = fields.CharField(
        max_length=11,
        null=True,
        description="用户手机号（11位数字字符串）"
    )

    # 权限相关（优化默认值+约束）
    roles = fields.JSONField(
        default=["R_USER"],  # 默认普通用户，避免null
        description="角色代码列表（如：['R_SUPER', 'R_USER']）"
    )
    buttons = fields.JSONField(
        default=[],  # 默认空数组，统一类型
        description="按钮权限编码列表（如：['btn_add', 'btn_edit']）"
    )

    # 状态控制（新增status字段，或基于is_active映射）
    # 方案1：新增status字段（直接对齐前端，推荐）
    status = fields.CharEnumField(
        reposen_model.UserStatus,
        default=reposen_model.UserStatus.ENABLE,
        description="账号状态（1=启用，2=禁用，3=锁定）"
    )

    is_admin = fields.BooleanField(default=False, description="账号为管理员")
    #
    # @property
    # def status(self) -> str:
    #     """从is_active映射为前端需要的status值"""
    #     return UserStatus.ENABLE.value if self.is_active else UserStatus.DISABLE.value

    # 时间审计字段（对齐 UserInfo 的 create_time/update_time）
    created_at = fields.DatetimeField(
        auto_now_add=True,
        description="创建时间（自动生成，格式：YYYY-MM-DD HH:MM:SS）"
    )
    updated_at = fields.DatetimeField(
        auto_now=True,
        description="最后修改时间（自动更新）"
    )
    get_clip_quota = fields.IntField(
        default=0, description="素材查询次数"
    )

    class Meta:
        table = "users"  # 数据库表名
        ordering = ["-created_at"]  # 按创建时间倒序
        indexes = (
            ("username", "status"),
        )
        description = "用户核心信息表（含基础信息、权限、状态）"

    # def __str__(self) -> str:
    #     """自定义字符串表示，便于日志/调试"""
    #     return f"User<{self.id}: {self.username}>"

    # def __repr__(self) -> str:
    #     """详细调试信息"""
    #     return f"User(id={self.id}, username='{self.username}', status='{self.status.value}', email='{self.email}')"

    # # 扩展：常用业务方法（对齐权限/状态逻辑）
    # def has_role(self, role_code: str) -> bool:
    #     """检查是否拥有指定角色"""
    #     return role_code in self.roles

    # def set_status(self, new_status: UserStatus) -> None:
    #     """更新状态（封装逻辑）"""
    #     self.status = new_status
    #     # 若保留is_active，同步更新
    #     # if new_status == UserStatus.ENABLE:
    #     #     self.is_active = True
    #     # else:
    #     #     self.is_active = False
# 5. 自动生成 Pydantic 模型（排除敏感字段）
# 这样你在 FastAPI 返回时直接用 User_Pydantic，就不会泄露密码哈希
User_Pydantic = pydantic_model_creator(
    User, name="User", exclude=("password_hash",))


class AccountList(Model):
    advertiser_id = fields.BigIntField(pk=True, description='账户id')  # 设为主键
    advertiser_type = fields.CharField(max_length=255, description='账户类型')
    advertiser_name = fields.CharField(max_length=255, description='账户名称')
    created_at = fields.DatetimeField(auto_now=True, description="创建时间")
