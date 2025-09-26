#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import uuid
import redis
import json
from dotenv import load_dotenv
import random
import secrets
from datetime import datetime

# 连接Redis
redis_client = redis.Redis.from_url(
    os.getenv('REDIS_URL', 'redis://:redis123@redis:6379/0'),
    decode_responses=True  # 自动将响应解码为字符串
)

# 任务状态常量
TASK_STATUS = {
    "QUEUED": "QUEUED",      # 任务已提交，等待worker获取
    "PENDING": "PENDING",   #
    "PROCESSING": "PROCESSING",   # worker已获取任务并开始处理
    "COMPLETED": "COMPLETED",    # 任务处理完成
    "FAILED": "FAILED",        # 任务处理失败
    "TIMEOUT": "TIMEOUT"        # 任务处理超时
}

# 任务列表键名
TASK_QUEUE_KEY = "cad_conversion_tasks"
# 任务计数器键名
TASK_COUNTER_KEY = "cad_conversion_task_counter"
from api.models.schemas import TaskStatusResponse


def generate_task_id():
    task_number = redis_client.incr(TASK_COUNTER_KEY)
    random_id = str(uuid.uuid4())[:8]
    return f"{int(time.time())}-{task_number}-{random_id}"

def create_task(input_file_url, output_format):
    """
    创建新的转换任务
    
    Args:
        input_file_url: R2中文件的URL
        output_format: 期望的输出格式
        
    Returns:
        task_id: 生成的任务ID
    """
    task_id = generate_task_id() #随机任务id
    
    # 创建任务信息

    task_info = TaskStatusResponse(
        task_id=task_id,
        status=TASK_STATUS["QUEUED"],
        input_file=input_file_url,
        output_format=output_format,
        created_at=time.time(),
        updated_at=time.time(),
        result_url="",
        error=""
    )

    redis_client.hset(f"task:{task_id}", mapping=task_info.model_dump())#转为字典
    redis_client.expire(f"task:{task_id}", 300)
    print(f"任务已创建: {task_id} (将 {input_file_url} 转换为 {output_format})")

    #使用dramatiq消费


    return task_id,task_info.model_dump()

    # task_info = {
    #     "id": task_id,
    #     "input_file": input_file_url,  # 存储 R2 文件 URL
    #     "output_format": output_format,
    #     "status": TASK_STATUS["QUEUED"],
    #     "created_at": time.time(),
    #     "updated_at": time.time(),
    # }
    
    # 保存任务信息到Redis

    
    # # 将任务添加到队列中
    # task_data = {
    #     "id": task_id,
    #     "input_file": input_file_url,
    #     "output_format": output_format,
    # }
    #
    # redis_client.lpush(TASK_QUEUE_KEY, json.dumps(task_data))


    # 设置TTL为5分钟(300秒)

    

    # return task_id,task_info

def clear_redis():
    r = redis.Redis.from_url(
        os.getenv('REDIS_URL', 'redis://:redis123@redis:6379/0'),
        decode_responses=True,
    )
    r.flushdb()  # 只清空当前 db
    print(f"Redis database has been cleared.")


