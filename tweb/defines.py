from tornado.options import define
import tornado.options
# conf options can not delete, see config.py get more information
define('conf',
       default='server',
       type=str,
       help='Read configure for options[dev, local, server]')
define('port', default=0, type=int, help='Run on the given port')
define('daemon', default=None, type=bool, help='Run in daemon')
define('debug', default=None, type=bool, help='Enable debug mode')
define('proc', default=None, type=int, help='Process number, default none')
define('pid', default=None, type=str, help='PID file path')
define('module',
       default=None,
       type=str,
       help='Start module, eg --module=admin or --module=admin,api')


def parse_command():
    tornado.options.parse_command_line()
