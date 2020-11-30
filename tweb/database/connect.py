import heapq
from typing import Union
import peewee
import pymysql
import psycopg2
from playhouse.pool import PooledMySQLDatabase, MySQLDatabase, \
    PooledPostgresqlDatabase, PostgresqlDatabase, make_int
from playhouse.db_url import register_database, connect, parse

from tweb.utils.log import logger

# peewee debug code
# import loggerging
# logger = logging.getLogger('peewee')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())
'''
mysql:
    2003 数据库连接不上
    1045 密码错误
'''


def set_session(conn: pymysql.connect) -> None:
    '''
    Set session parameters
    :param conn: `pymysql.connect`
    '''
    cursor = conn.cursor()
    cursor.execute("SET SESSION wait_timeout = 100000;")


class RetryDatabaseMixin:
    def execute_sql(self, sql: str, params: dict = None, commit: bool = True):
        '''
        execute sql

        :return Cursor:
        '''
        try:
            cursor = super().execute_sql(sql, params, commit)
        except (peewee.InterfaceError, peewee.OperationalError):
            conn = self.connection()
            if not self.is_closed():
                if conn:
                    conn.close()
                self._state.set_connection(self._connect())

            cursor = self.cursor(commit)
            cursor.execute(sql, params or ())
            if commit:
                self.commit()
        return cursor

    def _switch_slave(self):
        kwargs = parse(self._slave_url)
        self.database = kwargs.pop('database')
        self.connect_params = kwargs
        logger.error(f'Used slave url conn database[{self._slave_url}]')

    def _is_closed(self, conn) -> bool:
        if not conn:
            return True
        try:
            conn.ping(False)
        except Exception:
            return True
        else:
            return False


class RetryPooledDatabaseMixin:
    def execute_sql(self,
                    sql: str,
                    params: Union[dict, list, tuple] = None,
                    commit: bool = True):
        '''
        execute sql

        :return Cursor:
        '''
        try:
            cursor = super().execute_sql(sql, params, commit)
        except (peewee.InterfaceError, peewee.OperationalError):
            logger.error('Database conn error, try again connect')
            conn = self.connection()
            if self._is_closed(conn):
                self._in_use.pop(self.conn_key(conn), None)
                self._close(conn)
                self._state.set_connection(self._connect())
            logger.error('Connect id: %s' % id(self._state.conn))
            cursor = self.cursor(commit)
            cursor.execute(sql, params or ())
            if commit:
                self.commit()
        return cursor

    def _switch_slave(self):
        kwargs = parse(self._slave_url)
        self._max_connections = make_int(kwargs.pop('max_connections', None))
        self._stale_timeout = make_int(kwargs.pop('stale_timeout', None))
        self._wait_timeout = make_int(kwargs.pop('timeout', None))
        self.database = kwargs.pop('database')
        self.connect_params = kwargs
        self._used_slave = True
        logger.error(f'Used slave url conn database[{self._slave_url}]')

    def _close(self, conn, close_conn=False) -> None:
        key = self.conn_key(conn)
        if close_conn:
            super()._close(conn)
        elif key in self._in_use:
            ts = self._in_use.pop(key)
            if hasattr(self, 'cur_thread_id') and self.cur_thread_id != key:
                self._in_use.pop(self.cur_thread_id, True)
                self.cur_thread_id = None
            if self._stale_timeout and self._is_stale(ts.timestamp):
                logger.debug('Closing stale connection %s.', key)
                super()._close(conn)
            elif self._can_reuse(conn):
                logger.debug('Returning %s to pool.', key)
                heapq.heappush(self._connections, (ts.timestamp, conn))

    def _is_closed(self, conn) -> bool:
        if not conn:
            return True
        try:
            conn.ping(False)
        except Exception:
            return True
        else:
            return False


class RetryMySQLDatabase(RetryDatabaseMixin, MySQLDatabase):
    def __init__(self, database, **kwargs):
        self._slave_url = kwargs.pop('slave_url', None)
        self._used_slave = False
        super(MySQLDatabase, self).__init__(database, **kwargs)

    def _connect(self) -> pymysql.connect:
        try:
            conn = super()._connect()
        except pymysql.err.OperationalError as err:
            if not self._slave_url or self._used_slave or \
                    (err.args and err.args[0] != 2003):
                raise err
            self._switch_slave()
            conn = super()._connect()
        set_session(conn)
        return conn


class RetryPooledMySQLDatabase(RetryPooledDatabaseMixin, PooledMySQLDatabase):
    def __init__(self, database, **kwargs):
        self._slave_url = kwargs.pop('slave_url', None)
        self._used_slave = False
        super(PooledMySQLDatabase, self).__init__(database, **kwargs)

    def _connect(self) -> pymysql.connect:
        try:
            conn = super()._connect()
        except pymysql.err.OperationalError as err:
            if not self._slave_url or self._used_slave or \
                    (err.args and err.args[0] != 2003):
                raise err
            self._switch_slave()
            conn = super()._connect()
        # conn.connect()
        set_session(conn)
        logger.debug('Create new db connect, id: %s' % id(conn))
        self.cur_thread_id = id(conn)
        return conn


class RetryPostgresqlDatabase(RetryDatabaseMixin, PostgresqlDatabase):
    def __init__(self, database, **kwargs):
        self._slave_url = kwargs.pop('slave_url', None)
        self._used_slave = False
        super(PostgresqlDatabase, self).__init__(database, **kwargs)

    def _connect(self) -> psycopg2.connect:
        try:
            conn = super()._connect()
        except psycopg2.OperationalError as err:
            if not self._slave_url or self._used_slave:
                raise err
            self._switch_slave()
            conn = super()._connect()
        return conn


class RetryPooledPostgresqlDatabase(RetryPooledDatabaseMixin,
                                    PooledPostgresqlDatabase):
    def __init__(self, database, **kwargs):
        self._slave_url = kwargs.pop('slave_url', None)
        self._used_slave = False
        super(PooledPostgresqlDatabase, self).__init__(database, **kwargs)

    def _connect(self) -> psycopg2.connect:
        try:
            conn = super()._connect()
        except psycopg2.OperationalError as err:
            if not self._slave_url or self._used_slave:
                raise err
            self._switch_slave()
            conn = super()._connect()
        # conn.connect()
        logger.debug('Create new db connect, id: %s' % id(conn))
        self.cur_thread_id = id(conn)
        return conn


def connection(db_url: str, slave_url: str = None, autocommit: bool = True):
    kwargs = {}
    assert db_url, 'db_url is none, please configure.'
    db_maps = {
        'mysql': RetryMySQLDatabase,
        'mysql+pool': RetryPooledMySQLDatabase,
        'postgre': RetryPostgresqlDatabase,
        'postgre+pool': RetryPooledPostgresqlDatabase,
        'postgresql': RetryPostgresqlDatabase,
        'postgresql+pool': RetryPooledPostgresqlDatabase
    }
    for key, val in db_maps.items():
        register_database(val, key)

    kwargs['autocommit'] = autocommit
    if db_url.startswith('mysql'):
        kwargs['sql_mode'] = 'NO_AUTO_CREATE_USER'
        if slave_url:
            kwargs['slave_url'] = slave_url
    return connect(db_url, **kwargs)
