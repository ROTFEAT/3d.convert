#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from fastapi import APIRouter, HTTPException, Form
from urllib.parse import urlparse

from models.schemas import UniResponse
from service.task_manager import create_task
from utils.constants import SUPPORTED_FORMATS
from service.task_manager import *

# G-code转换支持的CAD格式
GCODE_SUPPORTED_CAD_FORMATS = {
    '.brep': 'BREP (Boundary Representation)',
    '.bep': 'BREP (Boundary Representation)',
    '.iges': 'IGES (Initial Graphics Exchange Specification)',
    '.igs': 'IGES (Initial Graphics Exchange Specification)',
    '.step': 'STEP (Standard for Exchange of Product Data)',
    '.stp': 'STEP (Standard for Exchange of Product Data)'
}

router = APIRouter(tags=["转换"])

from dr_worker import dramatiq_send_convert

@router.post("/convert", response_model=UniResponse)
async def convert_cad_file(
    file_url: str = Form(...),  # 修改为接收文件URL
    output_format: str = Form(...)
):
    """
    提交 CAD 文件转换任务
    
    - **file_url**: R2中已上传文件的URL
    - **output_format**: 输出格式 (例如: "step", "stl", "obj")
    
    返回:
    - 任务ID和状态信息
    """
    # 验证输出格式
    output_format = output_format.lower()
    if output_format not in SUPPORTED_FORMATS:
        return UniResponse(
            code=400,
            message="UnSupport format",
            data={}
        )
    try:
        # 从 URL 中提取文件名
        filename = os.path.basename(urlparse(file_url).path)
        # 创建转换任务
        task_id,task_info = create_task(file_url, output_format)
        print(task_id,"发送到dramatiq队列")
        #使用dramatiq消费
        dramatiq_send_convert.send(task_id,task_info)

        return UniResponse(
            code=200,
            message="create convert task",
            data=task_info,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"create task error: {str(e)}")

from models.schemas import TaskStatusResponse,Meta
@router.get("/convert/{task_id}", response_model=UniResponse)
async def get_task_info(task_id: str):
    """
    获取指定任务的状态和信息

    - **task_id**: 任务ID

    返回:
    - 任务状态和相关信息
    """
    task_info = get_task_status(task_id)

    if not task_info:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    # 将任务信息转换为响应格式
    response = UniResponse(
        code=200,
        message="ok",
        data=TaskStatusResponse(
            task_id=task_id,
            status=task_info.get("status"),
            input_file=task_info.get("input_file"),
            output_format = task_info.get("output_format"),
            created_at  = task_info.get("created_at"),
            updated_at = task_info.get("updated_at"),
            result_url = task_info.get("result_url"),
            error=task_info.get("error"),
        ),
        meta =Meta(
            timestamp=time.time()
        )
    )

    # 添加结果URL（如果有）
    # if "result_url" in task_info:
    #     response.result_url = task_info["result_url"]

    # 添加错误信息（如果有）
    # if "error" in task_info:
    #     response.error = task_info["error"]

    return response


