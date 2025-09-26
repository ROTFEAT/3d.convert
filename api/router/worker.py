#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional
from fastapi import APIRouter, HTTPException

from api.service.task_manager import update_task_status

router = APIRouter(prefix="/worker", tags=["Worker API"])

@router.get("/next-task")
async def get_next_task_api():
    """
    Worker API: 获取下一个待处理任务
    
    返回:
    - 任务数据或空对象
    """
    from api.service.task_manager import get_next_task
    
    task = get_next_task()
    if not task:
        return {"message": "No tasks available"}
    
    return task


from api.service.worker import claim_task_with_lua
from fastapi.responses import JSONResponse
#尝试确定一个task 如果可以就处理了
@router.get("/claim/{task_id}")
async def get_task_api(task_id: str):
    if not claim_task_with_lua(task_id):
        return JSONResponse(
            status_code=400,
            content={"message": "No tasks available"},
        )
    else:
        return JSONResponse(
            status_code=200,
            content={"message": "OK"},
        )
# @router.get("/tasks")
# async  def get_tasks(max_task:str)

@router.post("/update-task/{task_id}")
async def update_task_api(
    task_id: str, 
    status: str, 
    result_url: str = None, 
    error: str = None
):
    """
    Worker API: 更新任务状态
    
    - **task_id**: 任务ID
    - **status**: 新状态
    - **result_url**: 结果文件URL（可选）
    - **error**: 错误信息（可选）
    
    返回:
    - 更新状态
    """
    update_data = {}
    if result_url:
        update_data["result_url"] = result_url
    if error:
        update_data["error"] = error
        
    success = update_task_status(task_id, status, **update_data)
    
    if success:
        return {"status": "success", "message": f"任务 {task_id} 状态已更新为 {status}"}
    else:
        return {"status": "error", "message": f"更新任务 {task_id} 状态失败"} 