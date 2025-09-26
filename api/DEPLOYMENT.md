# CAD转换服务部署指南

本文档提供了如何使用Docker和GitHub Actions部署CAD转换服务的详细说明。

## 目录结构

```
.
├── Dockerfile          # API服务的Docker镜像构建文件
├── Dockerfile.worker   # Worker服务的Docker镜像构建文件
├── docker-compose.yml  # Docker Compose配置文件
├── env.example         # 环境变量示例文件
└── .github/workflows/  # GitHub Actions工作流配置
    └── cad_converter_deploy.yml  # 自动部署工作流配置
```

## 本地开发部署

### 准备工作

1. 安装Docker和Docker Compose
2. 确保可以访问基础镜像`wyxsg/freecad-python`（Worker服务使用）
3. 复制环境变量示例文件并配置

```bash
cp env.example .env
# 编辑.env文件，填入正确的配置信息
```

### 使用Docker Compose启动服务

```bash
docker-compose up -d
```

这将启动以下服务：
- Redis服务 - 用于任务队列和状态存储
- API服务 - 运行在4586端口
- Worker服务 - 2个实例处理转换任务

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 查看API服务日志
docker-compose logs api

# 查看Worker服务日志
docker-compose logs worker

# 实时跟踪所有服务日志
docker-compose logs -f
```

## 自动部署配置

本项目使用GitHub Actions实现自动化部署。当代码推送到main分支时，会自动触发部署流程。

### 前提条件

在GitHub项目设置中配置以下Secrets：

- `DOCKER_USERNAME`: Docker Hub用户名
- `DOCKER_PASSWORD`: Docker Hub密码
- `SERVER_HOST`: 部署服务器IP地址
- `SERVER_USERNAME`: 服务器SSH用户名 
- `SERVER_SSH_KEY`: 服务器SSH私钥
- `R2_ACCOUNT_ID`: Cloudflare R2账户ID
- `R2_ACCESS_KEY_ID`: R2访问密钥ID
- `R2_SECRET_ACCESS_KEY`: R2访问密钥
- `R2_BUCKET_NAME`: R2存储桶名称
- `R2_PUBLIC_URL`: R2公共访问URL

### 部署流程

1. GitHub Actions工作流检出代码
2. 构建API和Worker Docker镜像并推送到Docker Hub
   - Worker镜像基于`wyxsg/freecad-python`构建
   - Worker使用`python -m dramatiq dr_worker`命令启动
3. 生成.env文件
4. 将配置文件复制到服务器
5. 在服务器上拉取最新镜像并启动服务

### 手动触发部署

可以在GitHub项目的"Actions"选项卡中手动触发部署流程。

## 服务器配置要求

- Docker和Docker Compose
- 足够的磁盘空间存储临时文件
- 开放4586端口（API服务）

## 容器自动重启和容错策略

本项目的所有容器都配置了自动重启策略，具体如下：

1. **所有服务**：使用`restart: unless-stopped`策略，确保容器在崩溃或系统重启后自动重启，除非手动停止。

2. **健康检查**：
   - Redis服务：每10秒执行一次ping命令检查健康状态
   - API服务：每30秒通过HTTP请求检查服务健康状态

3. **Worker服务特殊配置**：
   - 使用`deploy`策略设置更精细的重启参数
   - 在任何故障条件下自动重启
   - 重启之间有5秒延迟
   - 短时间内最多尝试3次重启
   - 使用120秒窗口判断重启是否成功

这些配置确保了即使在面对临时故障时，系统也能快速恢复运行。

## 故障排除

### Worker基础镜像

本项目使用`wyxsg/freecad-python`作为Worker服务的基础镜像。确保：

1. 该镜像在您的环境中可用
2. 该镜像包含运行FreeCAD所需的所有依赖
3. 如需更改基础镜像，可以修改Dockerfile.worker文件中的BASE_IMAGE参数

### 常见问题

1. **服务无法启动**
   - 检查环境变量配置
   - 检查Docker和Docker Compose是否正确安装
   - 查看日志确认错误原因

2. **Worker无法连接到API**
   - 确保API服务已启动
   - 检查网络连接和防火墙设置
   - 验证API_BASE_URL配置是否正确

3. **R2存储问题**
   - 验证R2凭证是否正确
   - 检查存储桶权限设置
   - 查看API和Worker服务日志了解详细错误 