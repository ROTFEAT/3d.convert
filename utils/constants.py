#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# 从环境变量获取基础URL
BASE_URL = os.environ.get("HOST_URL", "http://localhost:4586")
if BASE_URL.endswith("/"):
    BASE_URL = BASE_URL[:-1]

# 支持的格式
SUPPORTED_FORMATS = [
    "step", "stp", "iges", "igs", "brep", "brp",  # 标准 CAD 格式
    "stl", "obj", "3mf", "ply",                   # 网格格式
    # "dxf",                                        # 2D 格式
    "gltf", "glb", "x3d"                         # 其他 3D 格式
] 