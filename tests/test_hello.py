from tweb.web import HttpServer
from tweb.handler import BaseHandler
from tweb.router import router


@router('/hello')
class HelloHandler(BaseHandler):
    async def get(self):
        return self.string('hello')


def main():
    server = HttpServer()
    server.start()


if __name__ == "__main__":
    main()
