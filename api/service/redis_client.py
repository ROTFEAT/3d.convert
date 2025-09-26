import redis
from trimesh.exchange.xyz import export_xyz
import os

redis_pool = redis.ConnectionPool.from_url(
    os.getenv('REDIS_URL', 'redis://:redis123@redis:6379/0'),
    decode_responses=True,
    max_connections=10  # 根据应用负载调整
)

redis_client = redis.Redis(connection_pool=redis_pool)