@router.post("/convert/gcode", response_model=UniResponse)
async def convert_cad_to_gcode(
    file_url: str = Form(..., description="R2中已上传CAD文件的URL"),
    # 基本参数（常用）
    tool_diameter: float = Form(3.0, description="刀具直径 (mm)"),
    material: str = Form("aluminum", description="材料类型 (aluminum/steel/plastic)"),
    operation_type: str = Form("profile", description="加工类型 (profile/roughing/finishing)"),
    # 高级参数（可选）
    spindle_speed: int = Form(None, description="主轴转速 (RPM，留空使用默认值)"),
    feed_rate: int = Form(None, description="进给速度 (mm/min，留空使用默认值)"),
    plunge_rate: int = Form(None, description="下刀速度 (mm/min，留空使用默认值)"),
    safe_height: float = Form(None, description="安全高度 (mm，留空使用默认值)"),
    step_down: float = Form(None, description="每层切削深度 (mm，留空使用默认值)"),
    step_over: float = Form(None, description="步距比例 (0.1-0.8，留空使用默认值)"),
    use_coolant: bool = Form(None, description="是否使用冷却液（留空使用默认值）")
):
    """
    将CAD文件转换为G-code
    
    **必需参数:**
    - **file_url**: R2中已上传CAD文件的URL
    
    **基本参数:**
    - **tool_diameter**: 刀具直径 (mm, 默认3.0)
    - **material**: 材料类型 (aluminum/steel/plastic, 默认aluminum)
    - **operation_type**: 加工类型 (profile/roughing/finishing, 默认profile)
    
    **高级参数 (可选，留空则使用基于材料和加工类型的最佳默认值):**
    - **spindle_speed**: 主轴转速 (RPM)
    - **feed_rate**: 进给速度 (mm/min)
    - **plunge_rate**: 下刀速度 (mm/min)
    - **safe_height**: 安全高度 (mm)
    - **step_down**: 每层切削深度 (mm)
    - **step_over**: 步距比例 (0.1-0.8)
    - **use_coolant**: 是否使用冷却液
    
    **推荐使用方式:**
    - 初学者: 只设置 file_url, tool_diameter, material
    - 高级用户: 可以精确控制每个加工参数
    
    返回:
    - G-code文件的下载URL和加工参数信息
    """
    import tempfile
    import requests
    from urllib.parse import urlparse
    from service.gcode import cad_to_gcode, is_cad_file
    from service.r2_upload import upload_file_to_r2
    
    try:
        # 1. 从URL提取文件名
        parsed_url = urlparse(file_url)
        original_filename = os.path.basename(parsed_url.path)
        file_ext = os.path.splitext(original_filename)[1].lower()
        
        print(f"[INFO] 开始处理文件: {original_filename}")
        
        # 2. 检查是否为支持的CAD格式
        cad_extensions = set(GCODE_SUPPORTED_CAD_FORMATS.keys())
        mesh_extensions = {'.stl', '.obj', '.ply', '.3mf', '.off'}
        
        if file_ext not in cad_extensions:
            if file_ext in mesh_extensions:
                return UniResponse(
                    code=400,
                    message=f"不支持网格格式 {file_ext}，请使用CAD格式文件（STEP、IGES、BREP）",
                    data={}
                )
            else:
                return UniResponse(
                    code=400,
                    message=f"不支持的文件格式 {file_ext}",
                    data={}
                )
        
        # 3. 下载文件到临时目录
        print(f"[INFO] 下载文件: {file_url}")
        response = requests.get(file_url, timeout=300)  # 5分钟超时
        response.raise_for_status()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_input:
            temp_input.write(response.content)
            temp_input_path = temp_input.name
        
        print(f"[INFO] 文件下载完成: {len(response.content)} 字节")
        
        # 4. 验证是否为有效的CAD文件
        if not is_cad_file(temp_input_path):
            os.unlink(temp_input_path)
            return UniResponse(
                code=400,
                message="文件不是有效的CAD格式",
                data={}
            )
        
        # 5. 准备G-code转换参数
        # 先获取材料和操作类型的预设参数
        from service.gcode import get_machining_presets
        presets = get_machining_presets()
        
        # 根据材料和操作类型获取默认参数
        default_params = {}
        if material in presets and operation_type in presets[material]:
            default_params = presets[material][operation_type].copy()
        elif material in presets:
            # 如果没有指定操作类型的预设，使用第一个可用的
            first_operation = list(presets[material].keys())[0]
            default_params = presets[material][first_operation].copy()
            print(f"[INFO] 未找到{operation_type}预设，使用{first_operation}预设")
        else:
            # 使用aluminum的profile作为后备默认值
            default_params = presets['aluminum']['roughing'].copy()
            print(f"[INFO] 未找到{material}材料预设，使用铝合金预设")
        
        # 构建最终参数（用户提供的参数优先于默认值）
        gcode_params = {
            'tool_diameter': tool_diameter,
            'spindle_speed': spindle_speed if spindle_speed is not None else default_params.get('spindle_speed', 10000),
            'feed_rate': feed_rate if feed_rate is not None else default_params.get('feed_rate', 300),
            'plunge_rate': plunge_rate if plunge_rate is not None else default_params.get('plunge_rate', 100),
            'safe_height': safe_height if safe_height is not None else 5.0,
            'step_down': step_down if step_down is not None else default_params.get('step_down', 1.0),
            'step_over': step_over if step_over is not None else default_params.get('step_over', 0.6),
            'operation_type': operation_type,
            'material': material,
            'use_coolant': use_coolant if use_coolant is not None else default_params.get('use_coolant', False)
        }
        
        print(f"[INFO] 开始G-code转换，参数: {gcode_params}")
        
        # 6. 创建临时输出文件
        base_name = os.path.splitext(original_filename)[0]
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        # 7. 执行G-code转换
        success, result = cad_to_gcode(
            temp_input_path,
            temp_output_path,
            **gcode_params
        )
        
        # 清理输入文件
        os.unlink(temp_input_path)
        
        if not success:
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)
            return UniResponse(
                code=500,
                message=f"G-code转换失败: {result}",
                data={}
            )
        
        print(f"[INFO] G-code转换成功: {result}")
        
        # 8. 读取生成的G-code文件
        with open(temp_output_path, 'r', encoding='utf-8') as f:
            gcode_content = f.read()
        
        # 9. 上传到R2
        gcode_filename = f"{base_name}_{operation_type}.gcode"
        r2_key = f"gcode/{gcode_filename}"
        
        print(f"[INFO] 上传G-code到R2: {r2_key}")
        
        # 将G-code内容写入临时文件用于上传
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gcode', delete=False, encoding='utf-8') as upload_temp:
            upload_temp.write(gcode_content)
            upload_temp_path = upload_temp.name
        
        try:
            # 上传到R2
            upload_success, upload_result = upload_file_to_r2(upload_temp_path, r2_key)
            
            if not upload_success:
                return UniResponse(
                    code=500,
                    message=f"G-code文件上传失败: {upload_result}",
                    data={}
                )
            
            # 10. 使用上传函数返回的实际URL
            download_url = upload_result
            
            # 11. 获取文件统计信息
            gcode_lines = gcode_content.count('\n')
            gcode_size = len(gcode_content.encode('utf-8'))
            
            print(f"[SUCCESS] G-code生成完成: {download_url}")
            
            return UniResponse(
                code=200,
                message="G-code转换成功",
                data={
                    "download_url": download_url,
                    "filename": gcode_filename,
                    "file_size": gcode_size,
                    "line_count": gcode_lines,
                    "parameters": gcode_params,
                    "original_file": original_filename
                }
            )
            
        finally:
            # 清理临时文件
            if os.path.exists(upload_temp_path):
                os.unlink(upload_temp_path)
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)
    
    except requests.RequestException as e:
        return UniResponse(
            code=400,
            message=f"文件下载失败: {str(e)}",
            data={}
        )
    except Exception as e:
        # 清理可能残留的临时文件
        for temp_path in [temp_input_path, temp_output_path]:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        return UniResponse(
            code=500,
            message=f"G-code转换失败: {str(e)}",
            data={}
        )

@router.get("/convert/gcode/supported-formats", response_model=UniResponse)
async def get_gcode_supported_formats():
    """
    获取G-code转换器支持的CAD文件格式
    
    返回:
    - 支持的CAD格式列表
    """
    try:
        # 提取格式名称（去掉点号）
        supported_formats = [ext.lstrip('.') for ext in GCODE_SUPPORTED_CAD_FORMATS.keys()]
        # 排序
        supported_formats.sort()
        
        return UniResponse(
            code=200,
            message="获取支持格式成功",
            data={
                "supported_formats": supported_formats
            }
        )
    
    except Exception as e:
        return UniResponse(
            code=500,
            message=f"获取支持格式失败: {str(e)}",
            data={}
        )

