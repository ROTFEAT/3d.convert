


import  dramatiq
from dramatiq.brokers.redis import RedisBroker
redis_broker = RedisBroker(url="redis://localhost:6379")
dramatiq.set_broker(redis_broker)

@dramatiq.actor()
def add_two_numbers(a):

    time.sleep(30)
    print(a)
    print("="*20)
    # return a+b


import time

if __name__ == '__main__':
    for i in range(1000):
        add_two_numbers.send(i)
        print("add",i)
        time.sleep(1)
