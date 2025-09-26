
from fastapi import APIRouter, HTTPException, Form
from urllib.parse import urlparse

from models.schemas import UniResponse,SignResponse
from service.task_manager import create_task
from utils.constants import SUPPORTED_FORMATS
from service.task_manager import *
from datetime import timedelta

router = APIRouter(prefix="/r2", tags=["r2 sign API"])
import boto3
from config import *

s3_client = boto3.client(
    "s3",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    endpoint_url=R2_ENDPOINT_URL,
    region_name="auto",
)

@router.post("/generate-upload-url")
def generate_upload_url(path:str):
    # 生成一个有效期1小时的预签名URL
    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": R2_BUCKET_NAME,
            "Key": path,
            "ContentType": "application/octet-stream",  # 可以根据需要修改前端上传的Content-Type
        },
        ExpiresIn=3600,  # 过期时间
    )
    download_url = f"{R2_PUBLIC_URL}/{path}"
    print("未来下载地址",download_url)
    return UniResponse(
        code=200,
        message="Upload URL has been generated",
        data=SignResponse(
            key=path,
            upload_url=presigned_url,
            download_url=download_url,
        )
    )