### Tweb

Tornado、uvloop、aioreids、peewee集成web环境，快速搭建应用开发

------

### 使用

#### 安装和依赖

##### Python版本

​	python3.6 

​	python 3.7

​	python3.8

##### pip安装

```shell
pip install git+https://github.com/marcohong/tweb.git
```

##### packages依赖

| package      | version  | requeired | remark                                           |
| ------------ | -------- | --------- | ------------------------------------------------ |
| configparser | >=5.0.0  | yes       |                                                  |
| tornado      | >=6.0.1  | yes       |                                                  |
| xform        | -        | yes       | 默认安装，使用xform表单验证                      |
| Pillow       | >=7.1.2  | -         | 默认不安装，使用了SourceHanSansSC-Normal.otf字体 |
| uvloop       | >=0.14.0 | -         | 默认安装，如果不存在使用asyncio默认的循环事件    |
| ujson        | >=3.0.0  | -         | 默认不安装，优先使用ujson                        |
| pyjwt        | >=1.7.1  | -         | 默认不安装，引用token模块时需要安装              |
| aredis       | >=1.1.8  | -         | 默认不安装，引用cache/pubsub模块时需要安装       |
| aio-pika     | >=6.7.0  | -         | 默认不安装，引用订阅pubsub模块的rabbitmq需要按照 |
| peewee       | >=3.13.1 | -         | 默认不安装，引用database模块时需要安装           |
| PyMySQL      | >=0.9.3  | -         | 默认不安装，引用database模块时需要安装           |
| psycopg2     | >=2.8.5  | -         | 默认不安装，引用database模块时需要安装           |

#### 创建应用

```python
# main.py
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

# python3 mian.py 默认使用8888端口
# option -c/--conf 选项[dev,local,server]配置文件，默认在main.py同级conf目录下，如果没有启动前默认创建conf/server.conf
# option -p/--port 端口默认8888
# option -d/--daemon 是否后台执行 默认true
# option -debug 是否打开debug 默认false
# option -pid pid输入文件 默认/tmp/web.{port}.pid
# option -proc 默认系统cpu个数，debug模式下proc=1
# option -s/--signal 选择[restart,stop] 重启或停止
# 注意: 命令行参数优先conf参数
```

#### 高级用法

##### 增加自定义命令行

```python
# 请在初始化HttpServer之前引入
from tornado.options import CommandLine
cmdline = CommandLine()
cmdline.add_argument('n','--name', type=str, help='App name')
```

##### 装载handler

```python
from tweb.web import HttpServer
from tweb.router import app
def main():
    server = HttpServer()
    # 相对路径模块
    # app.inject_module('admin.handler','user.handler')
    # or
    # 自动查找，当前打开文件目录下查找
    app.auto_inject()
    server.start()
```

##### 插件初始化

针对async组件可以采取启动后加载

```python
# 文件 app/extensions.py
from tweb.utils.plugins import plugins
from tweb.cache import Cache
# 创建redis连接
center_cache = Cache(conf_prefix='center')
# 注册redis组件
plugins.register(center_cache.initialize)

#文件 main.py
from tweb.web import HttpServer
from tweb.router import app
from app.extensions import plugins
def main():
    server = HttpServer()
    tasks = plugins.loading()
    server.start(tasks=tasks)
```

##### 国际化配置

msgid "Address your visit does not exist"  
msgid "Server to open a small guess"  
msgid "The content submitted is incorrect"  
msgid "Illegal token"  
msgid "Token has expired"  
msgid "Token authentication is successful"  
msgid "Token authentication failure"  
msgid "Login timed out, please log in again"  
msgid "Image format is not supported"  
msgid "Image pixel is too large"  
msgid "Image size is too large"  
msgid "Temporarily not uploading files over %sM"  
msgid "Video format is not supported"  

上述内容默认英文输入，[xform](https://github.com/marcohong/xform)国际化请参考文档

代码配置国际化

```python
# message.po文件详细请参考Python开发文档
# 使用Python的tools目录下msgfmt.py文件生产messages.mo
# python3 msgfmt.py -o messages.mo file1.po file2.po ...

from tweb.web import HttpServer
def main():
    server = HttpServer()
    # 目录
    # /project/locale
    #           en_US/LC_MESSAGES/messages.mo
    #           zh_CN/LC_MESSAGES/messages.mo
    locale_path = '/project/locale'
    server.configure_locale(locale_path)
    server.start()
```

