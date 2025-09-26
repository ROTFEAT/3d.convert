#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
import hashlib
import random
import string

def add_random_prefix(file_path):
    # 获取目录和文件名
    directory, filename = os.path.split(file_path)

    # 随机生成4个字符
    prefix = ''.join(random.choices(string.ascii_letters + string.digits, k=4))

    # 构造新文件名
    new_filename = prefix + "_" + filename
    new_path = os.path.join(directory, new_filename)

    # 重命名文件
    os.rename(file_path, new_path)

    return new_path
def generate_unique_filename(original_filename):
    """
    在原始文件名中添加哈希值以确保唯一性
    保持文件扩展名不变
    """
    # 生成8位哈希值
    hash_id = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:8]
    
    # 分离文件名和扩展名
    name, ext = os.path.splitext(original_filename)
    
    # 创建新文件名：原名_哈希值.扩展名
    return f"{name}_{hash_id}{ext}" 