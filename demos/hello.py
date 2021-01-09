from tweb.web import HttpServer
from tweb.handler import BaseHandler
from tweb.router import router
from xform.form import SubmitForm
from xform import fields


@router('/', '/index', '/hello')
class HelloHandler(BaseHandler):
    async def get(self):
        return self.string('hello')


@router('/login')
class LoginHandler(BaseHandler):
    form = SubmitForm(
        username=fields.Username(required=True),
        password=fields.Password(required=True)
    )

    async def post(self):
        data = await self.form_validate(self.form)
        return self.success(data=data)


def main():
    server = HttpServer()
    server.start()


if __name__ == "__main__":
    main()
