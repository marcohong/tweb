import signal


class SignalHandler:
    @classmethod
    def listen(cls, callback: callable) -> None:
        '''Listen system signal.

        signal.SIGKILL kill -9信号,捕获不了,强制终止进程
        signal.SIGINT 键盘中 Ctrl-C 组合键信号
        signal.SIGHUP nohup 守护进程发出的关闭信号
        signal.SIGTERM 命令行数据 kill pid 时的信号

        usage::

            def callback(signalnum, frame):
                # coding...

            SignalHandler.listen(callback)

        :param callback: `<callable>`> func(signalnum, frame)
        :return:
        '''
        for sig in [signal.SIGINT, signal.SIGHUP, signal.SIGTERM]:
            signal.signal(sig, callback)
