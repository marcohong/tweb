import asyncio
import types
from functools import partial
from typing import Callable, Any
try:
    import aio_pika
except ImportError:
    aio_pika = None


class PublishSubscribe:
    @classmethod
    async def prepare(cls, *args: Any, **kwargs: Any) -> None:
        pass

    @classmethod
    async def publish(cls, channel: str, content: str) -> None:
        raise NotImplementedError

    @classmethod
    async def subscribe(cls,
                        channel: str,
                        callback: Callable,
                        interval: float = 0.01) -> None:
        raise NotImplementedError

    @classmethod
    async def on_message(cls, message: Any) -> None:
        pass

    @classmethod
    async def unsubscribe(cls, channel: str) -> None:
        raise NotImplementedError


class RedisPublishSubscribe(PublishSubscribe):
    '''
    redis pubsub

    usage:

    url = 'redis://localhost:6379/0'
    cache = Cache(url)

    def handler_message(message):
        print('got message', message)

    class MyPubSub(RedisPublishSubscribe):
        cache = cache

    pulgins.register(cache.initialize)
    plugins.register(MyPubSub.subscribe, 'mychannel', handler_message)
    '''
    cache = None

    @classmethod
    async def prepare(cls, *args: Any, **kwargs: Any) -> None:
        retry = kwargs.get('retry', 3)
        while retry:
            if not cls.cache or hasattr(cls.cache, 'ping'):
                await asyncio.sleep(0.2)
            else:
                break
            retry -= 1

    @classmethod
    def publish(cls, channel: str, content: str) -> None:
        return cls.cache.publish(channel, content)

    @classmethod
    async def subscribe(cls,
                        channel: str,
                        callback: Callable,
                        interval: float = 0.01) -> None:
        await cls.prepare()
        assert callback, 'callback must be a function'
        pubsub = cls.cache.pubsub(ignore_subscribe_messages=False)
        assert pubsub.subscribed is False
        await pubsub.subscribe(channel)
        while True:
            message = await pubsub.get_message()
            if message and message['type'] == 'message':
                await cls.on_message(callback, message)
            await asyncio.sleep(interval)

    @classmethod
    async def on_message(cls, callback: Callable, message: dict) -> None:
        func = callback(message['data'])
        if isinstance(func, types.CoroutineType):
            await func

    @classmethod
    def unsubscribe(cls, channel: str) -> None:
        return cls.cache.unsubscribe(channel)


class AmqpPublishSubscribe(PublishSubscribe):
    '''
    rabbitmq pubsub

    usage::

    url = 'amqp://guest:guest@127.0.0.1:5672/'
    queue_name = 'test:channel'

    class MySubscribe(AmqpPublishSubscribe):
        @classmethod
        async def initialize(cls):
            loop = asyncio.get_event_loop()
            cls.connection = await aio_pika.connect_robust(url, loop=loop)

        @classmethod
        async def output(cls, message):
            print('got message', message)

    plugins.register(MySubscribe.initialize)
    plugins.register(MySubscribe.subscribe, queue_name, MySubscribe.output)
    '''
    connection = None
    channel = None

    @classmethod
    async def prepare(cls, *args: Any, **kwargs: Any) -> None:
        retry = kwargs.get('retry', 3)
        while retry:
            if not cls.connection:
                await asyncio.sleep(0.2)
            else:
                break
            retry -= 1
        cls.channel = await cls.connection.channel()
        await cls.channel.set_qos(
            prefetch_count=kwargs.get('prefetch_count', 100))

    @classmethod
    def publish(cls, channel: str, content: str) -> None:
        return cls.channel.default_exchange.publish(
            aio_pika.Message(body=content.encode('utf-8')),
            routing_key=channel)

    @classmethod
    async def subscribe(cls, channel: str, callback: Callable) -> None:
        await cls.prepare()
        queue = await cls.channel.declare_queue(channel)
        func = partial(cls.on_message, callback)
        await queue.consume(func)

    @classmethod
    async def on_message(cls, callback: Callable,
                         message: 'aio_pika.IncomingMessage') -> None:
        async with message.process():
            func = callback(message.body.decode('utf-8'))
            if isinstance(func, types.CoroutineType):
                await func

    @classmethod
    async def unsubscribe(cls, channel: str) -> None:
        queue = await cls.get_queue(channel)
        await queue.cancel()
