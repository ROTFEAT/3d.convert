#!/bin/bash

# 启动 FastAPI 应用
echo "Starting FastAPI app..."
nohup python app.py > out.log 2>&1 &

# 启动 Dramatiq worker
echo "Starting Dramatiq worker..."
nohup python -m dramatiq dr_worker > dramatiq.log 2>&1 &

echo "All processes started."
