import dramatiq
from dramatiq.brokers.redis import RedisBroker
import os

# 创建Redis broker
redis_broker = RedisBroker(url=os.getenv('REDIS_URL', 'redis://:redis123@redis:6379/0'))

# 设置为默认broker
dramatiq.set_broker(redis_broker) 