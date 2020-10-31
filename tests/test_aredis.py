from tweb.web import HttpServer
from tweb.handler import BaseHandler
from tweb.router import router
from tweb.utils.plugins import plugins
from tweb.cache import Cache
from tweb.pubsub import RedisPublishSubscribe

url = 'redis://localhost:6379/0'
cache = Cache(url)
channel = 'test:channel'


class MySubscribe(RedisPublishSubscribe):
    cache = cache


def on_message(message):
    print('got message:', message)


@router('/')
class HelloHandler(BaseHandler):
    async def get(self):
        '''
        curl http://localhost:8888/?value=test
        '''
        val = self.get_argument('value', 'none vlaue')
        await cache.publish(channel, val)
        return self.string('hello')


def main():
    server = HttpServer()
    plugins.register(cache.initialize)
    plugins.register(MySubscribe.subscribe, channel, on_message)
    server.start(tasks=plugins.loading())


if __name__ == "__main__":
    main()
