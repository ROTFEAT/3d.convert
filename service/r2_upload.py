#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import boto3

import mimetypes
import uuid
import requests
from urllib.parse import urlparse



# R2 配置
from config import *

def get_s3_client():
    """创建并返回 S3 客户端（R2 兼容）"""
    # 处理访问密钥格式
    access_key = R2_ACCESS_KEY_ID
    if '-' in access_key and len(access_key) == 35:
        access_key = access_key.split('-', 1)[1]  # 只保留短横线后面的部分
    
    # 使用 Cloudflare R2 标准端点格式
    endpoint_url = f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com'
    
    # 创建 S3 客户端
    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )

def upload_file_to_r2(file_path, object_name=None, folder_prefix=None):
    """
    上传文件到 Cloudflare R2 存储
    
    Args:
        file_path (str): 要上传的本地文件路径
        object_name (str, optional): 存储在 R2 中的对象名称，默认使用文件名
        folder_prefix (str, optional): 存储桶中的文件夹前缀
        
    Returns:
        tuple: (是否成功, 文件URL或错误信息)
    """
    try:
        # 验证文件存在
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"

        # 如果没有指定对象名称，使用文件名
        if object_name is None:
            object_name = os.path.basename(file_path)

        # 如果指定了文件夹前缀，添加到对象名称前
        if folder_prefix:
            if not folder_prefix.endswith('/'):
                folder_prefix += '/'
            object_name = f"{folder_prefix}{object_name}"

        # 生成8位唯一标识符作为前缀
        prefix_id = str(uuid.uuid4())[:8]
        # 添加前缀到文件名
        unique_object_name = f"{prefix_id}_{object_name}"
        
        # 获取文件的 MIME 类型
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'  # 默认 MIME 类型

        print(f"配置信息检查:")
        print(f"存储桶名: {R2_BUCKET_NAME}")
        
        # 使用 Cloudflare R2 标准端点格式
        endpoint_url = f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com'
        print(f"端点 URL: {endpoint_url}")

        # 获取 S3 客户端
        s3_client = get_s3_client()

        # 上传文件
        print(f"正在上传文件 {file_path} 到 R2 存储桶 {R2_BUCKET_NAME}...")
        print(f"使用文件名: {unique_object_name} (添加了8位UUID前缀: {prefix_id})")
        
        s3_client.upload_file(
            file_path, 
            R2_BUCKET_NAME, 
            unique_object_name,
            ExtraArgs={
                'ContentType': content_type
            }
        )

        # 构建文件的公共 URL
        if R2_PUBLIC_URL:
            if R2_PUBLIC_URL.endswith('/'):
                file_url = f"{R2_PUBLIC_URL}{unique_object_name}"
            else:
                file_url = f"{R2_PUBLIC_URL}/{unique_object_name}"
        else:
            # 使用默认的 R2 URL 格式
            file_url = f"https://{R2_BUCKET_NAME}.r2.cloudflarestorage.com/{unique_object_name}"

        print(f"上传成功！文件可访问链接: {file_url}")
        return True, file_url

    except Exception as e:
        error_msg = f"上传文件失败: {str(e)}"
        print(error_msg)
        return False, error_msg

def download_file_from_r2(file_url, output_path=None):
    """
    从 R2 下载文件到本地
    
    Args:
        file_url (str): R2 文件的完整 URL
        output_path (str, optional): 本地保存路径，默认保存到 input 目录
        
    Returns:
        tuple: (是否成功, 本地文件路径或错误信息)
    """
    try:
        # 确保 input 目录存在
        os.makedirs("../input", exist_ok=True)
        
        # 从 URL 中提取对象名
        parsed_url = urlparse(file_url)
        object_key = parsed_url.path.lstrip('/')
        
        # 如果是自定义域名，需要检查并确保取到正确的对象名
        if R2_PUBLIC_URL and R2_PUBLIC_URL in file_url:
            # 从公共 URL 中提取对象键
            object_key = file_url.replace(R2_PUBLIC_URL, '').lstrip('/')
        
        # 如果没有指定输出路径，使用 input 目录和对象名
        if output_path is None:

            output_path = os.path.join("../input", os.path.basename(object_key))
        
        print(f"正在从 R2 下载文件: {object_key} 到 {output_path}")
        
        # 尝试使用 S3 客户端下载
        try:
            s3_client = get_s3_client()
            s3_client.download_file(R2_BUCKET_NAME, object_key, output_path)
            print(f"使用 S3 API 下载成功: {output_path}")
        except Exception as s3_error:
            print(f"S3 API 下载失败: {str(s3_error)}，尝试使用公共 URL 下载...")
            
            # 直接通过 HTTP 请求下载公共 URL
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"通过 HTTP 下载成功: {output_path}")
        
        # 验证文件是否存在
        if not os.path.exists(output_path):
            return False, f"下载似乎成功，但文件未找到: {output_path}"
        
        # 验证文件大小
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            return False, f"下载的文件为空: {output_path}"
        
        print(f"文件下载成功，大小: {file_size} 字节")
        return True, output_path
        
    except Exception as e:
        error_msg = f"下载文件失败: {str(e)}"
        print(error_msg)
        return False, error_msg

def upload_output_file(output_filename):
    """
    上传转换后的输出文件到 R2 存储
    
    Args:
        output_filename (str): 输出文件名（位于 output 目录）
        
    Returns:
        tuple: (是否成功, 文件URL或错误信息)
    """
    # 构建完整的文件路径
    file_path = os.path.join("../output", output_filename)
    
    # 上传到 R2 存储桶的 'converted' 文件夹
    return upload_file_to_r2(file_path, folder_prefix="converted")


# 示例使用
if __name__ == "__main__":
    # 上传测试
    file_to_upload = "../output/biasda.igs"  # 替换为实际文件路径
    success, result = upload_file_to_r2(file_to_upload)
    
    if success:
        print(f"文件上传成功: {result}")
        
        # 下载测试
        download_success, download_path = download_file_from_r2(result)
        if download_success:
            print(f"文件下载成功: {download_path}")
        else:
            print(f"文件下载失败: {download_path}")
    else:
        print(f"文件上传失败: {result}") 