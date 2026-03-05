from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `accountlist` (
    `advertiser_id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '账户id',
    `advertiser_type` VARCHAR(255) NOT NULL COMMENT '账户类型',
    `advertiser_name` VARCHAR(255) NOT NULL COMMENT '账户名称',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID，自增主键',
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '登录账号（用户名），1-50个字符，唯一非空',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '加密后的密码（适配BCrypt/SHA256等算法）',
    `email` VARCHAR(128) COMMENT '用户邮箱（符合邮箱格式，业务层校验）',
    `create_by` VARCHAR(50) COMMENT '创建人（用户名/ID）' DEFAULT 'user_self',
    `update_by` VARCHAR(50) COMMENT '最后更新人（用户名/ID）',
    `user_gender` VARCHAR(2) NOT NULL COMMENT '用户性别（可选值：男/女/未知）' DEFAULT '未知',
    `nick_name` VARCHAR(50) NOT NULL COMMENT '用户昵称，最多50个字符' DEFAULT '',
    `user_phone` VARCHAR(11) COMMENT '用户手机号（11位数字字符串）',
    `roles` JSON NOT NULL COMMENT '角色代码列表（如：[\'R_SUPER\', \'R_USER\']）',
    `buttons` JSON NOT NULL COMMENT '按钮权限编码列表（如：[\'btn_add\', \'btn_edit\']）',
    `status` VARCHAR(1) NOT NULL COMMENT '账号状态（1=启用，2=禁用，3=锁定）' DEFAULT '1',
    `is_admin` BOOL NOT NULL COMMENT '账号为管理员' DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间（自动生成，格式：YYYY-MM-DD HH:MM:SS）' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后修改时间（自动更新）' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `get_clip_quota` INT NOT NULL COMMENT '素材查询次数' DEFAULT 0,
    KEY `idx_users_usernam_266d85` (`username`),
    KEY `idx_users_usernam_2eac0f` (`username`, `status`)
) CHARACTER SET utf8mb4 COMMENT='用户核心信息表（ORM 模型）';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
