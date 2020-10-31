import asyncio
import aio_pika
from tweb.web import HttpServer
from tweb.handler import BaseHandler
from tweb.router import router
from tweb.utils.plugins import plugins
from tweb.pubsub import AmqpPublishSubscribe
url = 'amqp://guest:guest@127.0.0.1:5672/'
queue_name = 'test:channel'


class MySubscribe(AmqpPublishSubscribe):
    connection = None

    @classmethod
    async def initialize(cls):
        loop = asyncio.get_event_loop()
        cls.connection = await aio_pika.connect_robust(url, loop=loop)

    @classmethod
    async def output(cls, message):
        print('got message', message)


@router('/')
class HelloHandler(BaseHandler):
    async def get(self):
        '''
        curl http://localhost:8888/?value=test1
        '''
        val = self.get_argument('value', 'none vlaue')
        await MySubscribe.publish(queue_name, val)
        return self.string('hello')


def main():
    server = HttpServer()
    plugins.register(MySubscribe.initialize)
    plugins.register(MySubscribe.subscribe, queue_name, MySubscribe.output)
    server.start(tasks=plugins.loading())


if __name__ == "__main__":
    main()