def get_task_status(task_id):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        task_info: 任务状态信息字典，如果任务不存在则返回None
    """
    # 检查任务是否存在
    if not redis_client.exists(f"task:{task_id}"):
        return None
        
    # 获取任务信息
    task_info = redis_client.hgetall(f"task:{task_id}")
    return task_info

def update_task_status(task_id, status, **additional_info):
    """
    更新任务状态
    
    Args:
        task_id: 任务ID
        status: 新状态
        additional_info: 其他信息字段，如结果URL等
        
    Returns:
        success: 是否成功更新
    """
    # 检查任务是否存在
    if not redis_client.exists(f"task:{task_id}"):
        return False
    
    # 更新状态和时间戳
    update_data = {
        "status": status,
        "updated_at": time.time()
    }
    
    # 添加额外信息
    update_data.update(additional_info)
    
    # 更新Redis中的任务信息
    redis_client.hset(f"task:{task_id}", mapping=update_data)
    return True

def get_next_task():
    """
    从队列中获取下一个待处理任务
    
    Returns:
        task_data: 任务数据字典，队列为空则返回None
    """
    # 从队列右端弹出一个任务（FIFO模式）
    task_json = redis_client.rpop(TASK_QUEUE_KEY)
    
    if not task_json:
        return None
    
    # 解析任务数据
    try:
        task_data = json.loads(task_json)
        # 将任务状态更新为处理中
        update_task_status(task_data["id"], TASK_STATUS["PROCESSING"])
        return task_data
    except Exception as e:
        print(f"解析任务数据失败: {e}")
        return None

def requeue_task(task_id):
    """
    将任务重新加入队列（用于失败重试）
    
    Args:
        task_id: 任务ID
        
    Returns:
        success: 是否成功重新入队
    """
    # 获取任务信息
    task_info = get_task_status(task_id)
    
    if not task_info:
        return False
    
    # 创建队列任务数据
    task_data = {
        "id": task_id,
        "input_file": task_info["input_file"],
        "output_format": task_info["output_format"],
        "retry": True  # 标记为重试任务
    }
    
    # 更新状态为队列中
    update_task_status(task_id, TASK_STATUS["QUEUED"], retry_count=int(task_info.get("retry_count", 0))+1)
    
    # 将任务添加到队列
    redis_client.lpush(TASK_QUEUE_KEY, json.dumps(task_data))
    return True

def cleanup_old_tasks(days=7):
    """
    清理指定天数之前的任务记录
    
    Args:
        days: 超过多少天的任务将被清理
    """
    # 计算截止时间戳
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    # 获取所有任务键
    task_keys = redis_client.keys("task:*")
    
    for key in task_keys:
        # 获取任务创建时间
        created_at = float(redis_client.hget(key, "created_at") or 0)
        
        # 如果任务创建时间早于截止时间，则删除
        if created_at < cutoff_time:
            redis_client.delete(key)
            print(f"已清理过期任务: {key}")

def get_queue_stats():
    """
    获取队列统计信息
    
    Returns:
        stats: 队列统计信息字典
    """
    # 获取队列长度
    queue_length = redis_client.llen(TASK_QUEUE_KEY)
    
    # 获取各状态任务数量
    status_counts = {}
    for status_key, status_value in TASK_STATUS.items():
        # 使用Redis的SCAN命令进行模式匹配查询，效率比keys高
        count = 0
        cursor = 0
        pattern = f"task:*"
        
        while True:
            cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
            for key in keys:
                task_status = redis_client.hget(key, "status")
                if task_status == status_value:
                    count += 1
            
            if cursor == 0:
                break
        
        status_counts[status_key] = count
    
    return {
        "queue_length": queue_length,
        "status_counts": status_counts,
        "current_time": time.time()
    }

def get_queued_tasks(max_count):
    """
    获取指定数量的等待中的任务
    
    Args:
        max_count: 最大返回任务数量
        
    Returns:
        tasks: 任务信息列表
    """
    # 获取所有任务键
    all_task_keys = redis_client.keys("task:*")
    queued_tasks = []
    
    # 遍历所有任务，查找状态为 QUEUED 的任务
    for task_key in all_task_keys:
        task_data = redis_client.hgetall(task_key)
        
        # 检查任务状态是否为 QUEUED
        if task_data and task_data.get("status") == TASK_STATUS["QUEUED"]:
            # 提取任务ID
            task_id = task_key.split(":")[-1]
            
            # 构建任务信息对象
            task_info = {
                "task_id": task_id,
                "status": task_data.get("status", "unknown"),
                "input_file": task_data.get("input_file", ""),
                "output_format": task_data.get("output_format", ""),
                "created_at": float(task_data.get("created_at", 0)),
                "updated_at": float(task_data.get("updated_at", 0)),
                "result_url": task_data.get("result_url", ""),
                "error": task_data.get("error", "")
            }
            
            queued_tasks.append(task_info)
            
            # 如果已达到最大数量，停止查找
            if len(queued_tasks) >= max_count:
                break
    
    return queued_tasks 