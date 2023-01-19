import redis
from django.conf import settings


class Client:
    def __init__(
        self,
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PSWD,
        db=1,
    ):
        pools = redis.ConnectionPool(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True,
        )
        self.__redis = redis.StrictRedis(connection_pool=pools)

    def set(self, key, value):
        return self.__redis.set(key, value, ex=settings.verification_code_EXPIRES)

    def get(self, key):
        if self.__redis.exists(key):
            return self.__redis.get(key)
        else:
            return None

    def get_expired(self, key):
        if self.__redis.exists(key):
            return self.__redis.ttl(key)
        else:
            return None

    def delete(self, key):
        return self.__redis.delete(key)


class Queue:
    def __init__(
        self,
        name,
        namespace="queue",
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PSWD,
        db=2,
    ):
        pools = redis.ConnectionPool(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True,
        )
        self.__redis = redis.StrictRedis(connection_pool=pools)
        self.__key = f"{namespace}:{name}"

    def insert(self, value):
        return self.__redis.lpush(self.__key, value)

    def append(self, value):
        return self.__redis.rpush(self.__key, value)

    def get(self):
        return self.__redis.lpop(self.__key)

    def get_wait(self, timeout=None):
        return self.__redis.blpop(self.key, timeout=timeout)

    def size(self):
        return self.__redis.llen(self.__key)

    def clear(self):
        return self.__redis.delete(self.__key)

    def get_all(self):
        return self.__redis.lrange(self.__key, 0, -1)
