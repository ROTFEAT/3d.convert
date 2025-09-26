#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from typing import List, Optional
from pydantic import BaseModel, Field

from models.schemas import TaskStatusResponse, QueueStatsResponse, UniResponse
from service.task_manager import get_task_status, get_queue_stats, TASK_STATUS, get_queued_tasks as fetch_queued_tasks

router = APIRouter(tags=["任务管理"])

@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_info(task_id: str):
    """
    获取指定任务的状态和信息
    
    - **task_id**: 任务ID
    
    返回:
    - 任务状态和相关信息
    """
    print("")
    task_info = get_task_status(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    # 将任务信息转换为响应格式
    response = TaskStatusResponse(
        task_id=task_id,
        status=task_info.get("status", "unknown"),
        input_file=task_info.get("input_file"),
        output_format=task_info.get("output_format"),
        created_at=float(task_info.get("created_at", 0)),
        updated_at=float(task_info.get("updated_at", 0)),
    )
    
    # 添加结果URL（如果有）
    if "result_url" in task_info:
        response.result_url = task_info["result_url"]
    
    # 添加错误信息（如果有）
    if "error" in task_info:
        response.error = task_info["error"]
    
    return response


@router.get("/download/{task_id}")
async def download_result(task_id: str):
    """
    下载转换后的文件
    
    - **task_id**: 任务ID
    
    返回:
    - 文件下载响应或重定向到R2存储URL
    """
    task_info = get_task_status(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    if task_info.get("status") != TASK_STATUS["COMPLETED"]:
        raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {task_info.get('status')}")
    
    # 检查是否有结果URL
    if "result_url" in task_info:
        # 返回重定向到R2文件URL
        return RedirectResponse(url=task_info["result_url"])
    else:
        raise HTTPException(status_code=404, detail="任务结果文件不存在")

@router.get("/queue/stats", response_model=QueueStatsResponse)
async def queue_statistics():
    """获取队列统计信息"""
    return get_queue_stats()

# 添加任务列表响应模型
# class TaskListResponse(BaseModel):
#     tasks: List[TaskStatusResponse] = Field(default_factory=list)
#     count: int = 0
@router.get("/tasks/queued/{max_count}", response_model=UniResponse)
async def get_queued_tasks(max_count: int = 10):
    """
    获取指定数量的等待中的任务
    
    - **max_count**: 最大返回任务数量，默认为10
    
    返回:
    - 等待中的任务列表
    """
    # 限制最大获取数量，防止请求过大
    if max_count > 100:
        max_count = 100
        
    # 将函数名改为 fetch_queued_tasks 避免递归调用
    tasks_data = fetch_queued_tasks(max_count)
    
    # 将任务数据转换为响应模型
    tasks = []
    for task_data in tasks_data:
        task = TaskStatusResponse(
            task_id=task_data["task_id"],
            status=task_data["status"],
            input_file=task_data["input_file"],
            output_format=task_data["output_format"],
            created_at=task_data["created_at"],
            updated_at=task_data["updated_at"],
            result_url=task_data["result_url"],
            error=task_data["error"]
        )
        tasks.append(task)
    
    return UniResponse(
        code="200",
        message="OK",
        data=tasks
    )