import os
import sys
import signal
import psutil


class SignalHandler:
    # cmdline -signal=restart/stop
    signals = {'restart': signal.SIGHUP, 'stop': signal.SIGTERM}

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

    @classmethod
    def signal_handler(cls, pid_file: str, signal_: int) -> bool:
        '''
        Send stop/restart signal to process.

        :param pid_file: `<str>` pid file path, e.g: {project}/server.pid
        :param signal_: `<int>` signal value,
            e.g: signal.SIGINT, signal.SIGHUP, signal.SIGTERM
        :return:
        '''
        if not os.path.exists(pid_file):
            return False
        with open(pid_file, 'r') as f:
            pid = f.readline()
        if not pid or not pid.strip().isdigit():
            return False
        pid = int(pid.strip())
        if not psutil.pid_exists(pid):
            return False
        ps = psutil.Process(pid)
        childrens = ps.children(recursive=True)
        for child in childrens:
            os.kill(child.pid, signal.SIGINT)
        os.kill(pid, signal_)
        return True

    @classmethod
    def restart(cls) -> None:
        '''
        Restart current process.
        '''
        argv = sys.argv
        try:
            os.execv(sys.executable, [sys.executable] + argv)
        except OSError:
            os.spawnv(  # type: ignore
                os.P_NOWAIT, sys.executable, [sys.executable] + argv)
            os._exit(0)
