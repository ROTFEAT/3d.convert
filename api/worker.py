#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import requests
import shutil
import uuid  # 添加uuid模块用于生成随机文件名
from dotenv import load_dotenv
import traceback
import random
import string
# 加载环境变量
load_dotenv()
# 导入转换函数
# 导入R2上传函数
from api.service.r2_upload import upload_file_to_r2
# API基础URL
from config import *
#本机部署的服务
# 去除URL末尾的斜杠




def get_next_task():
    """从API获取下一个待处理任务"""
    try:
        response = requests.get(f"{API_BASE_URL}/worker/next-task")
        
        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                return data
                
        return None
    except Exception as e:
        print(f"获取任务失败: {str(e)}")
        return None


def update_task_status(task_id, status, result_url=None, error=None):
    """更新任务状态到API服务器"""
    print(f"更新任务{task_id}",status)
    try:
        params = {"status": status}
        if result_url:
            params["result_url"] = result_url
        if error:
            params["error"] = error
        response = requests.post(
            f"{API_BASE_URL}/worker/update-task/{task_id}",
            params=params
        )
        
        return response.status_code == 200
    except Exception as e:
        print(f"更新任务状态失败: {str(e)}")
        return False

def clear_temp_folders():
    """清除input、tmp和output临时文件夹"""
    folders_to_clear = ["input", "tmp", "output"]
    for folder in folders_to_clear:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
    print("已清除临时文件")

def download_file(file_url, target_path):
    """直接从URL下载文件到指定路径"""
    try:
        # 确保目标目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 使用requests直接下载
        response = requests.get(file_url, stream=True)
        response.raise_for_status()  # 如果HTTP请求返回了不成功的状态码，将抛出异常
        
        # 写入文件
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = os.path.getsize(target_path)
        print(f"文件下载成功，大小: {file_size} 字节")
        return True, target_path
    except Exception as e:
        error_msg = f"下载文件失败: {str(e)}"
        print(error_msg)
        return False, error_msg


def process_task(task_id, input_file_url, output_format):
    """处理单个转换任务"""
    print(f"开始处理任务 {task_id}")
    
    # 更新任务状态为处理中
    # update_task_status(task_id, "PROCESSING")
    
    # 临时文件路径
    input_filename = os.path.basename(input_file_url.split('?')[0])  # 从URL中提取文件名，去除查询参数
    input_file_path = os.path.join(TMP_DIR, input_filename)
    
    # 构造带有随机前缀的输出文件名
    base_name = os.path.splitext(input_filename)[0]
    random_prefix = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
    output_filename = f"{random_prefix}_{base_name}.{output_format}"
    output_file_path = os.path.join(TMP_DIR, output_filename)
    
    try:
        # 1. 下载输入文件
        print(f"正在下载文件: {input_file_url}")
        download_success, download_result = download_file(input_file_url, input_file_path)
        if not download_success:
            raise Exception(f"下载文件失败: {download_result}")
        
        # 2. 转换文件
        print(f"开始转换文件: {input_file_path} -> {output_format}")
        convert_manager = ConverterManager()
        success, result_path = convert_manager.convert(input_path=input_file_path, output_path=output_file_path)
        
        if not success:
            raise Exception(f"文件转换失败: {result_path}")
        
        # 验证输出文件
        if not os.path.exists(result_path):
            raise Exception(f"转换成功但输出文件不存在: {result_path}")
        
        # 3. 上传转换结果到R2
        print(f"上传转换结果到R2: {result_path}")
        r2_success, r2_url = upload_file_to_r2(result_path)
        
        if not r2_success:
            raise Exception(f"R2上传失败: {r2_url}")
        
        # 4. 更新任务状态为完成
        update_task_status(task_id, "FINISH", result_url=r2_url)
        print(f"task {task_id} finish，result file: {r2_url}")
    
    except Exception as e:
        # 统一错误处理
        error_msg = f"FAILED: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        update_task_status(task_id, "FAILED", error=error_msg)
    
    finally:
        # 清理临时文件
        for file_path in [input_file_path, output_file_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"已清理临时文件: {file_path}")
                except Exception as e:
                    print(f"清理临时文件失败: {file_path}, 错误: {str(e)}")

def worker_loop():
    """Worker主循环，不断轮询新任务并处理"""
    
    print(f"任务轮询器启动: 连接到API服务器 {API_BASE_URL}")
    print(f"轮询间隔: {POLL_INTERVAL}秒")
    while True:
        try:
            # 获取下一个任务
            task = get_next_task()
            if task:
                task_id = task["id"]
                input_file_url = task["input_file"]  # R2 文件 URL
                output_format = task["output_format"]
                print(f"获取到新任务 {task_id}，开始处理，文件URL: {input_file_url}")
                # 直接处理任务
                process_task(task_id, input_file_url, output_format)
            else:
                # 没有任务，等待一段时间
                # print("没有待处理任务，等待...")
                time.sleep(POLL_INTERVAL)
            # 休眠指定的轮询间隔
        except KeyboardInterrupt:
            print("任务轮询器正在关闭...")
            break
        except Exception as e:
            print(f"轮询循环异常: {str(e)}")
            # 异常时稍微延长休眠时间，避免频繁错误
            time.sleep(POLL_INTERVAL * 2)

if __name__ == "__main__":
    # 直接启动工作循环
    worker_loop() 