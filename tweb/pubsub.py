import asyncio
import types
from typing import Callable
'''
publish subscribe
usage:
url = 'redis://localhost:6379/0'
cache = Cache(url)

def on_message(message):
    print('got message', message)

class MyPubSub(PublishSubscribe):
    cache = cache

pulgins.register(cache.initialize)
plugins.register(MyPubSub.subscribe, 'mychannel', on_message)
'''


class PublishSubscribe:
    cache = None

    @classmethod
    def publish(cls, channel: str, content: str) -> None:
        return cls.cache.publish(channel, content)

    @classmethod
    async def pubsub_numsub(cls, channel: str) -> int:
        data = await cls.cache.pubsub_numsub(channel)
        if not data:
            return 0
        return int(data[0][-1])

    @classmethod
    async def subscribe(cls,
                        channel: str,
                        callback: Callable,
                        interval: float = 0.01) -> None:
        assert callback, 'callback must be a function'
        if not hasattr(cls.cache, 'ping'):
            await asyncio.sleep(0.2)
        pubsub = cls.cache.pubsub(ignore_subscribe_messages=False)
        assert pubsub.subscribed is False
        await pubsub.subscribe(channel)
        while True:
            message = await pubsub.get_message()
            if message and message['type'] == 'message':
                await cls.reader(callback, message)
            await asyncio.sleep(interval)

    @classmethod
    async def reader(cls, callback: Callable, message: dict) -> None:
        func = callback(message['data'])
        if isinstance(func, types.CoroutineType):
            await func

    @classmethod
    def unsubscribe(cls, channel: str) -> None:
        return cls.cache.unsubscribe(channel)
