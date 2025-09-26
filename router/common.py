#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import APIRouter
from utils.constants import SUPPORTED_FORMATS

router = APIRouter(tags=["通用"])

@router.get("/formats")
async def get_supported_formats():
    """获取支持的格式列表"""
    return {
        "supported_formats": SUPPORTED_FORMATS
    } 