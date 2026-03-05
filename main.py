from fastapi import FastAPI, File, Form, requests, UploadFile, HTTPException, BackgroundTasks, Request, Depends
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import os
import logging
from pathlib import Path
from tortoise import Tortoise
import urllib.parse
from tortoise.contrib.fastapi import register_tortoise
from app import app02, app03, app01, app04, app05, app06, app07, app08, app09, app10, app11
from contextlib import asynccontextmanager
from redis.asyncio import Redis, ConnectionPool
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from dotenv import load_dotenv
import sys
from fastapi.responses import JSONResponse
import yagmail
from tortoise.expressions import F
import httpx
from tortoise.exceptions import DoesNotExist, IntegrityError

# 配置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
load_dotenv('.env', override=False)

# 1. 定义一个拦截器类


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # 获取对应的 Loguru 级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找到调用者所在的帧，以便显示正确的行号
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage())


def setup_logging():
    # 2. 移除所有现有的标准日志处理程序
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)

    # 3. 拦截所有 Uvicorn 和 FastAPI 的日志
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # 4. 配置 Loguru
    logger.configure(handlers=[{"sink": sys.stdout, "serialize": False}])


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    env_dict = get_env()
    # 添加文件输出，并确保使用绝对路径
    if env_dict['running_in_docker'] == 'false':
        logger.add("fastapi_dev.log", rotation="10 MB",
                   level="INFO", enqueue=True)
    else:
        logger.add("fastapi_production.log", rotation="10 MB",
                   level="INFO", enqueue=True)

    @app.exception_handler(DoesNotExist)  # DoesNotExist查无此人
    async def sql_does_not_exist_handler(request, exc):
        return JSONResponse(
            status_code=404,
            content={"detail": "资源不存在", "message": str(exc)}
        )

    @app.exception_handler(IntegrityError)  # IntegrityError（完整性错误）
    async def sql_integrity_error_handler(request, exc):
        return JSONResponse(
            status_code=422,
            content={"detail": "数据完整性错误（如唯一键冲突）", "message": str(exc)}
        )

    # REDIS_CONFIG = {
    #     "host": env_dict['redis_host'],
    #     "port": 6379,
    #     "db": 0,
    #     "password": env_dict['dbredis_pw'],           # 如有密码请填写
    #     "decode_responses": True,  # 自动将字节转为 str
    #     "max_connections": 20,
    #     # "timeout": 10.0,       # 可选：连接超时
    # }
    # # redis链接
    # pool = ConnectionPool(**REDIS_CONFIG)
    # app.state.redis = Redis(connection_pool=pool)
    # try:
    #     await app.state.redis.ping()  # type: ignore
    #     logger.info("Redis 异步连接验证成功")
    # except Exception as e:
    #     logger.error(f"Redis 连接验证失败: {e}")

    # logger.info("✅ 异步 Redis 连接成功")
    # # ymail创建
    # try:
    #     yagmail_qq = yagmail.SMTP(
    #         user=env_dict.get('qq_email'),
    #         password=env_dict.get('qq_auth_code'),
    #         host="smtp.qq.com",
    #         port=465,  # SSL 端口（固定465）
    #         smtp_ssl=True  # 启用SSL加密
    #     )
    #     app.state.yagmail_qq = yagmail_qq
    #     logger.info("✅ qq mail 连接成功")
    # except Exception as e:
    #     # raise RuntimeError(f"QQ邮箱连接失败：{str(e)}")
    #     logger.error(f"QQ邮箱连接失败：{str(e)}")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(demo_task, "interval", hours=10)  # 每5秒执行一次
    scheduler.start()
    logger.info("定时任务启动")

    # orm
    await Tortoise.init(config=TORTOISE_ORM)
    logger.info("✅ Tortoise ORM 初始化完成")
    try:
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        app.state.http_client = httpx.AsyncClient(limits=limits, timeout=10.0)
        logger.info("✅ 外部服务连接池 HTTP初始化完成")
    except Exception as e:
        # raise RuntimeError(f"QQ邮箱连接失败：{str(e)}")
        logger.error(f"❌ 启动资源初始化失败: {e}")
        raise e

    yield

    # 🔴 异步清理：关闭 Redis 连接
    # await app.state.redis.close()
    logger.info("🔴 异步 Redis 连接关闭")
    await app.state.http_client.aclose()
    logger.info("🔴 部服务连接池 HTTP管理成功")
    scheduler.shutdown()
    logger.info("🔴 定时任务停止")
    await Tortoise.close_connections()
    logger.info("🔴 所有资源已清理")


def demo_task():
    # logger.info("I'm live ")
    pass


