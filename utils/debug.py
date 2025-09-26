import os

def print_environment_variables():
    """打印所有环境变量，用于调试"""
    print("=" * 60)
    print("环境变量列表:")
    print("=" * 60)
    
    # 获取所有环境变量并按字母顺序排序
    env_vars = sorted(os.environ.items())
    
    for key, value in env_vars:
        # 对敏感信息进行部分隐藏
        if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
            if value:
                masked_value = value[:3] + "*" * (len(value) - 6) + value[-3:] if len(value) > 6 else "*" * len(value)
                print(f"{key}: {masked_value}")
            else:
                print(f"{key}: (空)")
        else:
            print(f"{key}: {value}")
    
    print("=" * 60)
    print("重要配置变量:")
    print("=" * 60)
    
    # 打印重要的配置变量
    important_vars = [
        'REDIS_HOST', 'REDIS_PORT', 'API_BASE_URL', 'DEPLOYMENT',
        'R2_ACCOUNT_ID', 'R2_BUCKET_NAME', 'R2_PUBLIC_URL',
        'WORKER_ID'
    ]
    
    for var in important_vars:
        value = os.environ.get(var, "未设置")
        if 'SECRET' in var or 'KEY' in var:
            if value and value != "未设置":
                masked_value = value[:3] + "*" * (len(value) - 6) + value[-3:] if len(value) > 6 else "*" * len(value)
                print(f"{var}: {masked_value}")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: {value}")
    
    print("=" * 60) 