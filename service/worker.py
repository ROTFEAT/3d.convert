import os

import requests
from config import  API_BASE_URL
from service.task_manager import redis_client
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

# Lua脚本：如果任务处于队列状态则置为处理中
CLAIM_TASK_SCRIPT = """
local task_key = KEYS[1]
local current_status = redis.call('HGET', task_key, 'status')
if current_status == 'QUEUED' then
    redis.call('HSET', task_key, 'status', 'PROCESSING')
    return 1
else
    return 0
end
"""

def claim_task_with_lua(task_id):
    """
    使用Lua脚本原子性地检查并更新任务状态
    如果任务处于队列状态，则置为处理中并返回True
    否则返回False
    """
    task_key = f"task:{task_id}"
    result = redis_client.eval(CLAIM_TASK_SCRIPT, 1, task_key)
    return result == 1

def claim_task(task_id):
    if os.getenv("DEPLOYMENT")=="CLOUD":
        return claim_task_with_lua(task_id) #直接本地就redis抢占了
    else:
        res = requests.get(
            f"{API_BASE_URL}/worker/claim/{task_id}",
        )
        if res.status_code == 200:
            return True
        else:
            return False



if __name__ == "__main__":
    print(claim_task_with_lua("1747281355-1-b5e4830d"))
