from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, crawler

app = FastAPI(
    title="Job Hunter API Gateway",
    description="职位信息猎手 API 网关",
    version="1.0.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置请求超时时间（单位：秒）
app.middleware("http")


async def timeout_middleware(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        raise e
    finally:
        request.scope["state"].setdefault("timeout", 3600)  # 设置为 1 小时


# 注册路由
app.include_router(auth.router, prefix="/api/v1", tags=["认证"])
app.include_router(crawler.router, prefix="/api/v1", tags=["爬虫管理"])


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
