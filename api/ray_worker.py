
import os
import time
import requests
import shutil
import uuid  # 添加uuid模块用于生成随机文件名
from dotenv import load_dotenv
import traceback
# 加载环境变量
load_dotenv()
# 导入转换函数
# 导入R2上传函数
# API基础URL
from config import *
#本机部署的服务
import  ray
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

def get_batch_task():
    # 获取批量任务
    try:
        pass
    except:
        pass


def update_task_status(task_id, status, result_url=None, error=None):
    """更新任务状态到API服务器"""
    print(f"更新任务{task_id}", status)
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


@ray.remote
def convert_cad(task_id):

    print(f"开始处理任务 {task_id}")
    update_task_status(task_id, "PROCESSING")  # 状态为处理中




if __name__ == "__main__":
    ray.init()