async def set_charset():
    # print("set UTF-8")
    pass


def get_env():
    running_in_docker = os.getenv('RUNNING_IN_DOCKER')
    redis_host = os.getenv('REDIS_HOST')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    dbredis_pw = os.getenv('DB_REDIS_PW')
    db_database = os.getenv('DB_DATABASE')
    qq_email = os.getenv('QQ_EMAIL')
    qq_auth_code = os.getenv('QQ_AUTH_CODE')
    return {
        'running_in_docker': running_in_docker,
        'redis_host': redis_host,
        'db_port': db_port,
        'db_host': db_host,
        'dbredis_pw': dbredis_pw,
        'db_database': db_database,
        'qq_email': qq_email,
        'qq_auth_code': qq_auth_code
    }


app = FastAPI(dependencies=[Depends(set_charset)], lifespan=lifespan)  # 全局依赖


def get_db_url():
    # load_dotenv('.env', override=False)
    env = get_env()
    user = "root"
    # 💡 再次强调：特殊字符密码必须转义
    password = urllib.parse.quote_plus(str(env.get('dbredis_pw', '')))

    print(password)
    host = env['db_host']
    port = env['db_port']
    db = env['db_database']
    return f"mysql://{user}:{password}@{host}:{port}/{db}"


# aerich init -t main.TORTOISE_ORM --location ./migrations
# aerich init-db
TORTOISE_ORM = {
    "connections": {"default": get_db_url()},
    "apps": {
        "models": {
            # 这里的 models 列表必须包含 aerich.models 才能使用迁移功能
            "models": ["orm.models", "aerich.models"],
            "default_connection": "default",
        },
    }, "use_tz": True,  # 改为 True
    "timezone": "Asia/Shanghai"  # 设置默认时区
}

# register_tortoise(
#     app,
#     config=TORTOISE_ORM,  # 直接传入上面定义的字典
#     generate_schemas=False,
#     add_exception_handlers=True,
# )
# logger.info("tortoise orm 连接成功")


# 创建上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

origins = [
    "http://localhost",
    "http://localhost:5173",   # 允许本地8080端口（常见前端开发端口）
    "http://127.0.0.1:8080",   # 允许本地5500端口（如VS Code Live Server）
    "http://localhost:3006",
    "http://127.0.0.1:3006",  # 例如前端静态页面的地址

]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的源列表
    allow_credentials=True,  # 允许携带 Cookie
    allow_methods=["*"],  # 允许所有 HTTP 方法（GET, POST, PUT 等）
    allow_headers=["*"],  # 允许所有请求头
)

# app.include_router(app01.router, prefix="/api/auth", tags=["登录"])
# app.include_router(app02.router, prefix="/api/user", tags=["user"])
# app.include_router(app03.router, prefix="/api/video", tags=["video"])
# app.include_router(
#     app04.router, prefix="/qianchuan/uni_promotion", tags=["千川"])
# app.include_router(app05.router, prefix="/report", tags=["zhenbuer数据"])
# app.include_router(app06.router, prefix="/violationrecord",
#                    tags=["violationrecord"])
# app.include_router(app07.router, prefix="/koc", tags=["koc"])
# app.include_router(app08.router, prefix="/get_data", tags=["get_data"])
# app.include_router(app09.router, prefix="/ad", tags=["ad"])
# app.include_router(app10.router, prefix="/feishusync", tags=["feishusync"])
# app.include_router(app11.router, prefix="/douyin", tags=["douyin解析服务"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,  # 这里就是你 raise 时写的内容
            "data": {}
        },
    )


@app.get('/')
async def root():
    logger.info("重定向到 /docs")
    return RedirectResponse(url='/docs')


@app.get('/test')
async def test():
    logger.info("test")
    return {test: "tets"}

# @app.get("/get_test")
# async def get_test(request):

#     conn = Tortoise.get_connection("default")
#     try:
#         await conn.execute_script("""
#             ALTER TABLE "uni_aweme_list"
#             ALTER COLUMN "created_at" TYPE TIMESTAMP WITH TIME ZONE;
#         """)
#         logger.info("🚀 数据库字段 created_at 已成功升级为带时区类型")
#     except Exception as e:
#         logger.warning(f"字段升级跳过或已存在: {e}")
#     # 如果输出是 'timestamp without time zone'，那就是方案一说的问题。
#     return


# @app.post("/post_test")
# async def post_test(req: Request, username: str = Form(..., description="用户名（必填）")):

#     print(username)
#     return "get"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000,
                reload=True, log_config=None)
#  uv run uvicorn main:app --host 0.0.0.0 --port 8003 --reload
