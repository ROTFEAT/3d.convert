#公网部署
import os
import time
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from config import *
# from prometheus_client import start_http_server, Gauge
import json
from datetime import datetime
# 导入路由
from router import conversion, tasks, worker, common,r2
from utils.constants import BASE_URL
from service.task_manager import redis_client

# 添加调试功能
from utils.debug import print_environment_variables
print("=== API 服务启动 - 环境变量检查 ===")
print_environment_variables()

app = FastAPI(title="CAD 文件格式转换 API",
              description="上传 CAD 文件并异步转换为其他格式",
              # docs_url=None,       # 禁用 Swagger UI (/docs)
              # redoc_url=None,      # 禁用 ReDoc 文档 (/redoc)
              # openapi_url=None     # 禁用 OpenAPI schema (/openapi.json)
              )

# 设置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由
app.include_router(conversion.router)
app.include_router(r2.router)
app.include_router(tasks.router)
app.include_router(worker.router)
app.include_router(common.router)

from service.redis_check import *

def update_task_status(task_id, status, **kwargs):
    """更新任务状态到Redis"""
    try:
        # 获取现有任务
        redis_key = f"task:{task_id}"
        task_json = redis_client.get(redis_key)
        if not task_json:
            return False
        # 检查并保存剩余TTL
        remaining_ttl = redis_client.ttl(redis_key)
        print(f"task_{redis_key}:",remaining_ttl)
        
        task = json.loads(task_json)
        
        # 更新状态和其他字段
        task["status"] = status
        task["updated_at"] = datetime.now().isoformat()

        print(f"更新状态{redis_key}")
        # 更新其他提供的字段
        for key, value in kwargs.items():
            task[key] = value
            
        # 保存回Redis
        redis_client.set(redis_key, json.dumps(task))
        
        # 如果原来有TTL并且是有效值，重新设置相同的TTL
        if remaining_ttl > 0:
            redis_client.expire(redis_key, remaining_ttl)
        else:
            # 如果没有TTL或TTL已过期，设置默认5分钟
            redis_client.expire(redis_key, 300)
            
        return True
    except Exception as e:
        print(f"更新任务状态失败: {str(e)}")
        return False
from service.task_manager import clear_redis
if __name__ == "__main__":
    clear_redis()
    print(f"服务启动: 基础URL为 {API_BASE_URL}")
    print("分布式队列服务已启动，等待Worker连接处理任务")
    select_prot = 6666
    print(f"服务启动: 使用接口为 {select_prot}")
    uvicorn.run("app:app", host="0.0.0.0", port=select_prot)