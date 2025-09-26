#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import redis
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 最大重试次数
MAX_RETRY = 3
RETRY_INTERVAL = 2  # 秒

def check_redis_connection():
    """
    检查Redis连接是否可用
    返回: (成功状态, 错误信息)
    """
    # 获取Redis URL
    redis_url = os.getenv('REDIS_URL', 'redis://:redis123@redis:6379/0')
    
    # 尝试连接Redis
    retry_count = 0
    last_error = None
    
    while retry_count < MAX_RETRY:
        try:
            redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            redis_client.ping()  # 测试连接
            print(f"已成功连接到Redis: {redis_url}")
            return True, None
        except redis.AuthenticationError as e:
            # 认证错误通常需要修改配置，不再重试
            return False, f"Redis认证错误: {str(e)}\n请检查环境变量中的REDIS_URL配置"
        except redis.ConnectionError as e:
            # 连接错误可能是暂时的，可以重试
            last_error = f"Redis连接错误: {str(e)}"
            retry_count += 1
            print(f"无法连接到Redis，正在重试 ({retry_count}/{MAX_RETRY})...")
            time.sleep(RETRY_INTERVAL)
        except Exception as e:
            # 其他错误
            last_error = f"Redis错误: {str(e)}"
            retry_count += 1
            print(f"连接Redis时发生错误，正在重试 ({retry_count}/{MAX_RETRY})...")
            time.sleep(RETRY_INTERVAL)
    
    return False, last_error

# 在模块导入时执行连接检查
success, error_message = check_redis_connection()
if not success:
    print(f"错误: 无法连接到Redis服务器 - {error_message}")
    print("应用将继续启动，但功能可能受限")
    # 对于关键应用，可以取消下面的注释来使应用在Redis连接失败时退出
    # sys.exit(1)
