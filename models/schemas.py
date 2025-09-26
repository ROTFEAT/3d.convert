#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional, Dict
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")  # 这是一个类型占位符

class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str
    status: str
    input_file: Optional[str] = None
    output_format: Optional[str] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    result_url: Optional[str] = None
    error: Optional[str] = None

class Meta(BaseModel):
    """元信息"""
    timestamp: Optional[float] = None   # 返回时间戳
    request_id: Optional[str] = None  # 追踪日志用
    duration: Optional[int] = None    # 接口处理耗时（ms）
    api_version: Optional[str] = None # 当前接口版本号

class SignResponse(BaseModel):
    key:str #key
    upload_url:str  #上传地址
    download_url:str


class UniResponse(BaseModel):
    """统一返回结构"""
    code:int
    message:str
    data:Optional[T]
    meta:Optional[Meta] = None


class QueueStatsResponse(BaseModel):
    """队列统计响应模型"""
    queue_length: int
    status_counts: Dict[str, int]
    current_time: float
import  time
from service.task_manager import *
import json

if __name__ == '__main__':
    task_info = TaskStatusResponse(
        task_id ="sadasd",
        status =  "QUEUED"
    )

    # dic = task_info.dict()

    redis_client.hset(f"task_id{task_info.id}"
                      ,mapping = {k: str(v) for k, v in task_info.model_dump().items() if v is not None}
                      )

    a = task_info
