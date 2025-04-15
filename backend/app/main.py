from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from .api.routes import router as api_router
from .core.config import settings
from .core.database import connect_to_mongodb, close_mongodb_connection

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000", "http://localhost:8080"],  # 明确包含前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 挂载API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 创建下载和预览目录
docs_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_docs"))
logger.info(f"文档生成路径: {docs_path}")
os.makedirs(docs_path, exist_ok=True)

# 确保目录具有正确的权限
os.chmod(docs_path, 0o777)

# 挂载静态文件服务
app.mount("/downloads", StaticFiles(directory=docs_path), name="downloads")
app.mount("/previews", StaticFiles(directory=docs_path), name="previews")

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Doc Platform API"}

@app.get("/api/health")
def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

# 启动事件
@app.on_event("startup")
async def startup_db_client():
    """启动时连接数据库"""
    await connect_to_mongodb()

# 关闭事件
@app.on_event("shutdown")
async def shutdown_db_client():
    """关闭时断开数据库连接"""
    await close_mongodb_connection()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True) 