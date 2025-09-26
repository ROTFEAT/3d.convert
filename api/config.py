import os
from dotenv import load_dotenv
import  random
import uuid
#环境
load_dotenv()

#目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(PROJECT_ROOT, 'input')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
TMP_DIR = os.path.join(PROJECT_ROOT, 'tmp')

#创建文件夹
directories = ["input", "output", "tmp"]
# 创建这些目录，只在根目录下
for dir_name in directories:
    dir_path = os.path.join(PROJECT_ROOT, dir_name)
    os.makedirs(dir_path, exist_ok=True)

#Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
REDIS_USERNAME = os.environ.get("REDIS_USERNAME", None)
REDIS_TTL = int(os.environ.get("REDIS_TTL", 100))
# R2
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "your-bucket-name")
R2_PUBLIC_URL = os.environ.get("R2_PUBLIC_URL", "")
R2_ENDPOINT_URL = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
# print("R2_PUBLIC_URL",R2_PUBLIC_URL)
# R2_ENDPOINT_URL
#中间节点的api地址
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:4586")
if API_BASE_URL.endswith("/"):
    API_BASE_URL = API_BASE_URL[:-1]
#Worker
WORKER_ID = os.environ.get("WORKER_ID", uuid.uuid4().hex) #WORKER id
POLL_INTERVAL = int(os.environ.get("WORKER_POLL_INTERVAL", "1"))  # 默认5秒轮询一次
MAX_RETRIES = int(os.environ.get("WORKER_MAX_RETRIES", "3"))      # 默认最大重试3次