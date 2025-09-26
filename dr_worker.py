#使用dramatiq

# 添加调试功能
from utils.debug import print_environment_variables
print("=== Worker 服务启动 - 环境变量检查 ===")
print_environment_variables()

from config import *
import dramatiq
from broker import redis_broker  # 导入配置好的broker
import requests
from service.worker import claim_task
from  service.converters.converter_manager import *
from service.worker import update_task_status
from worker import process_task
import time
from dramatiq.middleware import TimeLimitExceeded
# 定义处理失败的回调函数

# 修改原始actor配置，确保超时处理
@dramatiq.actor(time_limit=60000, broker=redis_broker)  # 显式指定broker
def dramatiq_send_convert(task_id, task_info):
    # 检查任务状态
    print("RUN ON", os.getenv("DEPLOYMENT"))
    if not claim_task(task_id):
        print("被抢占 无法执行")
        return
    
    print(f"已声明该任务 {task_id}")
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 设置最大执行时间（比dramatiq的time_limit略小）
        # max_execution_time = 9500  # 毫秒
        
        input_file_url = task_info["input_file"]
        output_format = task_info["output_format"]
        print(f"获取到新任务 {task_id}，开始处理，文件URL: {input_file_url}")
        
        # 处理任务
        process_task(task_id, input_file_url, output_format)

    except TimeLimitExceeded:
        print("任务执行超时")
        update_task_status(task_id=task_id, status="FAILED", error="FAILED because timeout")
    
    except Exception as e:
        # 记录执行时间
        elapsed_time = time.time() - start_time
        error_type = type(e).__name__
        error_message = str(e)
        
        print(f"任务执行异常: {error_type} - {error_message}，已执行{elapsed_time:.2f}秒")
        
        # 将异常信息更新到任务状态
        update_task_status(task_id=task_id, status="FAILED", error=f"{error_type}: {error_message}")
        
        # 重新抛出异常以触发 dramatiq 的失败处理机制
        raise




